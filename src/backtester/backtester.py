import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.data.data_fetcher import DataFetcher
from config import STRATEGY, SYMBOLS
import ta

class Backtester:
    """
    Professional Backtester with Monthly Returns, Trade Log, and robust error handling.
    """
    
    def __init__(self):
        self.fetcher = DataFetcher()
        self.trades = []
        self.equity_curve = []
        self.initial_capital = 100000.0
        
    def run(self, start_date="2024-01-01", end_date=None):
        print("🚀 Starting Enhanced Professional Backtest...")
        print(f"Risk: SL -{STRATEGY['stop_loss_pct']*100}% | TP +{STRATEGY['take_profit_pct']*100}% | Trailing: {STRATEGY.get('trailing_stop_pct', 0.05)*100}%")
        
        capital = self.initial_capital
        position = {sym: 0 for sym in SYMBOLS}
        entry_price = {sym: None for sym in SYMBOLS}
        
        for symbol in SYMBOLS:
            print(f"\n→ Backtesting {symbol}")
            df = self.fetcher.fetch_and_cache([symbol])
            df = df[df['symbol'] == symbol].copy()
            df.set_index('date', inplace=True)
            df = df.sort_index()
            
            if start_date: 
                df = df[df.index >= pd.to_datetime(start_date)]
            if end_date: 
                df = df[df.index <= pd.to_datetime(end_date)]
            
            # Pre-calculate indicators
            df['short_sma'] = df['Close'].rolling(STRATEGY["short_window"]).mean()
            df['long_sma'] = df['Close'].rolling(STRATEGY["long_window"]).mean()
            df['adx'] = ta.trend.ADXIndicator(df['High'], df['Low'], df['Close'], STRATEGY["adx_window"]).adx()
            df['avg_vol'] = df['Volume'].rolling(20).mean()
            df['vol'] = df['Close'].pct_change().rolling(20).std()
            
            for i in range(STRATEGY["long_window"], len(df)):
                row = df.iloc[i]
                prev = df.iloc[i-1]
                date = df.index[i]
                
                golden = (prev['short_sma'] <= prev['long_sma']) and (row['short_sma'] > row['long_sma'])
                death = (prev['short_sma'] >= prev['long_sma']) and (row['short_sma'] < row['long_sma'])
                
                filters_passed = (row['vol'] <= STRATEGY["max_volatility"] and 
                                row['adx'] >= STRATEGY["adx_threshold"] and 
                                row['Volume'] > row['avg_vol'] * STRATEGY["volume_multiplier"])
                
                signal = "buy" if golden and filters_passed else "sell" if death and filters_passed else "hold"
                
                # Risk Management: SL / TP / Trailing Stop
                if position[symbol] != 0:
                    pnl_pct = (row['Close'] - entry_price[symbol]) / entry_price[symbol] if position[symbol] > 0 else (entry_price[symbol] - row['Close']) / entry_price[symbol]
                    
                    exit_reason = ""
                    if pnl_pct <= -STRATEGY["stop_loss_pct"]:
                        exit_reason = f"STOP LOSS ({pnl_pct*100:.1f}%)"
                    elif pnl_pct >= STRATEGY["take_profit_pct"]:
                        exit_reason = f"TAKE PROFIT ({pnl_pct*100:.1f}%)"
                    elif pnl_pct >= STRATEGY.get("trailing_stop_pct", 0.05):
                        trailing_level = pnl_pct - STRATEGY.get("trailing_stop_pct", 0.05)
                        if pnl_pct < trailing_level:
                            exit_reason = f"TRAILING STOP ({pnl_pct*100:.1f}%)"
                    
                    if exit_reason:
                        capital += position[symbol] * row['Close']
                        self.trades.append({
                            'date': date, 'symbol': symbol, 'action': 'EXIT',
                            'price': row['Close'], 'pnl_pct': pnl_pct*100
                        })
                        position[symbol] = 0
                        entry_price[symbol] = None
                
                # New entry
                if signal in ["buy", "sell"] and position[symbol] == 0:
                    qty = max(STRATEGY["min_position_size"], min(STRATEGY["max_position_size"], 
                             int(STRATEGY["target_volatility"] / (row['vol'] + 1e-6))))
                    position[symbol] = qty if signal == "buy" else -qty
                    entry_price[symbol] = row['Close']
                    self.trades.append({
                        'date': date, 'symbol': symbol, 'action': signal.upper(),
                        'price': row['Close'], 'pnl_pct': None
                    })
                
                # Track equity
                current_equity = capital + sum(p * df.loc[date, 'Close'] for p in position.values() if p != 0)
                self.equity_curve.append({'date': date, 'equity': current_equity})
        
        self._generate_full_report()
        self._plot_equity_and_drawdown()
        self._export_trade_log()
        return self
    
    def _generate_full_report(self):
        print("\n" + "="*85)
        print("ENHANCED BACKTEST REPORT - FULL ANALYSIS")
        print("="*85)
        
        equity_df = pd.DataFrame(self.equity_curve)
        trades_df = pd.DataFrame(self.trades)
        
        total_return = (equity_df['equity'].iloc[-1] / equity_df['equity'].iloc[0] - 1) * 100 if len(equity_df) > 0 else 0
        print(f"Initial Capital : ${self.initial_capital:,.2f}")
        print(f"Final Equity    : ${equity_df['equity'].iloc[-1]:,.2f}" if len(equity_df) > 0 else "$100,000.00")
        print(f"Total Return    : {total_return:.2f}%")
        print(f"Total Trades    : {len(trades_df)}")
        
        completed = trades_df[trades_df.get('pnl_pct', pd.Series()).notna()]
        if not completed.empty:
            win_rate = (completed['pnl_pct'] > 0).mean() * 100
            avg_win = completed[completed['pnl_pct'] > 0]['pnl_pct'].mean() if 'pnl_pct' in completed.columns else 0
            avg_loss = completed[completed['pnl_pct'] <= 0]['pnl_pct'].mean() if 'pnl_pct' in completed.columns else 0
            print(f"Win Rate        : {win_rate:.1f}%")
            print(f"Avg Win         : {avg_win:.1f}%")
            print(f"Avg Loss        : {avg_loss:.1f}%")
        
        # Sharpe Ratio
        returns = equity_df['equity'].pct_change().dropna()
        if len(returns) > 1:
            sharpe = returns.mean() / returns.std() * np.sqrt(252) if returns.std() != 0 else 0
            print(f"Sharpe Ratio    : {sharpe:.2f}")
        
        # Max Drawdown
        if len(equity_df) > 0:
            equity_curve = equity_df['equity'].values
            peak = np.maximum.accumulate(equity_curve)
            drawdown = (equity_curve - peak) / peak
            max_dd = drawdown.min() * 100
            print(f"Max Drawdown    : {max_dd:.2f}%")
        
        # Monthly Returns (Fixed for modern pandas)
        if len(equity_df) > 0:
            equity_df.index = pd.to_datetime(equity_df['date'])
            monthly = equity_df['equity'].resample('ME').last().pct_change() * 100
            print("\nMonthly Returns (%):")
            print(monthly.round(2))
        
        print("="*85)
    
    def _plot_equity_and_drawdown(self):
        if not self.equity_curve:
            print("No equity data to plot.")
            return
        equity_df = pd.DataFrame(self.equity_curve)
        equity_df.set_index('date', inplace=True)
        
        plt.figure(figsize=(14, 10))
        
        plt.subplot(2, 1, 1)
        plt.plot(equity_df.index, equity_df['equity'], label='Equity Curve', color='blue', linewidth=2)
        plt.title('Backtest Equity Curve')
        plt.ylabel('Portfolio Value ($)')
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        equity_curve = equity_df['equity'].values
        peak = np.maximum.accumulate(equity_curve)
        drawdown = (equity_curve - peak) / peak * 100
        
        plt.subplot(2, 1, 2)
        plt.fill_between(equity_df.index, drawdown, 0, color='red', alpha=0.3)
        plt.plot(equity_df.index, drawdown, color='red', label='Drawdown %')
        plt.title('Drawdown Chart')
        plt.ylabel('Drawdown (%)')
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        plt.tight_layout()
        plt.savefig('backtests/enhanced_equity_drawdown.png', dpi=300)
        print("📊 Equity + Drawdown charts saved → backtests/enhanced_equity_drawdown.png")
    
    def _export_trade_log(self):
        if not self.trades:
            print("No trades to export.")
            return
        trades_df = pd.DataFrame(self.trades)
        trades_df.to_csv('backtests/trade_log.csv', index=False)
        print(f"📋 Detailed trade log exported → backtests/trade_log.csv ({len(trades_df)} trades)")

if __name__ == "__main__":
    bt = Backtester()
    bt.run()

