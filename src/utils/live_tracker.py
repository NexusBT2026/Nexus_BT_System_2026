#!/usr/bin/env python3
"""
Live Optimization Tracker
Shows real-time what strategies are being optimized
"""
import os
import time
import glob
import json
from datetime import datetime

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

class LiveOptimizationTracker:
    def __init__(self, results_dir=os.path.join(project_root, 'results')):
        self.results_dir = results_dir
        self.last_count = 0
        self.last_check = datetime.now()
        
    def track_live_optimizations(self, refresh_interval=10):
        """Track optimizations in real-time with fast refresh"""
        print("LIVE OPTIMIZATION TRACKER")
        print("=" * 60)
        print("Tracking new completions every 10 seconds...")
        print("Press Ctrl+C to stop")
        print("=" * 60)
        
        try:
            while True:
                current_time = datetime.now()
                
                # Get all completed results
                pattern = os.path.join(self.results_dir, '**', 'results_*.json')
                completed_files = glob.glob(pattern, recursive=True)
                current_count = len(completed_files)
                
                # Show progress
                print(f"\n{current_time.strftime('%H:%M:%S')} - Total completed: {current_count:,}")
                
                # Find new completions since last check
                if current_count > self.last_count:
                    new_completions = current_count - self.last_count
                    print(f"🔥 {new_completions} NEW completions in last {refresh_interval}s!")
                    
                    # Show the most recent ones
                    self.show_recent_completions(completed_files, new_completions)
                    
                    self.last_count = current_count
                else:
                    print("⏳ No new completions...")
                
                # Show optimization rate
                elapsed = (current_time - self.last_check).total_seconds()
                if elapsed > 0 and current_count > 0:
                    rate = current_count / elapsed
                    print(f"📊 Rate: {rate:.1f} optimizations/second")
                
                print("-" * 60)
                time.sleep(refresh_interval)
                
        except KeyboardInterrupt:
            print(f"\n🛑 Tracker stopped. Final count: {current_count:,}")
    
    def show_recent_completions(self, completed_files, count):
        """Show the most recent completions"""
        try:
            # Sort by modification time
            completed_files.sort(key=os.path.getmtime, reverse=True)
            
            print(f"📋 Last {min(count, 5)} completions:")
            
            for i, file_path in enumerate(completed_files[:min(count, 5)]):
                try:
                    # Extract info from path
                    path_parts = file_path.replace('\\', '/').split('/')
                    if len(path_parts) >= 3:
                        symbol = path_parts[-3]
                        timeframe = path_parts[-2] 
                        filename = path_parts[-1]
                        strategy_name = filename.replace('results_', '').replace('_strategy.json', '')
                        
                        # Get result details
                        try:
                            with open(file_path, 'r') as f:
                                data = json.load(f)
                                success = data.get('success', False)
                                score = data.get('composite_score', 0)
                                
                                if success and score != float('-inf'):
                                    status_icon = "✅"
                                    score_text = f"Score: {score:.2f}"
                                elif success:
                                    status_icon = "⚠️"
                                    score_text = "No score"
                                else:
                                    status_icon = "❌"
                                    score_text = "Failed"
                                
                                print(f"   {status_icon} {symbol} {timeframe} {strategy_name} ({score_text})")
                                
                        except:
                            print(f"   ❓ {symbol} {timeframe} {strategy_name} (Unknown)")
                            
                except Exception:
                    continue
                    
        except Exception as e:
            print(f"   Error showing recent: {e}")

def main():
    """Run the live tracker"""
    tracker = LiveOptimizationTracker()
    tracker.track_live_optimizations()

if __name__ == "__main__":
    main()