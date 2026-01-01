#!/usr/bin/env python3
"""
CloudFront Rate Limiter - Intelligent WebSocket connection management
Prevents CloudFront 403 blocks by managing connection timing and proxy distribution
"""

import asyncio
import time
from collections import defaultdict
from typing import Dict, List, Optional
import random

class CloudFrontRateLimiter:
    """Manages WebSocket connections to avoid CloudFront 403 blocks"""
    
    def __init__(self, max_connections_per_minute: int = 10, max_concurrent_connections: int = 5):
        self.max_connections_per_minute = max_connections_per_minute
        self.max_concurrent_connections = max_concurrent_connections
        
        # Track connection timing per IP
        self.connection_times: Dict[str, List[float]] = defaultdict(list)
        self.active_connections: Dict[str, int] = defaultdict(int)
        
        # Global connection queue
        self.connection_queue = asyncio.Queue()
        self.total_active_connections = 0
        
        print(f"🛡️  CloudFront Rate Limiter initialized:")
        print(f"   • Max connections per IP per minute: {max_connections_per_minute}")
        print(f"   • Max concurrent connections globally: {max_concurrent_connections}")
    
    async def can_connect(self, proxy_ip: str) -> bool:
        """Check if we can connect using this IP without triggering CloudFront"""
        current_time = time.time()
        
        # Clean old connection times (older than 1 minute)
        self.connection_times[proxy_ip] = [
            t for t in self.connection_times[proxy_ip] 
            if current_time - t < 60
        ]
        
        # Check per-IP rate limit
        connections_this_minute = len(self.connection_times[proxy_ip])
        if connections_this_minute >= self.max_connections_per_minute:
            return False
        
        # Check global concurrent limit
        if self.total_active_connections >= self.max_concurrent_connections:
            return False
        
        return True
    
    async def acquire_connection_slot(self, proxy_ip: str, symbol: str, timeframe: str) -> bool:
        """Acquire a connection slot with CloudFront-safe timing"""
        max_wait = 30  # Maximum wait time in seconds
        start_wait = time.time()
        
        while time.time() - start_wait < max_wait:
            if await self.can_connect(proxy_ip):
                # Record the connection
                current_time = time.time()
                self.connection_times[proxy_ip].append(current_time)
                self.active_connections[proxy_ip] += 1
                self.total_active_connections += 1
                
                print(f"    🔒 CloudFront slot acquired: {symbol} {timeframe} via {proxy_ip}")
                print(f"       • IP connections this minute: {len(self.connection_times[proxy_ip])}/{self.max_connections_per_minute}")
                print(f"       • Global active connections: {self.total_active_connections}/{self.max_concurrent_connections}")
                
                return True
            
            # Calculate smart wait time
            wait_time = min(3.0, random.uniform(1.0, 2.5))  # Randomized wait to avoid synchronization
            print(f"    ⏳ CloudFront rate limit: waiting {wait_time:.1f}s for {symbol} {timeframe}")
            await asyncio.sleep(wait_time)
        
        print(f"    ❌ CloudFront timeout: Could not acquire slot for {symbol} {timeframe} after {max_wait}s")
        return False
    
    async def release_connection_slot(self, proxy_ip: str, symbol: str, timeframe: str):
        """Release a connection slot"""
        self.active_connections[proxy_ip] = max(0, self.active_connections[proxy_ip] - 1)
        self.total_active_connections = max(0, self.total_active_connections - 1)
        
        print(f"    🔓 CloudFront slot released: {symbol} {timeframe} via {proxy_ip}")
        print(f"       • Global active connections: {self.total_active_connections}/{self.max_concurrent_connections}")
    
    def get_connection_stats(self) -> Dict:
        """Get current connection statistics"""
        current_time = time.time()
        stats = {
            "total_active_connections": self.total_active_connections,
            "max_concurrent_connections": self.max_concurrent_connections,
            "ip_stats": {}
        }
        
        for ip, times in self.connection_times.items():
            # Clean old times
            recent_times = [t for t in times if current_time - t < 60]
            stats["ip_stats"][ip] = {
                "connections_this_minute": len(recent_times),
                "active_connections": self.active_connections[ip],
                "max_per_minute": self.max_connections_per_minute
            }
        
        return stats
    
    async def smart_batch_connections(self, connection_tasks: List, batch_size: int = 3) -> List:
        """Execute connection tasks in CloudFront-safe batches"""
        results = []
        
        total_batches = (len(connection_tasks) + batch_size - 1) // batch_size
        print(f"🔄 CloudFront-safe batching: {len(connection_tasks)} connections in {total_batches} batches of {batch_size}")
        
        for i in range(0, len(connection_tasks), batch_size):
            batch = connection_tasks[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            print(f"📦 CloudFront Batch {batch_num}/{total_batches}: Starting {len(batch)} connections...")
            
            # Execute batch with CloudFront timing
            batch_results = await asyncio.gather(*batch, return_exceptions=True)
            results.extend(batch_results)
            
            # Smart inter-batch delay based on CloudFront behavior
            if i + batch_size < len(connection_tasks):
                delay = random.uniform(2.0, 4.0)  # Randomized to avoid detection patterns
                print(f"⏳ CloudFront inter-batch delay: {delay:.1f}s...")
                await asyncio.sleep(delay)
        
        # Summary
        successful = sum(1 for r in results if r is True)
        failed = len(results) - successful
        print(f"✅ CloudFront batch results: {successful} successful, {failed} failed")
        
        return results

# Global instance for the test
cloudfront_limiter = CloudFrontRateLimiter(max_connections_per_minute=8, max_concurrent_connections=4)
