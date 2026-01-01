#!/usr/bin/env python3
"""
Results Analysis Dashboard for Pipeline Optimization
Analyzes optimization results and provides comprehensive insights
"""
import os
import json
import pandas as pd
import numpy as np
from datetime import datetime

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

class OptimizationAnalyzer:
    def __init__(self, results_dir=os.path.join(project_root, 'results'), qualified_results_file=None):
        self.results_dir = results_dir
        self.analysis_data = None
        self.qualified_results = None
        self.qualified_results_file = qualified_results_file
        
    def load_results(self):
        """Load optimization results from saved files"""
        print("Loading optimization results...")
        
        # Load main analysis file
        analysis_file = os.path.join(self.results_dir, 'optimization_analysis.json')
        if os.path.exists(analysis_file):
            with open(analysis_file, 'r') as f:
                self.analysis_data = json.load(f)
            print(f"Loaded main analysis: {self.analysis_data.get('total_results', 0)} total results")
        
        # Load qualified results CSV (prefer custom file if provided)
        csv_file = self.qualified_results_file if self.qualified_results_file else os.path.join(self.results_dir, 'all_qualified_results.csv')
        if os.path.exists(csv_file):
            self.qualified_results = pd.read_csv(csv_file)
            # Only filter for win_rate >= 70% if using all_qualified_results.csv
            if (not self.qualified_results_file) and 'win_rate' in self.qualified_results.columns:
                before_count = len(self.qualified_results)
                self.qualified_results = self.qualified_results[self.qualified_results['win_rate'] >= 70]
                after_count = len(self.qualified_results)
                print(f"Filtered for win_rate >= 70%: {after_count} of {before_count} remain")
            print(f"Loaded qualified results: {len(self.qualified_results)} qualified strategies from {os.path.basename(csv_file)}")
            return True
        else:
            print("No qualified results file found yet")
            return False
    
    def create_performance_report(self):
        """Create comprehensive performance report"""
        if not self.load_results():
            print("Cannot create report - no results available yet")
            return
            
        print("\nGENERATING COMPREHENSIVE PERFORMANCE REPORT...")
        print("=" * 80)
        
        # Overall summary
        self.print_summary()
        
        # Strategy analysis
        self.analyze_by_strategy()
        
        # Symbol analysis
        self.analyze_by_symbol()
        
        # Timeframe analysis
        self.analyze_by_timeframe()
        
        # Top performers
        self.show_top_performers()
        
        # Risk analysis
        self.analyze_risk_metrics()
        
        # Export recommendations
        self.export_trading_recommendations()
        
        print("\n" + "=" * 80)
        print("ANALYSIS COMPLETE")
        
    def print_summary(self):
        """Print overall optimization summary"""
        if not self.analysis_data:
            print("No analysis data available")
            return
            
        print("\nOVERALL OPTIMIZATION SUMMARY")
        print("-" * 40)
        print(f"Total optimizations run: {self.analysis_data.get('total_results', 0):,}")
        print(f"Successful optimizations: {self.analysis_data.get('successful_results', 0):,}")
        print(f"Qualified strategies (>55% win rate): {self.analysis_data.get('qualified_results', 0):,}")
        
        if self.qualified_results is not None and not self.qualified_results.empty:
            success_rate = (len(self.qualified_results) / self.analysis_data.get('total_results', 1)) * 100
            print(f"Overall success rate: {success_rate:.1f}%")
            
            # Best overall strategy
            best = self.qualified_results.iloc[0]
            print(f"\nBEST STRATEGY FOUND:")
            print(f"  Strategy: {best['strategy_name']}")
            print(f"  Symbol: {best['symbol']} ({best['timeframe']})")
            print(f"  Score: {best['composite_score']:.2f}")
            print(f"  Return: {best['return_pct']:.1f}%")
            print(f"  Win Rate: {best['win_rate']:.1f}%")
    
    def analyze_by_strategy(self):
        """Analyze performance by strategy type"""
        if self.qualified_results is None or self.qualified_results.empty:
            return
            
        print("\nSTRATEGY PERFORMANCE ANALYSIS")
        print("-" * 40)
        
        strategy_stats = self.qualified_results.groupby('strategy_name').agg({
            'composite_score': ['count', 'mean', 'max'],
            'return_pct': 'mean',
            'win_rate': 'mean',
            'trades': 'mean'
        }).round(2)
        
        strategy_stats.columns = ['Count', 'Avg_Score', 'Max_Score', 'Avg_Return%', 'Avg_WinRate%', 'Avg_Trades']
        strategy_stats = strategy_stats.sort_values('Avg_Score', ascending=False)
        
        print(strategy_stats)
        
        # Best strategy per type
        print("\nBEST CONFIGURATION PER STRATEGY:")
        for strategy in self.qualified_results['strategy_name'].unique():
            best = self.qualified_results[self.qualified_results['strategy_name'] == strategy].iloc[0]
            print(f"  {strategy}: {best['symbol']} {best['timeframe']} (Score: {best['composite_score']:.2f})")
    
    def analyze_by_symbol(self):
        """Analyze performance by symbol"""
        if self.qualified_results is None or self.qualified_results.empty:
            return
            
        print("\nSYMBOL PERFORMANCE ANALYSIS")
        print("-" * 40)
        
        symbol_stats = self.qualified_results.groupby('symbol').agg({
            'composite_score': ['count', 'mean', 'max'],
            'return_pct': 'mean',
            'win_rate': 'mean'
        }).round(2)
        
        symbol_stats.columns = ['Count', 'Avg_Score', 'Max_Score', 'Avg_Return%', 'Avg_WinRate%']
        symbol_stats = symbol_stats.sort_values('Avg_Score', ascending=False)
        
        print("TOP 15 SYMBOLS:")
        print(symbol_stats.head(15))
        
        # Symbol diversity
        total_symbols = len(symbol_stats)
        qualified_symbols = len(symbol_stats[symbol_stats['Count'] > 0])
        print(f"\nSymbol Coverage: {qualified_symbols}/{total_symbols} symbols have qualified strategies")
    
    def analyze_by_timeframe(self):
        """Analyze performance by timeframe"""
        if self.qualified_results is None or self.qualified_results.empty:
            return
            
        print("\nTIMEFRAME PERFORMANCE ANALYSIS")
        print("-" * 40)
        
        tf_stats = self.qualified_results.groupby('timeframe').agg({
            'composite_score': ['count', 'mean', 'max'],
            'return_pct': 'mean',
            'win_rate': 'mean'
        }).round(2)
        
        tf_stats.columns = ['Count', 'Avg_Score', 'Max_Score', 'Avg_Return%', 'Avg_WinRate%']
        tf_stats = tf_stats.sort_values('Avg_Score', ascending=False)
        
        print(tf_stats)
    
    def show_top_performers(self, top_n=20):
        """Show top performing strategies for live trading"""
        if self.qualified_results is None or self.qualified_results.empty:
            return
            
        print(f"\nTOP {top_n} STRATEGIES FOR LIVE TRADING")
        print("-" * 40)
        
        top_strategies = self.qualified_results.head(top_n)
        
        for i, (_, row) in enumerate(top_strategies.iterrows(), 1):
            print(f"{i:2d}. {row['strategy_name']} | {row['symbol']} {row['timeframe']}")
            print(f"     Score: {row['composite_score']:.2f} | Return: {row['return_pct']:.1f}% | Win: {row['win_rate']:.1f}% | Trades: {row['trades']}")
    
    def analyze_risk_metrics(self):
        """Analyze risk characteristics of qualified strategies"""
        if self.qualified_results is None or self.qualified_results.empty:
            return
            
        print("\nRISK ANALYSIS")
        print("-" * 40)
        
        # Score distribution
        scores = self.qualified_results['composite_score']
        print(f"Score Statistics:")
        print(f"  Mean: {scores.mean():.2f}")
        print(f"  Median: {scores.median():.2f}")
        print(f"  Std Dev: {scores.std():.2f}")
        print(f"  Min: {scores.min():.2f}")
        print(f"  Max: {scores.max():.2f}")
        
        # Win rate distribution
        win_rates = self.qualified_results['win_rate']
        print(f"\nWin Rate Statistics:")
        print(f"  Mean: {win_rates.mean():.1f}%")
        print(f"  Median: {win_rates.median():.1f}%")
        print(f"  Min: {win_rates.min():.1f}%")
        print(f"  Max: {win_rates.max():.1f}%")
        
        # High-confidence strategies (top quartile)
        top_quartile_score = scores.quantile(0.75)
        high_confidence = self.qualified_results[scores >= top_quartile_score]
        print(f"\nHigh-Confidence Strategies (top 25%): {len(high_confidence)} strategies")
        print(f"  Average score: {high_confidence['composite_score'].mean():.2f}")
        print(f"  Average win rate: {high_confidence['win_rate'].mean():.1f}%")
    
    def export_trading_recommendations(self):
        """Export specific trading recommendations"""
        if self.qualified_results is None or self.qualified_results.empty:
            return
            
        print("\nTRADING RECOMMENDATIONS")
        print("-" * 40)
        
        # Conservative portfolio (top 10%)
        top_10_pct = max(1, len(self.qualified_results) // 10)
        conservative = self.qualified_results.head(top_10_pct)
        
        print(f"CONSERVATIVE PORTFOLIO ({len(conservative)} strategies):")
        print(f"  Expected return: {conservative['return_pct'].mean():.1f}%")
        print(f"  Average win rate: {conservative['win_rate'].mean():.1f}%")
        print(f"  Risk level: LOW")
        
        # Aggressive portfolio (top 25%)
        top_25_pct = max(5, len(self.qualified_results) // 4)
        aggressive = self.qualified_results.head(top_25_pct)
        
        print(f"\nAGGRESSIVE PORTFOLIO ({len(aggressive)} strategies):")
        print(f"  Expected return: {aggressive['return_pct'].mean():.1f}%")
        print(f"  Average win rate: {aggressive['win_rate'].mean():.1f}%")
        print(f"  Risk level: MEDIUM")
        
        # Save detailed recommendations
        recommendations_file = os.path.join(self.results_dir, 'trading_recommendations.csv')
        self.qualified_results.head(50).to_csv(recommendations_file, index=False)
        print(f"\nDetailed recommendations saved to: {recommendations_file}")
        
def main():
    analyzer = OptimizationAnalyzer()
    analyzer.create_performance_report()

if __name__ == "__main__":
    main()