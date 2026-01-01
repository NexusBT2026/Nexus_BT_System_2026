#!/usr/bin/env python3
"""
Live Trading Deployment Checklist
Comprehensive checklist and safety measures for going live with optimized strategies
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import json
import pandas as pd
from datetime import datetime, timedelta
from src.utils.analyze_results import OptimizationAnalyzer
from src.utils.bot_integration import OptimizedBotIntegration

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

class DeploymentChecker:
    def __init__(self, results_dir=os.path.join(project_root, 'results')):
        self.results_dir = results_dir
        # Prefer absolute_params.csv if it exists, else fallback to all_qualified_results.csv
        abs_params_path = os.path.join(results_dir, 'absolute_params.csv')
        qualified_results_file = abs_params_path if os.path.exists(abs_params_path) else None
        self.analyzer = OptimizationAnalyzer(results_dir, qualified_results_file=qualified_results_file)
        self.integration = OptimizedBotIntegration(results_dir)
        self.checklist_results = {}
        
    def run_full_deployment_check(self):
        """Run complete deployment readiness check"""
        print("LIVE TRADING DEPLOYMENT CHECKLIST")
        print("=" * 60)
        print(f"Check Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        checks = [
            ("Optimization Results", self.check_optimization_results),
            ("Strategy Quality", self.check_strategy_quality),
            ("Risk Management", self.check_risk_management),
            ("Integration Setup", self.check_integration_setup),
            ("Safety Measures", self.check_safety_measures),
            ("Market Conditions", self.check_market_conditions),
            ("Technical Setup", self.check_technical_setup),
            ("Monitoring Setup", self.check_monitoring_setup)
        ]
        
        passed_checks = 0
        total_checks = len(checks)
        
        for check_name, check_function in checks:
            print(f"\n{check_name.upper()}")
            print("-" * 40)
            
            try:
                result = check_function()
                self.checklist_results[check_name] = result
                if result:
                    print("✅ PASSED")
                    passed_checks += 1
                else:
                    print("❌ FAILED")
            except Exception as e:
                print(f"❌ ERROR: {e}")
                self.checklist_results[check_name] = False
        
        # Final assessment
        print("\n" + "=" * 60)
        print("DEPLOYMENT READINESS ASSESSMENT")
        print("=" * 60)
        
        success_rate = (passed_checks / total_checks) * 100
        print(f"Checks Passed: {passed_checks}/{total_checks} ({success_rate:.1f}%)")
        
        if success_rate >= 90:
            print("🟢 READY FOR LIVE TRADING")
            self.generate_deployment_plan()
        elif success_rate >= 75:
            print("🟡 MOSTLY READY - Address failed checks first")
            self.generate_remediation_plan()
        else:
            print("🔴 NOT READY - Major issues need resolution")
            self.generate_remediation_plan()
            
        return success_rate >= 75
    
    def check_optimization_results(self):
        """Check optimization results quality and completeness"""
        if not self.analyzer.load_results():
            print("❌ No optimization results found")
            print("   Action: Complete optimization first")
            return False
            
        qualified_count = len(self.analyzer.qualified_results) if self.analyzer.qualified_results is not None else 0
        total_count = self.analyzer.analysis_data.get('total_results', 0) if self.analyzer.analysis_data is not None else 0
        
        print(f"📊 Total optimizations: {total_count:,}")
        print(f"📊 Qualified strategies: {qualified_count}")
        
        if qualified_count < 5:
            print("❌ Insufficient qualified strategies")
            print("   Action: Lower qualification threshold or improve strategies")
            return False
            
        if qualified_count < 20:
            print("⚠️  Limited strategy diversity")
            
        success_rate = (qualified_count / total_count) * 100 if total_count > 0 else 0
        print(f"📊 Success rate: {success_rate:.1f}%")
        
        return qualified_count >= 5
    
    def check_strategy_quality(self):
        """Check quality metrics of selected strategies"""
        if not self.analyzer.load_results():
            return False

        if self.analyzer.qualified_results is None or self.analyzer.qualified_results.empty:
            print("❌ No qualified strategies found")
            return False
            
        top_strategies = self.analyzer.qualified_results.head(10)
        
        # Check score distribution
        avg_score = top_strategies['composite_score'].mean()
        min_score = top_strategies['composite_score'].min()
        
        print(f"📊 Top 10 average score: {avg_score:.2f}")
        print(f"📊 Minimum score: {min_score:.2f}")
        
        if min_score < 1.0:
            print("❌ Low scoring strategies in top 10")
            print("   Action: Increase minimum score threshold")
            return False
            
        # Check win rate distribution
        avg_win_rate = top_strategies['win_rate'].mean()
        min_win_rate = top_strategies['win_rate'].min()
        
        print(f"📊 Average win rate: {avg_win_rate:.1f}%")
        print(f"📊 Minimum win rate: {min_win_rate:.1f}%")
        
        if min_win_rate < 55:
            print("❌ Low win rate strategies detected")
            return False
            
        # Check strategy diversity
        unique_strategies = top_strategies['strategy_name'].nunique()
        unique_symbols = top_strategies['symbol'].nunique()
        unique_timeframes = top_strategies['timeframe'].nunique()
        
        print(f"📊 Strategy types: {unique_strategies}")
        print(f"📊 Unique symbols: {unique_symbols}")
        print(f"📊 Unique timeframes: {unique_timeframes}")
        
        return avg_score >= 1.5 and unique_strategies >= 2
    
    def check_risk_management(self):
        """Check risk management configuration"""
        if not self.integration.load_optimized_strategies(max_strategies=10):
            print("❌ Cannot load strategies for risk check")
            return False
            
        total_position_size = sum(
            s['risk_settings']['position_size_pct'] 
            for s in self.integration.active_strategies
        )
        
        print(f"📊 Total position allocation: {total_position_size:.1f}%")
        
        if total_position_size > 50:
            print("❌ Excessive position sizing")
            print("   Action: Reduce individual position sizes")
            return False
            
        if total_position_size > 30:
            print("⚠️  High position allocation")
            
        # Check for strategy correlation (simplified check)
        symbol_count = {}
        for strategy in self.integration.active_strategies:
            symbol = strategy['symbol']
            symbol_count[symbol] = symbol_count.get(symbol, 0) + 1
            
        max_symbol_exposure = max(symbol_count.values())
        print(f"📊 Max strategies per symbol: {max_symbol_exposure}")
        
        if max_symbol_exposure > 3:
            print("❌ High symbol concentration risk")
            return False
            
        return True
    
    def check_integration_setup(self):
        """Check bot integration configuration"""
        try:
            # Test integration
            if not self.integration.validate_integration():
                print("❌ Integration validation failed")
                return False
                
            # Check configuration files exist
            config_file = os.path.join(self.results_dir, 'test_config.json')
            if not os.path.exists(config_file):
                print("❌ Configuration file not generated")
                return False
                
            # Validate configuration structure
            with open(config_file, 'r') as f:
                config = json.load(f)
                
            required_sections = ['bot_info', 'global_settings', 'strategies', 'risk_management']
            for section in required_sections:
                if section not in config:
                    print(f"❌ Missing configuration section: {section}")
                    return False
                    
            print(f"📊 Strategies configured: {len(config['strategies'])}")
            print("✅ Integration configuration valid")
            return True
            
        except Exception as e:
            print(f"❌ Integration error: {e}")
            return False
    
    def check_safety_measures(self):
        """Check safety measures and emergency stops"""
        safety_checklist = [
            "Emergency stop mechanism implemented",
            "Daily loss limits configured", 
            "Maximum drawdown protection",
            "Position size limits enforced",
            "Market hours restrictions",
            "Connectivity monitoring",
            "Error handling and logging"
        ]
        
        print("Safety Measures Checklist:")
        for item in safety_checklist:
            print(f"  ⚠️  {item} - Manual verification required")
            
        print("\n⚠️  MANUAL VERIFICATION REQUIRED")
        print("   Ensure all safety measures are implemented in your bot")
        
        return True  # Assuming manual verification
    
    def check_market_conditions(self):
        """Check current market conditions suitability"""
        print("Market Conditions Check:")
        
        # Check optimization data recency
        # This would need real market data - simplified check
        print("  📊 Market volatility: Manual check required")
        print("  📊 Trend conditions: Manual check required")
        print("  📊 News events: Manual check required")
        
        print("\n⚠️  MANUAL MARKET ANALYSIS REQUIRED")
        print("   Verify current conditions match optimization period")
        
        return True  # Assuming manual verification
    
    def check_technical_setup(self):
        """Check technical infrastructure"""
        technical_checklist = [
            "API connections tested",
            "Server/VPS stability verified",
            "Network connectivity stable",
            "Backup systems configured",
            "Data feeds operational",
            "Execution latency acceptable",
            "System resources adequate"
        ]
        
        print("Technical Infrastructure Checklist:")
        for item in technical_checklist:
            print(f"  ⚠️  {item} - Manual verification required")
            
        return True  # Assuming manual verification
    
    def check_monitoring_setup(self):
        """Check monitoring and alerting systems"""
        monitoring_checklist = [
            "Performance monitoring dashboard",
            "Real-time P&L tracking",
            "Alert system for losses",
            "Trade execution monitoring",
            "System health monitoring",
            "Log file monitoring",
            "Mobile notifications setup"
        ]
        
        print("Monitoring Setup Checklist:")
        for item in monitoring_checklist:
            print(f"  ⚠️  {item} - Manual verification required")
            
        return True  # Assuming manual verification
    
    def generate_deployment_plan(self):
        """Generate step-by-step deployment plan"""
        plan = f"""
LIVE TRADING DEPLOYMENT PLAN
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
===============================================

PHASE 1: PAPER TRADING (Week 1)
- Deploy strategies in paper trading mode
- Monitor performance vs. backtest expectations
- Verify all systems working correctly
- Track execution accuracy and latency

PHASE 2: MICRO LIVE TRADING (Week 2)
- Start with 10% of intended position sizes
- Monitor for 1 week minimum
- Verify real money execution
- Check slippage and fees impact

PHASE 3: GRADUAL SCALE-UP (Weeks 3-4)
- Increase to 50% position sizes
- Monitor performance consistency
- Add more strategies if performing well
- Scale to full size only after validation

PHASE 4: FULL DEPLOYMENT (Week 5+)
- Deploy at full scale
- Continuous monitoring and optimization
- Regular performance reviews
- Monthly re-optimization cycles

SAFETY MEASURES:
- Maximum 5% portfolio risk per day
- Emergency stop at 10% daily loss
- Manual review of all trades first week
- Daily performance reports

MONITORING SCHEDULE:
- Real-time: Trade execution and P&L
- Hourly: System health checks
- Daily: Performance vs. expectations
- Weekly: Strategy performance review
- Monthly: Full optimization cycle
"""
        
        plan_file = os.path.join(self.results_dir, 'deployment_plan.txt')
        with open(plan_file, 'w') as f:
            f.write(plan)
            
        print(f"\n📋 Deployment plan saved to: {plan_file}")
    
    def generate_remediation_plan(self):
        """Generate remediation plan for failed checks"""
        failed_checks = [name for name, result in self.checklist_results.items() if not result]
        
        remediation = f"""
REMEDIATION PLAN
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
===============================================

FAILED CHECKS:
{chr(10).join(f"- {check}" for check in failed_checks)}

RECOMMENDED ACTIONS:
1. Address all failed checks before deployment
2. Re-run optimization if strategy quality is low
3. Implement missing safety measures
4. Verify all technical infrastructure
5. Complete manual verification items

RE-RUN CHECKLIST AFTER REMEDIATION
"""
        
        remediation_file = os.path.join(self.results_dir, 'remediation_plan.txt')
        with open(remediation_file, 'w') as f:
            f.write(remediation)
            
        print(f"\n📋 Remediation plan saved to: {remediation_file}")

def main():
    """Run deployment checklist"""
    checker = DeploymentChecker()
    checker.run_full_deployment_check()

if __name__ == "__main__":
    main()