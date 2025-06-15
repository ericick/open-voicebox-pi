from loguru import logger
import sys

def setup_logger():
    logger.remove()
    logger.add(sys.stdout, level="INFO", format="<green>{time}</green> <level>{message}</level>")
    logger.add("logs/voice_assistant.log", rotation="1 MB", retention="7 days")
    return logger

logger = setup_logger()
