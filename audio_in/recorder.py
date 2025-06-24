import sounddevice as sd
import numpy as np
import os
from utils.logger import logger
from datetime import datetime


class Recorder:
    def __init__(self, samplerate=16000, channels=6, dtype='int16', block_size=1280, max_record_time=15, save_pcm=True, pcm_save_dir="audio_out", device=0):
        self.samplerate = samplerate
        self.channels = channels
        self.dtype = dtype
        self.block_size = block_size  # 1280 samples @16kHz = 40ms
        self.max_record_time =  max_record_time
        self.save_pcm =  save_pcm
        self.pcm_save_dir =  pcm_save_dir
        self.device = device

    def record_stream(self, max_record_time=15):
        total_samples = int(self.samplerate * max_record_time)
        stream = sd.InputStream(samplerate=self.samplerate, channels=self.channels, dtype=self.dtype, blocksize=self.block_size, device=self.device)
        print("开始流式录音，请说话...")
        all_bytes = b""
        with stream:
            for _ in range(total_samples // self.block_size):
                block, _ = stream.read(self.block_size)
                logger.debug(f"第{i}帧录音, block形状: {block.shape}")
                all_bytes += block.tobytes()
                yield block.tobytes()
        if save_pcm:
            os.makedirs(pcm_save_dir, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            pcm_path = os.path.join(pcm_save_dir, f"stream_record_{ts}.pcm")
            with open(pcm_save_dir, "wb") as f:
                f.write(all_bytes)
            logger.info(f"流式录音PCM已保存: {pcm_path}，总长度: {len(all_bytes)} 字节")
        else:
            logger.debug("未保存流式录音到本地PCM文件。")
        

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
