# src/backtester/backtester.py  (updated version)
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
    def __init__(self, initial_capital=100000.0):
        self.fetcher = DataFetcher()
        self.trades = []
        self.equity_curve = []
        self.initial_capital = initial_capital

    def run(self, params=None, start_date="2015-01-01", end_date=None, 
            export_trade_log=True, plot_results=False, 
            slippage_pct=0.0008, commission_pct=0.0005):
        
        if params is None:
            params = STRATEGY.copy()
        
        print(f"🚀 Running CONSERVATIVE Backtest | Risk/Trade: {params.get('risk_per_trade', 0.002)*100:.2f}%")

        capital = float(self.initial_capital)
        position = {sym: 0.0 for sym in SYMBOLS}
        entry_price = {sym: None for sym in SYMBOLS}
        max_pnl = {symbol: 0.0 for symbol in SYMBOLS}
        peak_equity = capital
        self.trades = []
        self.equity_curve = []

        all_data = {}
        for symbol in SYMBOLS:
            df = self.fetcher.fetch_and_cache([symbol])
            if df.empty: continue
            df = df[df['symbol'] == symbol].copy()
            df.set_index('date', inplace=True)
            df = df.sort_index()
            if start_date: df = df[df.index >= pd.to_datetime(start_date)]
            if end_date: df = df[df.index <= pd.to_datetime(end_date)]
            
            df['short_sma'] = df['Close'].rolling(params["short_window"]).mean()
            df['long_sma'] = df['Close'].rolling(params["long_window"]).mean()
            df['regime_sma'] = df['Close'].rolling(200).mean()
            df['adx'] = ta.trend.ADXIndicator(df['High'], df['Low'], df['Close'], params["adx_window"]).adx()
            df['vol'] = df['Close'].pct_change().rolling(20).std().fillna(0.02)
            df['avg_vol'] = df['Volume'].rolling(20).mean()
            
            all_data[symbol] = df

        if not all_data:
            print("No data loaded")
            return self

        master_df = list(all_data.values())[0]
        for i in range(params.get("long_window", 50), len(master_df)):
            date = master_df.index[i]
            current_value = capital

            for sym, pos in position.items():
                if pos != 0:
                    try:
                        sym_df = all_data[sym]
                        price = sym_df.loc[date, 'Close'] if date in sym_df.index else sym_df.iloc[-1]['Close']
                        current_value += pos * price
                    except:
                        current_value += pos * 100

            self.equity_curve.append({'date': date, 'equity': float(current_value)})
            peak_equity = max(peak_equity, current_value)

            for symbol in SYMBOLS:
                df = all_data.get(symbol)
                if df is None or i >= len(df): continue

                row = df.iloc[i]
                prev = df.iloc[i-1] if i > 0 else row

                # Signal Logic (Current Best)
                in_strong_uptrend = row['Close'] > row['regime_sma'] * 1.02
                vol_ok = row['vol'] <= params.get("max_volatility", 0.07)
                adx_ok = row['adx'] >= params.get("adx_threshold", 18)
                volume_ok = row['Volume'] > row.get('avg_vol', row['Volume']) * 0.9
                golden_cross = (prev['short_sma'] <= prev['long_sma']) and (row['short_sma'] > row['long_sma'])

                signal = "hold"
                if golden_cross and in_strong_uptrend and vol_ok and adx_ok and volume_ok:
                    signal = "buy"
                elif in_strong_uptrend and adx_ok and volume_ok and -0.04 <= (row['Close'] - row.get('short_sma', row['Close'])) / row.get('short_sma', row['Close']) <= 0.03:
                    signal = "buy"

                # Strong Protection
                risk_mult = self._apply_portfolio_protection(current_value, peak_equity)

                # Exit
                if position[symbol] != 0:
                    pnl_pct = (row['Close'] - entry_price[symbol]) / entry_price[symbol] if position[symbol] > 0 else (entry_price[symbol] - row['Close']) / entry_price[symbol]
                    if pnl_pct > max_pnl[symbol]:
                        max_pnl[symbol] = pnl_pct
                    exit_reason = self._check_exit(pnl_pct,max_pnl[symbol], params)
                    if exit_reason:
                        exit_price = row['Close']
                        if position[symbol] > 0:
                            exit_price *= (1 - slippage_pct)
                        else:
                            exit_price *= (1 + slippage_pct)
                        pnl = position[symbol] * (exit_price - entry_price[symbol])
                        capital += pnl
                        capital -= abs(position[symbol] * exit_price * commission_pct)
                        self.trades.append({'date': date, 'symbol': symbol, 'action': 'EXIT', 'price': exit_price, 'pnl_pct': pnl_pct*100, 'reason': exit_reason})
                        position[symbol] = 0.0
                        max_pnl[symbol] = 0.0
                        entry_price[symbol] = None

                # Entry with Protection
                if signal == "buy" and position[symbol] == 0 and risk_mult > 0:
                    risk_amount = capital * params.get("risk_per_trade", 0.002) * risk_mult
                    stop_distance = params.get("stop_loss_pct", 0.05)
                    qty = risk_amount / (stop_distance * row['Close'])
                    qty = max(0.5, min(12.0, qty))

                    fill_price = row['Close'] * (1 + slippage_pct)
                    commission = qty * fill_price * commission_pct
                    
                    position[symbol] = qty
                    entry_price[symbol] = fill_price
                    capital -= commission

                    self.trades.append({'date': date, 'symbol': symbol, 'action': 'BUY', 'price': fill_price, 'qty': qty, 'risk_mult': risk_mult})

        self._generate_full_report(params)
        if plot_results:
            self._plot_equity_and_drawdown()
        if export_trade_log and self.trades:
            self._export_trade_log()

        return self

    def _apply_portfolio_protection(self, current_equity, peak_equity):
        """Very strong protection for capital preservation"""
        dd = (current_equity - peak_equity) / peak_equity
        if dd < -0.10:
            return 0.25
        elif dd < -0.07:
            return 0.5
        return 1.0

    def _check_exit(self, pnl_pct, max_pnl, params):
        if pnl_pct <= -params.get("stop_loss_pct", 0.05):
            return "STOP LOSS"
        if pnl_pct >= params.get("take_profit_pct", 0.25):
            return "TAKE PROFIT"
        if pnl_pct > 0.08:
            trailing_threshold = max_pnl * (params.get("trailing_stop_pct", 0.10))
            if pnl_pct < trailing_threshold:
                return "TRAILING STOP"
        return None


    def _export_trade_log(self):
        if not self.trades:
            return
        os.makedirs('backtests', exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'backtests/trade_log_{timestamp}.csv'
        trades_df = pd.DataFrame(self.trades)
        trades_df.to_csv(filename, index=False)
        if len(self.trades) > 10:  
            print(f"📋 Trade log saved → {filename}")

    def _plot_equity_and_drawdown(self):
        # (Your existing method - keep as is)
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

    def run_with_warmup(self, params=None, start_date=None, end_date=None, warmup_bars=200,
                        slippage_pct=0.0008, commission_pct=0.0005):
        """Run with extra history for indicator warm-up"""
        if params is None:
            params = STRATEGY.copy()
        
        extended_start = pd.to_datetime(start_date) - pd.DateOffset(days=warmup_bars*2) if start_date else None
        
        bt_temp = Backtester(initial_capital=self.initial_capital)
        bt_temp.run(params=params, start_date=extended_start, end_date=end_date, 
                   export_trade_log=False, plot_results=False, 
                   slippage_pct=slippage_pct, commission_pct=commission_pct)
        
        # Filter to requested period
        equity_df = pd.DataFrame(bt_temp.equity_curve)
        if not equity_df.empty:
            equity_df = equity_df[equity_df['date'] >= pd.to_datetime(start_date)]
            self.equity_curve = equity_df.to_dict('records')
            self.trades = [t for t in bt_temp.trades if pd.to_datetime(t['date']) >= pd.to_datetime(start_date)]
        
        return self
    
    def _generate_full_report(self, params=None):
        # (Keep your existing method)
        print("\n" + "="*85)
        print("BACKTEST REPORT")
        print("="*85)
        equity_df = pd.DataFrame(self.equity_curve)
        if equity_df.empty:
            print("No equity data")
            return
        total_return = (equity_df['equity'].iloc[-1] / equity_df['equity'].iloc[0] - 1) * 100
        print(f"Initial Capital : ${self.initial_capital:,.2f}")
        print(f"Final Equity    : ${equity_df['equity'].iloc[-1]:,.2f}")
        print(f"Total Return    : {total_return:.2f}%")
        print(f"Total Trades    : {len(self.trades)}")
        returns = equity_df['equity'].pct_change().dropna()
        sharpe = returns.mean() / returns.std() * np.sqrt(252) if len(returns) > 1 and returns.std() > 0 else 0
        print(f"Sharpe Ratio    : {sharpe:.2f}")
        equity_values = equity_df['equity'].values
        peak = np.maximum.accumulate(equity_values)
        drawdown = (equity_values - peak) / peak
        max_dd = drawdown.min() * 100
        print(f"Max Drawdown    : {max_dd:.2f}%")
        print("="*85)

    # Add the other methods (_plot, _export, etc.) from your previous file

if __name__ == "__main__":
    bt = Backtester()
    bt.run()