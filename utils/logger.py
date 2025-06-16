from loguru import logger
import os

LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR, exist_ok=True)

# 日志文件按天轮转，保留30天
logger.remove()
logger.add(lambda msg: print(msg, end=""), level="INFO", colorize=True)
logger.add(
    f"{LOG_DIR}/ai_speaker_{{time:YYYY-MM-DD}}.log",
    rotation="00:00",
    retention="30 days",
    level="DEBUG",
    encoding="utf-8",
    enqueue=True,
    backtrace=True,
    diagnose=True
)
