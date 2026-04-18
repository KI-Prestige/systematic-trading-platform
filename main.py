print("🚀 Systematic Trading Platform - Starting up...")
from config import SYMBOLS
from src.live.order_logger import OrderLogger
from src.strategies.signal_generator import SignalGenerator
from src.live.paper_trader import PaperTrader

print(f"Config loaded with {len(SYMBOLS)} symbols.\n")

# Generate latest signals
print("=== Generating Latest Trading Signals ===")
sg = SignalGenerator()
signals = sg.get_all_signals()

for symbol, sig in signals.items():
    print(f"{symbol}: {sig['signal'].upper()} | Price ${sig['latest_price']:.2f} | Suggested Size {sig['suggested_size']}")

# Safe paper execution with position awareness
print("\n=== Safe Paper Trading Execution with Position Awareness ===")
trader = PaperTrader()
logger = OrderLogger()
trader.get_account()

print("\nCurrent positions before execution:", logger.get_current_positions())

print("\nExecuting safe paper orders (position-aware)...")
for symbol, sig in signals.items():
    trader.submit_safe_order(symbol, sig['signal'], sig['suggested_size'], logger=logger)

print("\nUpdated positions:", logger.get_current_positions())
print("\n✅ Full cycle with position tracking complete.")