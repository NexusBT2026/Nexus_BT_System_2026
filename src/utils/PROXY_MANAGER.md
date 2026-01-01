# ProxyManager Utility Module

## Purpose
- Provides robust, thread-safe proxy management for HTTP(S) requests.
- Supports proxy rotation, error tracking, and performance metrics.
- Used by all network modules that require proxy support.

## Key Features
- Loads proxies from CSV files or environment variables.
- Scrapes new proxies from public sources if needed.
- Tracks proxy performance and errors, removes bad proxies automatically.
- Integrates with `requests` and other HTTP clients.

## Usage Example
```python
from utils.proxy_manager import ProxyManager

pm = ProxyManager()
session = pm.get_session_with_proxy()
response = session.get('https://api.example.com/data')
```

## Best Practices
- Keep proxy lists up to date and monitor error logs.
- Use the `report_error` and `report_success` methods to maintain proxy health.
- Only one instance of `proxy_manager.py` should exist in the modular project.

## File Location
- `src/utils/proxy_manager.py`
