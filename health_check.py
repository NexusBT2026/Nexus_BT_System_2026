#!/usr/bin/env python3
"""
Nexus Backtesting System - Health Check
Monitor system health and performance metrics.
"""

import os
import psutil
import time
from datetime import datetime
from pathlib import Path
import json

def get_system_info():
    """Get basic system information."""
    info = {
        "cpu_count": psutil.cpu_count(),
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_total": psutil.virtual_memory().total,
        "memory_used": psutil.virtual_memory().used,
        "memory_percent": psutil.virtual_memory().percent,
    }

    # Try to get disk usage (handle Windows path issues)
    try:
        disk_path = 'C:\\' if os.name == 'nt' else '/'
        disk_usage = psutil.disk_usage(disk_path)
        info.update({
            "disk_total": disk_usage.total,
            "disk_used": disk_usage.used,
            "disk_percent": disk_usage.percent,
        })
    except Exception:
        # Fallback values if disk usage fails
        info.update({
            "disk_total": 0,
            "disk_used": 0,
            "disk_percent": 0,
        })

    return info

def get_nexus_info():
    """Get Nexus-specific information."""
    info = {}

    # Check directories
    dirs = ['data', 'results', 'logs', 'src/strategy']
    info['directories'] = {}
    for dir_name in dirs:
        path = Path(dir_name)
        info['directories'][dir_name] = {
            'exists': path.exists(),
            'size_mb': sum(f.stat().st_size for f in path.rglob('*') if f.is_file()) / (1024*1024) if path.exists() else 0
        }

    # Check config
    config_path = Path('config.json')
    info['config'] = {
        'exists': config_path.exists(),
        'size_kb': config_path.stat().st_size / 1024 if config_path.exists() else 0
    }

    # Check strategies
    try:
        from src.strategy import strategies
        info['strategies'] = {
            'count': len(strategies),
            'names': list(strategies.keys())
        }
    except Exception as e:
        info['strategies'] = {'error': str(e)}

    # Check recent results
    results_dir = Path('results')
    if results_dir.exists():
        result_files = list(results_dir.rglob('*.json'))
        info['results'] = {
            'count': len(result_files),
            'recent': max((f.stat().st_mtime for f in result_files), default=0)
        }
    else:
        info['results'] = {'count': 0}

    return info

def format_bytes(bytes_val):
    """Format bytes to human readable."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_val < 1024:
            return f"{bytes_val:.1f}{unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f}TB"

def print_health_report():
    """Print a comprehensive health report."""
    print(f"Nexus Backtesting System - Health Report")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # System info
    sys_info = get_system_info()
    print("🖥️  SYSTEM RESOURCES:")
    print(f"  CPU: {sys_info['cpu_count']} cores ({sys_info['cpu_percent']:.1f}% used)")
    print(f"  Memory: {format_bytes(sys_info['memory_used'])} / {format_bytes(sys_info['memory_total'])} ({sys_info['memory_percent']:.1f}%)")
    print(f"  Disk: {format_bytes(sys_info['disk_used'])} / {format_bytes(sys_info['disk_total'])} ({sys_info['disk_percent']:.1f}%)")

    # Nexus info
    nexus_info = get_nexus_info()
    print("🎯 NEXUS SYSTEM:")
    print(f"  Strategies: {nexus_info['strategies'].get('count', 'Error')}")
    if 'names' in nexus_info['strategies']:
        print(f"  Available: {', '.join(nexus_info['strategies']['names'])}")

    print(f"  Results: {nexus_info['results']['count']} files")
    if nexus_info['results']['count'] > 0:
        recent_time = datetime.fromtimestamp(nexus_info['results']['recent'])
        print(f"  Last result: {recent_time.strftime('%Y-%m-%d %H:%M')}")

    # Directory status
    print("📁 DIRECTORIES:")
    for dir_name, dir_info in nexus_info['directories'].items():
        status = "✅" if dir_info['exists'] else "❌"
        size = f"{dir_info['size_mb']:.1f}MB"
        print(f"  {status} {dir_name}/ ({size})")

    # Config status
    config_status = "✅" if nexus_info['config']['exists'] else "❌"
    config_size = f"{nexus_info['config']['size_kb']:.1f}KB"
    print(f"  {config_status} config.json ({config_size})")

    # Health assessment
    print("🏥 HEALTH ASSESSMENT:")    
    issues = []

    if sys_info['memory_percent'] > 90:
        issues.append("High memory usage")
    if sys_info['disk_percent'] > 95:
        issues.append("Low disk space")
    if not nexus_info['config']['exists']:
        issues.append("Missing config.json")
    if nexus_info['strategies'].get('count', 0) == 0:
        issues.append("No strategies found")

    if issues:
        print("❌ Issues found:")
        for issue in issues:
            print(f"   • {issue}")
    else:
        print("✅ System is healthy")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    print_health_report()
