import time
from utils.logger import logger

def retry(max_attempts=3, wait=2, exceptions=(Exception,), msg="自动重试"):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    logger.error(f"{msg}，第{attempt+1}次失败: {e}")
                    if attempt < max_attempts - 1:
                        time.sleep(wait)
            raise e
        return wrapper
    return decorator
