import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.data.data_fetcher import DataFetcher
from config import STRATEGY, SYMBOLS
import ta  # for ADX

class Backtester:
    """
    Efficient historical backtester using the EXACT same logic as live trading.
    Pre-calculates indicators once → no more endless loading spam.
    """
    
    def __init__(self):
        self.fetcher = DataFetcher()
        self.trades = []
        self.equity_curve = []
        
    def run(self, start_date: str = None, end_date: str = None, initial_capital: float = 100000.0):
        print("🚀 Starting Efficient Backtest...")
        print(f"Strategy: Golden Cross (20/50) + ADX ≥ {STRATEGY['adx_threshold']} + Volume filter")
        print(f"Risk: SL {STRATEGY['stop_loss_pct']*100}% | TP {STRATEGY['take_profit_pct']*100}%")
        
        capital = initial_capital
        position = {symbol: 0 for symbol in SYMBOLS}
        entry_price = {symbol: None for symbol in SYMBOLS}
        
        for symbol in SYMBOLS:
            print(f"\n=== Backtesting {symbol} ===")
            
            # Load data once
            df = self.fetcher.fetch_and_cache([symbol])
            df = df[df['symbol'] == symbol].copy()
            df.set_index('date', inplace=True)
            df = df.sort_index()
            
            if start_date:
                df = df[df.index >= pd.to_datetime(start_date)]
            if end_date:
                df = df[df.index <= pd.to_datetime(end_date)]
            
            if len(df) < STRATEGY["long_window"]:
                print(f"   Not enough data for {symbol}")
                continue
            
            # Pre-calculate indicators once (same as live strategy)
            df['short_sma'] = df['Close'].rolling(window=STRATEGY["short_window"]).mean()
            df['long_sma'] = df['Close'].rolling(window=STRATEGY["long_window"]).mean()
            df['adx'] = ta.trend.ADXIndicator(high=df['High'], low=df['Low'], close=df['Close'], window=STRATEGY["adx_window"]).adx()
            df['avg_volume'] = df['Volume'].rolling(window=20).mean()
            df['volatility'] = df['Close'].pct_change().rolling(20).std()
            
            for i in range(STRATEGY["long_window"], len(df)):
                current_date = df.index[i]
                row = df.iloc[i]
                prev_row = df.iloc[i-1]
                
                # === Generate signal (exact same logic as live) ===
                golden_cross = (prev_row['short_sma'] <= prev_row['long_sma']) and (row['short_sma'] > row['long_sma'])
                death_cross = (prev_row['short_sma'] >= prev_row['long_sma']) and (row['short_sma'] < row['long_sma'])
                
                vol_ok = row['volatility'] <= STRATEGY["max_volatility"]
                adx_ok = row['adx'] >= STRATEGY["adx_threshold"]
                volume_ok = row['Volume'] > (row['avg_volume'] * STRATEGY["volume_multiplier"])
                
                signal = "hold"
                reason = "No crossover or filters not met"
                
                if golden_cross and vol_ok and adx_ok and volume_ok:
                    signal = "buy"
                    reason = "GOLDEN CROSS + filters passed"
                elif death_cross and vol_ok and adx_ok and volume_ok:
                    signal = "sell"
                    reason = "DEATH CROSS + filters passed"
                
                # === SL/TP check if in position ===
                if position[symbol] != 0:
                    pnl_pct = (row['Close'] - entry_price[symbol]) / entry_price[symbol] if position[symbol] > 0 else (entry_price[symbol] - row['Close']) / entry_price[symbol]
                    if pnl_pct <= -STRATEGY["stop_loss_pct"] or pnl_pct >= STRATEGY["take_profit_pct"]:
                        exit_reason = "STOP LOSS" if pnl_pct <= -STRATEGY["stop_loss_pct"] else "TAKE PROFIT"
                        capital += position[symbol] * row['Close']
                        self.trades.append({
                            'date': current_date, 'symbol': symbol, 'action': 'EXIT',
                            'qty': abs(position[symbol]), 'price': row['Close'],
                            'reason': exit_reason, 'pnl_pct': pnl_pct * 100
                        })
                        position[symbol] = 0
                        entry_price[symbol] = None
                        continue
                
                # === New position ===
                if signal in ["buy", "sell"] and position[symbol] == 0:
                    qty = max(STRATEGY["min_position_size"], min(STRATEGY["max_position_size"],
                              int(STRATEGY["target_volatility"] / (row['volatility'] + 0.0001))))
                    
                    position[symbol] = qty if signal == "buy" else -qty
                    entry_price[symbol] = row['Close']
                    
                    self.trades.append({
                        'date': current_date, 'symbol': symbol, 'action': signal.upper(),
                        'qty': qty, 'price': row['Close'], 'reason': reason
                    })
                
                # Record equity
                current_value = capital + sum(p * df.loc[current_date, 'Close'] for p in position.values() if p != 0)
                self.equity_curve.append({'date': current_date, 'equity': current_value})
        
        self._generate_report()
        return self
    
    def _generate_report(self):
        print("\n" + "="*70)
        print("BACKTEST COMPLETE - PERFORMANCE SUMMARY")
        print("="*70)
        
        trades_df = pd.DataFrame(self.trades)
        equity_df = pd.DataFrame(self.equity_curve)
        
        if not trades_df.empty:
            print(f"Total Trades: {len(trades_df)}")
            if 'pnl_pct' in trades_df.columns:
                win_rate = (trades_df['pnl_pct'] > 0).mean() * 100
                print(f"Win Rate: {win_rate:.1f}%")
        
        if not equity_df.empty:
            total_return = (equity_df['equity'].iloc[-1] / equity_df['equity'].iloc[0] - 1) * 100
            print(f"Total Return: {total_return:.2f}%")
            print(f"Final Equity: ${equity_df['equity'].iloc[-1]:,.2f}")
        
        print("\nBacktest finished successfully. No more spam!")

# Quick test
if __name__ == "__main__":
    bt = Backtester()
    bt.run()