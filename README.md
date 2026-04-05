# Systematic Trading Platform

Production-grade Python framework for systematic trading.  
Built as a quant developer portfolio project focusing on clean architecture, data caching, backtesting, and risk management.

## Features
- Robust data pipeline with SQLite caching (yfinance)
- Modular backtester with transaction costs and risk controls
- Walk-forward validation
- RiskManager for position sizing and drawdown limits

## Tech Stack
- Python, pandas, yfinance, sqlite3
- Modular package structure

## How to Run
1. `git clone https://github.com/KI-Prestige/systematic-trading-platform.git`
2. `cd systematic-trading-platform`
3. `python -m venv venv`
4. `venv\Scripts\activate` (Windows)
5. `pip install -r requirements.txt`
6. `python main.py`

## Project Status (April 2026)
- Phase 1-5 complete: Data → Backtester → Risk → Walk-forward
- Next: Dashboard and paper-trading integration
- Phase 1 (Engineering Foundation) COMPLETE


## Goal
Demonstrate real-world quant developer skills: reliable infrastructure, risk awareness, and reproducible results.
To run dashboard: streamlit run dashboard/app.py