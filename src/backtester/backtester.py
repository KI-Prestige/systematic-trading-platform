import pandas as pd
import numpy as np
from typing import Dict, Tuple
import os

# Safe import for config and data
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.data.data_fetcher import DataFetcher
from config import SYMBOLS

class SimpleBacktester:
    """Modular backtester with transaction costs and basic risk controls."""
    
    def __init__(self, transaction_cost: float = 0.001, max_position: float = 1.0):
        self.transaction_cost = transaction_cost  # 0.1% round-trip per trade
        self.max_position = max_position
        self.fetcher = DataFetcher()
    
    def run_simple_sma_strategy(self, symbol: str, short_window: int = 20, long_window: int = 50) -> Dict:
        """Simple SMA crossover strategy as baseline (using our cached data)."""
        df = self.fetcher.fetch_and_cache([symbol])
        if df.empty:
            return {"error": "No data"}
        
        # Prepare data for this symbol only
        data = df[df['symbol'] == symbol].copy()
        data.set_index('date', inplace=True)
        
        # Calculate SMAs
        data['short_sma'] = data['Close'].rolling(window=short_window).mean()
        data['long_sma'] = data['Close'].rolling(window=long_window).mean()
        
        # Generate signals
        data['signal'] = 0
        data.loc[data['short_sma'] > data['long_sma'], 'signal'] = 1   # Long
        data.loc[data['short_sma'] < data['long_sma'], 'signal'] = -1  # Short (for now, we'll treat as flat later if needed)
        
        # Calculate returns
        data['market_return'] = data['Close'].pct_change()
        data['position'] = data['signal'].shift(1).fillna(0)
        data['strategy_return'] = data['position'] * data['market_return']
        
        # Apply transaction costs (only on position changes)
        data['position_change'] = data['position'].diff().fillna(0)
        data['cost'] = abs(data['position_change']) * self.transaction_cost
        data['strategy_return'] = data['strategy_return'] - data['cost']
        
        # Performance metrics
        total_return = (1 + data['strategy_return']).prod() - 1
        sharpe = data['strategy_return'].mean() / data['strategy_return'].std() * np.sqrt(252) if data['strategy_return'].std() > 0 else 0
        max_dd = (data['strategy_return'].cumsum().cummax() - data['strategy_return'].cumsum()).min()
        
        equity_curve = (1 + data['strategy_return']).cumprod()
        
        results = {
            "symbol": symbol,
            "total_return": total_return,
            "sharpe_ratio": sharpe,
            "max_drawdown": max_dd,
            "num_trades": int(abs(data['position_change']).sum()),
            "equity_curve": equity_curve,
            "final_equity": equity_curve.iloc[-1] if not equity_curve.empty else 1.0,
            "data_points": len(data)
        }
        
        self.fetcher.close()
        return results
    
    def run_on_all_symbols(self) -> Dict:
        """Run strategy on all symbols and aggregate."""
        results = {}
        for symbol in SYMBOLS:
            print(f"Running SMA strategy on {symbol}...")
            res = self.run_simple_sma_strategy(symbol)
            results[symbol] = res
        return results

# Test
if __name__ == "__main__":
    bt = SimpleBacktester(transaction_cost=0.001)
    results = bt.run_on_all_symbols()
    for symbol, res in results.items():
        print(f"\n{symbol}:")
        print(f"  Total Return: {res['total_return']:.2%}")
        print(f"  Sharpe: {res['sharpe_ratio']:.2f}")
        print(f"  Max DD: {res['max_drawdown']:.2%}")
        print(f"  Trades: {res['num_trades']}")