"""
Proxy Management Integration
Integrates monthly proxy generation with your main trading bot.
"""

import os
import sys
from pathlib import Path
# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
import logging
from src.utils.proxy_scheduler import ProxyScheduler
import threading
import time

class ProxyManagementService:
    """
    Service to manage proxy generation and updates for the trading bot.
    Integrates with your existing UnifiedDataSource and ProxyManager.
    """
    
    def __init__(self, enable_scheduler=True, force_initial_update=False):
        self.scheduler = None
        self.enable_scheduler = enable_scheduler
        self.running = False
        
        # Start proxy management service
        if enable_scheduler:
            self.start_proxy_service(force_initial_update)
    
    def start_proxy_service(self, force_initial_update=False):
        """Start the proxy management service"""
        try:
            # Check if proxy files exist
            http_exists = os.path.exists('outputs/http_proxies_all_working.csv')
            socks4_exists = os.path.exists('outputs/socks4_proxies.csv')
            
            if not http_exists or force_initial_update:
                logging.info("🔧 Initial proxy generation needed...")
                self.scheduler = ProxyScheduler(run_on_startup=True)
            else:
                logging.info("📁 Proxy files exist, starting scheduler only...")
                self.scheduler = ProxyScheduler(run_on_startup=False)
            
            # Start background scheduler
            self.scheduler.start_scheduler()
            self.running = True
            
            logging.info("✅ Proxy management service started")
            logging.info(f"📅 Next update: {self.scheduler.get_next_run_time()}")
            
        except Exception as e:
            logging.error(f"❌ Failed to start proxy service: {e}")
    
    def force_proxy_update(self):
        """Force an immediate proxy update"""
        if self.scheduler:
            logging.info("🔧 Forcing proxy update...")
            self.scheduler.force_update()
        else:
            logging.warning("⚠️ Scheduler not initialized")
    
    def get_proxy_status(self):
        """Get current proxy management status"""
        if self.scheduler:
            return self.scheduler.get_status()
        return {'running': False, 'error': 'Scheduler not initialized'}
    
    def stop_proxy_service(self):
        """Stop the proxy management service"""
        if self.scheduler:
            self.scheduler.stop_scheduler()
            self.running = False
            logging.info("🛑 Proxy management service stopped")

# Global proxy service instance
_proxy_service = None

def get_proxy_service(enable_scheduler=True, force_initial_update=False):
    """
    Get the global proxy service instance (singleton pattern).
    Call this from your main trading bot to ensure proxies are managed.
    """
    global _proxy_service
    if _proxy_service is None:
        _proxy_service = ProxyManagementService(enable_scheduler, force_initial_update)
    return _proxy_service

def ensure_proxies_available():
    """
    Ensure proxy files are available for ProxyManager.
    Call this before starting streaming or any proxy-dependent operations.
    """
    http_exists = os.path.exists('outputs/http_proxies.csv')
    socks4_exists = os.path.exists('outputs/socks4_proxies.csv')
    
    if not http_exists:
        logging.warning("⚠️ HTTP proxy file missing, generating...")
        service = get_proxy_service(enable_scheduler=False, force_initial_update=True)
        return True
    
    logging.info("✅ Proxy files available")
    return True

# Example integration with your main trading bot
def integrate_with_trading_bot():
    """
    Example of how to integrate proxy management with your trading bot.
    Add this to your main bot initialization.
    """
    logging.info("🚀 Starting trading bot with proxy management...")
    
    # 1. Ensure proxies are available
    ensure_proxies_available()
    
    # 2. Start proxy management service
    proxy_service = get_proxy_service(enable_scheduler=True)
    
    # 3. Your existing trading bot code here
    # from src.data.unified_data_fetcher import UnifiedDataSource
    # uds = UnifiedDataSource(config_path)
    # uds.start_streaming()  # Will use proxies from outputs/
    
    logging.info("✅ Trading bot started with proxy management")
    
    return proxy_service

if __name__ == "__main__":
    # Test the proxy management service
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 Testing Proxy Management Service...")
    
    # Test service initialization
    service = get_proxy_service(enable_scheduler=True, force_initial_update=False)
    
    # Show status
    status = service.get_proxy_status()
    print(f"📊 Service Status: {status}")
    
    # Test force update (uncomment to test)
    # service.force_proxy_update()
    
    print("✅ Proxy management service test completed!")
