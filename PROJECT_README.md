# Systematic Trading Platform

**Production-grade systematic trading framework** built as a Junior Quant Developer portfolio project.

## Overview
End-to-end Python system that fetches market data, runs risk-managed backtests, generates trading signals, executes safely in paper trading, and provides live monitoring via dashboard.

## Features
- Robust data pipeline with SQLite caching (yfinance)
- Modular backtester with transaction costs, Sharpe, drawdown, and risk management
- SMA-based signal generator with volatility targeting
- Alpaca paper trading integration with position-aware execution
- Order logging and basic P&L tracking
- Interactive Streamlit dashboard (Backtest / Signals / Paper Portfolio)

## Tech Stack
- Python, pandas, yfinance, sqlite3, alpaca-py, streamlit
- Modular architecture with clear separation of concerns

## How to Run
1. `git clone https://github.com/KI-Prestige/systematic-trading-platform.git`
2. `cd systematic-trading-platform`
3. `python -m venv venv`
4. `venv\Scripts\activate` (Windows)
5. `pip install -r requirements.txt`
6. `python main.py` → Full cycle (backtest + signals + paper execution)
7. `streamlit run dashboard/app.py` → Interactive dashboard

## Project Status
- Phase 1 (Foundation) & Phase 2 (Live Execution) **COMPLETE**
- Running daily paper trading to build track record

## Goal
Demonstrate practical quant developer skills: reliable infrastructure, risk management, execution, and monitoring — ready for junior systematic trading / quant dev roles.

Built in Abuja, Nigeria | April 2026


## Goal
Demonstrate real-world quant developer skills: reliable infrastructure, risk awareness, and reproducible results.
To run dashboard: streamlit run dashboard/app.py