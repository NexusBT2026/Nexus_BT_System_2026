#!/usr/bin/env python3
"""
API Rate Monitor - Dynamic TokenBucket Monitoring and Dashboard Integration
===========================================================================

Purpose: Real-time API rate limiting monitoring and analytics for all exchanges
- Track API usage patterns across all exchanges
- Monitor TokenBucket status and utilization
- Provide dashboard-ready metrics
- Dynamic rate adjustment recommendations
- Alert system for API overuse

Integration Points:
✅ TokenBucket: Existing rate limiting infrastructure
✅ Data Fetchers: Phemex, Coinbase, Hyperliquid
✅ Balance Modules: All 9 modules with API calls
✅ Dashboard: JSON export for web interface

Author: Trading Bot Infrastructure Team
Date: October 4, 2025
"""

import asyncio
import aiofiles
import json
import os
import sys
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# Import TokenBucket infrastructure
from src.utils.token_bucket import TokenBucket, create_exchange_buckets

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

@dataclass
class APICallMetrics:
    """Data class for tracking individual API call metrics"""
    timestamp: float
    exchange: str
    endpoint: str
    method: str
    success: bool
    response_time: float
    tokens_consumed: int
    tokens_remaining: float
    rate_limited: bool
    
class APIRateMonitor:
    """
    Centralized API rate monitoring and analytics system.
    
    Features:
    - Real-time TokenBucket monitoring across all exchanges
    - API call pattern analysis and trending
    - Rate limiting alerts and recommendations
    - Dashboard integration with JSON exports
    - Historical usage analytics
    """
    
    def __init__(self, output_dir: str = os.path.join(project_root, 'data', 'outputs', 'api_monitoring')):
        """Initialize API rate monitor"""
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Shared storage for cross-process API calls
        self.shared_calls_file = os.path.join(output_dir, "shared_api_calls.jsonl")
        
        # Initialize TokenBucket instances for monitoring
        self.buckets = create_exchange_buckets()
        
        # Metrics storage
        self.call_history: deque = deque(maxlen=10000)  # Last 10k API calls
        self.exchange_stats: Dict[str, Dict] = defaultdict(dict)
        self.hourly_stats: Dict[str, Dict] = defaultdict(dict)
        
        # Alert thresholds
        self.alert_thresholds = {
            'high_utilization': 80.0,  # % utilization
            'consecutive_blocks': 5,    # Consecutive blocked requests
            'low_tokens': 0.1,         # Tokens remaining ratio
        }
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Start monitoring thread
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        logger.info(f"🎯 API Rate Monitor initialized - Output: {output_dir}")
    
    def record_api_call(self, exchange: str, endpoint: str, method: str = "GET", 
                       success: bool = True, response_time: float = 0.0, 
                       tokens_consumed: int = 1) -> Dict[str, Any]:
        """
        Record an API call for monitoring and analytics.
        
        Args:
            exchange: Exchange name (phemex, hyperliquid, coinbase)
            endpoint: API endpoint called
            method: HTTP method (GET, POST, etc.)
            success: Whether the call was successful
            response_time: Response time in seconds
            tokens_consumed: Number of tokens consumed
            
        Returns:
            Dict with call status and bucket metrics
        """
        timestamp = time.time()
        
        with self.lock:
            # Get bucket for this exchange
            bucket = self.buckets.get(exchange.lower())
            if not bucket:
                logger.warning(f"⚠️ No TokenBucket found for exchange: {exchange}")
                return {"error": f"Unknown exchange: {exchange}"}
            
            # Try to consume tokens
            rate_limited = not bucket.consume(tokens_consumed)
            tokens_remaining = bucket.tokens
            
            # Create metrics record
            metrics = APICallMetrics(
                timestamp=timestamp,
                exchange=exchange,
                endpoint=endpoint,
                method=method,
                success=success,
                response_time=response_time,
                tokens_consumed=tokens_consumed,
                tokens_remaining=tokens_remaining,
                rate_limited=rate_limited
            )
            
            # Store in history
            self.call_history.append(metrics)
            
            # Write to shared storage for cross-process tracking
            self._write_to_shared_storage(metrics)
            
            # Update exchange stats
            self._update_exchange_stats(exchange, metrics)
            
            # Check for alerts
            alerts = self._check_alerts(exchange, bucket)
            
            return {
                "timestamp": timestamp,
                "exchange": exchange,
                "rate_limited": rate_limited,
                "tokens_remaining": tokens_remaining,
                "bucket_status": bucket.get_status(),
                "alerts": alerts
            }
    
    def get_exchange_status(self, exchange: Optional[str] = None) -> Dict[str, Any]:
        """
        Get current status for specific exchange or all exchanges.
        
        Args:
            exchange: Specific exchange name, or None for all
            
        Returns:
            Dict with exchange status and metrics
        """
        with self.lock:
            if exchange:
                bucket = self.buckets.get(exchange.lower())
                if not bucket:
                    return {"error": f"Unknown exchange: {exchange}"}
                
                return {
                    "exchange": exchange,
                    "bucket_status": bucket.get_status(),
                    "recent_calls": self._get_recent_calls(exchange, minutes=10),
                    "hourly_trend": self._get_hourly_trend(exchange),
                    "recommendations": self._get_recommendations(exchange)
                }
            else:
                # Return all exchanges
                all_status = {}
                for ex_name, bucket in self.buckets.items():
                    all_status[ex_name] = {
                        "bucket_status": bucket.get_status(),
                        "recent_calls": self._get_recent_calls(ex_name, minutes=10),
                        "hourly_trend": self._get_hourly_trend(ex_name),
                        "recommendations": self._get_recommendations(ex_name)
                    }
                return all_status
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Get comprehensive data formatted for dashboard display.
        
        Returns:
            Dict with all monitoring data for dashboard
        """
        with self.lock:
            current_time = time.time()
            
            # Overall system status using shared calls from all processes
            all_calls = self._load_shared_calls()
            system_status = {
                "timestamp": current_time,
                "total_calls_last_hour": len([c for c in all_calls 
                                            if current_time - c.timestamp <= 3600]),
                "active_exchanges": len(self.buckets),
                "monitoring_active": self.monitoring_active
            }
            
            # Exchange summaries using shared data from all processes
            exchange_summaries = {}
            for exchange_name, bucket in self.buckets.items():
                recent_calls = self._get_recent_calls(exchange_name, minutes=60)
                
                # Calculate true token consumption from all processes
                total_tokens_consumed = sum(call.tokens_consumed for call in recent_calls)
                capacity = bucket.capacity
                
                # Get most recent token state (latest call has most current token count)
                latest_call = max(recent_calls, key=lambda x: x.timestamp) if recent_calls else None
                tokens_remaining = latest_call.tokens_remaining if latest_call else capacity
                
                # Calculate utilization based on total consumption
                utilization_percentage = ((capacity - tokens_remaining) / capacity) * 100 if capacity > 0 else 0
                
                # Count failures and rate limits from shared data
                failed_calls = len([call for call in recent_calls if not call.success])
                rate_limited_calls = len([call for call in recent_calls if call.rate_limited])
                
                exchange_summaries[exchange_name] = {
                    "name": exchange_name.title(),
                    "tokens_remaining": tokens_remaining,
                    "capacity": capacity,
                    "utilization_percentage": utilization_percentage,
                    "total_requests": len(recent_calls),  # True total from all processes
                    "successful_requests": len(recent_calls) - failed_calls,
                    "failed_requests": failed_calls,
                    "blocked_requests": rate_limited_calls,
                    "calls_last_hour": len(recent_calls),
                    "avg_response_time": self._calculate_avg_response_time(recent_calls),
                    "health_status": self._get_health_status_from_calls(exchange_name, recent_calls),
                    "alerts": self._get_alerts_from_calls(exchange_name, recent_calls, tokens_remaining, capacity)
                }
            
            # Historical trends (last 24 hours)
            historical_data = self._get_historical_trends(hours=24)
            
            # Top endpoints by usage
            top_endpoints = self._get_top_endpoints(limit=10)
            
            return {
                "system_status": system_status,
                "exchange_summaries": exchange_summaries,
                "historical_trends": historical_data,
                "top_endpoints": top_endpoints,
                "alert_summary": self._get_alert_summary(),
                "recommendations": self._get_system_recommendations()
            }
    
    def export_dashboard_json(self) -> str:
        """
        Export dashboard data to JSON file.
        
        Returns:
            Path to exported JSON file
        """
        dashboard_data = self.get_dashboard_data()
        
        # Add metadata
        dashboard_data["export_info"] = {
            "generated_at": datetime.now().isoformat(),
            "version": "1.0",
            "module": "api_rate_monitor"
        }
        
        # Export to file
        output_file = os.path.join(self.output_dir, "api_rate_dashboard.json")
        
        try:
            with open(output_file, 'w') as f:
                json.dump(dashboard_data, f, indent=2, default=str)
            
            logger.info(f"📊 Dashboard data exported: {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"❌ Failed to export dashboard data: {e}")
            return ""
    
    def reset_exchange_metrics(self, exchange: Optional[str] = None):
        """
        Reset metrics for specific exchange or all exchanges.
        
        Args:
            exchange: Exchange name, or None for all exchanges
        """
        with self.lock:
            if exchange:
                bucket = self.buckets.get(exchange.lower())
                if bucket:
                    bucket.reset_metrics()
                    logger.info(f"🔄 Reset metrics for {exchange}")
            else:
                for bucket in self.buckets.values():
                    bucket.reset_metrics()
                self.call_history.clear()
                self.exchange_stats.clear()
                self.hourly_stats.clear()
                logger.info("🔄 Reset all exchange metrics")
    
    def _update_exchange_stats(self, exchange: str, metrics: APICallMetrics):
        """Update internal exchange statistics"""
        if exchange not in self.exchange_stats:
            self.exchange_stats[exchange] = {
                'total_calls': 0,
                'successful_calls': 0,
                'failed_calls': 0,
                'rate_limited_calls': 0,
                'total_response_time': 0.0,
                'endpoints': defaultdict(int)
            }
        
        stats = self.exchange_stats[exchange]
        stats['total_calls'] += 1
        stats['total_response_time'] += metrics.response_time
        stats['endpoints'][metrics.endpoint] += 1
        
        if metrics.success:
            stats['successful_calls'] += 1
        else:
            stats['failed_calls'] += 1
        
        if metrics.rate_limited:
            stats['rate_limited_calls'] += 1

    def _write_to_shared_storage(self, metrics: APICallMetrics):
        """Write API call to shared storage for cross-process tracking"""
        try:
            call_data = {
                "timestamp": metrics.timestamp,
                "exchange": metrics.exchange,
                "endpoint": metrics.endpoint,
                "method": metrics.method,
                "success": metrics.success,
                "response_time": metrics.response_time,
                "tokens_consumed": metrics.tokens_consumed,
                "tokens_remaining": metrics.tokens_remaining,
                "rate_limited": metrics.rate_limited,
                "process_id": os.getpid()
            }
            
            # Append to shared JSONL file
            with open(self.shared_calls_file, 'a', encoding='utf-8') as f:
                json.dump(call_data, f)
                f.write('\n')
                
        except Exception as e:
            # Don't break the main flow if shared storage fails
            logger.debug(f"Shared storage write failed: {e}")

    def _get_health_status_from_calls(self, exchange: str, recent_calls: List[APICallMetrics]) -> str:
        """Calculate health status from recent calls across all processes"""
        if not recent_calls:
            return "HEALTHY"
        
        total_calls = len(recent_calls)
        failed_calls = len([call for call in recent_calls if not call.success])
        rate_limited_calls = len([call for call in recent_calls if call.rate_limited])
        
        # Get latest token info
        latest_call = max(recent_calls, key=lambda x: x.timestamp)
        tokens_remaining = latest_call.tokens_remaining
        capacity = self.buckets[exchange].capacity
        utilization = ((capacity - tokens_remaining) / capacity) * 100 if capacity > 0 else 0
        
        # Determine health status
        if rate_limited_calls > 0:
            return "RATE_LIMITED"
        elif utilization > 80:
            return "WARNING"
        elif failed_calls > total_calls * 0.1:  # More than 10% failures
            return "DEGRADED"
        else:
            return "HEALTHY"

    def _get_alerts_from_calls(self, exchange: str, recent_calls: List[APICallMetrics], 
                              tokens_remaining: float, capacity: float) -> List[Dict[str, str]]:
        """Generate alerts from recent calls across all processes"""
        alerts = []
        
        if not recent_calls:
            return alerts
        
        # Check for rate limiting
        rate_limited_calls = len([call for call in recent_calls if call.rate_limited])
        if rate_limited_calls > 0:
            alerts.append({
                "level": "CRITICAL",
                "message": f"{exchange} has {rate_limited_calls} rate-limited calls in last hour"
            })
        
        # Check token utilization
        utilization = ((capacity - tokens_remaining) / capacity) * 100 if capacity > 0 else 0
        if utilization > 80:
            alerts.append({
                "level": "WARNING", 
                "message": f"{exchange} token utilization at {utilization:.1f}%"
            })
        
        # Check failure rate
        total_calls = len(recent_calls)
        failed_calls = len([call for call in recent_calls if not call.success])
        if failed_calls > total_calls * 0.1:
            failure_rate = (failed_calls / total_calls) * 100
            alerts.append({
                "level": "WARNING",
                "message": f"{exchange} has {failure_rate:.1f}% failure rate"
            })
        
        return alerts

    def _load_shared_calls(self) -> List[APICallMetrics]:
        """Load all API calls from shared storage across all processes"""
        shared_calls = []
        
        if not os.path.exists(self.shared_calls_file):
            return shared_calls
            
        try:
            with open(self.shared_calls_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            call_data = json.loads(line)
                            # Convert back to APICallMetrics
                            metrics = APICallMetrics(
                                timestamp=call_data['timestamp'],
                                exchange=call_data['exchange'],
                                endpoint=call_data['endpoint'],
                                method=call_data['method'],
                                success=call_data['success'],
                                response_time=call_data['response_time'],
                                tokens_consumed=call_data['tokens_consumed'],
                                tokens_remaining=call_data['tokens_remaining'],
                                rate_limited=call_data['rate_limited']
                            )
                            shared_calls.append(metrics)
                        except (json.JSONDecodeError, KeyError):
                            continue
        except Exception as e:
            logger.debug(f"Failed to load shared calls: {e}")
            
        return shared_calls
    
    def _get_recent_calls(self, exchange: str, minutes: int = 10) -> List[APICallMetrics]:
        """Get recent API calls for an exchange from all processes"""
        cutoff_time = time.time() - (minutes * 60)
        all_calls = self._load_shared_calls()
        return [call for call in all_calls 
                if call.exchange.lower() == exchange.lower() and call.timestamp >= cutoff_time]
    
    def _get_hourly_trend(self, exchange: str) -> Dict[str, int]:
        """Get hourly call trends for an exchange"""
        now = time.time()
        hourly_data = {}
        
        for hour in range(24):
            hour_start = now - (hour * 3600)
            hour_end = hour_start + 3600
            
            calls_in_hour = len([call for call in self.call_history 
                               if call.exchange.lower() == exchange.lower() 
                               and hour_start <= call.timestamp < hour_end])
            
            hour_label = f"{hour}h_ago"
            hourly_data[hour_label] = calls_in_hour
        
        return hourly_data
    
    def _calculate_avg_response_time(self, calls: List[APICallMetrics]) -> float:
        """Calculate average response time for a list of calls"""
        if not calls:
            return 0.0
        return sum(call.response_time for call in calls) / len(calls)
    
    def _get_health_status(self, exchange: str) -> str:
        """Determine health status for an exchange"""
        bucket = self.buckets.get(exchange.lower())
        if not bucket:
            return "UNKNOWN"
        
        status = bucket.get_status()
        utilization = status['utilization_rate']
        tokens_ratio = status['tokens'] / status['capacity']
        
        if utilization > self.alert_thresholds['high_utilization']:
            return "CRITICAL"
        elif utilization > 50 or tokens_ratio < 0.3:
            return "WARNING"
        else:
            return "HEALTHY"
    
    def _check_alerts(self, exchange: str, bucket: TokenBucket) -> List[Dict[str, Any]]:
        """Check for alerts on an exchange"""
        alerts = []
        status = bucket.get_status()
        
        # High utilization alert
        if status['utilization_rate'] > self.alert_thresholds['high_utilization']:
            alerts.append({
                "type": "HIGH_UTILIZATION",
                "severity": "WARNING",
                "message": f"{exchange} API utilization at {status['utilization_rate']:.1f}%",
                "recommendation": "Consider reducing API call frequency"
            })
        
        # Low tokens alert
        tokens_ratio = status['tokens'] / status['capacity']
        if tokens_ratio < self.alert_thresholds['low_tokens']:
            alerts.append({
                "type": "LOW_TOKENS",
                "severity": "CRITICAL",
                "message": f"{exchange} tokens critically low: {status['tokens']:.1f}",
                "recommendation": "Implement exponential backoff for API calls"
            })
        
        return alerts
    
    def _get_recommendations(self, exchange: str) -> List[str]:
        """Get optimization recommendations for an exchange"""
        recommendations = []
        bucket = self.buckets.get(exchange.lower())
        if not bucket:
            return recommendations
        
        status = bucket.get_status()
        recent_calls = self._get_recent_calls(exchange, minutes=30)
        
        # Rate limiting recommendations
        if status['utilization_rate'] > 70:
            recommendations.append("Consider implementing request batching")
            recommendations.append("Add exponential backoff between requests")
        
        # Performance recommendations
        if recent_calls:
            avg_response = self._calculate_avg_response_time(recent_calls)
            if avg_response > 2.0:  # 2 seconds
                recommendations.append("API response times are high - check network connectivity")
        
        # Usage pattern recommendations
        if len(recent_calls) > 100:  # High frequency
            recommendations.append("High API usage detected - consider caching strategies")
        
        return recommendations
    
    def _get_historical_trends(self, hours: int = 24) -> Dict[str, List[Dict]]:
        """Get historical trends for dashboard charts using all processes"""
        trends = {}
        
        # Load shared calls from all processes
        all_calls = self._load_shared_calls()
        
        for exchange_name in self.buckets.keys():
            exchange_trend = []
            now = time.time()
            
            for hour in range(hours):
                # Fix: hour 0 = current hour, hour 1 = 1 hour ago, etc.
                hour_end = now - (hour * 3600)
                hour_start = hour_end - 3600
                
                calls_in_hour = [call for call in all_calls 
                               if call.exchange.lower() == exchange_name.lower() 
                               and hour_start <= call.timestamp < hour_end]
                
                exchange_trend.append({
                    "hour": hour,
                    "timestamp": hour_start,
                    "total_calls": len(calls_in_hour),
                    "successful_calls": len([c for c in calls_in_hour if c.success]),
                    "rate_limited_calls": len([c for c in calls_in_hour if c.rate_limited]),
                    "avg_response_time": self._calculate_avg_response_time(calls_in_hour)
                })
            
            trends[exchange_name] = exchange_trend
        
        return trends
    
    def _get_top_endpoints(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most frequently called endpoints from all processes"""
        endpoint_counts = defaultdict(int)
        all_calls = self._load_shared_calls()
        
        for call in all_calls:
            endpoint_key = f"{call.exchange}:{call.endpoint}"
            endpoint_counts[endpoint_key] += 1
        
        # Sort by frequency and get top N
        top_endpoints = sorted(endpoint_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        
        return [{"endpoint": endpoint, "calls": count} for endpoint, count in top_endpoints]
    
    def _get_alert_summary(self) -> Dict[str, int]:
        """Get summary of current alerts"""
        alert_counts = {"CRITICAL": 0, "WARNING": 0, "INFO": 0}
        
        for exchange_name, bucket in self.buckets.items():
            alerts = self._check_alerts(exchange_name, bucket)
            for alert in alerts:
                severity = alert.get("severity", "INFO")
                alert_counts[severity] += 1
        
        return alert_counts
    
    def _get_system_recommendations(self) -> List[str]:
        """Get system-wide recommendations"""
        recommendations = []
        
        # Check overall system health
        total_utilization = sum(bucket.get_status()['utilization_rate'] 
                              for bucket in self.buckets.values()) / len(self.buckets)
        
        if total_utilization > 60:
            recommendations.append("System-wide API usage is high - consider load balancing")
        
        # Check for imbalanced usage
        exchange_rates = [(name, bucket.get_status()['utilization_rate']) 
                         for name, bucket in self.buckets.items()]
        max_rate = max(rate for _, rate in exchange_rates)
        min_rate = min(rate for _, rate in exchange_rates)
        
        if max_rate - min_rate > 40:  # 40% difference
            recommendations.append("Unbalanced API usage across exchanges - redistribute load")
        
        return recommendations
    
    def _monitoring_loop(self):
        """Background monitoring loop"""
        while self.monitoring_active:
            try:
                # Export dashboard data every 5 minutes
                if int(time.time()) % 60 == 0:  # Every minute
                    self.export_dashboard_json()
                
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"❌ Monitoring loop error: {e}")
                time.sleep(60)
    
    def stop_monitoring(self):
        """Stop the monitoring thread"""
        self.monitoring_active = False
        if self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5)
        logger.info("🛑 API Rate Monitor stopped")

# Global monitor instance
_global_monitor: Optional[APIRateMonitor] = None

def get_api_monitor() -> APIRateMonitor:
    """Get or create global API monitor instance"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = APIRateMonitor()
    return _global_monitor

def record_api_call(exchange: str, endpoint: str, **kwargs) -> Dict[str, Any]:
    """Convenience function to record API call"""
    monitor = get_api_monitor()
    return monitor.record_api_call(exchange, endpoint, **kwargs)

def get_exchange_status(exchange: Optional[str] = None) -> Dict[str, Any]:
    """Convenience function to get exchange status"""
    monitor = get_api_monitor()
    return monitor.get_exchange_status(exchange)

def export_dashboard_data() -> str:
    """Convenience function to export dashboard data"""
    monitor = get_api_monitor()
    return monitor.export_dashboard_json()

# Async convenience functions for concurrent API monitoring
async def async_record_api_call(exchange: str, endpoint: str, **kwargs) -> Dict[str, Any]:
    """Async convenience function to record API call"""
    import functools
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        # Use functools.partial to properly pass keyword arguments
        func = functools.partial(record_api_call, exchange, endpoint, **kwargs)
        return await loop.run_in_executor(executor, func)

async def async_get_exchange_status(exchange: Optional[str] = None) -> Dict[str, Any]:
    """Async convenience function to get exchange status"""
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        return await loop.run_in_executor(executor, get_exchange_status, exchange)

async def async_export_dashboard_data() -> str:
    """Async convenience function to export dashboard data"""
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        return await loop.run_in_executor(executor, export_dashboard_data)

async def async_get_dashboard_data() -> Dict[str, Any]:
    """Async convenience function to get dashboard data"""
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        monitor = get_api_monitor()
        return await loop.run_in_executor(executor, monitor.get_dashboard_data)

async def async_monitor_concurrent_calls(*calls) -> List[Any]:
    """Monitor multiple API calls concurrently"""
    tasks = []
    for exchange, endpoint, kwargs in calls:
        task = async_record_api_call(exchange, endpoint, **kwargs)
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out exceptions and return successful results
    successful_results = []
    for result in results:
        if isinstance(result, Exception):
            logger.error(f"Concurrent API call monitoring error: {result}")
        else:
            successful_results.append(result)
    
    return successful_results

# Test function
def main():
    """Test the API Rate Monitor"""
    print("🎯 API Rate Monitor - Testing Dynamic TokenBucket Monitoring")
    print("=" * 80)
    
    # Initialize monitor
    monitor = APIRateMonitor()
    
    # Simulate some API calls
    print("📡 Simulating API calls...")
    
    # Simulate Phemex calls
    for i in range(10):
        result = monitor.record_api_call("phemex", "/v1/md/orderbook", "GET", True, 0.5, 1)
        print(f"Phemex call {i+1}: Rate limited = {result.get('rate_limited', False)}")
    
    # Simulate Hyperliquid calls
    for i in range(5):
        result = monitor.record_api_call("hyperliquid", "/info", "POST", True, 0.3, 1)
        print(f"Hyperliquid call {i+1}: Rate limited = {result.get('rate_limited', False)}")
    
    # Get dashboard data
    print("\n📊 Generating dashboard data...")
    dashboard_file = monitor.export_dashboard_json()
    print(f"Dashboard data exported: {dashboard_file}")
    
    # Print summary
    print("\n📈 Exchange Status Summary:")
    status = monitor.get_exchange_status()
    for exchange, data in status.items():
        bucket_status = data['bucket_status']
        print(f"  {exchange.title()}: {bucket_status['tokens']:.1f}/{bucket_status['capacity']} tokens, "
              f"{bucket_status['utilization_rate']:.1f}% utilization")
    
    print("\n✅ API Rate Monitor test completed!")

async def main_async():
    """Test the API Rate Monitor with ASYNC methods"""
    print("🚀 API Rate Monitor - Testing ASYNC Methods")
    print("=" * 80)
    
    # Test async API call recording
    print("📡 Testing ASYNC API call recording...")
    
    start_time = time.time()
    
    # Test concurrent API call monitoring
    calls_to_monitor = [
        ("phemex", "/v1/md/orderbook", {"method": "GET", "success": True, "response_time": 0.5, "tokens_consumed": 1}),
        ("hyperliquid", "/info", {"method": "POST", "success": True, "response_time": 0.3, "tokens_consumed": 1}),
        ("coinbase", "/accounts", {"method": "GET", "success": True, "response_time": 0.7, "tokens_consumed": 1}),
    ]
    
    # Monitor multiple calls concurrently
    results = await async_monitor_concurrent_calls(*calls_to_monitor)
    concurrent_time = time.time() - start_time
    
    print(f"⚡ Concurrent monitoring completed in {concurrent_time:.3f} seconds")
    print(f"📊 Monitored {len(results)} API calls successfully")
    
    # Test async dashboard data export
    print("\n📊 Testing ASYNC dashboard export...")
    dashboard_data = await async_get_dashboard_data()
    dashboard_json = await async_export_dashboard_data()
    
    print(f"✅ Dashboard data retrieved: {len(dashboard_data)} metrics")
    print(f"✅ Dashboard JSON exported successfully")
    
    # Test async exchange status
    print("\n📈 Testing ASYNC exchange status...")
    for exchange in ["phemex", "hyperliquid", "coinbase"]:
        status = await async_get_exchange_status(exchange)
        bucket_info = status.get(exchange, {}).get('bucket_status', {})
        tokens = bucket_info.get('tokens', 0)
        capacity = bucket_info.get('capacity', 1)
        utilization = bucket_info.get('utilization_rate', 0)
        print(f"  {exchange.title()}: {tokens:.1f}/{capacity} tokens, {utilization:.1f}% utilization")
    
    total_time = time.time() - start_time
    print(f"\n⚡ ASYNC API Rate Monitor test completed in {total_time:.3f} seconds!")

if __name__ == "__main__":
    import time
    
    # Performance comparison: SYNC vs ASYNC
    print("=" * 60)
    print("🏁 API RATE MONITOR PERFORMANCE COMPARISON")
    print("=" * 60)
    
    # Run SYNC test
    sync_start = time.time()
    main()
    sync_time = time.time() - sync_start
    
    # Run ASYNC test
    print("\n" + "=" * 60)
    async_start = time.time()
    asyncio.run(main_async())
    async_time = time.time() - async_start
    
    print("\n" + "=" * 60)
    print("📊 PERFORMANCE SUMMARY:")
    print(f"🐌 SYNC version:  {sync_time:.3f} seconds")
    print(f"⚡ ASYNC version: {async_time:.3f} seconds")
    
    if sync_time > async_time:
        improvement = ((sync_time - async_time) / sync_time) * 100
        print(f"🚀 ASYNC is {improvement:.1f}% faster!")
    elif async_time > sync_time:
        overhead = ((async_time - sync_time) / sync_time) * 100
        print(f"📝 ASYNC has {overhead:.1f}% overhead (expected for concurrent setup)")
    else:
        print("⚖️ Performance is equivalent")
    
    print("=" * 60)
    print("✅ API Rate Monitor now supports ASYNC operations!")