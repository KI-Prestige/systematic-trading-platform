print("🚀 Systematic Trading Platform - Starting up...")

from config import SYMBOLS
from src.backtester.backtester import SimpleBacktester
from src.strategies.signal_generator import SignalGenerator
from src.live.execution import PaperTrader

print(f"Config loaded with {len(SYMBOLS)} symbols.\n")

# 1. Run backtest
bt = SimpleBacktester()
results = bt.run_on_all_symbols()

print("\n=== Backtest Summary ===")
for symbol, res in results.items():
    print(f"{symbol}: Return {res['total_return']:.2%} | Sharpe {res['sharpe_ratio']:.2f} | Max DD {res['max_drawdown_pct']:.2f}%")

# 2. Generate live signals
print("\n=== Latest Trading Signals ===")
sg = SignalGenerator()
signals = sg.get_all_signals()

for symbol, sig in signals.items():
    print(f"{symbol}: {sig['signal'].upper()} | Price ${sig['latest_price']:.2f} | Suggested Size {sig['suggested_position_size']}")

# 3. Paper trading demo (SAFE - only print, no auto-order yet)
print("\n=== Paper Trading Connection ===")
trader = PaperTrader()
trader.get_account()

print("\n✅ Full flow ready: Backtest → Signals → Paper Execution")
print("Next step: Auto-execute safe paper orders from signals.")