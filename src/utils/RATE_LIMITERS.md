# Rate Limiter Utilities

## Overview
This folder contains modular, reusable rate limiter classes for robust API usage in trading bots.

### Files:
- `advanced_rate_limiter.py`: Specialized rate limiter for HyperLiquid, with progressive backoff and optional response header parsing.
- `phemex_rate_limiter.py`: Specialized rate limiter for Phemex, with per-symbol throttling and a hook for proxy rotation.

## Usage Example
```python
from utils.phemex_rate_limiter import PhemexRateLimiter
from utils.proxy_manager import ProxyManager

rate_limiter = PhemexRateLimiter(max_requests=120, period=60)
proxy_manager = ProxyManager()

def rotate_proxy():
    session = proxy_manager.get_session_with_proxy()
    # Use new session for next request

# Before each API call:
rate_limiter.wait(symbol='BTCUSDT', on_rate_limit=rotate_proxy)
```

## Best Practices
- Always use a rate limiter for all API calls, even with proxies.
- Use the `on_rate_limit` callback to rotate proxies if you hit a rate limit.
- Monitor logs for warnings about rate limits and adjust parameters as needed.

---

**Note:**
- Proxy rotation only helps with IP-based limits. Account/API key limits still apply.
- Tune `max_requests` and `period` to match the exchange's published limits.
