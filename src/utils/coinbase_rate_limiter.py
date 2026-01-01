"""
coinbase_rate_limiter.py: Rate limiting utility for Coinbase REST API requests.
"""
import time
import logging
from typing import Optional, Callable

def log_message(msg: str, level: int = logging.INFO) -> None:
    logging.log(level, msg)

class CoinbaseRateLimiter:
    """
    Implements a rate limiter for Coinbase REST API requests.
    Default: 3 requests/sec, burst up to 6/sec, 10,000/hour.
    """
    def __init__(self, max_requests: int = 3, period: float = 1.0, burst: int = 6, hourly_limit: int = 10000):
        self.max_requests = max_requests
        self.period = period
        self.burst = burst
        self.hourly_limit = hourly_limit
        self.requests = 0
        self.start_time = time.time()
        self.hourly_requests = 0
        self.hour_start_time = time.time()

    def wait(self, on_rate_limit: Optional[Callable[[], None]] = None) -> None:
        current_time = time.time()
        elapsed_time = current_time - self.start_time
        hour_elapsed = current_time - self.hour_start_time

        # Reset per-second window
        if elapsed_time > self.period:
            self.requests = 0
            self.start_time = current_time
        # Reset per-hour window
        if hour_elapsed > 3600:
            self.hourly_requests = 0
            self.hour_start_time = current_time

        # Check hourly limit
        if self.hourly_requests >= self.hourly_limit:
            sleep_time = 3600 - hour_elapsed
            log_message(f"Coinbase hourly rate limit exceeded. Sleeping for {sleep_time:.2f} seconds...", level=logging.WARNING)
            if on_rate_limit:
                on_rate_limit()
            time.sleep(sleep_time)
            self.hourly_requests = 0
            self.hour_start_time = time.time()

        # Check per-second limit
        if self.requests >= self.max_requests:
            sleep_time = self.period - elapsed_time
            if sleep_time < 0:
                sleep_time = 0.1
            log_message(f"Coinbase per-second rate limit exceeded. Sleeping for {sleep_time:.2f} seconds...", level=logging.WARNING)
            if on_rate_limit:
                on_rate_limit()
            time.sleep(sleep_time)
            self.requests = 0
            self.start_time = time.time()

        self.requests += 1
        self.hourly_requests += 1

    def is_rate_limit_exceeded(self) -> bool:
        return self.requests >= self.max_requests or self.hourly_requests >= self.hourly_limit
