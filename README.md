# Algorithmic Trading Backtesting Engine

## Live Demo
🔗 **Dashboard:** http://35.154.235.211/
🔗 **API:** https://algo-trading-api-mpd1.onrender.com

## Architecture Overview

Hybrid cloud deployment with split frontend/backend:

- **API (Backend)**: FastAPI on Render — managed HTTPS, auto-deploy on push, SQLite caching
- **Dashboard (Frontend)**: Streamlit on AWS EC2 t3.micro — Docker + Nginx reverse proxy
- **Infrastructure**: AWS Free Tier (EC2, Elastic IP), Render Free Tier

[Full Architecture Details](ARCHITECTURE.md)

## Strategies Implemented
- SMA Crossover (Trend Following)
- RSI Mean Reversion
- Composite (SMA + RSI Filter)

## Metrics Tracked
- Win Rate, Max Drawdown, Sharpe Ratio, Total Trades, Avg Trade Return

## Quick Start (Local)

```bash
# Backend
cd algo-trading-api
pip install -r requirements.txt
uvicorn main:app --reload

# Dashboard (separate terminal)
streamlit run dashboard.py
```

## Deployment

- **API**: Auto-deploys on `git push` to Render
- **Dashboard**: Manual `git pull && docker compose up -d` on EC2 (or add GitHub Actions)

## Tech Stack
FastAPI • Streamlit • Pandas • NumPy • Docker • Nginx • AWS EC2 • Render