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

def play_audio_stream(audio_generator, device=2, samplerate=44100, channels=2, dtype='int16'):
    with _audio_play_lock:
        try:
            logger.info("流式播放音频启动...")
            with sd.OutputStream(samplerate=samplerate, channels=channels, dtype=dtype, device=device) as stream:
                for audio_chunk in audio_generator:
                    # 假设音频帧为16kHz单声道PCM
                    block = np.frombuffer(audio_chunk, dtype=dtype)
                    # 升采样到44.1k
                    target_len = int(len(block) * 44100 / 16000)
                    xp = np.linspace(0, len(block)-1, target_len)
                    x = np.arange(len(block))
                    upsampled = np.interp(xp, x, block).astype(np.int16)
                    # 扩展为双声道
                    stereo = np.stack([upsampled, upsampled], axis=-1)
                    stream.write(stereo)
            logger.info("流式音频播放结束。")
        except Exception as e:
            logger.error(f"流式播放失败: {e}")
