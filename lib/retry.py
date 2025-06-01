import asyncio
import functools
from simple_logger import Logger
import time
from lib.config import Config

conf=Config()
log=Logger()

def retry_async(
    max_retries: int = conf.NEXTCLOUD_MAX_RETRIES,
    base_delay: float = conf.NEXTCLOUD_RETRY_DELAY,
    exceptions: tuple = (Exception,),
    backoff: float = conf.NEXTCLOUD_BACKOFF
):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    log.warning(f"[Retry-Async] Attempt {attempt + 1}/{max_retries} failed for {func}: {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(base_delay * (backoff ** attempt))
                    else:
                        log.error(f"[Retry-Async] Gave up {func} after {max_retries} attempts.")
                        raise
        return wrapper
    return decorator

def retry_sync(
    max_retries: int = 3,
    base_delay: float = 1.0,
    exceptions: tuple = (Exception,),
    backoff: float = 2.0
):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    log.warning(f"[Retry-Sync] Attempt {attempt + 1}/{max_retries} failed for {func}: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(base_delay * (backoff ** attempt))
                    else:
                        log.error(f"[Retry-Sync] Gave up {func} after {max_retries} attempts.")
                        raise
        return wrapper
    return decorator