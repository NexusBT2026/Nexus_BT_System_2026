#!/usr/bin/env python3
"""
Real-time Optimization Progress Monitor
Monitors the ongoing optimization and provides live status updates
"""
import os
import json
import time
import glob
from datetime import datetime, timedelta

# Define base data path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
BASE_DATA_PATH = os.path.join(project_root, 'markets_info')

class OptimizationMonitor:
    def __init__(self, results_dir=os.path.join(project_root, 'results')):
        self.results_dir = results_dir
        self.start_time = datetime.now()
        self._cached_total_tasks = None
        
    def calculate_dynamic_total_tasks(self):
        """Dynamically calculate total tasks based on current pipeline configuration"""
        if self._cached_total_tasks is not None:
            return self._cached_total_tasks
            
        try:
            # Import strategies dynamically to get available strategies
            from src.strategy import strategies
            
            # Get all available strategy names (excluding RL agent which is special)
            all_strategies = [name for name in strategies.keys() if name != 'rl_trading_agent']
            
            timeframes = ['5m', '15m', '30m', '1h', '2h', '4h', '6h', '12h', '1d']
            
            # Try to get actual symbol count from running optimization
            symbol_count = self.get_actual_symbol_count()
            if symbol_count == 0:
                print(f"[WARNING] Could not detect symbols, using minimal fallback of 1")
                symbol_count = 1  # Minimal fallback for scheduler mode
            
            # FIXED: Count result files, not trials - each optimization produces one result file
            total_result_files = len(all_strategies) * len(timeframes) * symbol_count
            
            self._cached_total_tasks = total_result_files
            print(f"[INFO] Calculated total result files: {total_result_files:,} ({len(all_strategies)} strategies x {len(timeframes)} timeframes x {symbol_count} symbols)")
            print(f"[NOTE] If running in scheduler/reoptimization mode, only a subset of these tasks will be executed")
            return total_result_files
            
        except Exception as e:
            print(f"[WARNING] Error calculating dynamic total, using fallback: {e}")
            return 810  # Calculated fallback (6×9×15)
    
    def get_actual_symbol_count(self):
        """Get actual symbol count from cached market files - counts per-exchange symbols"""
        try:
            import json
            
            # Count symbols per exchange (NOT deduplicated - BTC on Phemex + BTC on Coinbase = 2)
            total_symbols = 0
            
            # Read from cached market files
            market_files = {
                'phemex': os.path.join(BASE_DATA_PATH, 'phemex', 'phemex_markets_loads_data_bot.json'),
                'coinbase': os.path.join(BASE_DATA_PATH, 'coinbase', 'coinbase_markets_loads_data_bot.json'),
                'hyperliquid': os.path.join(BASE_DATA_PATH, 'hyperliquid', 'hyperliquid_symbols_meta_data_bot.json'),
                'binance': os.path.join(BASE_DATA_PATH, 'binance', 'binance_markets_loads_data_bot.json'),
                'kucoin': os.path.join(BASE_DATA_PATH, 'kucoin', 'kucoin_markets_loads_data_bot.json')
            }
            
            exchange_counts = {}
            for exchange, file_path in market_files.items():
                try:
                    if os.path.exists(file_path):
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                            
                            count = 0
                            # Handle different file structures
                            if isinstance(data, list):
                                # Phemex, Kucoin: list of objects
                                count = len(data)
                            elif isinstance(data, dict):
                                # Coinbase, Binance: {"symbols": [...]}
                                if 'symbols' in data and isinstance(data['symbols'], list):
                                    count = len(data['symbols'])
                                elif 'base_symbols' in data:
                                    count = len(data['base_symbols'])
                            
                            if count > 0:
                                exchange_counts[exchange] = count
                                total_symbols += count
                except Exception as e:
                    continue
            
            if total_symbols > 0:
                counts_str = ', '.join([f'{ex}: {cnt}' for ex, cnt in exchange_counts.items()])
                print(f"[INFO] Detected {total_symbols} total symbols across exchanges ({counts_str})")
                return total_symbols
            else:
                # Fallback to directory structure
                symbols = set()
                for root, dirs, files in os.walk(self.results_dir):
                    for dir_name in dirs:
                        if dir_name not in ['1d', '1h', '2h', '4h', '5m', '6h', '12h', '15m', '30m']:
                            symbols.add(dir_name)
                
                if symbols:
                    print(f"[INFO] Detected {len(symbols)} symbols from directory structure")
                    return len(symbols)
                else:
                    print(f"[WARNING] No symbols detected, using fallback estimate")
                    return 1  # Conservative fallback for scheduler mode
                    
        except Exception as e:
            print(f"[WARNING] Error detecting symbols: {e}, using fallback")
            return 1  # Conservative fallback
        
    def monitor_progress(self, total_tasks=None, refresh_interval=60):
        """Monitor optimization progress with live updates"""
        if total_tasks is None:
            total_tasks = self.calculate_dynamic_total_tasks()
            
        print("Starting Optimization Progress Monitor")
        print(f"Expected total tasks: {total_tasks:,}")
        print(f"Refresh interval: {refresh_interval} seconds")
        print("=" * 80)
        
        try:
            while True:
                pattern = os.path.join(self.results_dir, '**', 'results_*.json')
                completed_files = glob.glob(pattern, recursive=True)
                completed = len(completed_files)
                progress_pct = (completed / total_tasks * 100) if total_tasks > 0 else 0
                
                # Create progress bar
                bar_length = 50
                filled_length = int(bar_length * completed // total_tasks) if total_tasks > 0 else 0
                bar = '█' * filled_length + '░' * (bar_length - filled_length)
                
                # Calculate ETA
                elapsed = datetime.now() - self.start_time
                remaining_tasks = total_tasks - completed
                
                if completed > 0 and elapsed.total_seconds() > 0:
                    rate_per_second = completed / elapsed.total_seconds()
                    rate_per_hour = rate_per_second * 3600
                    eta_seconds = remaining_tasks / rate_per_second if rate_per_second > 0 else 0
                    
                    if eta_seconds < 86400:  # Less than 1 day
                        eta_time = (datetime.now() + timedelta(seconds=eta_seconds))
                        eta_str = eta_time.strftime("%H:%M:%S")
                    else:
                        eta_days = eta_seconds / 86400
                        eta_str = f"{eta_days:.1f} days"
                else:
                    rate_per_hour = 0
                    eta_str = "Unknown"
                
                # Get latest optimization details
                latest_info = self.get_latest_optimization_info()
                
                print(f"\n{datetime.now().strftime('%H:%M:%S')} - CORRECTED Optimization Progress")
                print(f"[{bar}] {progress_pct:.1f}%")
                print(f"Completed: {completed:,} / {total_tasks:,} (Remaining: {remaining_tasks:,})")
                print(f"Elapsed: {str(elapsed).split('.')[0]}")
                print(f"Rate: {rate_per_hour:.1f} optimizations/hour")
                print(f"ETA: {eta_str}")
                
                if latest_info:
                    print(f"Recently completed: {latest_info}")
                
                if completed >= total_tasks:
                    print(f"\nOPTIMIZATION COMPLETE! All {total_tasks:,} tasks finished!")
                    break
                    
                print("-" * 80)
                time.sleep(refresh_interval)
                
        except KeyboardInterrupt:
            print(f"\nMonitor stopped. Current progress: {completed:,}/{total_tasks:,}")
    
    def get_latest_optimization_info(self):
        """Get info about the most recently completed optimizations"""
        try:
            pattern = os.path.join(self.results_dir, '**', 'results_*.json')
            completed_files = glob.glob(pattern, recursive=True)
            
            if not completed_files:
                return None
            
            # Sort by file modification time (most recent first)
            completed_files.sort(key=os.path.getmtime, reverse=True)
            
            # Get info from the most recent file only
            if completed_files:
                file_path = completed_files[0]
                try:
                    # Extract info from file path
                    path_parts = file_path.replace('\\', '/').split('/')
                    if len(path_parts) >= 3:
                        symbol = path_parts[-3]
                        timeframe = path_parts[-2]
                        filename = path_parts[-1]
                        
                        # Extract strategy name from filename
                        strategy_name = filename.replace('results_', '').replace('_strategy.json', '')
                        
                        # Try to get success status and score
                        try:
                            with open(file_path, 'r') as f:
                                data = json.load(f)
                                success = data.get('success', False)
                                status = "SUCCESS" if success else "FAILED"
                                
                                # Get score if available
                                score = data.get('composite_score', 0)
                                if score and score != float('-inf'):
                                    return f"{status} {symbol} {timeframe} {strategy_name} (Score: {score:.2f})"
                                else:
                                    return f"{status} {symbol} {timeframe} {strategy_name}"
                        except:
                            return f"UNKNOWN {symbol} {timeframe} {strategy_name}"
                            
                except Exception:
                    return None
            
            return None
                
        except Exception:
            return None
    
    def get_strategy_progress_analysis(self, elapsed_time=None):
        """Analyze progress by strategy to show individual ETAs and performance"""
        try:
            pattern = os.path.join(self.results_dir, '**', 'results_*.json')
            all_files = glob.glob(pattern, recursive=True)
            
            strategy_stats = {}
            
            # Only consider files modified in the last 2 hours for rate calculation
            recent_threshold = datetime.now() - timedelta(hours=2)
            
            for file_path in all_files:
                try:
                    # Extract strategy from filename
                    filename = os.path.basename(file_path)
                    strategy_name = filename.replace('results_', '').replace('_strategy.json', '')
                    
                    # Get file modification time
                    mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    if strategy_name not in strategy_stats:
                        strategy_stats[strategy_name] = {
                            'completed': 0,
                            'recent_completions': [],
                            'new_completions': 0
                        }
                    
                    strategy_stats[strategy_name]['completed'] += 1
                    
                    # ONLY track very recent completions for accurate ETA
                    if mod_time > recent_threshold:
                        strategy_stats[strategy_name]['recent_completions'].append(mod_time)
                    
                    # Count new completions since the monitor started
                    if mod_time > self.start_time:
                        strategy_stats[strategy_name]['new_completions'] += 1
                        
                except Exception:
                    continue
            
            # Calculate rates and ETAs for each strategy  
            # Each strategy runs on multiple symbol-timeframe combinations
            # NOTE: Each combination produces ONE result file (trials are internal to the optimization)
            symbols_count = self.get_actual_symbol_count() or 15
            timeframes_count = 9  # From pipeline: ['5m', '15m', '30m', '1h', '2h', '4h', '6h', '12h', '1d']
            total_per_strategy = symbols_count * timeframes_count  # One result file per symbol-timeframe combo
            analysis = []
            
            for strategy, stats in strategy_stats.items():
                completed = stats['completed']
                new_completed = stats['new_completions']
                recent_completions = stats['recent_completions']
                
                # Calculate completion rate based on ONLY recent activity
                avg_minutes_per_completion = 0
                if len(recent_completions) >= 2:
                    recent_completions.sort()
                    time_differences = []
                    for i in range(1, len(recent_completions)):
                        diff_seconds = (recent_completions[i] - recent_completions[i-1]).total_seconds()
                        time_differences.append(diff_seconds / 60)  # Convert to minutes
                    
                    if time_differences:
                        avg_minutes_per_completion = sum(time_differences) / len(time_differences)
                
                # If no recent activity, estimate based on current progress rate
                elif new_completed > 0:
                    elapsed_minutes = (datetime.now() - self.start_time).total_seconds() / 60
                    avg_minutes_per_completion = elapsed_minutes / new_completed
                
                remaining = total_per_strategy - completed
                
                if avg_minutes_per_completion > 0 and remaining > 0:
                    total_minutes_remaining = remaining * avg_minutes_per_completion
                    eta_hours = total_minutes_remaining / 60
                    
                    # More realistic ETA formatting
                    if eta_hours < 1:
                        eta_str = f"{int(total_minutes_remaining)}m"
                    elif eta_hours < 24:
                        eta_str = f"{int(eta_hours)}h {int((eta_hours % 1) * 60)}m"
                    elif eta_hours < 168:  # Less than a week
                        eta_days = eta_hours / 24
                        eta_str = f"{int(eta_days)}d {int((eta_days % 1) * 24)}h"
                    else:
                        # If over a week, show in weeks
                        eta_weeks = eta_hours / 168
                        eta_str = f"{eta_weeks:.1f} weeks"
                else:
                    eta_str = "Calculating..."
                
                progress_pct = (completed / total_per_strategy * 100) if total_per_strategy > 0 else 0
                
                # Show recent activity info
                recent_count = len(recent_completions)
                activity_indicator = f"({recent_count} in 2h)" if recent_count > 0 else "(no recent)"
                
                analysis.append({
                    'strategy': strategy,
                    'completed': completed,
                    'total': total_per_strategy,
                    'progress_pct': progress_pct,
                    'avg_time': avg_minutes_per_completion,
                    'eta': eta_str,
                    'activity': activity_indicator,
                    'new_count': new_completed,
                    'recent_count': recent_count
                })
            
            # Sort by progress percentage
            analysis.sort(key=lambda x: x['progress_pct'], reverse=True)
            return analysis
            
        except Exception as e:
            return [{'error': f"Analysis failed: {e}"}]

    def get_active_optimization_status(self):
        try:
            # Check for any files modified in the last 10 minutes
            recent_threshold = datetime.now() - timedelta(minutes=10)
            pattern = os.path.join(self.results_dir, '**', 'results_*.json')
            all_files = glob.glob(pattern, recursive=True)
            
            recent_files = []
            for file_path in all_files:
                mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                if mod_time > recent_threshold:
                    recent_files.append((mod_time, file_path))
            
            if recent_files:
                recent_files.sort(reverse=True)
                return f"[ACTIVE] {len(recent_files)} files modified in last 10 minutes"
            else:
                # Check if any Python processes are running that might be doing optimization
                import psutil
                optuna_processes = []
                try:
                    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                        if proc.info['cmdline']:
                            cmd_str = ' '.join(proc.info['cmdline'])
                            if 'pipeline_BT_unified_async.py' in cmd_str and 'optuna' in cmd_str:
                                optuna_processes.append(proc.info['pid'])
                except:
                    pass
                
                if optuna_processes:
                    return f"[WAITING] Pipeline running (PID: {optuna_processes}), no recent results"
                else:
                    return "[IDLE] No recent activity, no optimization process found"
                
        except Exception as e:
            return f"[ERROR] Error checking activity: {e}"

    def monitor_progress_detailed(self, total_tasks=None, refresh_interval=30):
        """Enhanced monitor with more detailed status"""
        if total_tasks is None:
            total_tasks = self.calculate_dynamic_total_tasks()
            
        print("Starting DETAILED Optimization Progress Monitor")
        print(f"Expected total tasks: {total_tasks:,}")
        print(f"Refresh interval: {refresh_interval} seconds")
        print("=" * 80)
        
        last_count = 0
        started_optimizing = False
        
        try:
            while True:
                pattern = os.path.join(self.results_dir, '**', 'results_*.json')
                completed_files = glob.glob(pattern, recursive=True)
                completed = len(completed_files)
                progress_pct = (completed / total_tasks * 100) if total_tasks > 0 else 0
                
                # Track progress but don't warn about "stalling" since optimizations take time
                if completed > last_count:
                    started_optimizing = True
                    
                last_count = completed
                
                # Create progress bar
                bar_length = 50
                filled_length = int(bar_length * completed // total_tasks)
                bar = '█' * filled_length + '░' * (bar_length - filled_length)
                
                # Calculate ETA
                elapsed = datetime.now() - self.start_time
                # Only calculate ETA if we have meaningful elapsed time (at least 10 seconds)
                if completed > 0 and elapsed.total_seconds() > 10:
                    rate = completed / elapsed.total_seconds()
                    remaining = total_tasks - completed
                    eta_seconds = remaining / rate if rate > 0 else 0
                    eta = datetime.now() + timedelta(seconds=eta_seconds)
                    eta_str = eta.strftime("%H:%M:%S")
                else:
                    eta_str = "Calculating..."
                
                # Get activity status and strategy analysis
                activity_status = self.get_active_optimization_status()
                latest_info = self.get_latest_optimization_info()
                strategy_analysis = self.get_strategy_progress_analysis()
                
                print(f"\n{datetime.now().strftime('%H:%M:%S')} - Detailed Optimization Progress")
                print(f"[{bar}] {progress_pct:.1f}%")
                print(f"Completed: {completed:,} / {total_tasks:,}")
                print(f"Elapsed: {str(elapsed).split('.')[0]}")
                print(f"ETA: {eta_str}")
                
                print(f"Activity: {activity_status}")
                
                if latest_info:
                    print(f"Last completed: {latest_info}")
                
                # Show overall ETA based on current rate
                # Only show if we have at least 30 seconds of elapsed time to avoid inflated rates
                if completed > 0 and elapsed.total_seconds() > 30:
                    current_rate_per_hour = (completed / elapsed.total_seconds()) * 3600
                    remaining_tasks = total_tasks - completed
                    hours_remaining = remaining_tasks / current_rate_per_hour if current_rate_per_hour > 0 else 0
                    
                    if hours_remaining < 1:
                        overall_eta_str = f"{int(hours_remaining * 60)}m"
                    elif hours_remaining < 24:
                        overall_eta_str = f"{int(hours_remaining)}h {int((hours_remaining % 1) * 60)}m"
                    else:
                        days_remaining = hours_remaining / 24
                        overall_eta_str = f"{int(days_remaining)}d {int((days_remaining % 1) * 24)}h"
                    
                    print(f"\nOverall ETA (current rate): {overall_eta_str} ({current_rate_per_hour:.1f}/hour)")
                else:
                    print(f"\nOverall ETA: Calculating... (need more data)")
                
                if completed >= total_tasks:
                    print(f"\nOPTIMIZATION COMPLETE! All {total_tasks:,} tasks finished!")
                    break
                    
                print("-" * 80)
                time.sleep(refresh_interval)
                
        except KeyboardInterrupt:
            print(f"\nMonitor stopped. Current progress: {completed:,}/{total_tasks:,}")

    def get_quick_status(self):
        """Get a quick status summary without continuous monitoring"""
        total_tasks = self.calculate_dynamic_total_tasks()
        pattern = os.path.join(self.results_dir, '**', 'results_*.json')
        completed_files = glob.glob(pattern, recursive=True)
        completed = len(completed_files)
        progress_pct = (completed / total_tasks * 100) if total_tasks > 0 else 0
        
        elapsed = datetime.now() - self.start_time
        if completed > 0:
            rate = completed / elapsed.total_seconds()
            remaining = total_tasks - completed  
            eta_seconds = remaining / rate if rate > 0 else 0
            eta = datetime.now() + timedelta(seconds=eta_seconds)
            eta_str = eta.strftime("%H:%M:%S")
        else:
            eta_str = "Unknown"
            
        activity_status = self.get_active_optimization_status()
        
        return {
            'completed': completed,
            'total_tasks': total_tasks,
            'progress_pct': progress_pct,
            'elapsed': str(elapsed).split('.')[0],
            'eta': eta_str,
            'activity': activity_status
        }

def main():
    monitor = OptimizationMonitor()
    # Use detailed monitor for better insights
    monitor.monitor_progress_detailed()

if __name__ == "__main__":
    main()