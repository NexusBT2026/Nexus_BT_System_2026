#!/usr/bin/env python3
"""
Automated Re-optimization Scheduler
Runs optimization cycles based on strategy-specific schedules
"""
import os
import sys
import time
import schedule
import logging
from datetime import datetime

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from src.pipeline.pipeline_unified import run_reoptimization_cycle, discover_symbols, run_strategy_optimization

class AutoOptimizationScheduler:
    # Per-strategy re-optimization frequency in days
    STRATEGY_SCHEDULE = {
        'adaptive_rsi': 14,
        'ema_channel_scalping': 7,
        'macd_ema_atr': 14,
        'mean_reversion_bb_rsi': 30,
        'rsi_divergence': 30,
        'supply_demand_spot': 30
    }

    # Map strategy name to last run file
    LAST_RUN_FILES = {
        'adaptive_rsi': os.path.join(project_root, 'results', 'last_run_adaptive_rsi.json'),
        'ema_channel_scalping': os.path.join(project_root, 'results', 'last_run_ema_channel_scalping.json'),
        'macd_ema_atr': os.path.join(project_root, 'results', 'last_run_macd_ema_atr.json'),
        'mean_reversion_bb_rsi': os.path.join(project_root, 'results', 'last_run_mean_reversion_bb_rsi.json'),
        'rsi_divergence': os.path.join(project_root, 'results', 'last_run_rsi_divergence.json'),
        'supply_demand_spot': os.path.join(project_root, 'results', 'last_run_supply_demand_spot.json')
    }

    def get_due_strategies(self):
        from datetime import datetime, timedelta
        import json
        due = []
        now = datetime.now()
        for strat, freq in self.STRATEGY_SCHEDULE.items():
            last_file = self.LAST_RUN_FILES.get(strat)
            last_run = None
            if last_file and os.path.exists(last_file):
                try:
                    with open(last_file, 'r') as f:
                        data = json.load(f)
                        last_run = datetime.fromisoformat(data.get('last_run'))
                except Exception:
                    pass
            if not last_run or (now - last_run).days >= freq:
                due.append(strat)
        return due
    def __init__(self, max_workers=16):
        self.max_workers = max_workers
        self.is_running = False
        self.optimizer = 'hyperopt'  # Default optimizer, can be overridden later
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s %(levelname)s %(message)s',
            handlers=[
                logging.FileHandler('outputs/log/scheduler.log'),
                logging.StreamHandler()
            ]
        )
        
    def run_scheduled_optimization(self):
        """Run optimization cycle for strategies that are due (per-strategy schedule)"""
        if self.is_running:
            logging.info("Optimization already running, skipping scheduled run")
            return
        self.is_running = True
        try:
            logging.info("Starting scheduled optimization cycle (per-strategy)...")
            symbols = discover_symbols()
            due_strategies = self.get_due_strategies()
            if not due_strategies:
                logging.info("No strategies are due for re-optimization.")
                return
            logging.info(f"Strategies due for optimization: {due_strategies}")
            # If run_reoptimization_cycle does not support filtering, filter symbols/strategies before calling
            result = run_reoptimization_cycle(symbols=symbols, max_workers=self.max_workers, optimizer=getattr(self, 'optimizer', 'hyperopt'))
            if result.get('total_optimizations', 0) > 0:
                logging.info(f"Completed {result['total_optimizations']} optimizations")
                logging.info(f"Successful: {result['successful_optimizations']}")
                self.update_bot_configs_if_needed(result)
            else:
                logging.info("No strategies required optimization")
        except Exception as e:
            logging.error(f"Scheduled optimization failed: {e}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
        finally:
            self.is_running = False
    
    def run_full_optimization(self):
        """Run full optimization for all strategies (monthly full sweep)"""
        if self.is_running:
            logging.info("Optimization already running, skipping full run")
            return
            
        self.is_running = True
        try:
            logging.info("Starting FULL optimization cycle...")
            
            symbols = discover_symbols()
            
            # Run full optimization (all strategies)
            result = run_strategy_optimization(
                symbols=symbols, 
                max_workers=self.max_workers,
                reoptimization_mode=False,  # Full run
                optimizer=getattr(self, 'optimizer', 'hyperopt')
            )
            
            logging.info(f"Full optimization completed: {result['total_optimizations']} total")
            
            # Always update configs after full run
            self.update_bot_configs_if_needed(result)
            
        except Exception as e:
            logging.error(f"Full optimization failed: {e}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
        finally:
            self.is_running = False
    
    def update_bot_configs_if_needed(self, optimization_result):
        """Update bot configurations if optimization found improvements"""
        try:
            from src.utils.bot_integration import OptimizedBotIntegration
            
            # Load optimization results and update bot configs
            integration = OptimizedBotIntegration()
            if integration.load_optimized_strategies(max_strategies=20, min_score=1.0):
                # Generate new bot configuration
                integration.generate_bot_configuration_file('live_bot_config.json')
                logging.info("Updated bot configuration with new optimization results")
            else:
                logging.warning("No qualified strategies found for bot update")
                
        except Exception as e:
            logging.error(f"Failed to update bot configs: {e}")
    
    def setup_schedules(self):
        """Setup optimization schedules"""
        # Daily check for strategies that need reoptimization
        schedule.every().day.at("02:00").do(self.run_scheduled_optimization)
        
        # Weekly more thorough check
        schedule.every().sunday.at("01:00").do(self.run_scheduled_optimization)
        
        # Monthly full optimization sweep (run on the 1st day of each month at 03:00)
        schedule.every().day.at("03:00").do(self.run_monthly_full_optimization_if_first_day)
        
        logging.info("Optimization schedules configured:")
        logging.info("  Daily at 02:00 - Check for due strategies")
        logging.info("  Sunday at 01:00 - Weekly thorough check")
        logging.info("  1st day of month at 03:00 - Full optimization sweep")
    
    def run_monthly_full_optimization_if_first_day(self):
        """Run full optimization if today is the first day of the month"""
        if datetime.now().day == 1:
            self.run_full_optimization()

    def run_scheduler(self):
        """Run the scheduler loop"""
        self.setup_schedules()
        
        logging.info(f"Automated optimization scheduler started (max_workers={self.max_workers})")
        logging.info("Press Ctrl+C to stop")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            logging.info("Scheduler stopped by user")
        except Exception as e:
            logging.error(f"Scheduler error: {e}")
    
    def run_now(self, full=False):
        """Run optimization immediately"""
        if full:
            self.run_full_optimization()
        else:
            self.run_scheduled_optimization()


def main():
    """Main scheduler entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Automated Optimization Scheduler')
    parser.add_argument('--workers', type=int, default=16, help='Max worker threads (default: 16)')
    parser.add_argument('--run-now', action='store_true', help='Run optimization immediately')
    parser.add_argument('--full', action='store_true', help='Run full optimization (all strategies)')
    parser.add_argument('--daemon', action='store_true', help='Run as daemon scheduler')
    parser.add_argument('--rl-only', action='store_true', help='Run only RL agent optimization jobs')
    parser.add_argument('--strategy', type=str, nargs='+', help='Run only these strategies (space/comma separated)')
    parser.add_argument('--force', action='store_true', help='Force rerun even if results exist')
    parser.add_argument('--optimizer', choices=['hyperopt', 'optuna'], default='hyperopt', help='Choose optimizer: hyperopt or optuna (default: hyperopt)')

    args = parser.parse_args()

    scheduler = AutoOptimizationScheduler(max_workers=args.workers)
    scheduler.optimizer = args.optimizer  # Attach optimizer to scheduler instance

    if args.rl_only:
        print(f"Running RL agent optimization only (workers={args.workers}, optimizer={args.optimizer})")
        from src.pipeline.pipeline_unified import discover_symbols, run_strategy_optimization
        symbols = discover_symbols()
        result = run_strategy_optimization(symbols=symbols, max_workers=args.workers, target_strategies=['rl_trading_agent'], optimizer=args.optimizer)
        print(f"RL agent optimization complete. Ran {result.get('total_optimizations', 0)} RL jobs.")
        print(f"Successful RL optimizations: {result.get('successful_optimizations', 0)}")
    elif args.run_now:
        if args.strategy:
            # Allow comma-separated or space-separated
            if len(args.strategy) == 1 and ',' in args.strategy[0]:
                strategies = [s.strip() for s in args.strategy[0].split(',')]
            else:
                strategies = args.strategy
            print(f"Running optimization now for strategies: {strategies} (workers={args.workers}, force={args.force}, optimizer={args.optimizer})")
            from src.pipeline.pipeline_unified import discover_symbols, run_reoptimization_cycle
            symbols = discover_symbols()
            result = run_reoptimization_cycle(symbols=symbols, max_workers=args.workers, target_strategies=strategies, force_rerun=args.force, optimizer=args.optimizer)
            print(f"Optimization complete. Ran {result.get('total_optimizations', 0)} jobs.")
            print(f"Successful optimizations: {result.get('successful_optimizations', 0)}")
        else:
            print(f"Running optimization now (full={args.full}, workers={args.workers}, optimizer={args.optimizer})")
            # For full run, pass optimizer to run_full_optimization if needed
            # But run_now() does not currently accept optimizer, so call run_strategy_optimization directly
            from src.pipeline.pipeline_unified import discover_symbols, run_strategy_optimization
            symbols = discover_symbols()
            result = run_strategy_optimization(symbols=symbols, max_workers=args.workers, reoptimization_mode=False, optimizer=args.optimizer)
            print(f"Full optimization complete. Ran {result.get('total_optimizations', 0)} jobs.")
            print(f"Successful optimizations: {result.get('successful_optimizations', 0)}")
    elif args.daemon:
        print(f"Starting scheduler daemon (workers={args.workers})")
        scheduler.run_scheduler()
    else:
        print("Usage:")
        print("  python src/backtest/scheduler.py --run-now              # Run optimization now")
        print("  python src/backtest/scheduler.py --run-now --full       # Run full optimization now")
        print("  python src/backtest/scheduler.py --run-now --strategy rsi_divergence")
        print("  python src/backtest/scheduler.py --run-now --strategy macd_ema_atr --optimizer optuna --force")
        print("  python src/backtest/scheduler.py --daemon               # Run as scheduled daemon")
        print("  python src/backtest/scheduler.py --workers 16 --daemon  # Custom worker count")
        print("  python src/backtest/scheduler.py --rl-only              # Run only RL agent optimization jobs")

if __name__ == "__main__":
    main()