import pandas as pd
import numpy as np
from typing import Dict
import os
import sys

# Safe import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.data.data_fetcher import DataFetcher
from config import SYMBOLS

class RiskManager:
    """Basic risk management - position sizing and drawdown control."""
    def __init__(self, max_position: float = 1.0, max_drawdown_limit: float = -0.20):
        self.max_position = max_position
        self.max_drawdown_limit = max_drawdown_limit  # Stop if DD exceeds 20%
    
    def calculate_position_size(self, volatility: float) -> float:
        """Simple volatility-based sizing (inverse volatility)."""
        if volatility == 0:
            return self.max_position
        return min(self.max_position, 0.10 / volatility)  # Target ~10% vol contribution

class SimpleBacktester:
    """Improved modular backtester with risk controls."""
    
    def __init__(self, transaction_cost: float = 0.001):
        self.transaction_cost = transaction_cost
        self.fetcher = DataFetcher()
        self.risk_manager = RiskManager()
    
    def run_simple_sma_strategy(self, symbol: str, short_window: int = 20, long_window: int = 50) -> Dict:
        df = self.fetcher.fetch_and_cache([symbol])
        if df.empty:
            return {"error": "No data"}
        
        data = df[df['symbol'] == symbol].copy()
        data.set_index('date', inplace=True)
        
        data['short_sma'] = data['Close'].rolling(short_window).mean()
        data['long_sma'] = data['Close'].rolling(long_window).mean()
        
        data['signal'] = 0
        data.loc[data['short_sma'] > data['long_sma'], 'signal'] = 1
        data.loc[data['short_sma'] < data['long_sma'], 'signal'] = 0  # Flat instead of short for simplicity
        
        data['market_return'] = data['Close'].pct_change()
        data['position'] = data['signal'].shift(1).fillna(0)
        
        # Risk-adjusted position (simple volatility targeting)
        rolling_vol = data['market_return'].rolling(20).std()
        data['position'] = data['position'] * data['position'].apply(
            lambda p: self.risk_manager.calculate_position_size(rolling_vol.iloc[-1] if not rolling_vol.empty else 0.01)
        )
        
        data['strategy_return'] = data['position'] * data['market_return']
        
        # Transaction costs on position changes
        data['position_change'] = data['position'].diff().fillna(0)
        data['cost'] = abs(data['position_change']) * self.transaction_cost
        data['strategy_return'] -= data['cost']
        
        # Proper equity curve and drawdown
        data['equity'] = (1 + data['strategy_return']).cumprod()
        data['cum_return'] = data['equity'] - 1
        data['peak'] = data['equity'].cummax()
        data['drawdown'] = (data['equity'] - data['peak']) / data['peak']
        
        total_return = data['equity'].iloc[-1] - 1
        sharpe = data['strategy_return'].mean() / data['strategy_return'].std() * np.sqrt(252) if data['strategy_return'].std() > 0 else 0
        max_dd = data['drawdown'].min()
        
        results = {
            "symbol": symbol,
            "total_return": total_return,
            "sharpe_ratio": sharpe,
            "max_drawdown": max_dd,
            "num_trades": int((data['position_change'] != 0).sum()),
            "final_equity": data['equity'].iloc[-1],
            "max_drawdown_pct": max_dd * 100
        }
        
        return results, data  # Return data for potential plotting later
    
    def run_on_all_symbols(self):
        results = {}
        for symbol in SYMBOLS:
            print(f"Running improved SMA strategy on {symbol}...")
            res, _ = self.run_simple_sma_strategy(symbol)
            results[symbol] = res
        return results
    
    def close(self):
        self.fetcher.close()


# Test
if __name__ == "__main__":
    bt = SimpleBacktester()
    results = bt.run_on_all_symbols()
    for symbol, res in results.items():
        print(f"\n{symbol}: Return {res['total_return']:.2%} | Sharpe {res['sharpe_ratio']:.2f} | Max DD {res['max_drawdown_pct']:.2f}% | Trades {res['num_trades']}")

    bt.close()