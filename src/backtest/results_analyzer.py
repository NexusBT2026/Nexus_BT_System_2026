import os
import json
import glob

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

class OptimizationMonitor:
    def __init__(self, results_dir=os.path.join(project_root, 'results')):
        self.results_dir = results_dir
        self.last_check = None
        
    def scan_results(self):
        """Scan for completed optimization results"""
        if not os.path.exists(self.results_dir):
            return {"error": "Results directory not found"}
        
        # Find all individual result files
        pattern = os.path.join(self.results_dir, '**/results_*_strategy.json')
        result_files = glob.glob(pattern, recursive=True)
        
        results = []
        for file_path in result_files:
            try:
                with open(file_path, 'r') as f:
                    result = json.load(f)
                    results.append(result)
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
        
        return self.analyze_current_results(results)
    
    def analyze_current_results(self, results):
        """Analyze current optimization results"""
        if not results:
            return {"message": "No results found yet"}
        
        # Filter successful results
        successful = [r for r in results if r.get('success', False)]
        qualified = [r for r in successful if r.get('composite_score', float('-inf')) > float('-inf')]
        
        # Strategy breakdown
        strategy_stats = {}
        for result in successful:
            strategy = result.get('strategy_name', 'unknown')
            if strategy not in strategy_stats:
                strategy_stats[strategy] = {
                    'total': 0,
                    'qualified': 0,
                    'best_score': float('-inf'),
                    'best_return': 0,
                    'symbols': set()
                }
            
            stats = strategy_stats[strategy]
            stats['total'] += 1
            stats['symbols'].add(result.get('symbol', 'unknown'))
            
            score = result.get('composite_score', float('-inf'))
            if score > float('-inf'):
                stats['qualified'] += 1
                if score > stats['best_score']:
                    stats['best_score'] = score
                    stats['best_return'] = result.get('return_pct', 0)

        # Prepare summary
        summary = {
            "total": len(results),
            "successful": len(successful),
            "qualified": len(qualified),
            "strategy_stats": {
                k: {
                    "total": v["total"],
                    "qualified": v["qualified"],
                    "best_score": v["best_score"],
                    "best_return": v["best_return"],
                    "symbols": list(v["symbols"])
                }
                for k, v in strategy_stats.items()
            }
        }
        return summary
    
    def _group_by_strategy(self, results):
        """Group results by strategy type"""
        by_strategy = {}
        for result in results:
            strategy = result.get('strategy_name', 'unknown')
            if strategy not in by_strategy:
                by_strategy[strategy] = []
            by_strategy[strategy].append(result)
        
        # Get best for each strategy
        strategy_bests = {}
        for strategy, strategy_results in by_strategy.items():
            best = max(strategy_results, key=lambda x: x.get('composite_score', 0))
            strategy_bests[strategy] = {
                "best_result": best,
                "count": len(strategy_results),
                "avg_score": sum(r.get('composite_score', 0) for r in strategy_results) / len(strategy_results)
            }
        
        return strategy_bests
    
    def get_progress_summary(self):
        """Summarize progress of optimization results"""
        results = []
        pattern = os.path.join(self.results_dir, '**/results_*_strategy.json')
        result_files = glob.glob(pattern, recursive=True)
        for file_path in result_files:
            try:
                with open(file_path, 'r') as f:
                    result = json.load(f)
                    results.append(result)
            except Exception as e:
                print(f"Error reading {file_path}: {e}")

        total_completed = len(results)
        successful = len([r for r in results if r.get('success', False)])
        failed = total_completed - successful
        success_rate = (successful / total_completed * 100) if total_completed > 0 else 0.0

        return {
            "total_completed": total_completed,
            "successful": successful,
            "failed": failed,
            "success_rate": success_rate
        }

    def analyze_top_performers(self):
        """Analyze and return top performers and best by strategy"""
        results = []
        pattern = os.path.join(self.results_dir, '**/results_*_strategy.json')
        result_files = glob.glob(pattern, recursive=True)
        for file_path in result_files:
            try:
                with open(file_path, 'r') as f:
                    result = json.load(f)
                    results.append(result)
            except Exception as e:
                print(f"Error reading {file_path}: {e}")

        # Filter successful results
        successful = [r for r in results if r.get('success', False)]
        if not successful:
            return {"best_strategy": None, "best_by_strategy": {}}

        # Find best overall
        best_strategy = max(successful, key=lambda x: x.get('composite_score', float('-inf')))
        # Find best by strategy
        best_by_strategy = self._group_by_strategy(successful)
        return {
            "best_strategy": best_strategy,
            "best_by_strategy": best_by_strategy
        }

    def generate_report(self):
        """Generate and print a comprehensive optimization report"""
        from datetime import datetime
        progress = self.get_progress_summary()
        top_performers = self.analyze_top_performers()

        print("=" * 80)
        print("🚀 OPTIMIZATION PROGRESS REPORT")
        print("=" * 80)
        print(f"📊 Progress Summary:")
        print(f"   Total Completed: {progress['total_completed']}")
        print(f"   Successful: {progress['successful']} ({progress['success_rate']:.1f}%)")
        print(f"   Failed: {progress['failed']}")

        if top_performers['best_strategy']:
            best = top_performers['best_strategy']
            print(f"\n🏆 Current Best Strategy:")
            print(f"   {best.get('symbol', 'N/A')} {best.get('timeframe', 'N/A')} {best.get('strategy_name', 'N/A')}")
            print(f"   Score: {best.get('composite_score', 0):.3f}")
            print(f"   Return: {best.get('return_pct', 0):.2f}%")
            print(f"   Win Rate: {best.get('win_rate', 0):.1f}%")
            print(f"   Trades: {best.get('trades', 0)}")

        print(f"\n📈 Strategy Performance Summary:")
        for strategy, data in top_performers['best_by_strategy'].items():
            best_result = data['best_result']
            print(f"   {strategy}:")
            print(f"     Best: {best_result.get('symbol', 'N/A')} {best_result.get('timeframe', 'N/A')} (Score: {best_result.get('composite_score', 0):.3f})")
            print(f"     Completed: {data['count']}, Avg Score: {data['avg_score']:.3f}")

        print("=" * 80)

        return {
            "progress": progress,
            "top_performers": top_performers,
            "timestamp": datetime.now().isoformat()
        }

def main():
    from datetime import datetime
    analyzer = OptimizationMonitor()
    report = analyzer.generate_report()

    # Save report
    report_file = f"outputs/optimization_progress.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\n📄 Report saved to: {report_file}")

if __name__ == "__main__":
    main()