import subprocess
import sounddevice as sd
import numpy as np
from utils.logger import logger

def play_audio(file_path, volume=None, device="plughw:3,0"):
    """播放本地音频文件（mp3/wav）"""
    try:
        logger.debug(f"准备播放音频: {file_path}")
        cmd = ['mpg123', '-q', '-a', device, file_path]
        subprocess.run(cmd)
        logger.info(f"播放音频完成: {file_path}")
    except Exception as e:
        logger.error(f"播放失败: {e}")

def play_audio_stream(audio_generator, samplerate=16000, channels=1, dtype='int16', device=None):
    """
    audio_generator: 生成器或可迭代，每次yield一帧PCM音频（bytes）
    """
    try:
        logger.info("流式播放音频启动...")
        # 打开输出流，实时写入音频块
        with sd.OutputStream(samplerate=samplerate, channels=channels, dtype=dtype, device=device) as stream:
            for audio_chunk in audio_generator:
                block = np.frombuffer(audio_chunk, dtype=dtype)
                if channels > 1:
                    block = block.reshape(-1, channels)
                stream.write(block)
        logger.info("流式音频播放结束。")
    except Exception as e:
        logger.error(f"流式播放失败: {e}")
