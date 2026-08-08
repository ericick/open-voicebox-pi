import sounddevice as sd
import numpy as np
import time
from utils.logger import logger
import audio_out.player as player

class Recorder:
    def __init__(self, samplerate=16000, channels=4, dtype='int16', block_size=1280, max_record_time=15, silence_threshold=2000, silence_duration=2.0, device=None):
        self.samplerate = samplerate
        self.channels = channels
        self.dtype = dtype
        self.block_size = block_size  # 1280 samples @16kHz = 40ms
        self.max_record_time =  max_record_time
        self.silence_threshold = silence_threshold
        self.silence_duration = silence_duration
        self.device = device

    def record_stream(self, max_wait_s=15.0):
        """
        流式录音：打开麦克风后先等待用户开口，开口后才开始有效录音。
        - 开口前持续发送静音帧，保持 ASR 连接不断
        - 开口需连续两帧超过阈值（约150ms），避免误触发
        - 开口后静音 silence_duration 秒自动停止
        - 等 max_wait_s 秒无人说话则放弃本轮
        """
        player.wait_until_idle(timeout_s=10)
        time.sleep(0.3)  # 播放结束后留一点回响消散时间
        silence_chunk = int(self.samplerate * self.silence_duration)
        max_total = int(self.samplerate * self.max_record_time)
        max_wait = int(self.samplerate * max_wait_s)

        state = {
            "speech_started": False,
            "onset_count": 0,
            "silence_count": 0,
            "waited": 0,
            "total": 0,
        }

        def gen():
            with sd.InputStream(
                samplerate=self.samplerate,
                channels=self.channels,
                dtype=self.dtype,
                blocksize=self.block_size,
                device=self.device,
            ) as stream:
                logger.info("开始流式录音，请说话...")
                while True:
                    block, _ = stream.read(self.block_size)
                    mono = block[:, 0] if self.channels > 1 else block
                    level = np.abs(mono).mean()

                    if not state["speech_started"]:
                        # 等待用户开口
                        if level >= self.silence_threshold:
                            state["onset_count"] += 1
                            if state["onset_count"] >= 2:
                                state["speech_started"] = True
                                state["silence_count"] = 0
                                logger.debug("检测到用户开口，开始有效录音。")
                        else:
                            state["onset_count"] = 0
                            state["waited"] += len(mono)
                            if state["waited"] >= max_wait:
                                logger.info("等待用户说话超时，结束本轮。")
                                return
                        # 开口前也发送音频（静音帧），保持 ASR 连接
                        yield mono.tobytes()
                        continue

                    # 已开口：正常录音，静音自动停止
                    yield mono.tobytes()
                    state["total"] += len(mono)
                    if state["total"] >= max_total:
                        logger.info("达到最长录音时间，自动停止。")
                        break
                    if level < self.silence_threshold:
                        state["silence_count"] += len(mono)
                        if state["silence_count"] >= silence_chunk:
                            logger.info("检测到静音，自动停止流式录音。")
                            break
                    else:
                        state["silence_count"] = 0

        return gen()

    def record(self, max_record_time=15, silence_threshold=500, silence_duration=1.0):
        """
        常规录音，录完返回整个音频（numpy数组），支持自动静音停止。
        """
        total_samples = int(self.samplerate * max_record_time)
        buffer = []
        stream = sd.InputStream(samplerate=self.samplerate, channels=self.channels, dtype=self.dtype)
        silence_chunk = int(self.samplerate * silence_duration)
        last_audio = np.zeros(silence_chunk, dtype=self.dtype)
        silence_count = 0
        print("开始录音，请说话...")

        with stream:
            for _ in range(total_samples // self.block_size):
                block, _ = stream.read(self.block_size)
                block = block.flatten()
                buffer.append(block)
                # 判断静音
                if np.abs(block).mean() < silence_threshold:
                    silence_count += len(block)
                    if silence_count >= silence_chunk:
                        print("检测到静音，自动停止录音。")
                        break
                else:
                    silence_count = 0
        audio = np.concatenate(buffer)
        return audio
