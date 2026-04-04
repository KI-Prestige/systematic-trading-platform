print("🚀 Systematic Trading Platform - Starting up...")

from config import SYMBOLS
from src.data.data_fetcher import DataFetcher
from src.backtester.backtester import SimpleBacktester

print(f"Config loaded with {len(SYMBOLS)} symbols.")

# Test backtester
bt = SimpleBacktester(transaction_cost=0.001)
results = bt.run_on_all_symbols()

print("\n=== Backtest Results ===")
for symbol, res in results.items():
    print(f"{symbol}: Return {res['total_return']:.2%} | Sharpe {res['sharpe_ratio']:.2f} | DD {res['max_drawdown']:.2%} | Trades {res['num_trades']}")

print("\n✅ Step 3 backtester test completed.")