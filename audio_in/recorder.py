import sounddevice as sd
import numpy as np


class Recorder:
    def __init__(self, samplerate=16000, channels=1, dtype='int16', block_size=1280):
        self.samplerate = samplerate
        self.channels = channels
        self.dtype = dtype
        self.block_size = block_size  # 1280 samples @16kHz = 40ms

    def record_stream(self, max_record_time=15):
        total_samples = int(self.samplerate * max_record_time)
        stream = sd.InputStream(samplerate=self.samplerate, channels=self.channels, dtype=self.dtype, blocksize=self.block_size)
        print("开始流式录音，请说话...")
        with stream:
            for _ in range(total_samples // self.block_size):
                block, _ = stream.read(self.block_size)
                with open("debug_audio.pcm", "ab") as f:
                    f.write(block.tobytes())
                yield block.tobytes()

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
