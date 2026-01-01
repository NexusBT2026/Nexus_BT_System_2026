"""
ProtonVPN Proxy Manager for Exchange APIs

Uses ProtonVPN as a proxy for specific API calls without taking over your entire PC.
Only routes exchange API traffic through Proton, everything else stays on your direct connection.

Requirements:
1. ProtonVPN account (free or paid)
2. `pip install python-socks[asyncio]` for SOCKS5 support
3. ProtonVPN credentials in config.json

Usage:
- Binance futures: ALWAYS uses Proton (Belgium restriction)
- Other exchanges: Uses direct IP, falls back to Proton when rate-limited
"""

import logging
import requests
from typing import Optional, Dict
import threading
from datetime import datetime, timedelta

logger = logging.getLogger('proton_proxy_manager')


class ProtonProxyManager:
    """
    Manages ProtonVPN SOCKS5 proxy for exchange API calls.
    Doesn't take over your whole PC - only routes specific API calls through VPN.
    """
    
    def __init__(self, proton_server: str = "jp-free-01.protonvpn.net", 
                 proton_port: int = 1080,
                 proton_username: Optional[str] = None,
                 proton_password: Optional[str] = None):
        """
        Initialize ProtonVPN proxy manager.
        
        Args:
            proton_server: ProtonVPN server (e.g., "jp-free-01.protonvpn.net" for Japan)
                          Use Japan, Switzerland, or Germany - NOT US (Binance banned)
            proton_port: SOCKS5 port (usually 1080)
            proton_username: Your ProtonVPN OpenVPN/IKEv2 username
            proton_password: Your ProtonVPN OpenVPN/IKEv2 password
        """
        self.proton_server = proton_server
        self.proton_port = proton_port
        self.proton_username = proton_username
        self.proton_password = proton_password
        
        # State tracking
        self.proxy_healthy = False
        self.last_check = datetime.min
        self.rate_limit_mode = {}  # exchange -> bool
        self.lock = threading.Lock()
        
        # Stats
        self.direct_requests = 0
        self.proxy_requests = 0
        self.proxy_failures = 0
        
        logger.info(f"ProtonProxyManager initialized (server: {proton_server})")
        
        # Initial health check
        self._check_proxy_health()
    
    def _check_proxy_health(self) -> bool:
        """
        Check if ProtonVPN proxy is working.
        Tests basic connectivity through the proxy.
        """
        # Build SOCKS5 proxy URL
        if self.proton_username and self.proton_password:
            proxy_url = f"socks5://{self.proton_username}:{self.proton_password}@{self.proton_server}:{self.proton_port}"
        else:
            proxy_url = f"socks5://{self.proton_server}:{self.proton_port}"
        
        proxies = {
            'http': proxy_url,
            'https': proxy_url
        }
        
        # Test with a simple endpoint
        try:
            response = requests.get("http://httpbin.org/ip", proxies=proxies, timeout=10)
            if response.status_code == 200:
                ip_data = response.json()
                detected_ip = ip_data.get('origin', 'unknown')
                
                with self.lock:
                    self.proxy_healthy = True
                    self.last_check = datetime.now()
                
                logger.info(f"✅ ProtonVPN proxy healthy - detected IP: {detected_ip}")
                return True
        except Exception as e:
            logger.warning(f"⚠️ ProtonVPN proxy health check failed: {e}")
        
        with self.lock:
            self.proxy_healthy = False
            self.last_check = datetime.now()
        
        return False
    
    def get_proxy_dict(self, exchange_name: str, force_proxy: bool = False) -> Optional[Dict[str, str]]:
        """
        Get proxy configuration for requests library.
        
        Args:
            exchange_name: Exchange name (binance, coinbase, etc.)
            force_proxy: Force proxy usage (True for Binance futures)
        
        Returns:
            Dict with 'http' and 'https' proxy URLs, or None for direct connection
        """
        # Periodic health check (every 5 minutes)
        if datetime.now() - self.last_check > timedelta(minutes=5):
            self._check_proxy_health()
        
        exchange_lower = exchange_name.lower()
        
        # RULE 1: Binance futures MUST use proxy (Belgium restriction)
        if exchange_lower == 'binance' or force_proxy:
            if not self.proxy_healthy:
                logger.error(f"❌ Proxy required for {exchange_name} but proxy is unhealthy!")
                raise ConnectionError(f"ProtonVPN proxy required for {exchange_name} but proxy is down")
            
            with self.lock:
                self.proxy_requests += 1
            
            # Build SOCKS5 proxy URL
            if self.proton_username and self.proton_password:
                proxy_url = f"socks5://{self.proton_username}:{self.proton_password}@{self.proton_server}:{self.proton_port}"
            else:
                proxy_url = f"socks5://{self.proton_server}:{self.proton_port}"
            
            logger.debug(f"🌐 Using ProtonVPN for {exchange_name}: {self.proton_server}")
            return {
                'http': proxy_url,
                'https': proxy_url
            }
        
        # RULE 2: Other exchanges - use proxy only if rate limited
        with self.lock:
            is_rate_limited = self.rate_limit_mode.get(exchange_lower, False)
        
        if is_rate_limited and self.proxy_healthy:
            with self.lock:
                self.proxy_requests += 1
            
            if self.proton_username and self.proton_password:
                proxy_url = f"socks5://{self.proton_username}:{self.proton_password}@{self.proton_server}:{self.proton_port}"
            else:
                proxy_url = f"socks5://{self.proton_server}:{self.proton_port}"
            
            logger.info(f"🔄 Using ProtonVPN for {exchange_name} (rate limited)")
            return {
                'http': proxy_url,
                'https': proxy_url
            }
        
        # RULE 3: Default - direct connection
        with self.lock:
            self.direct_requests += 1
        
        logger.debug(f"📡 Using direct connection for {exchange_name}")
        return None
    
    def get_ccxt_config(self, exchange_name: str, force_proxy: bool = False) -> Dict:
        """
        Get CCXT-compatible proxy configuration.
        
        Args:
            exchange_name: Exchange name
            force_proxy: Force proxy usage
        
        Returns:
            Dict with proxy config for CCXT
        """
        proxy_dict = self.get_proxy_dict(exchange_name, force_proxy)
        
        if proxy_dict:
            return {
                'proxies': proxy_dict,
                'httpProxy': proxy_dict['http'],
                'httpsProxy': proxy_dict['https'],
                'aiohttp_proxy': proxy_dict['http']  # For async
            }
        
        return {}
    
    def report_rate_limit(self, exchange_name: str, duration: int = 600):
        """
        Report rate limit - will use proxy for this exchange temporarily.
        
        Args:
            exchange_name: Exchange that rate limited us
            duration: How long to use proxy (seconds, default 10 minutes)
        """
        exchange_lower = exchange_name.lower()
        
        with self.lock:
            self.rate_limit_mode[exchange_lower] = True
        
        logger.warning(f"⚠️ Rate limit on {exchange_name} - switching to ProtonVPN for {duration}s")
        
        # Auto-reset after cooldown
        def reset():
            import time
            time.sleep(duration)
            with self.lock:
                self.rate_limit_mode[exchange_lower] = False
            logger.info(f"✅ Rate limit cooldown complete for {exchange_name}")
        
        threading.Thread(target=reset, daemon=True).start()
    
    def get_stats(self) -> Dict:
        """Get usage statistics."""
        with self.lock:
            return {
                'proton_server': self.proton_server,
                'proxy_healthy': self.proxy_healthy,
                'direct_requests': self.direct_requests,
                'proxy_requests': self.proxy_requests,
                'proxy_failures': self.proxy_failures,
                'rate_limited_exchanges': list(self.rate_limit_mode.keys())
            }


# Global instance
_global_proxy_manager: Optional[ProtonProxyManager] = None


def get_proton_proxy_manager(proton_server: Optional[str] = None,
                              proton_username: Optional[str] = None,
                              proton_password: Optional[str] = None) -> ProtonProxyManager:
    """
    Get or create global ProtonVPN proxy manager.
    
    On first call, loads credentials from config.json if not provided.
    """
    global _global_proxy_manager
    
    if _global_proxy_manager is None:
        # Load from config if not provided
        if not proton_server or not proton_username or not proton_password:
            try:
                from src.exchange.config import load_config
                config = load_config()
                proton_server = proton_server or config.get('protonvpn_server', 'jp-free-01.protonvpn.net')
                proton_username = proton_username or config.get('protonvpn_username')
                proton_password = proton_password or config.get('protonvpn_password')
            except Exception as e:
                logger.warning(f"Could not load ProtonVPN config: {e}")
        
        _global_proxy_manager = ProtonProxyManager(
            proton_server=proton_server or 'jp-free-01.protonvpn.net',  # Japan - allowed by Binance
            proton_username=proton_username,
            proton_password=proton_password
        )
    
    return _global_proxy_manager


if __name__ == '__main__':
    # Test script
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print("=" * 80)
    print("ProtonVPN Proxy Manager Test")
    print("=" * 80)
    print("\nNOTE: This test requires ProtonVPN credentials in config.json:")
    print("  {")
    print('    "protonvpn_server": "jp-free-01.protonvpn.net",  // Japan or Switzerland (NOT US!)')
    print('    "protonvpn_username": "your_openvpn_username",')
    print('    "protonvpn_password": "your_openvpn_password"')
    print("  }")
    print("=" * 80)
    
    try:
        manager = get_proton_proxy_manager()
        
        print(f"\n✅ Manager initialized")
        print(f"   Server: {manager.proton_server}")
        print(f"   Healthy: {manager.proxy_healthy}")
        
        if manager.proxy_healthy:
            print("\n--- Test 1: Binance (forced proxy) ---")
            proxy = manager.get_proxy_dict('binance', force_proxy=True)
            print(f"Proxy: {proxy}")
            
            print("\n--- Test 2: Coinbase (direct) ---")
            proxy = manager.get_proxy_dict('coinbase')
            print(f"Proxy: {proxy}")
            
            print("\n--- Test 3: Stats ---")
            stats = manager.get_stats()
            for key, val in stats.items():
                print(f"  {key}: {val}")
        else:
            print("\n⚠️ Proxy not healthy - check your ProtonVPN credentials")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
