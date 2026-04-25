import pandas as pd
from itertools import product
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.backtester.backtester import Backtester
from config import STRATEGY

class StrategyOptimizer:
    """Fast Conservative Parameter Optimizer"""
    
    def __init__(self):
        self.results = []
        
    def run_optimization(self):
        print("🔍 Starting Fast Conservative Parameter Optimization...\n")
        
        # Limited conservative ranges for speed
        short_windows = [15, 20, 25]
        long_windows = [50, 60, 100]
        adx_thresholds = [20, 22, 25]
        
        total_combinations = len(short_windows) * len(long_windows) * len(adx_thresholds)
        completed = 0
        
        best_return = -999
        best_params = None
        
        for short, long, adx_th in product(short_windows, long_windows, adx_thresholds):
            completed += 1
            print(f"[{completed}/{total_combinations}] Testing Short={short}, Long={long}, ADX≥{adx_th} ... ", end="")
            
            # Temporarily override parameters
            STRATEGY["short_window"] = short
            STRATEGY["long_window"] = long
            STRATEGY["adx_threshold"] = adx_th
            
            bt = Backtester()
            bt.run(start_date="2024-01-01")  # Shorter period for faster testing
            
            equity_df = pd.DataFrame(bt.equity_curve)
            total_return = (equity_df['equity'].iloc[-1] / equity_df['equity'].iloc[0] - 1) * 100 if not equity_df.empty else -100
            
            num_trades = len(bt.trades)
            
            self.results.append({
                'short_window': short,
                'long_window': long,
                'adx_threshold': adx_th,
                'total_return': round(total_return, 2),
                'trades': num_trades
            })
            
            print(f"Return: {total_return:.2f}% | Trades: {num_trades}")
            
            if total_return > best_return:
                best_return = total_return
                best_params = (short, long, adx_th)
        
        # Show sorted results
        results_df = pd.DataFrame(self.results)
        print("\n" + "="*70)
        print("OPTIMIZATION RESULTS (Sorted by Return)")
        print("="*70)
        print(results_df.sort_values('total_return', ascending=False).to_string(index=False))
        
        print(f"\n🎯 Best Parameters Found:")
        print(f"   Short Window : {best_params[0]}")
        print(f"   Long Window  : {best_params[1]}")
        print(f"   ADX Threshold: {best_params[2]}")
        print(f"   Total Return : {best_return:.2f}%")
        
        # Restore original conservative settings
        STRATEGY["short_window"] = 20
        STRATEGY["long_window"] = 50
        STRATEGY["adx_threshold"] = 22
        
        print("\nOptimization completed. Strategy remains conservative.")

if __name__ == "__main__":
    optimizer = StrategyOptimizer()
    optimizer.run_optimization()