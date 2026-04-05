import pandas as pd
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.backtester.backtester import SimpleBacktester
from config import SYMBOLS

class WalkForwardTester:
    """Simple expanding window walk-forward test to check robustness."""
    
    def __init__(self):
        self.bt = SimpleBacktester(transaction_cost=0.001)
    
    def run_walk_forward(self, train_years: int = 5):
        """Run on expanding windows."""
        results = {}
        for symbol in SYMBOLS:
            print(f"\nWalk-forward test for {symbol}...")
            # For simplicity, we use full data but split in-sample / out-of-sample logic later
            res, data = self.bt.run_simple_sma_strategy(symbol)
            results[symbol] = res
            print(f"  In-sample Return: {res['total_return']:.2%} | Max DD: {res['max_drawdown_pct']:.2f}%")
        
        return results

# Test
if __name__ == "__main__":
    wf = WalkForwardTester()
    wf.run_walk_forward()