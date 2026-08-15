import os
import queue
import sys
import time
import threading

import numpy as np
import sherpa_onnx
import sounddevice as sd

from utils.logger import logger
from utils.audio_device import find_input_device, refresh_audio_devices, wait_for_input_device

RESTART_LIMIT = 3


def _self_restart():
    """原地重启进程（PID 不变），重新加载音频引擎；带次数上限防循环。"""
    count = int(os.environ.get("VOICEBOX_RESTART_COUNT", "0")) + 1
    os.environ["VOICEBOX_RESTART_COUNT"] = str(count)
    if count > RESTART_LIMIT:
        logger.warning("已达到自动重启上限，转入安静等待。")
        return False
    logger.warning(f"连续打开失败，自动重启程序以重新加载音频引擎（第{count}次）...")
    script = os.path.abspath(sys.argv[0])
    if not os.path.exists(script):
        script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "main.py")
    os.execv(sys.executable, [sys.executable, script])
    return True


class WakewordDetector:
    """基于 sherpa-onnx 的离线中文唤醒词检测（替换原 Porcupine 实现）。"""

    def __init__(
        self,
        model_dir,
        keywords_file,
        audio_device_index=None,
        channels=4,
        keywords_score=1.0,
        keywords_threshold=0.25,
        num_threads=2,
        sample_rate=16000,
        feature_dim=80,
    ):
        self.model_dir = model_dir
        self.keywords_file = keywords_file
        self.audio_device_index = audio_device_index
        self.channels = channels
        self.sample_rate = sample_rate

        encoder = os.path.join(model_dir, "encoder-epoch-13-avg-2-chunk-16-left-64.onnx")
        decoder = os.path.join(model_dir, "decoder-epoch-13-avg-2-chunk-16-left-64.onnx")
        joiner = os.path.join(model_dir, "joiner-epoch-13-avg-2-chunk-16-left-64.onnx")
        tokens = os.path.join(model_dir, "tokens.txt")

        self.kws = sherpa_onnx.KeywordSpotter(
            tokens=tokens,
            encoder=encoder,
            decoder=decoder,
            joiner=joiner,
            keywords_file=keywords_file,
            num_threads=num_threads,
            keywords_score=keywords_score,
            keywords_threshold=keywords_threshold,
            provider="cpu",
        )

    def start(self, callback):
        """持续监听麦克风，检测到唤醒词后释放资源并回调。
        麦克风未接入、中途断线或静默拔线时自动等待并重连，不再崩溃退出。"""
        logger.info("唤醒词检测已启动，等待麦克风...")
        consecutive_failures = 0
        try:
            while True:
                device_id = wait_for_input_device(self.audio_device_index)
                keyword = None
                stream = self.kws.create_stream()
                stop_monitor = threading.Event()
                dead_event = threading.Event()
                monitor = None
                try:
                    audio_queue = queue.Queue(maxsize=100)

                    def audio_callback(indata, frames, time_info, status):
                        if dead_event.is_set():
                            raise sd.CallbackAbort
                        try:
                            audio_queue.put_nowait(indata.copy())
                        except queue.Full:
                            pass

                    with sd.InputStream(
                        samplerate=self.sample_rate,
                        channels=self.channels,
                        dtype="int16",
                        blocksize=1600,
                        device=device_id,
                        callback=audio_callback,
                    ) as mic:
                        consecutive_failures = 0
                        os.environ["VOICEBOX_RESTART_COUNT"] = "0"
                        logger.info("唤醒词检测已启动，等待唤醒...")
                        monitor = threading.Thread(
                            target=self._monitor_device,
                            args=(mic, stop_monitor, dead_event),
                            daemon=True,
                        )
                        monitor.start()
                        while True:
                            try:
                                pcm = audio_queue.get(timeout=0.5)
                            except queue.Empty:
                                if dead_event.is_set():
                                    logger.warning("检测到麦克风设备异常，退出当前监听流，等待重新接入...")
                                    break
                                continue
                            mono = np.ascontiguousarray(pcm[:, 0])
                            samples = mono.astype(np.float32) / 32768.0
                            stream.accept_waveform(self.sample_rate, samples)
                            if self.kws.is_ready(stream):
                                self.kws.decode_stream(stream)
                                keyword = self.kws.get_result(stream)
                                if keyword:
                                    logger.info(f"检测到唤醒词: {keyword}")
                                    self.kws.reset_stream(stream)
                                    break
                except Exception as e:
                    consecutive_failures += 1
                    if consecutive_failures == 1 or consecutive_failures % 12 == 0:
                        logger.warning(f"麦克风打开失败：{e}，等待重新接入...")
                finally:
                    stop_monitor.set()
                    dead_event.set()
                    if monitor is not None:
                        monitor.join(timeout=1.0)
                if keyword:
                    break
                # 连续失败：每约12秒刷新一次设备列表（清除幽灵条目）；约1分钟后仍不行则自动重启兜底
                if consecutive_failures and consecutive_failures % 4 == 0:
                    refresh_audio_devices()
                if consecutive_failures and consecutive_failures % 20 == 0:
                    if _self_restart():
                        return
                time.sleep(3)
        except KeyboardInterrupt:
            logger.info("唤醒词检测终止。")
        # 资源释放后再回调
        callback()

    def _monitor_device(self, mic, stop_event, dead_event, interval=3.0, probe_interval=30.0):
        """后台监视麦克风是否仍在线；发现异常则设置 dead_event，让读取循环干净退出。"""
        probe_fail_count = 0
        last_probe = time.monotonic()
        while not stop_event.is_set():
            if find_input_device(self.audio_device_index) is None:
                logger.warning("检测到麦克风断开，准备重新接入...")
                dead_event.set()
                return
            try:
                if not mic.active:
                    logger.warning("检测到麦克风流已停止，准备重新接入...")
                    dead_event.set()
                    return
            except Exception:
                pass
            # 定期主动探测设备健康（应对 macOS 静默拔线：不报错、列表不更新、流不停止）
            if time.monotonic() - last_probe >= probe_interval:
                last_probe = time.monotonic()
                if self._probe_input_device():
                    probe_fail_count = 0
                else:
                    probe_fail_count += 1
                    if probe_fail_count >= 2:
                        logger.warning("检测到麦克风设备异常（连续探测失败），准备重新接入...")
                        dead_event.set()
                        return
            stop_event.wait(timeout=interval)

    def _probe_input_device(self):
        """尝试在目标麦克风上打开并读取一小段音频，验证设备当前是否可用。"""
        try:
            device_id = find_input_device(self.audio_device_index)
            if device_id is None:
                return False
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype="int16",
                blocksize=320,
                device=device_id,
            ) as probe:
                probe.read(320)
            return True
        except Exception:
            return False
