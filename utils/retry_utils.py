import time
from functools import wraps
from utils.logger import logger

def retry(max_attempts=3, wait=2, exceptions=(Exception,), msg="重试中..."):
    """
    通用自动重试装饰器，适用于网络/IO操作。
    :param max_attempts: 最大重试次数
    :param wait: 重试等待时间（秒）
    :param exceptions: 捕获的异常类型
    :param msg: 重试时的日志信息
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    logger.warning(f"{msg} 第{attempt}次: {e}")
                    if attempt == max_attempts:
                        logger.error(f"已重试{max_attempts}次，仍然失败，抛出异常。")
                        raise
                    time.sleep(wait)
        return wrapper
    return decorator
