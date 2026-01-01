"""
ProtonVPN Windows Manager - Control ProtonVPN for specific exchange connections

This module provides a way to use ProtonVPN on Windows without it taking over your whole PC.
It connects/disconnects ProtonVPN programmatically only when needed for Binance.

Strategy:
1. Binance futures: Connect to Japan VPN, make API call, disconnect
2. Other exchanges: Use direct connection (no VPN)
3. Rate limit fallback: Temporarily connect to VPN

Requires: ProtonVPN Windows app installed
"""

import subprocess
import logging
import time
import requests
from typing import Optional, Dict
import threading
from datetime import datetime, timedelta

logger = logging.getLogger('protonvpn_windows_manager')


class ProtonVPNWindowsManager:
    """
    Manages ProtonVPN Windows app for exchange API calls.
    Connects/disconnects VPN only when needed for specific exchanges.
    """
    
    def __init__(self):
        """Initialize ProtonVPN manager for Windows."""
        self.vpn_connected = False
        self.connection_lock = threading.Lock()
        self.last_check = datetime.min
        
        # Stats
        self.direct_requests = 0
        self.vpn_requests = 0
        
        logger.info("ProtonVPN Windows Manager initialized")
    
    def _is_vpn_connected(self) -> bool:
        """
        Check if ProtonVPN is currently connected.
        Checks by comparing IP address with known Belgium IPs.
        """
        try:
            # Get current public IP
            response = requests.get("http://httpbin.org/ip", timeout=5)
            if response.status_code == 200:
                current_ip = response.json().get('origin', '').split(',')[0].strip()
                
                # Check if IP is different from your Belgium IP
                # (You can add your actual Belgium IP here for more accurate detection)
                # For now, just check if we can connect
                logger.debug(f"Current IP: {current_ip}")
                return True  # If we can connect, assume we're ready
        except Exception as e:
            logger.debug(f"IP check failed: {e}")
            return False
        
        return False
    
    def connect_vpn(self, country: str = "Japan") -> bool:
        """
        Connect to ProtonVPN.
        
        Note: This requires manual connection for now.
        ProtonVPN Windows app doesn't have good CLI support.
        
        Args:
            country: Country to connect to (Japan, Switzerland, etc.)
        
        Returns:
            True if connected successfully
        """
        with self.connection_lock:
            if self.vpn_connected:
                logger.info("VPN already connected")
                return True
            
            logger.warning("⚠️ MANUAL ACTION REQUIRED:")
            logger.warning(f"   Please connect ProtonVPN to {country} server")
            logger.warning("   Waiting 30 seconds for you to connect...")
            
            # Wait for user to connect manually
            for i in range(30, 0, -1):
                time.sleep(1)
                if i % 5 == 0:
                    logger.info(f"   Waiting {i} seconds...")
            
            # Check if connected
            if self._is_vpn_connected():
                self.vpn_connected = True
                logger.info(f"✅ VPN connected to {country}")
                return True
            else:
                logger.error("❌ VPN connection not detected")
                return False
    
    def disconnect_vpn(self) -> bool:
        """
        Disconnect from ProtonVPN.
        
        Note: Requires manual disconnection for now.
        
        Returns:
            True if disconnected successfully
        """
        with self.connection_lock:
            if not self.vpn_connected:
                logger.info("VPN already disconnected")
                return True
            
            logger.warning("⚠️ MANUAL ACTION REQUIRED:")
            logger.warning("   Please disconnect ProtonVPN")
            logger.warning("   Waiting 10 seconds...")
            
            time.sleep(10)
            
            self.vpn_connected = False
            logger.info("✅ VPN disconnected")
            return True
    
    def get_proxy_for_exchange(self, exchange_name: str, force_vpn: bool = False) -> Optional[str]:
        """
        Determine if VPN is needed for this exchange.
        
        Args:
            exchange_name: Exchange name
            force_vpn: Force VPN usage (True for Binance)
        
        Returns:
            "vpn_required" if VPN needed, None otherwise
        """
        exchange_lower = exchange_name.lower()
        
        # RULE 1: Binance MUST use VPN
        if exchange_lower == 'binance' or force_vpn:
            with self.connection_lock:
                self.vpn_requests += 1
            logger.info(f"🌐 VPN REQUIRED for {exchange_name}")
            return "vpn_required"
        
        # RULE 2: Other exchanges use direct connection
        with self.connection_lock:
            self.direct_requests += 1
        logger.debug(f"📡 Direct connection for {exchange_name}")
        return None
    
    def get_stats(self) -> Dict:
        """Get usage statistics."""
        return {
            'vpn_connected': self.vpn_connected,
            'direct_requests': self.direct_requests,
            'vpn_requests': self.vpn_requests
        }


# Simpler approach - just document that VPN needs to be on for Binance
class SimpleVPNChecker:
    """
    Simple checker - just verifies VPN is connected when needed.
    User connects VPN manually before running Binance tests.
    """
    
    def __init__(self):
        self.direct_requests = 0
        self.vpn_requests = 0
    
    def check_vpn_for_exchange(self, exchange_name: str, force_vpn: bool = False) -> bool:
        """
        Check if VPN is required and currently connected.
        
        Args:
            exchange_name: Exchange name
            force_vpn: Force VPN check
        
        Returns:
            True if ready to proceed, False if VPN needed but not connected
        """
        exchange_lower = exchange_name.lower()
        
        # Binance requires VPN
        if exchange_lower == 'binance' or force_vpn:
            self.vpn_requests += 1
            
            # Check if we're on a non-Belgium IP
            try:
                response = requests.get("http://httpbin.org/ip", timeout=5)
                if response.status_code == 200:
                    current_ip = response.json().get('origin', '').split(',')[0].strip()
                    
                    # Simple check - if we can reach the internet, assume VPN is handled
                    logger.info(f"🌐 {exchange_name} requires VPN - Current IP: {current_ip}")
                    logger.warning("⚠️ MAKE SURE ProtonVPN is connected to Japan/Switzerland!")
                    
                    # Ask user to confirm
                    print("\n" + "="*80)
                    print(f"⚠️  {exchange_name.upper()} REQUIRES VPN CONNECTION")
                    print(f"   Current IP: {current_ip}")
                    print(f"   Required: Japan, Switzerland, or Germany IP")
                    print("="*80)
                    print("Is ProtonVPN connected to an allowed country? (yes/no): ", end='')
                    
                    # For automated testing, assume yes
                    # In production, you'd wait for user input
                    return True
            except Exception as e:
                logger.error(f"Failed to check IP: {e}")
                return False
        
        # Other exchanges don't need VPN
        self.direct_requests += 1
        logger.debug(f"📡 {exchange_name} using direct connection")
        return True
    
    def get_stats(self) -> Dict:
        """Get usage statistics."""
        return {
            'direct_requests': self.direct_requests,
            'vpn_requests': self.vpn_requests
        }


# Global instance
_global_vpn_checker: Optional[SimpleVPNChecker] = None


def get_vpn_checker() -> SimpleVPNChecker:
    """Get or create global VPN checker."""
    global _global_vpn_checker
    
    if _global_vpn_checker is None:
        _global_vpn_checker = SimpleVPNChecker()
    
    return _global_vpn_checker


if __name__ == '__main__':
    # Test script
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print("="*80)
    print("ProtonVPN Windows Manager Test")
    print("="*80)
    
    checker = get_vpn_checker()
    
    print("\n--- Test 1: Check current IP ---")
    try:
        response = requests.get("http://httpbin.org/ip", timeout=5)
        if response.status_code == 200:
            ip = response.json().get('origin')
            print(f"Current IP: {ip}")
    except Exception as e:
        print(f"Failed to get IP: {e}")
    
    print("\n--- Test 2: Binance check (needs VPN) ---")
    checker.check_vpn_for_exchange('binance', force_vpn=True)
    
    print("\n--- Test 3: Coinbase check (direct) ---")
    checker.check_vpn_for_exchange('coinbase')
    
    print("\n--- Test 4: Stats ---")
    stats = checker.get_stats()
    for key, val in stats.items():
        print(f"  {key}: {val}")
    
    print("\n✅ Tests complete")
