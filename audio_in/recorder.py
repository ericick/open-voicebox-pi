import sounddevice as sd
import numpy as np
import queue
import threading
import os
from utils.logger import logger

class Recorder:
    def __init__(self,
                 samplerate=16000,
                 channels=1,
                 dtype='int16',
                 device=None,
                 max_record_time=15,
                 silence_threshold=500,    # 按样本幅度
                 silence_duration=1.0,     # 静音超过x秒自动停止
                 save_dir=None):
        self.samplerate = samplerate
        self.channels = channels
        self.dtype = dtype
        self.device = device
        self.max_record_time = max_record_time
        self.silence_threshold = silence_threshold
        self.silence_duration = silence_duration
        self.save_dir = save_dir
        if self.save_dir and not os.path.isdir(self.save_dir):
            os.makedirs(self.save_dir, exist_ok=True)

    def record(self, save_to_file=False, file_prefix="recorded"):
        logger.info("开始录音...")
        q = queue.Queue()
        is_recording = threading.Event()
        is_recording.set()
        frames = []
        last_non_silence = 0
        silence_samples = int(self.samplerate * self.silence_duration)

        def callback(indata, frames_count, time_info, status):
            if status:
                logger.warning(f"录音状态异常: {status}")
            q.put(indata.copy())

        try:
            with sd.InputStream(samplerate=self.samplerate,
                                channels=self.channels,
                                dtype=self.dtype,
                                callback=callback,
                                device=self.device):
                n_samples = 0
                silent_samples = 0
                while is_recording.is_set():
                    try:
                        indata = q.get(timeout=0.5)
                    except queue.Empty:
                        continue
                    frames.append(indata)
                    n_samples += len(indata)
                    # 静音检测
                    if np.abs(indata).max() > self.silence_threshold:
                        silent_samples = 0
                    else:
                        silent_samples += len(indata)
                    # 检查静音持续时间
                    if silent_samples >= silence_samples and n_samples > silence_samples:
                        logger.info("检测到长时间静音，自动停止录音。")
                        is_recording.clear()
                    # 最长录音时长
                    if n_samples / self.samplerate >= self.max_record_time:
                        logger.info("录音达到最大时长，自动停止。")
                        is_recording.clear()
            # 录音完成
            audio = np.concatenate(frames, axis=0)
            logger.info(f"录音结束，共采集{len(audio)}帧。")
            # 可选保存
            file_path = None
            if save_to_file and self.save_dir:
                import soundfile as sf
                file_path = os.path.join(self.save_dir, f"{file_prefix}_{int(time.time())}.wav")
                sf.write(file_path, audio, self.samplerate)
                logger.info(f"录音音频已保存: {file_path}")
            return audio if not save_to_file else (audio, file_path)
        except Exception as e:
            logger.error(f"录音异常: {e}")
            return None
