import sounddevice as sd
import numpy as np
import queue
from utils.logger import logger

class Recorder:
    def __init__(self, samplerate=16000, channels=1, max_sec=8, silence_sec=1.0, silence_threshold=400):
        self.samplerate = samplerate
        self.channels = channels
        self.max_sec = max_sec
        self.silence_sec = silence_sec
        self.silence_threshold = silence_threshold
        self.audio_q = queue.Queue()

    def _callback(self, indata, frames, time, status):
        self.audio_q.put(indata.copy())

    def record(self):
        logger.info("开始录音，说话吧！（最长{}秒）".format(self.max_sec))
        audio_buffer = []
        try:
            with sd.InputStream(samplerate=self.samplerate, channels=self.channels, dtype='int16', callback=self._callback):
                silence_count = 0
                for _ in range(int(self.samplerate / 1024 * self.max_sec)):
                    try:
                        data = self.audio_q.get(timeout=1.0)
                        audio_buffer.append(data)
                        if np.abs(data).mean() < self.silence_threshold:
                            silence_count += 1
                            if silence_count >= (self.samplerate / 1024 * self.silence_sec):
                                logger.info("检测到静音，自动停止录音。")
                                break
                        else:
                            silence_count = 0
                    except queue.Empty:
                        logger.warning("未检测到语音输入，录音自动终止。")
                        break
            if not audio_buffer:
                logger.warning("未录到有效语音。")
                return None
            audio_data = np.concatenate(audio_buffer, axis=0)
            return audio_data.flatten()
        except Exception as e:
            logger.error(f"录音设备异常：{e}")
            return None
