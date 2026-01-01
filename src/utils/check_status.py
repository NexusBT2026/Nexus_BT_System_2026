#!/usr/bin/env python3
"""
Quick Optimization Status Checker
Provides instant status without full monitoring
"""
import os
import glob
import json
from datetime import datetime

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

def check_optimization_status():
    """Quick status check of optimization progress"""
    results_dir = os.path.join(project_root, 'results')
    
    print("OPTIMIZATION STATUS CHECK")
    print("=" * 50)
    print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Count completed optimizations
    pattern = os.path.join(results_dir, '**', 'results_*.json')
    completed_files = glob.glob(pattern, recursive=True)
    completed_count = len(completed_files)
    
    print(f"Completed optimizations: {completed_count:,}")
    
    print("\nAvailable commands:")
    print("   python src/utils/analyze_results.py     - Full results analysis")
    print("   python src/utils/generate_configs.py    - Generate trading configs") 
    print("   python src/utils/monitor_progress.py    - Real-time monitoring")

if __name__ == "__main__":
    check_optimization_status()