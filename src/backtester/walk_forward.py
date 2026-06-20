# src/backtester/walk_forward.py - Simplified (No Random Forest)

import pandas as pd
import numpy as np
from itertools import product
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.backtester.backtester import Backtester
from config import STRATEGY, SYMBOLS

class WalkForwardAnalyzer:
    def __init__(self, initial_capital=100000.0):
        self.initial_capital = initial_capital
        self.wfa_results = None

    def rolling_walk_forward(self, is_years=2, oos_months=6, step_months=3,
                           slippage_pct=0.0008, commission_pct=0.0005):
        
        print("🚀 Walk-Forward Analysis - Pure Pullback-in-Trend Strategy (No RF)")
        print(f"Window: {is_years}y IS | {oos_months}m OOS | Step: {step_months}m\n")
        
        fetcher = Backtester().fetcher
        sample_df = fetcher.fetch_and_cache([SYMBOLS[0]])
        all_dates = pd.to_datetime(sample_df['date']).sort_values()
        
        current_start = pd.to_datetime("2017-01-01")
        end_date = all_dates.max()
        results = []
        window_count = 0
        
        # Simple but effective parameter grid
        param_grid = {
            "short_window": [20, 25, 30],
            "adx_threshold": [18, 20, 22],
            "risk_per_trade": [0.004, 0.0045, 0.005]
        }
        
        while True:
            is_end = current_start + pd.DateOffset(years=is_years)
            oos_start = is_end
            oos_end = is_end + pd.DateOffset(months=oos_months)
            
            if oos_end > end_date:
                break
            
            print(f"\n→ Window {window_count} | IS: {current_start.date()} → {is_end.date()} | OOS: {oos_start.date()} → {oos_end.date()}")
            
            best_params, best_calmar = self._optimize_is(
                current_start, is_end, param_grid, slippage_pct, commission_pct
            )
            
            oos_result = self._test_oos(best_params, oos_start, oos_end, 
                                      slippage_pct, commission_pct)
            
            results.append({
                "window": window_count,
                "oos_start": str(oos_start.date()),
                "oos_end": str(oos_end.date()),
                "oos_return": oos_result["oos_return"],
                "oos_max_dd": oos_result["oos_max_dd"],
                "oos_calmar": oos_result["oos_calmar"],
                "oos_trades": oos_result["oos_trades"]
            })
            
            window_count += 1
            current_start += pd.DateOffset(months=step_months)
        
        self.wfa_results = pd.DataFrame(results)
        self._summarize()
        return self.wfa_results

    def _optimize_is(self, start, end, param_grid, slippage_pct, commission_pct):
        best_calmar = -np.inf
        best_params = None
        
        for combo in product(*[param_grid[k] for k in param_grid]):
            params = STRATEGY.copy()
            for k, v in zip(param_grid.keys(), combo):
                params[k] = v
            
            bt = Backtester(initial_capital=self.initial_capital)
            bt.run_with_warmup(params=params, start_date=start, end_date=end,
                             slippage_pct=slippage_pct, commission_pct=commission_pct)
            
            equity_df = pd.DataFrame(bt.equity_curve)
            if len(equity_df) < 100:
                continue
            
            total_ret = (equity_df['equity'].iloc[-1] / equity_df['equity'].iloc[0] - 1)
            max_dd = abs(self._calculate_max_dd(equity_df['equity'].values))
            calmar = total_ret / max_dd if max_dd > 0 else 0
            
            if calmar > best_calmar:
                best_calmar = calmar
                best_params = params.copy()
        
        return best_params, best_calmar

    def _test_oos(self, params, start, end, slippage_pct, commission_pct):
        bt = Backtester(initial_capital=self.initial_capital)
        bt.run_with_warmup(params=params, start_date=start, end_date=end,
                         slippage_pct=slippage_pct, commission_pct=commission_pct)
        
        equity_df = pd.DataFrame(bt.equity_curve)
        total_return = (equity_df['equity'].iloc[-1] / equity_df['equity'].iloc[0] - 1) * 100 if len(equity_df) > 1 else 0
        max_dd = abs(self._calculate_max_dd(equity_df['equity'].values)) * 100
        calmar = (total_return/100) / (max_dd/100) if max_dd > 0 else 0
        
        print(f"   → Trades: {len(bt.trades)} | Return: {total_return:.2f}% | Calmar: {calmar:.2f} | Max DD: {max_dd:.2f}%")
        
        return {
            "oos_return": total_return,
            "oos_max_dd": max_dd,
            "oos_calmar": calmar,
            "oos_trades": len(bt.trades)
        }
    
    def _add_monthly_tables(self, bt, oos_start, oos_end):
        """Generate monthly performance for the current OOS window"""
        equity_df = pd.DataFrame(bt.equity_curve)
        if equity_df.empty:
            return None
        
        equity_df['date'] = pd.to_datetime(equity_df['date'])
        equity_df.set_index('date', inplace=True)
        
        monthly = equity_df['equity'].resample('ME').last().pct_change() * 100
        monthly_df = pd.DataFrame({
            'Month': monthly.index.strftime('%Y-%m'),
            'Return_%': monthly.round(2)
        })
        
        print(f"\nMonthly Returns for OOS {oos_start.date()} to {oos_end.date()}:")
        print(monthly_df.to_string(index=False))
        return monthly_df
    
    def _calculate_max_dd(self, equity):
        peak = np.maximum.accumulate(equity)
        drawdown = (equity - peak) / peak
        return drawdown.min()

    def _summarize(self):
        df = self.wfa_results
        print("\n" + "="*120)
        print("WALK-FORWARD ANALYSIS SUMMARY - PURE PULLBACK STRATEGY")
        print("="*120)
        print(df.round(3))
        
        print(f"\nKey Metrics:")
        print(f"   Avg OOS Return (6m)     : {df['oos_return'].mean():.3f}%")
        print(f"   Avg Calmar              : {df['oos_calmar'].mean():.3f}")
        print(f"   Median Calmar           : {df['oos_calmar'].median():.3f}")
        print(f"   Win Rate (positive OOS) : {(df['oos_return'] > 0).mean()*100:.1f}%")
        print(f"   Avg Trades per window   : {df['oos_trades'].mean():.1f}")
        
        print("\n" + "="*80)
        if df['oos_calmar'].mean() > 1.0 and (df['oos_return'] > 0).mean() > 0.65:
            print("✅ STRATEGY PASSED WFA - Good robustness")
        else:
            print("⚠️  Strategy needs further improvement")
        print("="*80)

# Quick test
if __name__ == "__main__":
    wfa = WalkForwardAnalyzer()
    results = wfa.rolling_walk_forward(is_years=2, oos_months=6, step_months=3)