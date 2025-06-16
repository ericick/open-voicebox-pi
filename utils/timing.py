import time
from functools import wraps
from utils.logger import logger

def timing(tag):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            t0 = time.perf_counter()
            result = func(*args, **kwargs)
            t1 = time.perf_counter()
            logger.info(f"{tag}耗时: {t1-t0:.3f}s")
            return result
        return wrapper
    return decorator
