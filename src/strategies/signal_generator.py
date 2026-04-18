import pandas as pd
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.data.data_fetcher import DataFetcher
from config import STRATEGY, SYMBOLS
import ta  # Technical Analysis library (we'll install if needed)

class SignalGenerator:
    """
    Phase 2: Professional Golden Cross with Multiple Filters
    - ADX Trend Strength
    - Volume Confirmation  
    - Volatility Guard
    """
    
    def __init__(self):
        self.fetcher = DataFetcher()
        self.short_window = STRATEGY["short_window"]
        self.long_window = STRATEGY["long_window"]
        self.min_data = STRATEGY["min_data_required"]
        self.previous_signals = {}
        
    def get_latest_signal(self, symbol: str) -> dict:
        df = self.fetcher.fetch_and_cache([symbol])
        
        if df.empty or len(df) < self.min_data:
            return {"symbol": symbol, "signal": "hold", "reason": "Insufficient data", 
                    "latest_price": None, "suggested_size": 0.0, "volatility": 0.0}

        data = df[df['symbol'] == symbol].copy()
        data.set_index('date', inplace=True)
        data = data.sort_index()
        
        # === Core Indicators ===
        data['short_sma'] = data['Close'].rolling(window=self.short_window).mean()
        data['long_sma'] = data['Close'].rolling(window=self.long_window).mean()
        
        # ADX (Trend Strength)
        data['adx'] = ta.trend.ADXIndicator(
            high=data['High'], 
            low=data['Low'], 
            close=data['Close'], 
            window=STRATEGY["adx_window"]
        ).adx()
        
        # Volume
        data['avg_volume'] = data['Volume'].rolling(window=20).mean()
        
        latest = data.iloc[-1]
        previous = data.iloc[-2] if len(data) > 1 else latest
        
        recent_vol = data['Close'].pct_change().tail(20).std()
        
        # Volatility-adjusted size
        suggested_size = STRATEGY["target_volatility"] / (recent_vol + 0.0001)
        suggested_size = max(STRATEGY["min_position_size"], 
                           min(STRATEGY["max_position_size"], suggested_size))
        
        # === FILTERS ===
        filters_passed = []
        reason_parts = []
        
        # 1. Volatility Filter
        if recent_vol > STRATEGY["max_volatility"]:
            return {"symbol": symbol, "signal": "hold", 
                    "reason": f"Volatility too high ({recent_vol:.4f})", 
                    "latest_price": round(latest['Close'], 2), "suggested_size": 0.0}
        
        # 2. ADX Trend Strength Filter
        adx_value = latest['adx']
        if adx_value < STRATEGY["adx_threshold"]:
            reason_parts.append(f"Weak trend (ADX {adx_value:.1f} < {STRATEGY['adx_threshold']})")
        else:
            filters_passed.append("Strong trend")
        
        # 3. Volume Confirmation
        volume_confirm = latest['Volume'] > (latest['avg_volume'] * STRATEGY["volume_multiplier"])
        if volume_confirm:
            filters_passed.append("Volume confirmed")
        else:
            reason_parts.append("Low volume")
        
        # === Crossover Detection ===
        golden_cross = (previous['short_sma'] <= previous['long_sma']) and (latest['short_sma'] > latest['long_sma'])
        death_cross = (previous['short_sma'] >= previous['long_sma']) and (latest['short_sma'] < latest['long_sma'])
        
        if golden_cross and len(filters_passed) >= 1:
            signal = "buy"
            reason = f"GOLDEN CROSS + Filters passed: {', '.join(filters_passed)}"
        elif death_cross and len(filters_passed) >= 1:
            signal = "sell"
            reason = f"DEATH CROSS + Filters passed: {', '.join(filters_passed)}"
        else:
            signal = "hold"
            reason = " | ".join(reason_parts) if reason_parts else "No crossover or filters not met"
        
        # Anti-repeat logic
        if signal != "hold" and self.previous_signals.get(symbol) == signal:
            signal = "hold"
            reason = f"Waiting for opposite signal (last: {signal.upper()})"
        
        if signal != "hold":
            self.previous_signals[symbol] = signal
        
        return {
            "symbol": symbol,
            "signal": signal,
            "reason": reason,
            "latest_price": round(latest['Close'], 2),
            "suggested_size": round(suggested_size, 2),
            "volatility": round(recent_vol, 4),
            "adx": round(adx_value, 1),
            "short_sma": round(latest['short_sma'], 2),
            "long_sma": round(latest['long_sma'], 2)
        }
    
    def get_all_signals(self):
        signals = {}
        for symbol in SYMBOLS:
            signals[symbol] = self.get_latest_signal(symbol)
        return signals


# Test
if __name__ == "__main__":
    sg = SignalGenerator()
    signals = sg.get_all_signals()
    print("=== Latest Trading Signals (Phase 2) ===\n")
    for symbol, sig in signals.items():
        print(f"{symbol}: {sig['signal'].upper()} | Price ${sig['latest_price']} | Size {sig['suggested_size']} | ADX {sig.get('adx', 'N/A')}")
        print(f"   → {sig['reason']}\n")