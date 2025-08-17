import sounddevice as sd
import numpy as np
import time
from utils.logger import logger
import audio_out.player as player

class Recorder:
    def __init__(self, samplerate=16000, channels=6, dtype='int16', block_size=1280, max_record_time=15, device=1):
        self.samplerate = samplerate
        self.channels = channels
        self.dtype = dtype
        self.block_size = block_size  # 1280 samples @16kHz = 40ms
        self.max_record_time =  max_record_time
        self.device = device

    def record_stream(self, max_record_time=15, silence_threshold=500, silence_duration=2.0):
        player.wait_until_idle(timeout_s=10)
        total_samples = int(self.samplerate * max_record_time)
        silence_chunk = int(self.samplerate * silence_duration)
        silence_count = 0
    
        stream = sd.InputStream(
            samplerate=self.samplerate,
            channels=self.channels,
            dtype=self.dtype,
            blocksize=self.block_size,
            device=self.device
        )
        logger.info("开始流式录音，请说话...")
        with stream:
            for i in range(total_samples // self.block_size):
                block, _ = stream.read(self.block_size)
                logger.debug(f"第{i}帧录音, block形状: {block.shape}")
                mono_block = block[:, 0] if self.channels > 1 else block
                yield mono_block.tobytes()
                # === 新增静音检测 ===
                if np.abs(mono_block).mean() < silence_threshold:
                    silence_count += len(mono_block)
                    if silence_count >= silence_chunk:
                        logger.info("检测到静音，自动停止流式录音。")
                        break
                else:
                    silence_count = 0

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
