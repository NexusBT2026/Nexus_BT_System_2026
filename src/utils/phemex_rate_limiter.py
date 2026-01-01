"""
phemex_rate_limiter.py: Rate limiting utility for Phemex API requests.
"""
import time
import random
import logging
from typing import Optional, Callable, Dict
from src.exchange.logging_utils import setup_logger
#from src.exchange.retry import retry_on_exception

logger = setup_logger('phemex_rate_limiter', json_logs=True)

def log_message(msg: str, level: int = logging.INFO, extra: Optional[dict] = None) -> None:
    logger.log(level, msg, extra=extra or {})

class PhemexRateLimiter:
    """
    Implements a rate limiter for Phemex API requests, supporting per-symbol and global limits.
    """
    def __init__(self, max_requests: int, period: float) -> None:
        self.max_requests: int = max_requests
        self.period: float = period
        self.requests: int = 0
        self.start_time: float = time.time()
        self.last_call_times: Dict[str, float] = {}  # Track per-symbol call times

    def wait(self, weight: int = 1, symbol: Optional[str] = None, on_rate_limit: Optional[Callable[[], None]] = None) -> None:
        """
        Wait if the rate limit would be exceeded, supporting per-symbol and global limits.
        Args:
            weight (int): The weight of the request.
            symbol (Optional[str]): Symbol for per-symbol rate limiting.
            on_rate_limit (Optional[Callable]): Callback if rate limit is hit.
        """
        current_time = time.time()
        elapsed_time = current_time - self.start_time

        # If a symbol is provided, check if we need additional delay for this symbol
        if symbol:
            last_call = self.last_call_times.get(symbol, 0)
            symbol_elapsed = current_time - last_call
            min_symbol_interval = 3.0
            if symbol_elapsed < min_symbol_interval:
                sleep_time = min_symbol_interval - symbol_elapsed + (random.random() * 0.5)
                log_message(f"Symbol-specific rate limit for {symbol}, sleeping {sleep_time:.2f}s", level=logging.INFO)
                time.sleep(sleep_time)
            self.last_call_times[symbol] = time.time()

        if elapsed_time > self.period:
            self.requests = 0
            self.start_time = current_time

        if self.requests + weight > self.max_requests:
            sleep_time = self.period - elapsed_time
            if sleep_time <= 0:
                sleep_time = 1.0
            log_message(f"Phemex Rate limit exceeded. Sleeping for {sleep_time:.2f} seconds...", level=logging.WARNING)
            if on_rate_limit:
                on_rate_limit()  # e.g., rotate proxy
            time.sleep(sleep_time)
            self.requests = 0
            self.start_time = time.time()

        self.requests += weight

    def is_rate_limit_exceeded(self) -> bool:
        """
        Check if the rate limit has been exceeded.
        Returns:
            bool: True if rate limit is exceeded, False otherwise.
        """
        current_time = time.time()
        elapsed_time = current_time - self.start_time
        return self.requests >= self.max_requests and elapsed_time <= self.period
