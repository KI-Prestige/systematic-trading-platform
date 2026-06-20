# stress_tester.py - Fixed Monte Carlo
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.backtester.backtester import Backtester
from config import STRATEGY, SYMBOLS

class StressTester:
    def __init__(self, initial_capital=100000.0):
        self.initial_capital = initial_capital

    def run_full_stress_test(self, start_date="2018-01-01", n_mc_sims=1500):
        print("🚀 Running Enhanced Stress Test - Capital Preservation Focus\n")
        
        bt = Backtester(initial_capital=self.initial_capital)
        bt.run(start_date=start_date, plot_results=True, export_trade_log=True)
        
        equity_df = pd.DataFrame(bt.equity_curve)
        base_dd = self._calculate_max_dd(equity_df['equity'].values)
        
        print(f"\nBase Performance:")
        print(f"   Return     : {((equity_df['equity'].iloc[-1] / equity_df['equity'].iloc[0] - 1)*100):.2f}%")
        print(f"   Max DD     : {base_dd:.2f}%")
        print(f"   Trades     : {len(bt.trades)}")
        
        # Monte Carlo - FIXED
        print("\n=== Monte Carlo Stress Test (Fixed) ===")
        mc_results = self.monte_carlo_stress_test(equity_df['equity'].values, n_sims=n_mc_sims)
        
        self._risk_recommendations(base_dd, mc_results)
        
        return mc_results

    def monte_carlo_stress_test(self, equity, n_sims=1500, noise_level=0.008):
        returns = pd.Series(equity).pct_change().dropna()
        if len(returns) < 50:
            print("⚠️ Not enough data")
            return {}
        
        sim_final = []
        sim_maxdds = []
        
        for _ in range(n_sims):
            # Better bootstrap
            sim_ret = returns.sample(len(returns), replace=True).values.copy()
            
            # Add realistic noise
            sim_ret += np.random.normal(0, noise_level, len(sim_ret))
            
            # Random regime shocks
            if np.random.rand() < 0.20:
                shock_start = np.random.randint(0, len(sim_ret) - 100)
                shock = np.random.uniform(0.75, 0.90)
                sim_ret[shock_start:shock_start+60] *= shock
            
            # Reconstruct equity curve
            sim_eq = self.initial_capital * np.cumprod(1 + sim_ret)
            sim_final.append(sim_eq[-1])
            sim_maxdds.append(self._calculate_max_dd(sim_eq))
        
        final = np.array(sim_final)
        ruin_prob = (final < self.initial_capital * 0.5).mean() * 100
        
        print(f"Monte Carlo ({n_sims} sims):")
        print(f"   Mean Final Equity : ${np.mean(final):,.0f}")
        print(f"   5th Percentile    : ${np.percentile(final, 5):,.0f}")
        print(f"   Ruin Prob (>50% DD): {ruin_prob:.2f}%")
        print(f"   Avg Max DD        : {np.mean(sim_maxdds):.2f}%")
        print(f"   Worst Max DD      : {np.min(sim_maxdds):.2f}%")
        
        return {'ruin_prob': ruin_prob, 'worst_5pct': np.percentile(final, 5)}

    def _calculate_max_dd(self, equity):
        equity = np.array(equity, dtype=float)
        peak = np.maximum.accumulate(equity)
        return ((equity - peak) / peak).min() * 100

    def _risk_recommendations(self, base_dd, mc_results):
        print("\n" + "="*70)
        print("RISK RECOMMENDATIONS FOR CAPITAL PRESERVATION")
        print("="*70)
        print(f"Current risk_per_trade in config: {STRATEGY.get('risk_per_trade', 0.005)*100:.1f}%")
        
        if base_dd < -20:
            print("⚠️ Max DD is high → Consider reducing risk_per_trade")
        if mc_results.get('ruin_prob', 0) > 5:
            print("⚠️ High ruin probability detected")
        else:
            print("✅ Current ruin risk looks acceptable")
        
        print("\nNext steps suggestion:")
        print("1. Lower risk_per_trade to 0.005-0.007 in config.py")
        print("2. Re-run this stress test")
        print("3. Add equity curve protection rule")

if __name__ == "__main__":
    tester = StressTester()
    tester.run_full_stress_test(n_mc_sims=1000)  # Reduced for speed