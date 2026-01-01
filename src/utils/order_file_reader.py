"""
Order File Reader Utility

Utility functions to read saved order data from the OrderExecutionEngine.
This allows other parts of the bot to access order history and tracking data.

Usage Examples:
    from src.utils.order_file_reader import get_recent_orders, get_order_by_id
    
    # Get last 10 orders across all exchanges
    recent_orders = get_recent_orders(limit=10)
    
    # Get specific order by ID
    order = get_order_by_id("c610dfa7-3740-4b72-bcf9-7b3150e745e6", "phemex")
    
    # Get all orders from specific exchange
    coinbase_orders = get_exchange_orders("coinbase")
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

def get_exchange_orders(exchange: str) -> List[Dict[str, Any]]:
    """
    Get all orders from a specific exchange
    
    Args:
        exchange: Exchange name (phemex, coinbase, hyperliquid)
        
    Returns:
        List of order dictionaries
    """
    try:
        orders_file = os.path.join(project_root, 'data', 'outputs', exchange.lower(), 'execution_engine_orders.json')
        
        if not os.path.exists(orders_file):
            logger.warning(f"No order file found for {exchange}: {orders_file}")
            return []
        
        with open(orders_file, 'r') as f:
            data = json.load(f)
            return data.get('orders', [])
            
    except Exception as e:
        logger.error(f"Error reading {exchange} orders: {e}")
        return []

def get_recent_orders(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get recent orders across all exchanges, sorted by timestamp
    
    Args:
        limit: Maximum number of orders to return
        
    Returns:
        List of order dictionaries sorted by timestamp (newest first)
    """
    all_orders = []
    
    # Get orders from all exchanges
    for exchange in ['phemex', 'coinbase', 'hyperliquid']:
        exchange_orders = get_exchange_orders(exchange)
        all_orders.extend(exchange_orders)
    
    # Sort by timestamp (newest first)
    try:
        all_orders.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    except Exception as e:
        logger.warning(f"Error sorting orders by timestamp: {e}")
    
    return all_orders[:limit]

def get_order_by_id(order_id: str, exchange: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Find a specific order by ID
    
    Args:
        order_id: The order ID to search for
        exchange: Optional exchange name to limit search
        
    Returns:
        Order dictionary if found, None otherwise
    """
    exchanges_to_search = [exchange.lower()] if exchange else ['phemex', 'coinbase', 'hyperliquid']
    
    for exch in exchanges_to_search:
        orders = get_exchange_orders(exch)
        for order in orders:
            if order.get('order_id') == order_id:
                return order
    
    return None

def get_orders_by_symbol(symbol: str, exchange: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get all orders for a specific symbol
    
    Args:
        symbol: Trading symbol to search for
        exchange: Optional exchange name to limit search
        
    Returns:
        List of matching order dictionaries
    """
    matching_orders = []
    exchanges_to_search = [exchange.lower()] if exchange else ['phemex', 'coinbase', 'hyperliquid']
    
    for exch in exchanges_to_search:
        orders = get_exchange_orders(exch)
        for order in orders:
            if order.get('symbol', '').upper() == symbol.upper():
                matching_orders.append(order)
    
    return matching_orders

def get_orders_by_strategy(strategy_name: str) -> List[Dict[str, Any]]:
    """
    Get all orders from a specific strategy
    
    Args:
        strategy_name: Strategy name to search for
        
    Returns:
        List of matching order dictionaries
    """
    matching_orders = []
    
    for exchange in ['phemex', 'coinbase', 'hyperliquid']:
        orders = get_exchange_orders(exchange)
        for order in orders:
            if order.get('strategy_name') == strategy_name:
                matching_orders.append(order)
    
    return matching_orders

def get_order_summary() -> Dict[str, Any]:
    """
    Get summary statistics of all orders
    
    Returns:
        Dictionary with order statistics
    """
    summary = {
        'total_orders': 0,
        'by_exchange': {},
        'by_status': {},
        'by_side': {},
        'total_volume': 0.0,
        'latest_timestamp': None
    }
    
    for exchange in ['phemex', 'coinbase', 'hyperliquid']:
        orders = get_exchange_orders(exchange)
        summary['by_exchange'][exchange] = len(orders)
        summary['total_orders'] += len(orders)
        
        for order in orders:
            # Count by status
            status = order.get('status', 'unknown')
            summary['by_status'][status] = summary['by_status'].get(status, 0) + 1
            
            # Count by side
            side = order.get('side', 'unknown')
            summary['by_side'][side] = summary['by_side'].get(side, 0) + 1
            
            # Add to volume (quantity * average_price if available)
            quantity = order.get('quantity', 0)
            avg_price = order.get('average_price', 0)
            if avg_price and avg_price > 0:
                summary['total_volume'] += quantity * avg_price
            
            # Track latest timestamp
            timestamp = order.get('timestamp')
            if timestamp and (not summary['latest_timestamp'] or timestamp > summary['latest_timestamp']):
                summary['latest_timestamp'] = timestamp
    
    return summary

# Convenience function for quick testing
def print_recent_orders(limit: int = 10):
    """Print recent orders in a readable format"""
    orders = get_recent_orders(limit)
    
    print(f"\n🔍 Last {len(orders)} Orders:")
    print("=" * 80)
    
    for i, order in enumerate(orders):
        print(f"{i+1:2d}. {order.get('timestamp', 'Unknown')} | "
              f"{order.get('exchange', '').upper():10s} | "
              f"{order.get('symbol', ''):8s} | "
              f"{order.get('side', '').upper():4s} | "
              f"{order.get('status', ''):10s} | "
              f"${order.get('quantity', 0):8.2f} | "
              f"{order.get('strategy_name', '')}")
    
    print("=" * 80)

if __name__ == "__main__":
    # Test the utility functions
    print("🔍 Order File Reader Test")
    
    # Print summary
    summary = get_order_summary()
    print(f"\n📊 Order Summary: {summary}")
    
    # Print recent orders
    print_recent_orders(5)