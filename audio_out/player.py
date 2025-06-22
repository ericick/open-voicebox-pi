import subprocess
from utils.logger import logger

def play_audio(file_path, volume=None, device=None):
    try:
        logger.debug(f"准备播放音频: {file_path}")
        subprocess.run(['mpg123', '-q', file_path])
        logger.info(f"播放音频完成: {file_path}")
    except Exception as e:
        logger.error(f"播放失败: {e}")
