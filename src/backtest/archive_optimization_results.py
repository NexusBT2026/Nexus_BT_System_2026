"""
archive_optimization_results.py

Helper script to archive all key outputs from the optimization analysis pipeline.
- Archives HTML, PNG, CSV, and JSON outputs from the results directory.
- Creates a timestamped archive folder for each run.
- Intended to be called after analysis completes.

Usage:
    python archive_optimization_results.py --results-dir results/

"""
import os
import shutil
import argparse
from datetime import datetime

def archive_results(results_dir):
    if not os.path.exists(results_dir):
        print(f"Results directory does not exist: {results_dir}")
        return
    # Create archive directory with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    archive_dir = os.path.join(results_dir, f"archive_{timestamp}")
    os.makedirs(archive_dir, exist_ok=True)
    # File patterns to archive
    patterns = [
        'top20_strategies.html',
        'winrate_heatmap.png',
        'win_rate_distribution.png',
        'live_trading_config.json',
        'optimization_analysis.json',
        'all_qualified_results.csv',
        'top_10_results.csv',
        'absolute_params.csv',
        'strategy_performance_summary.json',
    ]
    # Copy files if they exist
    for fname in patterns:
        src = os.path.join(results_dir, fname)
        if os.path.exists(src):
            shutil.copy2(src, archive_dir)
            print(f"Archived: {fname}")
    # Optionally, archive all per-symbol result folders
    for symbol in os.listdir(results_dir):
        symbol_path = os.path.join(results_dir, symbol)
        if os.path.isdir(symbol_path) and not symbol.startswith('archive_'):
            dest = os.path.join(archive_dir, symbol)
            shutil.copytree(symbol_path, dest, dirs_exist_ok=True)
            print(f"Archived symbol folder: {symbol}")
    print(f"Archive complete: {archive_dir}")

    # --- NEW: Keep only the last 3 archives, delete older ones ---
    archives = [d for d in os.listdir(results_dir) if d.startswith('archive_') and os.path.isdir(os.path.join(results_dir, d))]
    # Sort by timestamp descending (most recent first)
    archives_sorted = sorted(archives, reverse=True)
    # Keep only the 3 most recent
    archives_to_delete = archives_sorted[3:]
    for old_archive in archives_to_delete:
        old_archive_path = os.path.join(results_dir, old_archive)
        try:
            shutil.rmtree(old_archive_path)
            print(f"Deleted old archive: {old_archive}")
        except Exception as e:
            print(f"Error deleting archive {old_archive}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Archive optimization results.")
    parser.add_argument('--results-dir', type=str, required=True, help='Path to results directory')
    args = parser.parse_args()
    archive_results(args.results_dir)

if __name__ == "__main__":
    main()
