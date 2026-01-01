"""
proxy_manager.py: Proxy management and rotation utilities for trading bots.
"""

import requests
from requests.adapters import HTTPAdapter
import random
import time
import logging
import threading
import csv
import os.path
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Optional, Dict, Any
from src.exchange.retry import retry_on_exception
import http.server
import socketserver
from threading import Thread

class ProxyManager:
    """
    Manages a pool of HTTP/SOCKS proxies for use with trading APIs.
    Handles loading, testing, refreshing, and selecting proxies based on performance and error metrics.
    Thread-safe for concurrent use.
    """

    def __init__(self, min_proxies: int = 10, refresh_interval: int = 600, revalidate_interval: int = 300) -> None:
        self.proxies: List[str] = []
        self.working_proxies: List[str] = []
        self.last_refresh: float = 0
        self.refresh_interval: int = refresh_interval  # Refresh every 10 minutes
        self.min_proxies: int = min_proxies
        self.lock = threading.Lock()
        self.current_index: int = 0
        
        # New attributes for performance tracking
        self.proxy_performance: Dict[str, float] = {}  # Track response times
        self.proxy_errors: Dict[str, int] = {}         # Track error counts
        self.last_used: Dict[str, float] = {}          # Track when each proxy was last used
        self.last_success: Dict[str, float] = {}       # Track last successful validation time
        self.revalidate_interval: int = revalidate_interval  # How often to revalidate proxies (seconds)
        self._stop_revalidate = threading.Event()
        self._revalidate_thread = threading.Thread(target=self._revalidate_proxies_loop, daemon=True)
        self._revalidate_thread.start()
        
        # Proxy usage, success, and failure analytics
        self.proxy_usage: Dict[str, int] = {}  # Track how many times each proxy is used
        self.proxy_successes: Dict[str, int] = {}  # Track successful uses
        self.proxy_failures: Dict[str, int] = {}  # Track failures
        
        # Exchange-specific proxy segmentation
        self.exchange_segments: Dict[str, List[str]] = {}  # exchange_name -> proxy_list
        self.exchange_indexes: Dict[str, int] = {}  # exchange_name -> current_index
        self.exchange_registry: Dict[str, str] = {}  # exchange_id -> segment_name
        self.alert_webhook_url = os.environ.get('SLACK_WEBHOOK_URL')  # For alerting
        
        # Try to load from saved files first
        self.load_saved_proxies()

    def load_saved_proxies(self) -> None:
        """
        Load proxies from saved CSV files (HTTP and SOCKS4) in outputs/ directory.
        If files don't exist, generate them first using ProxyGenerator.
        Populates self.working_proxies if enough proxies are found.
        """
        # Use the comprehensive working proxy list first
        http_file_all = 'outputs/http_proxies_all_working.csv'
        http_file = 'outputs/http_proxies.csv'
        socks4_file = 'outputs/socks4_proxies.csv'
        
        # Check if comprehensive proxy file exists first
        if not os.path.exists(http_file_all) and not os.path.exists(http_file) and not os.path.exists(socks4_file):
            logging.warning("⚠️ Proxy CSV files not found! Run proxy_scheduler.py to generate them.")
            logging.warning("   For now, continuing with no proxies (will use direct connections)")
            self.working_proxies = []
            return
        
        loaded_proxies = []
        
        # Load HTTP proxies - prioritize the comprehensive list
        proxy_file_to_use = http_file_all if os.path.exists(http_file_all) else http_file
        
        if os.path.exists(proxy_file_to_use):
            try:
                with open(proxy_file_to_use, 'r') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if row and len(row) > 0:
                            proxy = row[0].strip()
                            if proxy and proxy.startswith('http'):
                                loaded_proxies.append(proxy)
                logging.info(f"Loaded {len(loaded_proxies)} HTTP proxies from {proxy_file_to_use}")
            except Exception as e:
                logging.error(f"Error loading HTTP proxies from {proxy_file_to_use}: {e}")
        
        # Load SOCKS4 proxies
        socks_loaded = []
        if os.path.exists(socks4_file):
            try:
                with open(socks4_file, 'r') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if row and len(row) > 0:
                            proxy = row[0].strip()
                            if proxy and proxy.startswith('socks4'):
                                socks_loaded.append(proxy)
                                loaded_proxies.append(proxy)
                logging.info(f"Loaded {len(socks_loaded)} SOCKS4 proxies from file")
            except Exception as e:
                logging.error(f"Error loading SOCKS4 proxies: {e}")
        
        # If we loaded enough proxies, use them as working proxies
        if len(loaded_proxies) >= self.min_proxies:
            self.working_proxies = loaded_proxies
            self.last_refresh = time.time()
            logging.info(f"Using {len(self.working_proxies)} pre-saved working proxies")
        else:
            logging.warning(f"Only loaded {len(loaded_proxies)} proxies, need {self.min_proxies} minimum")
        
    @retry_on_exception()
    def get_proxies_from_free_proxy_list(self) -> List[str]:
        """
        Fetch proxies from a public GitHub proxy list.
        Returns a list of proxy URLs.
        """
        logging.info("Fetching new proxies from TheSpeedX/PROXY-List (GitHub)")
        try:
            response = requests.get('https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt', timeout=15)
            response.raise_for_status()
            lines = response.text.strip().splitlines()
            proxy_list = [f"http://{line.strip()}" for line in lines if line.strip()]
            logging.info(f"Found {len(proxy_list)} proxies from GitHub list")
            return proxy_list
        except Exception as e:
            logging.error(f"Error fetching proxies from GitHub list: {e}")
            return []
            
    @retry_on_exception()
    def test_proxy(self, proxy: str) -> bool:
        """
        Test if a proxy works with the HyperLiquid API.
        Returns True if successful, False otherwise.
        """
        try:
            proxies = {
                'http': proxy,
                'https': proxy,
            }
            start_time = time.time()
            response = requests.get('https://api.hyperliquid.xyz/info', proxies=proxies, timeout=8)
            elapsed = time.time() - start_time
            if response.status_code == 200:
                self.proxy_performance[proxy] = elapsed
                self.last_success[proxy] = time.time()  # Update last successful validation
                logging.debug(f"Proxy {proxy} is working with HyperLiquid (response time: {elapsed:.2f}s)")
                return True
            else:
                logging.debug(f"Proxy {proxy} returned status {response.status_code}")
                return False
        except Exception as e:
            logging.debug(f"Proxy {proxy} failed: {e}")
            return False
            
    def refresh_proxies(self) -> None:
        """
        Refresh the proxy list if needed (time-based or not enough working proxies).
        Loads from file or scrapes new proxies and tests them.
        """
        current_time = time.time()
        
        with self.lock:
            # Check if we need to refresh (time-based or not enough working proxies)
            if (current_time - self.last_refresh > self.refresh_interval or 
                len(self.working_proxies) < self.min_proxies):
                
                # First try to use any saved proxies we have from the files
                if not self.working_proxies:
                    self.load_saved_proxies()
                
                # If we still don't have enough, get new proxies
                if len(self.working_proxies) < self.min_proxies:
                    new_proxies = self.get_proxies_from_free_proxy_list()
                    self.proxies = new_proxies
                    
                    # Test the proxies in parallel
                    working_proxies = list(self.working_proxies)  # Start with existing working proxies
                    for proxy in self.proxies:
                        if self.test_proxy(proxy):
                            working_proxies.append(proxy)
                            
                            # If we have enough working proxies, stop testing
                            if len(working_proxies) >= self.min_proxies * 2:
                                break
                                
                    self.working_proxies = working_proxies
                    
                self.last_refresh = current_time
                
                logging.info(f"Refreshed proxies. Found {len(self.working_proxies)} working proxies")
                
    def get_proxy_country(self, proxy: str, cache: Dict[str, str] = {}) -> Optional[str]:
        """
        Lookup the country for a proxy using a public GeoIP API. Caches results for efficiency.
        Returns ISO country code or None if unavailable.
        """
        # Extract IP from proxy string
        import re
        match = re.search(r'([\d.]+):\d+', proxy)
        if not match:
            return None
        ip = match.group(1)
        if ip in cache:
            return cache[ip]
        try:
            resp = requests.get(f'http://ip-api.com/json/{ip}?fields=countryCode', timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                country = data.get('countryCode')
                if country:
                    cache[ip] = country
                    return country
        except Exception as e:
            logging.debug(f"GeoIP lookup failed for {ip}: {e}")
        return None

    def filter_proxies(self, proxies: List[str], country: Optional[str] = None, max_latency: Optional[float] = None, proxy_type: Optional[str] = None) -> List[str]:
        """
        Filter proxies by country, latency, and type (http, socks4, socks5).
        - country: ISO country code (requires proxy format with country info, or extend to use external geoip lookup)
        - max_latency: Only include proxies with measured latency below this threshold
        - proxy_type: 'http', 'socks4', or 'socks5'. If None, defaults to 'http' (https).
        """
        # Default to http/https proxies only unless explicitly overridden
        if proxy_type is None:
            proxy_type = 'http'
        filtered = []
        geoip_cache = {}
        for proxy in proxies:
            # Filter by type
            if proxy_type:
                if proxy_type == 'http' and not proxy.startswith('http'):
                    continue
                if proxy_type == 'socks4' and not proxy.startswith('socks4'):
                    continue
                if proxy_type == 'socks5' and not proxy.startswith('socks5'):
                    continue
            # Filter by latency
            if max_latency is not None and proxy in self.proxy_performance:
                if self.proxy_performance[proxy] > max_latency:
                    continue
            # Filter by country (now with GeoIP lookup)
            if country:
                # Example: if proxy string contains country code, e.g. 'http://xx.xx.xx.xx:port|US'
                if '|' in proxy:
                    parts = proxy.split('|')
                    if len(parts) > 1 and parts[1].upper() != country.upper():
                        continue
                else:
                    # Use GeoIP lookup if no country info
                    proxy_country = self.get_proxy_country(proxy, cache=geoip_cache)
                    if not proxy_country or proxy_country.upper() != country.upper():
                        continue
            filtered.append(proxy)
        return filtered

    def send_alert(self, message: str):
        """
        Send an alert via Slack webhook or log if not configured.
        """
        if self.alert_webhook_url:
            try:
                import json
                requests.post(self.alert_webhook_url, json={"text": message}, timeout=5)
            except Exception as e:
                logging.error(f"Failed to send alert: {e}")
        else:
            logging.warning(f"ALERT: {message}")

    def get_best_proxy_from_list(self, candidates: List[str]) -> Optional[str]:
        """
        Select the best proxy from a filtered list, using performance, error metrics, and data freshness (last successful use and last_success).
        """
        if not candidates:
            self.send_alert("No proxies available for selection!")
            return None
        current_time = time.time()
        # Prefer proxies with low errors, not recently used, and recently validated
        filtered = [p for p in candidates if self.proxy_errors.get(p, 0) < 3 and current_time - self.last_used.get(p, 0) > 10 and current_time - self.last_success.get(p, 0) < self.revalidate_interval * 2]
        if not filtered:
            filtered = candidates
        proxies_with_perf = [p for p in filtered if p in self.proxy_performance]
        if proxies_with_perf:
            # Sort by latency, then by most recent last_success (freshness)
            sorted_proxies = sorted(
                proxies_with_perf,
                key=lambda x: (self.proxy_performance.get(x, float('inf')), -self.last_success.get(x, 0))
            )
            proxy = sorted_proxies[0]
            self.last_used[proxy] = current_time
            self.proxy_usage[proxy] = self.proxy_usage.get(proxy, 0) + 1
            return proxy
        # Fallback: random
        proxy = random.choice(filtered)
        self.last_used[proxy] = current_time
        self.proxy_usage[proxy] = self.proxy_usage.get(proxy, 0) + 1
        return proxy

    def report_error(self, proxy: str) -> None:
        """
        Report an error with a proxy, incrementing its error count and removing if too many errors.
        """
        if proxy and proxy in self.working_proxies:
            with self.lock:
                # Increment error count
                self.proxy_errors[proxy] = self.proxy_errors.get(proxy, 0) + 1
                self.proxy_failures[proxy] = self.proxy_failures.get(proxy, 0) + 1
                
                # If too many errors, remove from working proxies
                if self.proxy_errors[proxy] >= 5:
                    if proxy in self.working_proxies:
                        self.working_proxies.remove(proxy)
                    self.send_alert(f"Removed proxy {proxy} due to too many errors")

    def report_success(self, proxy: str, response_time: float) -> None:
        """
        Report a successful request with a proxy, updating performance and resetting error count.
        """
        if proxy and proxy in self.working_proxies:
            with self.lock:
                # Update performance metrics
                self.proxy_performance[proxy] = response_time
                # Reset error count
                self.proxy_errors[proxy] = 0
                self.proxy_successes[proxy] = self.proxy_successes.get(proxy, 0) + 1

    def check_proxy_health_and_alert(self):
        """
        Check proxy pool health and send alerts if all proxies are down or error rates are high.
        Call this periodically from your health monitor.
        """
        with self.lock:
            if not self.working_proxies:
                self.send_alert("All proxies are down! No working proxies available.")
            elif sum(self.proxy_errors.values()) > len(self.working_proxies) * 3:
                self.send_alert("High proxy error rate detected!")

    def _revalidate_proxies_loop(self):
        """
        Background thread to periodically re-test all working proxies and update their health/freshness.
        """
        while not self._stop_revalidate.is_set():
            time.sleep(self.revalidate_interval)
            with self.lock:
                proxies_to_check = list(self.working_proxies)
            for proxy in proxies_to_check:
                if self.test_proxy(proxy):
                    self.last_success[proxy] = time.time()
                # If test_proxy fails, error count is incremented as usual

    def stop_revalidation(self):
        """
        Stop the background revalidation thread (for clean shutdown).
        """
        self._stop_revalidate.set()
        self._revalidate_thread.join()

    def get_proxy(self, country: Optional[str] = None, max_latency: Optional[float] = None, proxy_type: Optional[str] = None, exclude: Optional[List[str]] = None) -> Optional[str]:
        """
        Select and return a proxy from the working pool, with optional filtering and exclusion.
        """
        with self.lock:
            candidates = self.filter_proxies(self.working_proxies, country=country, max_latency=max_latency, proxy_type=proxy_type)
            if exclude:
                candidates = [p for p in candidates if p not in exclude]
            return self.get_best_proxy_from_list(candidates)

    def get_session_with_proxy(self, country: Optional[str] = None, max_latency: Optional[float] = None, proxy_type: Optional[str] = None, exclude: Optional[List[str]] = None) -> requests.Session:
        """
        Get a requests.Session with a proxy configured, with advanced filtering.
        Defaults to https proxies and lowest latency/freshest.
        """
        # Default to https proxies
        if proxy_type is None:
            proxy_type = 'http'
        proxy = self.get_proxy(country=country, max_latency=max_latency, proxy_type=proxy_type, exclude=exclude)
        if not proxy:
            return requests.Session()
        session = requests.Session()
        session.proxies = {
            'http': proxy,
            'https': proxy
        }
        adapter = HTTPAdapter(
            pool_connections=5,
            pool_maxsize=10,
            max_retries=3
        )
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session

    def register_exchange(self, exchange_id: str, segment_preference: Optional[str] = None, min_proxies: int = 3) -> str:
        """
        Register an exchange and assign it a dedicated proxy segment.
        
        Args:
            exchange_id: Unique identifier for the exchange instance
            segment_preference: Preferred segment name (e.g., 'phemex', 'coinbase', 'hyperliquid')
            min_proxies: Minimum proxies needed for this exchange
        
        Returns:
            The assigned segment name
        """
        import random
        
        with self.lock:
            # If preference specified and segment exists with enough proxies, use it
            if segment_preference and segment_preference in self.exchange_segments:
                if len(self.exchange_segments[segment_preference]) >= min_proxies:
                    self.exchange_registry[exchange_id] = segment_preference
                    logging.info(f"✅ Assigned {exchange_id} to existing segment: {segment_preference}")
                    return segment_preference
            
            # Create new segment or find available one
            segment_name = segment_preference or f"exchange_{len(self.exchange_segments)}"
            
            # Ensure we have enough total proxies
            required_total = sum(len(seg) for seg in self.exchange_segments.values()) + min_proxies
            if len(self.working_proxies) < required_total:
                logging.warning(f"⚠️ May need more proxies. Have: {len(self.working_proxies)}, Need: {required_total}")
                self.refresh_proxies()
            
            # Get unused proxies
            used_proxies = set()
            for seg_proxies in self.exchange_segments.values():
                used_proxies.update(seg_proxies)
            
            available_proxies = [p for p in self.working_proxies if p not in used_proxies]
            
            if len(available_proxies) >= min_proxies:
                # Randomly select proxies to avoid clustering at beginning
                segment_proxies = random.sample(available_proxies, min_proxies)
                self.exchange_segments[segment_name] = segment_proxies
                self.exchange_indexes[segment_name] = 0
                self.exchange_registry[exchange_id] = segment_name
                logging.info(f"✅ Created segment '{segment_name}' for {exchange_id} with {len(segment_proxies)} proxies")
            else:
                # Redistribute existing proxies if needed
                self._redistribute_exchange_proxies()
                self.exchange_registry[exchange_id] = segment_name
                logging.warning(f"⚠️ Had to redistribute proxies for {exchange_id}")
            
            return segment_name
    
    def get_proxy_for_exchange(self, exchange_id: str) -> Optional[str]:
        """
        Get the next proxy for a specific exchange from its assigned segment.
        """
        with self.lock:
            if exchange_id not in self.exchange_registry:
                logging.error(f"❌ Exchange {exchange_id} not registered. Call register_exchange() first.")
                return self.get_proxy()  # Fall back to regular proxy
                
            segment_name = self.exchange_registry[exchange_id]
            if segment_name not in self.exchange_segments or not self.exchange_segments[segment_name]:
                logging.warning(f"⚠️ No proxies in segment {segment_name} for {exchange_id}")
                return self.get_proxy()  # Fall back to regular proxy
            
            # Round-robin within the segment
            segment_proxies = self.exchange_segments[segment_name]
            current_index = self.exchange_indexes[segment_name]
            proxy = segment_proxies[current_index]
            
            # Advance to next proxy in segment
            self.exchange_indexes[segment_name] = (current_index + 1) % len(segment_proxies)
            
            logging.debug(f"🔄 {exchange_id} using proxy {current_index + 1}/{len(segment_proxies)}: {proxy}")
            return proxy
    
    def get_session_for_exchange(self, exchange_id: str):
        """Get a requests session with dedicated proxy for specific exchange"""
        proxy = self.get_proxy_for_exchange(exchange_id)
        if not proxy:
            return self.get_session_with_proxy()
        
        import requests
        from requests.adapters import HTTPAdapter
        
        session = requests.Session()
        session.proxies = {'http': proxy, 'https': proxy}
        adapter = HTTPAdapter(pool_connections=5, pool_maxsize=10, max_retries=3)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session
    
    def _redistribute_exchange_proxies(self):
        """Redistribute proxies evenly across all exchange segments"""
        import random
        
        if not self.exchange_segments:
            return
            
        all_proxies = self.working_proxies.copy()
        random.shuffle(all_proxies)  # Randomize distribution
        
        num_segments = len(self.exchange_segments)
        proxies_per_segment = len(all_proxies) // num_segments
        
        if proxies_per_segment < 1:
            logging.warning(f"⚠️ Not enough proxies for {num_segments} segments")
            return
        
        # Redistribute
        segment_names = list(self.exchange_segments.keys())
        for i, segment_name in enumerate(segment_names):
            start_idx = i * proxies_per_segment
            if i == len(segment_names) - 1:  # Last segment gets remainder
                self.exchange_segments[segment_name] = all_proxies[start_idx:]
            else:
                self.exchange_segments[segment_name] = all_proxies[start_idx:start_idx + proxies_per_segment]
            self.exchange_indexes[segment_name] = 0
        
        logging.info(f"♻️ Redistributed {len(all_proxies)} proxies across {num_segments} segments")

def start_prometheus_metrics_server(proxy_manager, port=8000):
    """
    Start a simple HTTP server exposing Prometheus metrics for proxy health.
    """
    class MetricsHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/metrics':
                metrics = []
                # type: ignore is used to suppress type checker warning for custom attribute
                pm = self.server.proxy_manager  # type: ignore[attr-defined]
                with pm.lock:
                    metrics.append(f"proxy_healthy_total {len(pm.working_proxies)}")
                    metrics.append(f"proxy_total {len(pm.proxies)}")
                    metrics.append(f"proxy_error_total {sum(pm.proxy_errors.values())}")
                    avg_latency = (sum(pm.proxy_performance.values()) / len(pm.proxy_performance)) if pm.proxy_performance else 0
                    metrics.append(f"proxy_avg_latency_seconds {avg_latency}")
                    now = time.time()
                    freshness = [now - pm.last_success.get(p, 0) for p in pm.working_proxies]
                    min_fresh = min(freshness) if freshness else 0
                    max_fresh = max(freshness) if freshness else 0
                    metrics.append(f"proxy_min_freshness_seconds {min_fresh}")
                    metrics.append(f"proxy_max_freshness_seconds {max_fresh}")
                output = '\n'.join(metrics) + '\n'
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain; version=0.0.4')
                self.end_headers()
                self.wfile.write(output.encode())
            else:
                self.send_response(404)
                self.end_headers()
    class ProxyMetricsTCPServer(socketserver.TCPServer):
        def __init__(self, server_address, RequestHandlerClass, proxy_manager):
            super().__init__(server_address, RequestHandlerClass)
            self.proxy_manager = proxy_manager

    def serve():
        with ProxyMetricsTCPServer(("", port), MetricsHandler, proxy_manager) as httpd:
            httpd.serve_forever()
    t = Thread(target=serve, daemon=True)
    t.start()
    return t