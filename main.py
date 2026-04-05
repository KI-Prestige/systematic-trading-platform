print("🚀 Systematic Trading Platform - Starting up...")

from config import SYMBOLS
from src.backtester.backtester import SimpleBacktester
from src.backtester.walk_forward import WalkForwardTester
import os

print(f"Config loaded with {len(SYMBOLS)} symbols.\n")

# Run full backtest
bt = SimpleBacktester(transaction_cost=0.001)
results = bt.run_on_all_symbols()

print("\n=== Backtest Results with Risk ===")
for symbol, res in results.items():
    print(f"{symbol}: Return {res['total_return']:.2%} | Sharpe {res['sharpe_ratio']:.2f} | Max DD {res['max_drawdown_pct']:.2f}% | Trades {res['num_trades']}")

# Run walk-forward
print("\n=== Walk-Forward Validation ===")
wf = WalkForwardTester()
wf_results = wf.run_walk_forward()

# Create backtests folder if not exists and save summary
os.makedirs("backtests", exist_ok=True)
with open("backtests/results_summary.txt", "w") as f:
    f.write("Backtest Summary\n")
    f.write("================\n\n")
    for symbol, res in results.items():
        f.write(f"{symbol}:\n")
        f.write(f"  Return: {res['total_return']:.2%}\n")
        f.write(f"  Sharpe: {res['sharpe_ratio']:.2f}\n")
        f.write(f"  Max DD: {res['max_drawdown_pct']:.2f}%\n")
        f.write(f"  Trades: {res['num_trades']}\n\n")

print("\n✅ Results saved to backtests/results_summary.txt")
print("✅ Step 5: Walk-forward + documentation test completed.")

print("🚀 Systematic Trading Platform - Starting up...")
print("Run `streamlit run dashboard/app.py` for the dashboard.")
print("All core modules loaded successfully.")

print("\nTo test paper trading: python -m src.live.paper_trader")