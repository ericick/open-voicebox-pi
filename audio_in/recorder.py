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
        with sd.InputStream(samplerate=self.samplerate, channels=self.channels, dtype='int16', callback=self._callback):
            silence_count = 0
            for _ in range(int(self.samplerate / 1024 * self.max_sec)):
                data = self.audio_q.get()
                audio_buffer.append(data)
                # 检测静音
                if np.abs(data).mean() < self.silence_threshold:
                    silence_count += 1
                    if silence_count >= (self.samplerate / 1024 * self.silence_sec):
                        logger.info("检测到静音，自动停止录音。")
                        break
                else:
                    silence_count = 0
        audio_data = np.concatenate(audio_buffer, axis=0)
        return audio_data.flatten()
