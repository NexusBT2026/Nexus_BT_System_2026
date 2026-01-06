"""
Real-time Backtesting Dashboard - Professional Client-Ready Monitoring

Features:
- Live progress bars with ETA
- CPU and memory usage monitoring
- Success/failure statistics with color coding
- Current task tracking
- Clean, organized output for client presentations
"""

import os
import sys
import time
import psutil
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from collections import defaultdict, deque
from threading import Lock

try:
    from rich.console import Console
    from rich.live import Live
    from rich.table import Table
    from rich.progress import (
        Progress, SpinnerColumn, BarColumn, TextColumn, 
        TimeRemainingColumn, TimeElapsedColumn, TaskProgressColumn
    )
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("⚠️  Rich library not available. Install with: pip install rich")
    print("   Falling back to basic output...")


class BacktestDashboard:
    """
    Professional real-time dashboard for backtest monitoring.
    Provides beautiful, client-ready progress visualization.
    """
    
    def __init__(self, total_tasks: int, enable_system_monitor: bool = True):
        """
        Initialize dashboard.
        
        Args:
            total_tasks: Total number of optimization tasks
            enable_system_monitor: Enable CPU/memory monitoring
        """
        self.total_tasks = total_tasks
        self.enable_system_monitor = enable_system_monitor
        self.rich_available = RICH_AVAILABLE
        
        # Statistics tracking
        self.completed = 0
        self.successful = 0
        self.failed = 0
        self.skipped = 0
        self.strategies_passed = 0  # Strategies that met profitability criteria
        self.strategies_failed_criteria = 0  # Strategies that failed criteria
        self.final_selected = 0  # Final selected strategies after all filtering
        self.start_time = time.time()
        self.lock = Lock()
        
        # Current tasks tracking (last 10)
        self.recent_tasks = deque(maxlen=10)
        
        # Strategy performance tracking
        self.strategy_stats = defaultdict(lambda: {'success': 0, 'failed': 0})
        self.symbol_stats = defaultdict(lambda: {'success': 0, 'failed': 0})
        
        # System monitoring
        self.process = psutil.Process()
        self.cpu_history = deque(maxlen=60)  # Last 60 samples
        self.mem_history = deque(maxlen=60)
        self.initial_system_cpu = psutil.cpu_percent(interval=None)  # Baseline
        
        if self.rich_available:
            self.console = Console()
            self.progress = Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(complete_style="green", finished_style="bold green"),
                TaskProgressColumn(),
                TextColumn("•"),
                TimeElapsedColumn(),
                TextColumn("•"),
                TimeRemainingColumn(),
                console=self.console
            )
            self.task_id = self.progress.add_task(
                "[cyan]Backtesting Progress", 
                total=total_tasks
            )
            self.live = None
    
    def start(self):
        """Start the live dashboard."""
        if self.rich_available:
            self.live = Live(
                self._generate_layout(),
                console=self.console,
                refresh_per_second=2,
                screen=True  # Fixed position, no scrolling
            )
            self.live.start()
    
    def stop(self):
        """Stop the live dashboard and show final summary."""
        if self.rich_available and self.live:
            self.live.stop()
            self._print_final_summary()
    
    def update_task(self, symbol: str, timeframe: str, strategy: str, 
                   status: str, category: str = "general", 
                   error_msg: Optional[str] = None,
                   passed_criteria: Optional[bool] = None):
        """
        Update dashboard with completed task.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe (e.g., '1h')
            strategy: Strategy name
            status: 'success', 'failed', or 'skipped'
            category: Strategy category
            error_msg: Error message if failed
            passed_criteria: Whether strategy passed profitability criteria (True/False/None)
        """
        with self.lock:
            self.completed += 1
            
            if status == 'success':
                self.successful += 1
                self.strategy_stats[strategy]['success'] += 1
                self.symbol_stats[symbol]['success'] += 1
                # Track if strategy passed profitability criteria
                if passed_criteria is True:
                    self.strategies_passed += 1
                elif passed_criteria is False:
                    self.strategies_failed_criteria += 1
            elif status == 'failed':
                self.failed += 1
                self.strategy_stats[strategy]['failed'] += 1
                self.symbol_stats[symbol]['failed'] += 1
            elif status == 'skipped':
                self.skipped += 1
            
            # Add to recent tasks
            task_info = {
                'symbol': symbol,
                'timeframe': timeframe,
                'strategy': strategy,
                'status': status,
                'category': category,
                'timestamp': datetime.now(),
                'error': error_msg
            }
            self.recent_tasks.append(task_info)
            
            # Print errors below dashboard (on stderr so they appear below live display)
            if status == 'failed' and error_msg:
                import sys
                sys.stderr.write(f"\n[ERROR] {strategy} on {symbol} {timeframe}: {error_msg}\n")
                sys.stderr.flush()
            
            # Update system metrics
            if self.enable_system_monitor:
                # Measure TOTAL system CPU (includes all worker processes)
                system_cpu = psutil.cpu_percent(interval=0.1)  # 100ms sample
                self.cpu_history.append(system_cpu)
                self.mem_history.append(self.process.memory_info().rss / 1024 / 1024)  # MB
            
            if self.rich_available:
                self.progress.update(self.task_id, advance=1)
                if self.live:
                    self.live.update(self._generate_layout())
    
    def _generate_layout(self) -> Layout:
        """Generate the dashboard layout."""
        layout = Layout()
        
        # Split into sections
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main", ratio=2),
            Layout(name="footer", size=10)
        )
        
        # Split main section
        layout["main"].split_row(
            Layout(name="progress", ratio=2),
            Layout(name="stats", ratio=1)
        )
        
        # Header
        layout["header"].update(self._create_header())
        
        # Progress section
        layout["progress"].update(Panel(
            self.progress,
            title="[bold cyan]Overall Progress",
            border_style="cyan"
        ))
        
        # Statistics section
        layout["stats"].update(self._create_stats_panel())
        
        # Footer - recent tasks
        layout["footer"].update(self._create_recent_tasks_panel())
        
        return layout
    
    def _create_header(self) -> Panel:
        """Create header with system info."""
        elapsed = time.time() - self.start_time
        elapsed_str = str(timedelta(seconds=int(elapsed)))
        
        # Calculate ETA
        if self.completed > 0:
            avg_time = elapsed / self.completed
            remaining = (self.total_tasks - self.completed) * avg_time
            eta_str = str(timedelta(seconds=int(remaining)))
        else:
            eta_str = "calculating..."
        
        # System metrics
        if self.enable_system_monitor:
            cpu_avg = sum(self.cpu_history) / len(self.cpu_history) if self.cpu_history else 0
            mem_current = self.mem_history[-1] if self.mem_history else 0
            system_info = f" | CPU: {cpu_avg:.1f}% | Memory: {mem_current:.0f} MB"
        else:
            system_info = ""
        
        header_text = Text()
        header_text.append("🚀 NEXUS BACKTESTING SYSTEM ", style="bold cyan")
        header_text.append(f"| Elapsed: {elapsed_str} | ETA: {eta_str}{system_info}", style="white")
        
        return Panel(header_text, style="bold blue")
    
    def _create_stats_panel(self) -> Panel:
        """Create statistics panel."""
        success_rate = (self.successful / self.completed * 100) if self.completed > 0 else 0
        
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column(style="cyan")
        table.add_column(style="bold white", justify="right")
        
        # Overall stats
        table.add_row("Total Tasks", f"{self.total_tasks:,}")
        table.add_row("Completed", f"{self.completed:,}")
        table.add_row("─────────", "─────────")
        table.add_row("✅ Success", f"[green]{self.successful:,}[/green]")
        table.add_row("❌ Failed", f"[red]{self.failed:,}[/red]")
        table.add_row("⏭️  Skipped", f"[yellow]{self.skipped:,}[/yellow]")
        table.add_row("─────────", "─────────")
        table.add_row("Success Rate", f"[green bold]{success_rate:.1f}%[/green bold]")
        
        # Tasks per second
        if self.completed > 0:
            elapsed = time.time() - self.start_time
            tps = self.completed / elapsed
            table.add_row("Speed", f"{tps:.2f} tasks/sec")
        
        # Strategy pass/fail criteria tracking
        if self.strategies_passed > 0 or self.strategies_failed_criteria > 0:
            table.add_row("─────────", "─────────")
            table.add_row("🎯 Passed Criteria", f"[green]{self.strategies_passed:,}[/green]")
            table.add_row("💔 Failed Criteria", f"[dim]{self.strategies_failed_criteria:,}[/dim]")
            
            if self.successful > 0:
                pass_rate = (self.strategies_passed / self.successful * 100)
                table.add_row("Pass Rate", f"[cyan]{pass_rate:.1f}%[/cyan]")
        
        # Final selection tracking
        if self.final_selected > 0:
            table.add_row("─────────", "─────────")
            table.add_row("✨ Final Selected", f"[bold yellow]{self.final_selected:,}[/bold yellow]")
        
        return Panel(table, title="[bold green]Statistics", border_style="green")
    
    def _create_recent_tasks_panel(self) -> Panel:
        """Create panel showing recent tasks."""
        table = Table(show_header=True, header_style="bold cyan", box=None)
        table.add_column("Time", style="dim", width=8)
        table.add_column("Symbol", style="cyan", width=15)
        table.add_column("TF", width=6)
        table.add_column("Strategy", style="yellow", width=25)
        table.add_column("Category", style="magenta", width=15)
        table.add_column("Status", width=10)
        
        for task in reversed(list(self.recent_tasks)):
            time_str = task['timestamp'].strftime('%H:%M:%S')
            
            if task['status'] == 'success':
                status_str = "[green]✅ SUCCESS[/green]"
            elif task['status'] == 'failed':
                status_str = "[red]❌ FAILED[/red]"
            else:
                status_str = "[yellow]⏭️  SKIPPED[/yellow]"
            
            table.add_row(
                time_str,
                task['symbol'][:15],
                task['timeframe'],
                task['strategy'][:25],
                task['category'],
                status_str
            )
        
        return Panel(table, title="[bold yellow]Recent Tasks", border_style="yellow")
    
    def _print_final_summary(self):
        """Print final summary after completion."""
        elapsed = time.time() - self.start_time
        elapsed_str = str(timedelta(seconds=int(elapsed)))
        
        # Create final summary table
        summary = Table(title="[bold green]🎉 BACKTEST COMPLETE![/bold green]", 
                       show_header=True, header_style="bold cyan")
        summary.add_column("Metric", style="cyan")
        summary.add_column("Value", justify="right", style="bold white")
        
        summary.add_row("Total Time", elapsed_str)
        summary.add_row("Total Tasks", f"{self.total_tasks:,}")
        summary.add_row("Successful", f"[green]{self.successful:,}[/green]")
        summary.add_row("Failed", f"[red]{self.failed:,}[/red]")
        summary.add_row("Skipped", f"[yellow]{self.skipped:,}[/yellow]")
        
        success_rate = (self.successful / self.completed * 100) if self.completed > 0 else 0
        summary.add_row("Success Rate", f"[green bold]{success_rate:.1f}%[/green bold]")
        
        if self.completed > 0:
            avg_time = elapsed / self.completed
            summary.add_row("Avg Time/Task", f"{avg_time:.2f}s")
        
        self.console.print("\n")
        self.console.print(summary)
        
        # Top performing strategies
        if self.strategy_stats:
            self._print_top_strategies()
    
    def _print_top_strategies(self):
        """Print top performing strategies."""
        strategy_table = Table(title="[bold cyan]📊 Strategy Performance[/bold cyan]",
                              show_header=True, header_style="bold yellow")
        strategy_table.add_column("Strategy", style="cyan")
        strategy_table.add_column("Success", justify="right", style="green")
        strategy_table.add_column("Failed", justify="right", style="red")
        strategy_table.add_column("Success Rate", justify="right", style="bold white")
        
        # Sort by success count
        sorted_strategies = sorted(
            self.strategy_stats.items(),
            key=lambda x: x[1]['success'],
            reverse=True
        )[:10]  # Top 10
        
        for strategy, stats in sorted_strategies:
            total = stats['success'] + stats['failed']
            rate = (stats['success'] / total * 100) if total > 0 else 0
            strategy_table.add_row(
                strategy,
                str(stats['success']),
                str(stats['failed']),
                f"{rate:.1f}%"
            )
        
        self.console.print("\n")
        self.console.print(strategy_table)


# Fallback simple progress tracker if rich not available
class SimpleProgressTracker:
    """Simple text-based progress tracker (fallback)."""
    
    def __init__(self, total_tasks: int, enable_system_monitor: bool = True):
        self.total_tasks = total_tasks
        self.completed = 0
        self.successful = 0
        self.failed = 0
        self.skipped = 0
        self.strategies_passed = 0
        self.strategies_failed_criteria = 0
        self.final_selected = 0
        self.start_time = time.time()
        self.last_print = 0
        self.lock = Lock()
    
    def start(self):
        print(f"\n{'='*60}")
        print(f"  NEXUS BACKTESTING SYSTEM - {self.total_tasks:,} tasks")
        print(f"{'='*60}\n")
    
    def stop(self):
        elapsed = time.time() - self.start_time
        print(f"\n{'='*60}")
        print(f"  BACKTEST COMPLETE!")
        print(f"  Time: {timedelta(seconds=int(elapsed))}")
        print(f"  Success: {self.successful:,} | Failed: {self.failed:,}")
        if self.strategies_passed > 0:
            print(f"  Passed Criteria: {self.strategies_passed:,}")
        if self.final_selected > 0:
            print(f"  Final Selected: {self.final_selected:,}")
        print(f"{'='*60}\n")
    
    def set_final_selected(self, count: int):
        """
        Set the count of final selected strategies after filtering.
        
        Args:
            count: Number of strategies that passed final selection
        """
        with self.lock:
            self.final_selected = count
    
    def update_task(self, symbol: str, timeframe: str, strategy: str,
                   status: str, category: str = "general", 
                   error_msg: Optional[str] = None,
                   passed_criteria: Optional[bool] = None):
        with self.lock:
            self.completed += 1
            
            if status == 'success':
                self.successful += 1
                status_icon = "✅"
                # Track if strategy passed profitability criteria
                if passed_criteria is True:
                    self.strategies_passed += 1
                elif passed_criteria is False:
                    self.strategies_failed_criteria += 1
            elif status == 'failed':
                self.failed += 1
                status_icon = "❌"
            else:
                self.skipped += 1
                status_icon = "⏭️"
            
            # Print every 10 tasks or key milestones
            if self.completed % 10 == 0 or self.completed in [1, 100, 1000]:
                progress_pct = (self.completed / self.total_tasks * 100)
                elapsed = time.time() - self.start_time
                rate = self.completed / elapsed if elapsed > 0 else 0
                
                print(f"[{self.completed:,}/{self.total_tasks:,}] {progress_pct:.1f}% | "
                      f"{status_icon} {symbol} {timeframe} {strategy} | "
                      f"Rate: {rate:.2f} tasks/sec")


def create_dashboard(total_tasks: int, enable_system_monitor: bool = True):
    """
    Factory function to create appropriate dashboard.
    
    Args:
        total_tasks: Total number of optimization tasks
        enable_system_monitor: Enable CPU/memory monitoring
    
    Returns:
        Dashboard instance (BacktestDashboard or SimpleProgressTracker)
    """
    if RICH_AVAILABLE:
        return BacktestDashboard(total_tasks, enable_system_monitor)
    else:
        return SimpleProgressTracker(total_tasks, enable_system_monitor)


def show_initialization_screen(phase: str, details: Optional[dict] = None):
    """
    Display professional initialization/loading screen.
    
    Args:
        phase: Current phase (e.g., 'symbol_discovery', 'data_fetch', 'backtest_prep')
        details: Additional details to display
    """
    if not RICH_AVAILABLE:
        print(f"\n{'='*80}")
        print(f"  {phase.upper().replace('_', ' ')}")
        if details:
            for key, value in details.items():
                print(f"  {key}: {value}")
        print(f"{'='*80}\n")
        return
    
    from rich.panel import Panel
    from rich.text import Text
    from rich.table import Table
    from rich.console import Console
    
    console = Console()
    
    # Phase-specific messages
    phase_info = {
        'symbol_discovery': {
            'title': '🔍 PHASE 1: Symbol Discovery',
            'description': 'Scanning multiple exchanges for tradable symbols...',
            'emoji': '🌐'
        },
        'data_fetch': {
            'title': '📊 PHASE 2: Historical Data Fetching',
            'description': 'Fetching OHLCV data from exchanges with rate limiting...',
            'emoji': '💾'
        },
        'backtest_prep': {
            'title': '🚀 PHASE 3: Backtest Initialization',
            'description': 'Preparing optimization engine for strategy testing...',
            'emoji': '⚙️'
        },
        'optimization_start': {
            'title': '🎯 PHASE 4: Strategy Optimization',
            'description': 'Running Bayesian hyperparameter optimization across strategies...',
            'emoji': '🔬'
        }
    }
    
    info = phase_info.get(phase, {
        'title': f'⚡ {phase.upper().replace("_", " ")}',
        'description': 'Processing...',
        'emoji': '⏳'
    })
    
    # Create header
    header = Text()
    header.append("\n\n")
    header.append("╔═══════════════════════════════════════════════════════════════════════╗\n", style="bold cyan")
    header.append("║                                                                       ║\n", style="bold cyan")
    header.append("║", style="bold cyan")
    header.append("                  🚀 NEXUS BACKTESTING SYSTEM v2.0 🚀                  ", style="bold white")
    header.append("║\n", style="bold cyan")
    header.append("║                                                                       ║\n", style="bold cyan")
    header.append("║", style="bold cyan")
    header.append("             Professional Multi-Exchange Strategy Optimizer            ", style="dim white")
    header.append("║\n", style="bold cyan")
    header.append("║                                                                       ║\n", style="bold cyan")
    header.append("╚═══════════════════════════════════════════════════════════════════════╝\n", style="bold cyan")
    header.append("\n")
    
    console.print(header)
    
    # Create main panel
    content = Text()
    content.append(f"{info['emoji']}  ", style="bold yellow")
    content.append(info['title'], style="bold cyan")
    content.append("\n\n")
    content.append(info['description'], style="white")
    
    if details:
        content.append("\n\n")
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column(style="cyan bold")
        table.add_column(style="white")
        
        for key, value in details.items():
            table.add_row(f"{key}:", str(value))
        
        console.print(Panel(content, border_style="cyan", padding=(1, 2)))
        console.print(table)
    else:
        console.print(Panel(content, border_style="cyan", padding=(1, 2)))
    
    console.print("\n")
