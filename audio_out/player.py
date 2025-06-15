from playsound import playsound
from utils.logger import logger

def play_audio(file_path):
    try:
        playsound(file_path)
        logger.info(f"播放音频: {file_path}")
    except Exception as e:
        logger.error(f"播放失败: {e}")
