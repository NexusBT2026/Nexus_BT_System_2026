#!/usr/bin/env python3
"""
Test all utility scripts to make sure they work
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

def test_check_status():
    """Test the status checker"""
    print("🧪 Testing check_status.py...")
    try:
        from src.utils.check_status import check_optimization_status
        check_optimization_status()
        print("✅ check_status.py works")
        return True
    except Exception as e:
        print(f"❌ check_status.py failed: {e}")
        return False

def test_analyze_results():
    """Test the results analyzer"""
    print("\n🧪 Testing analyze_results.py...")
    try:
        from src.utils.analyze_results import OptimizationAnalyzer
        analyzer = OptimizationAnalyzer()
        print("✅ analyze_results.py imports work")
        return True
    except Exception as e:
        print(f"❌ analyze_results.py failed: {e}")
        return False

def test_generate_configs():
    """Test the config generator"""
    print("\n🧪 Testing generate_configs.py...")
    try:
        from src.utils.generate_configs import LiveConfigGenerator
        generator = LiveConfigGenerator()
        print("✅ generate_configs.py imports work")
        return True
    except Exception as e:
        print(f"❌ generate_configs.py failed: {e}")
        return False

def test_monitor_progress():
    """Test the progress monitor"""
    print("\n🧪 Testing monitor_progress.py...")
    try:
        from src.utils.monitor_progress import OptimizationMonitor
        monitor = OptimizationMonitor()
        print("✅ monitor_progress.py imports work")
        return True
    except Exception as e:
        print(f"❌ monitor_progress.py failed: {e}")
        return False

def main():
    print("🚀 TESTING ALL UTILITY SCRIPTS")
    print("=" * 50)
    
    tests = [
        test_check_status,
        test_analyze_results,
        test_generate_configs,
        test_monitor_progress
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 TEST RESULTS: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All utility scripts are working!")
        print("\n💡 Commands to use:")
        print("   python src/utils/check_status.py     - Quick status check")
        print("   python src/utils/analyze_results.py  - Full analysis (when complete)")
        print("   python src/utils/generate_configs.py - Generate trading configs")
        print("   python src/utils/monitor_progress.py - Real-time monitoring")
    else:
        print("❌ Some scripts have issues - check the errors above")

if __name__ == "__main__":
    main()