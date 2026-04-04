print("🚀 Systematic Trading Platform - Starting up...")

from config import SYMBOLS
from src.backtester.backtester import SimpleBacktester

print(f"Config loaded with {len(SYMBOLS)} symbols.\n")

bt = SimpleBacktester(transaction_cost=0.001)
results = bt.run_on_all_symbols()

print("\n=== Improved Backtest Results (with Risk) ===")
for symbol, res in results.items():
    print(f"{symbol}: Return {res['total_return']:.2%} | Sharpe {res['sharpe_ratio']:.2f} | Max DD {res['max_drawdown_pct']:.2f}% | Trades {res['num_trades']}")

print("\n✅ Step 4 backtester + risk module test completed.")