#!/usr/bin/env python3
"""
Live Trading Configuration Generator
Converts optimization results into production-ready trading configurations
"""
import os
import json
import pandas as pd
from datetime import datetime

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

class LiveConfigGenerator:
    def __init__(self, results_dir=os.path.join(project_root, 'results'), output_dir=os.path.join(project_root, 'live_configs')):
        self.results_dir = results_dir
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def generate_all_configs(self):
        """Generate all configuration files"""
        print("\nGENERATING LIVE TRADING CONFIGURATIONS")
        print("="*60)
        
        # Load qualified results
        csv_file = os.path.join(self.results_dir, 'all_qualified_results.csv')
        if not os.path.exists(csv_file):
            print("No qualified results found. Run optimization first!")
            return False
            
        df = pd.read_csv(csv_file)
        print(f"Found {len(df)} qualified strategies")
        return True

def main():
    generator = LiveConfigGenerator()
    generator.generate_all_configs()

if __name__ == "__main__":
    main()