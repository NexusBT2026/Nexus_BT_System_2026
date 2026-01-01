"""
Monthly Proxy Generator Scheduler
Runs proxy generation as a subprocess every month to keep proxies fresh.
"""

import subprocess
import schedule
import time
import logging
import os
import threading
from datetime import datetime, timedelta
import sys

class ProxyScheduler:
    """
    Scheduler to run proxy generation monthly as a subprocess.
    Ensures fresh proxies are always available for streaming.
    """
    
    def __init__(self, run_on_startup=True, log_file='outputs/proxy_scheduler.log'):
        self.log_file = log_file
        self.setup_logging()
        self.running = False
        self._stop_event = threading.Event()
        
        # Run immediately on startup if requested
        if run_on_startup:
            self.run_proxy_generation()
        
        # Schedule monthly runs on the 1st of each month at 2 AM
        schedule.every(30).days.at("02:00").do(self.run_proxy_generation)  # Every 30 days
        
        # Also allow weekly checks for testing (uncomment if needed)
        # schedule.every().week.do(self.run_proxy_generation)
        
    def setup_logging(self):
        """Setup logging for the scheduler"""
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler()
            ]
        )
        
    def run_proxy_generation(self):
        """
        Run proxy generation as a subprocess.
        This prevents blocking the main application.
        """
        try:
            logging.info("🚀 Starting monthly proxy generation...")
            
            # Get the current working directory
            cwd = os.getcwd()
            script_path = os.path.join(cwd, 'src', 'utils', 'proxy_generator.py')
            
            # Run proxy generator as subprocess
            result = subprocess.run(
                [sys.executable, script_path],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minute timeout
            )
            
            if result.returncode == 0:
                logging.info("✅ Proxy generation completed successfully")
                self._log_proxy_stats()
            else:
                logging.error(f"❌ Proxy generation failed with code {result.returncode}")
                logging.error(f"Error output: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            logging.error("❌ Proxy generation timed out after 30 minutes")
        except Exception as e:
            logging.error(f"❌ Error running proxy generation: {e}")
    
    def _log_proxy_stats(self):
        """Log statistics about the generated proxy files"""
        try:
            http_file = 'outputs/http_proxies.csv'
            socks4_file = 'outputs/socks4_proxies.csv'
            
            http_count = 0
            socks4_count = 0
            
            if os.path.exists(http_file):
                with open(http_file, 'r') as f:
                    http_count = sum(1 for line in f if line.strip())
            
            if os.path.exists(socks4_file):
                with open(socks4_file, 'r') as f:
                    socks4_count = sum(1 for line in f if line.strip())
            
            logging.info(f"📊 Proxy files updated:")
            logging.info(f"   • HTTP proxies: {http_count}")
            logging.info(f"   • SOCKS4 proxies: {socks4_count}")
            logging.info(f"   • Files: {http_file}, {socks4_file}")
            
        except Exception as e:
            logging.error(f"Error reading proxy stats: {e}")
    
    def start_scheduler(self):
        """Start the scheduler in a background thread"""
        if self.running:
            logging.warning("Scheduler is already running")
            return
        
        self.running = True
        self._scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self._scheduler_thread.start()
        logging.info("📅 Proxy scheduler started (monthly updates)")
        
    def _run_scheduler(self):
        """Main scheduler loop"""
        while self.running and not self._stop_event.is_set():
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logging.error(f"Scheduler error: {e}")
                time.sleep(300)  # Wait 5 minutes on error
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        self.running = False
        self._stop_event.set()
        logging.info("📅 Proxy scheduler stopped")
    
    def force_update(self):
        """Force an immediate proxy update (for testing)"""
        logging.info("🔧 Force updating proxies...")
        self.run_proxy_generation()
    
    def get_next_run_time(self):
        """Get the next scheduled run time"""
        next_run = schedule.next_run()
        if next_run:
            return next_run.strftime("%Y-%m-%d %H:%M:%S")
        return "Not scheduled"
    
    def get_status(self):
        """Get scheduler status"""
        return {
            'running': self.running,
            'next_run': self.get_next_run_time(),
            'proxy_files_exist': {
                'http': os.path.exists('outputs/http_proxies.csv'),
                'socks4': os.path.exists('outputs/socks4_proxies.csv')
            }
        }


def main():
    """
    Main function to run the proxy scheduler.
    Can be used standalone or imported into other modules.
    """
    print("📅 Starting Proxy Scheduler...")
    
    # Create scheduler with immediate run
    scheduler = ProxyScheduler(run_on_startup=True)
    
    # Start the background scheduler
    scheduler.start_scheduler()
    
    try:
        print(f"📅 Scheduler running. Next update: {scheduler.get_next_run_time()}")
        print("📊 Scheduler status:", scheduler.get_status())
        print("Press Ctrl+C to stop...")
        
        # Keep the main thread alive
        while True:
            time.sleep(60)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping proxy scheduler...")
        scheduler.stop_scheduler()
        print("✅ Proxy scheduler stopped")


if __name__ == "__main__":
    main()
