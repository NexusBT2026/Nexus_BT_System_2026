"""
retry.py: Retry and backoff logic for API/network calls in Hyperliquid integration.
Enhanced with structured logging for retry attempts and errors.
"""
import time
import functools
from typing import Callable, Any, Type, Tuple
from .logging_utils import setup_logger

logger = setup_logger('hyperliquid_retry', json_logs=True)

def retry_on_exception(
    retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[BaseException], ...] = (Exception,)
) -> Callable:
    """
    Decorator to retry a function on specified exceptions with exponential backoff and structured logging.

    Args:
        retries (int): Number of retry attempts before giving up.
        delay (float): Initial delay between retries in seconds.
        backoff (float): Multiplier applied to delay after each failure.
        exceptions (Tuple[Type[BaseException], ...]): Exception types to catch and retry on.

    Returns:
        Callable: Decorated function with retry logic.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            _retries, _delay = retries, delay
            while _retries > 0:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    logger.warning(
                        'Retrying after exception',
                        extra={
                            "event": "retry_attempt",
                            "function": func.__name__,
                            "exception": str(e),
                            "retries_left": _retries - 1,
                            "next_delay": _delay
                        }
                    )
                    _retries -= 1
                    if _retries == 0:
                        logger.error(
                            'All retries exhausted',
                            extra={
                                "event": "retry_exhausted",
                                "function": func.__name__,
                                "exception": str(e)
                            }
                        )
                        raise
                    time.sleep(_delay)
                    _delay *= backoff
        return wrapper
    return decorator
