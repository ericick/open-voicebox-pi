import subprocess
import sounddevice as sd
import numpy as np
import threading
from utils.logger import logger

_audio_play_lock = threading.Lock()  # 新增：全局锁

def play_audio(file_path, volume=None, device="plughw:3,0"):
    with _audio_play_lock:
        try:
            logger.debug(f"准备播放音频: {file_path}")
            cmd = ['mpg123', '-q', '-a', device, file_path]
            subprocess.run(cmd)
            logger.info(f"播放音频完成: {file_path}")
        except Exception as e:
            logger.error(f"播放失败: {e}")

def play_audio_stream(audio_generator, samplerate=16000, channels=1, dtype='int16', device=2):
    with _audio_play_lock:
        try:
            logger.info("流式播放音频启动...")
            with sd.OutputStream(samplerate=samplerate, channels=channels, dtype=dtype, device=device) as stream:
                for audio_chunk in audio_generator:
                    block = np.frombuffer(audio_chunk, dtype=dtype)
                    if channels > 1:
                        block = block.reshape(-1, channels)
                    stream.write(block)
            logger.info("流式音频播放结束。")
        except Exception as e:
            logger.error(f"流式播放失败: {e}")
