import pandas as pd
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.data.data_fetcher import DataFetcher
from src.backtester.backtester import SimpleBacktester

class SignalGenerator:
    """Generates trading signals from backtester logic for live/paper execution."""
    
    def __init__(self):
        self.fetcher = DataFetcher()
        self.backtester = SimpleBacktester(transaction_cost=0.001)
    
    def get_latest_signal(self, symbol: str) -> dict:
        """Generate current signal based on latest data (SMA crossover)."""
        df = self.fetcher.fetch_and_cache([symbol])
        if df.empty or len(df) < 50:
            return {"symbol": symbol, "signal": "hold", "reason": "insufficient data"}
        
        data = df[df['symbol'] == symbol].copy()
        data.set_index('date', inplace=True)
        
        data['short_sma'] = data['Close'].rolling(20).mean()
        data['long_sma'] = data['Close'].rolling(50).mean()
        
        latest = data.iloc[-1]
        
        if latest['short_sma'] > latest['long_sma']:
            signal = "buy"
            reason = "Short SMA crossed above Long SMA"
        elif latest['short_sma'] < latest['long_sma']:
            signal = "sell"
            reason = "Short SMA crossed below Long SMA"
        else:
            signal = "hold"
            reason = "No clear crossover"
        
        # Add risk check (simple volatility)
        recent_vol = data['Close'].pct_change().tail(20).std()
        position_size = min(1.0, 0.10 / (recent_vol + 0.001))  # volatility targeting
        
        return {
            "symbol": symbol,
            "signal": signal,
            "reason": reason,
            "latest_price": latest['Close'],
            "suggested_position_size": round(position_size, 2),
            "volatility": round(recent_vol, 4)
        }
    
    def get_all_signals(self):
        signals = {}
        for symbol in ["AAPL", "MSFT", "GOOGL", "TSLA"]:  # Use config later
            signals[symbol] = self.get_latest_signal(symbol)
        return signals

# Test
if __name__ == "__main__":
    sg = SignalGenerator()
    signals = sg.get_all_signals()
    for symbol, sig in signals.items():
        print(f"{symbol}: {sig['signal'].upper()} | Price ${sig['latest_price']:.2f} | Size {sig['suggested_position_size']}")