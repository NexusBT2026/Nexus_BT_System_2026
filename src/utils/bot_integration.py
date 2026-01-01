#!/usr/bin/env python3
"""
Bot Integration Module
Integrates optimization results with existing trading bot
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import json
import pandas as pd
import logging
from datetime import datetime
from src.utils.analyze_results import OptimizationAnalyzer
from src.utils.token_bucket import TokenBucket, create_exchange_buckets

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

class OptimizedBotIntegration:
    def export_all_absolute_params_to_json(self, csv_file='absolute_params.csv', output_file='live_trading_config.json'):
        """Export all rows from absolute_params.csv as a structured JSON file with all fields and parsed nested objects."""
        import ast
        csv_path = os.path.join(self.results_dir, csv_file)
        if not os.path.exists(csv_path):
            print(f"CSV file not found: {csv_path}")
            return False
        df = pd.read_csv(csv_path)
        records = []
        for _, row in df.iterrows():
            record = {}
            for col in df.columns:
                val = row[col]
                # Try to parse stringified dict/list fields
                if col in ['best_params', 'stats', 'exchanges', 'params']:
                    try:
                        if isinstance(val, str):
                            val = ast.literal_eval(val)
                    except Exception:
                        pass
                record[col] = val
            records.append(record)
        output_path = os.path.join(self.results_dir, output_file)
        with open(output_path, 'w') as f:
            json.dump(records, f, indent=2, default=str)
        print(f"Exported {len(records)} strategies to {output_path}")
        return True
    def __init__(self, results_dir=os.path.join(project_root, 'results')):
        self.results_dir = results_dir
        self.analyzer = OptimizationAnalyzer(results_dir)
        self.active_strategies = []
        
    def load_optimized_strategies(self, max_strategies=10, min_score=1.0):
        """Load top optimized strategies for live trading"""
        print("Loading optimized strategies for live trading...")
        
        if not self.analyzer.load_results():
            print("No optimization results available")
            return False
            
        # Filter by minimum score and get top strategies
        qualified = self.analyzer.qualified_results
        if qualified is None or qualified.empty:
            print("No qualified strategies found")
            return False
            
        # Apply filters
        filtered = qualified[qualified['composite_score'] >= min_score]
        top_strategies = filtered.head(max_strategies)
        
        print(f"Selected {len(top_strategies)} strategies for live trading")
        
        # Convert to bot-compatible format
        self.active_strategies = []
        for _, row in top_strategies.iterrows():
            is_rl = row['strategy_name'] == 'rl_trading_agent'
            strategy_config = {
                'strategy_name': row['strategy_name'],
                'symbol': row['symbol'],
                'timeframe': row['timeframe'],
                'optimized_params': self._load_strategy_params(row),
                'performance_metrics': {
                    'composite_score': float(row['composite_score']),
                    'expected_return': float(row['return_pct']),
                    'win_rate': float(row['win_rate']),
                    'total_trades': int(row['trades']) if pd.notna(row['trades']) else 0
                },
                'risk_settings': self._calculate_risk_settings(row),
                'enabled': True
            }
            if is_rl:
                # Add RL-specific config fields if needed
                strategy_config['rl_agent'] = True
                strategy_config['rl_stats'] = row['stats'] if 'stats' in row else {}
            self.active_strategies.append(strategy_config)
            
        return True
    
    def _load_strategy_params(self, strategy_row):
        """Load optimized parameters for a strategy"""
        symbol = strategy_row['symbol']
        timeframe = strategy_row['timeframe']
        strategy_name = strategy_row['strategy_name']
        
        # Look for individual result file
        result_file = os.path.join(
            self.results_dir, 
            symbol, 
            timeframe, 
            f'results_{strategy_name}_strategy.json'
        )
        
        if os.path.exists(result_file):
            try:
                with open(result_file, 'r') as f:
                    result_data = json.load(f)
                return result_data.get('best_params', {})
            except:
                pass
        
        return {}
    
    def _calculate_risk_settings(self, strategy_row):
        """Calculate risk management settings based on performance"""
        score = strategy_row['composite_score']
        win_rate = strategy_row['win_rate']
        
        # Dynamic position sizing based on performance
        if score >= 2.0:
            position_size = 3.0  # High confidence
        elif score >= 1.5:
            position_size = 2.0  # Medium confidence
        else:
            position_size = 1.0  # Conservative
            
        # Adjust based on win rate
        if win_rate >= 70:
            position_size *= 1.2
        elif win_rate < 60:
            position_size *= 0.8
            
        return {
            'position_size_pct': min(position_size, 5.0),  # Max 5%
            'stop_loss_pct': 2.0,
            'take_profit_pct': 6.0,
            'max_concurrent_trades': 1
        }
    
    def get_strategy_configs_for_bot(self):
        """Get strategy configurations in format compatible with existing bot"""
        if not self.active_strategies:
            return []
            
        bot_configs = []
        for strategy in self.active_strategies:
            if strategy['enabled']:
                config = {
                    'name': strategy['strategy_name'],
                    'symbol': strategy['symbol'],
                    'timeframe': strategy['timeframe'],
                    'parameters': strategy['optimized_params'],
                    'position_size': strategy['risk_settings']['position_size_pct'],
                    'stop_loss': strategy['risk_settings']['stop_loss_pct'],
                    'take_profit': strategy['risk_settings']['take_profit_pct'],
                    'expected_performance': strategy['performance_metrics']
                }
                if strategy.get('rl_agent'):
                    config['rl_agent'] = True
                    config['rl_stats'] = strategy.get('rl_stats', {})
                bot_configs.append(config)
        return bot_configs
    
    def generate_bot_configuration_file(self, output_file='optimized_bot_config.json'):
        """Generate configuration file for bot integration"""
        if not self.active_strategies:
            print("No strategies loaded. Run load_optimized_strategies() first.")
            return False
            
        bot_config = {
            'bot_info': {
                'name': 'Optimized Trading Bot',
                'version': '2.0',
                'optimization_date': datetime.now().isoformat(),
                'total_strategies': len(self.active_strategies)
            },
            'global_settings': {
                'max_portfolio_risk': 0.15,  # 15% max portfolio risk
                'max_daily_trades': 50,
                'emergency_stop_loss': 0.20,  # 20% portfolio emergency stop
                'rebalance_frequency': 'daily'
            },
            'strategies': self.get_strategy_configs_for_bot(),
            'risk_management': {
                'portfolio_heat': 0.02,  # 2% heat per trade
                'max_correlation': 0.7,   # Max 70% correlation
                'drawdown_limit': 0.15    # 15% max drawdown
            }
        }
        
        output_path = os.path.join(self.results_dir, output_file)
        with open(output_path, 'w') as f:
            json.dump(bot_config, f, indent=2)
            
        print(f"Bot configuration saved to: {output_path}")
        return True
    
    def create_integration_example(self):
        """Create example code for integrating with existing bot"""
        example_code = '''
# INTEGRATION EXAMPLE FOR YOUR EXISTING BOT
# Add this to your run_bot.py or main trading script

from src.utils.bot_integration import OptimizedBotIntegration

def load_optimized_strategies():
    """Load optimized strategies instead of hardcoded ones"""
    integration = OptimizedBotIntegration()
    
    # Load top 10 strategies with minimum score of 1.0
    if integration.load_optimized_strategies(max_strategies=10, min_score=1.0):
        
        # Get strategy configurations
        strategy_configs = integration.get_strategy_configs_for_bot()
        
        print(f"Loaded {len(strategy_configs)} optimized strategies:")
        for config in strategy_configs:
            print(f"  {config['name']} | {config['symbol']} {config['timeframe']}")
            print(f"    Expected Return: {config['expected_performance']['expected_return']:.1f}%")
            print(f"    Win Rate: {config['expected_performance']['win_rate']:.1f}%")
            print(f"    Position Size: {config['position_size']:.1f}%")
        
        # Generate bot config file
        integration.generate_bot_configuration_file()
        
        return strategy_configs
    else:
        print("Using fallback strategies - optimization results not available")
        return []

# REPLACE YOUR EXISTING STRATEGY LOADING WITH:
optimized_strategies = load_optimized_strategies()

# USE optimized_strategies INSTEAD OF HARDCODED CONFIGURATIONS
'''
        
        example_file = os.path.join(self.results_dir, 'integration_example.py')
        with open(example_file, 'w') as f:
            f.write(example_code)
            
        print(f"Integration example saved to: {example_file}")
        
    def validate_integration(self):
        """Validate that integration will work with optimization results"""
        print("VALIDATING BOT INTEGRATION")
        print("-" * 40)
        
        # Check if results exist
        if not self.analyzer.load_results():
            print("❌ No optimization results found")
            print("   Run optimization first before integration")
            return False
            
        qualified_count = len(self.analyzer.qualified_results) if self.analyzer.qualified_results is not None else 0
        print(f"✅ Found {qualified_count} qualified strategies")
        
        # Test loading strategies
        if self.load_optimized_strategies(max_strategies=5, min_score=0.5):
            print(f"✅ Successfully loaded {len(self.active_strategies)} strategies")
            
            # Test configuration generation
            if self.generate_bot_configuration_file('test_config.json'):
                print("✅ Configuration file generation works")
                
                # Create integration example
                self.create_integration_example()
                print("✅ Integration example created")
                
                print("\n🚀 INTEGRATION READY!")
                print("Files created:")
                print(f"  - {os.path.join(self.results_dir, 'test_config.json')}")
                print(f"  - {os.path.join(self.results_dir, 'integration_example.py')}")
                
                return True
        
        print("❌ Integration validation failed")
        return False

def main():
    """Test the bot integration"""
    integration = OptimizedBotIntegration()
    integration.validate_integration()

if __name__ == "__main__":
    main()