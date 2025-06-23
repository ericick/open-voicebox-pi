import subprocess
from utils.logger import logger

def play_audio(file_path, volume=None, device="plughw:3,0"):
    try:
        logger.debug(f"准备播放音频: {file_path}")
        cmd = ['mpg123', '-q', '-a', device, file_path]
        subprocess.run(cmd)
        logger.info(f"播放音频完成: {file_path}")
    except Exception as e:
        logger.error(f"播放失败: {e}")
