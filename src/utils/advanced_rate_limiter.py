"""
advanced_rate_limiter.py: Advanced rate limiting utility for Hyperliquid API requests.
"""
import time
import random
import logging
from typing import Optional, Callable, Dict, Any

def log_message(msg: str, level: int = logging.INFO) -> None:
    """
    Log a message with the specified logging level.
    Args:
        msg (str): The message to log.
        level (int): The logging level.
    """
    logging.log(level, msg)

class AdvancedRateLimiter:
    """
    Implements an advanced rate limiter for Hyperliquid API requests, supporting dynamic limits from response headers.
    """
    def __init__(self, max_requests: int, period: float) -> None:
        self.max_requests: int = max_requests
        self.period: float = period
        self.requests: int = 0
        self.start_time: float = time.time()

    def wait(self, response_headers: Optional[Dict[str, Any]] = None, on_rate_limit: Optional[Callable[[], None]] = None) -> None:
        """
        Wait if the rate limit would be exceeded, supporting dynamic limits from response headers.
        Args:
            response_headers (Optional[Dict[str, Any]]): Headers with rate limit info.
            on_rate_limit (Optional[Callable]): Callback if rate limit is hit.
        """
        current_time = time.time()
        elapsed_time = current_time - self.start_time

        if response_headers:
            self.max_requests = int(response_headers.get('X-RateLimit-Limit', self.max_requests))
            reset_time = int(response_headers.get('X-RateLimit-Reset', self.start_time + self.period))
            self.period = reset_time - self.start_time

        if elapsed_time > self.period:
            self.requests = 0
            self.start_time = current_time

        if self.requests >= self.max_requests:
            sleep_time = self.period - elapsed_time
            log_message(f"Advanced Rate limit exceeded. Sleeping for {sleep_time} seconds...", level=logging.WARNING)
            if on_rate_limit:
                on_rate_limit()  # e.g., rotate proxy
            time.sleep(sleep_time)
            self.requests = 0
            self.start_time = time.time()

        self.requests += 1

    def is_rate_limit_exceeded(self) -> bool:
        """
        Check if the rate limit has been exceeded.
        Returns:
            bool: True if rate limit is exceeded, False otherwise.
        """
        current_time = time.time()
        elapsed_time = current_time - self.start_time
        return self.requests >= self.max_requests and elapsed_time <= self.period
