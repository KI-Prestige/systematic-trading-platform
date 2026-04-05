print("🚀 Systematic Trading Platform - Starting up...")

from config import SYMBOLS
from src.strategies.signal_generator import SignalGenerator
from src.live.paper_trader import PaperTrader

print(f"Config loaded with {len(SYMBOLS)} symbols.\n")

# Generate latest signals
print("=== Generating Latest Trading Signals ===")
sg = SignalGenerator()
signals = sg.get_all_signals()

for symbol, sig in signals.items():
    print(f"{symbol}: {sig['signal'].upper()} | Price ${sig['latest_price']:.2f} | Suggested Size {sig['suggested_position_size']}")

# Safe paper execution
print("\n=== Safe Paper Trading Execution ===")
trader = PaperTrader()
trader.get_account()

print("\nExecuting safe paper orders based on signals (small sizes only)...")
for symbol, sig in signals.items():
    trader.submit_safe_order(symbol, sig['signal'], sig['suggested_position_size'])

print("\n✅ Full cycle complete: Signals → Risk-checked Paper Execution")
print("Note: This is PAPER trading only. No real money is used.")