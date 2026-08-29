from fastapi import FastAPI, HTTPException, Path, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Annotated, Optional
from typing_extensions import Self
import yfinance as yf
import sqlite3
import pandas as pd
from engine import apply_sma_crossover, apply_rsi_strategy, apply_composite_strategy, calculate_metrics

VALID_PERIODS = {"1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"}

# Pydantic model for query/body validation (not path params)
class TickerRequest(BaseModel):
    ticker: Annotated[str, Field(
        min_length=1,
        max_length=20,
        pattern=r'^[A-Z0-9\.\-]+$',
        description='Stock ticker symbol (e.g., GOOG, TSLA, RELIANCE.NS)',
        examples=['GOOG', 'TSLA', 'RELIANCE.NS']
    )]
    fast: Optional[Annotated[int, Field(ge=1, le=200)]] = None
    slow: Optional[Annotated[int, Field(ge=1, le=500)]] = None
    rsi: Optional[Annotated[int, Field(ge=1, le=100)]] = None
    period: Annotated[str, Field(pattern="^(1d|5d|1mo|3mo|6mo|1y|2y|5y|10y|ytd|max)$")] = "max"

    @field_validator('ticker')
    @classmethod
    def validate_ticker_format(cls, v: str) -> str:
        """Validate ticker format - uppercase, alphanumeric with dots/hyphens"""
        v = v.strip().upper()
        if not v:
            raise ValueError('Ticker cannot be empty')
        if not all(c.isalnum() or c in '.-' for c in v):
            raise ValueError('Ticker can only contain letters, numbers, dots, and hyphens')
        return v

    @model_validator(mode='after')
    def validate_combination(self) -> Self:
        has_sma = self.fast is not None and self.slow is not None
        has_rsi = self.rsi is not None

        if not has_sma and not has_rsi:
            raise ValueError('Provide either (fast + slow) for SMA, rsi for RSI, or all three for Composite')

        if has_sma and self.fast >= self.slow:
            raise ValueError('Fast SMA must be less than Slow SMA')

        return self


app = FastAPI(title="Algo Trading Backtest API")

# CORS middleware for cross-origin requests (e.g., from dashboard on different domain)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your dashboard domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
DB_NAME = os.getenv("DB_PATH", "market_data.db")

def fetch_or_cache_data(ticker: str, period: str = "max") -> pd.DataFrame:
    """Fetch data from cache or yfinance with period-based caching"""
    if period not in VALID_PERIODS:
        period = "max"

    conn = sqlite3.connect(DB_NAME)
    table_name = ticker.replace(".", "_")
    cache_key = f"{table_name}_{period}"

    try:
        df = pd.read_sql(f"SELECT * FROM {cache_key}", conn, parse_dates=['Date'])
        df.set_index('Date', inplace=True)
        print(f"Loaded {ticker} from Database Cache (period={period})!")
    except Exception:
        print(f"Downloading {ticker} from Yahoo Finance (period={period})...")
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)
        if not df.empty:
            df.to_sql(cache_key, conn, if_exists='replace')
    conn.close()
    return df


def validate_ticker_exists(ticker: str, period: str = "max") -> pd.DataFrame:
    """Fetch data and raise 404 if ticker not found"""
    hist = fetch_or_cache_data(ticker, period)
    if hist.empty:
        raise HTTPException(
            status_code=404,
            detail=f"Ticker '{ticker}' not found or no data available for period '{period}'"
        )
    return hist


@app.get("/")
def landing():
    return {"detail": "Hello,Welcome to Algo Backtesting Engine"}


@app.get("/health")
def health():
    return {"status": "healthy", "service": "api"}


# Use Path parameter with validation for path parameters
@app.get("/backtest/{ticker}")
def run_sma_backtest(
    ticker: Annotated[str, Path(
        min_length=1,
        max_length=20,
        description='Stock ticker symbol',
        examples=['GOOG', 'TSLA', 'RELIANCE.NS']
    )],
    fast: Annotated[int, Query(ge=1, le=200)] = 10,
    slow: Annotated[int, Query(ge=1, le=500)] = 50,
    period: Annotated[str, Query(pattern="^(1d|5d|1mo|3mo|6mo|1y|2y|5y|10y|ytd|max)$")] = "max"
):
    if fast >= slow:
        raise HTTPException(status_code=422, detail='Fast SMA must be less than Slow SMA')

    ticker = ticker.strip().upper()
    hist = validate_ticker_exists(ticker, period)

    results = apply_sma_crossover(hist, fast, slow)
    metrics = calculate_metrics(results)
    chart_df = results.copy()
    chart_df['Date_Str'] = chart_df.index.astype(str)
    chart_data = chart_df[['Date_Str', 'Close', 'Fast_SMA', 'Slow_SMA']].to_dict(orient="list")

    return {
        "ticker": ticker,
        "strategy": f"SMA Crossover ({fast}/{slow})",
        "performance": {
            "market_return_percent": round((results['Cumulative_Market'].iloc[-1] - 1) * 100, 2),
            "strategy_return_percent": round((results['Cumulative_Strategy'].iloc[-1] - 1) * 100, 2),
            "total_trades": metrics["total_trades"],
            "win_rate_percent": metrics["win_rate_percent"],
            "max_drawdown_percent": metrics["max_drawdown_percent"],
            "sharpe_ratio": metrics["sharpe_ratio"]
        },
        "chart_data": chart_data
    }


@app.get("/backtest/rsi/{ticker}")
def run_rsi_backtest(
    ticker: Annotated[str, Path(
        min_length=1,
        max_length=20,
        description='Stock ticker symbol',
        examples=['GOOG', 'TSLA', 'RELIANCE.NS']
    )],
    period: Annotated[int, Query(ge=1, le=200)] = 14,
    data_period: Annotated[str, Query(pattern="^(1d|5d|1mo|3mo|6mo|1y|2y|5y|10y|ytd|max)$")] = "max"
):
    ticker = ticker.strip().upper()
    hist = validate_ticker_exists(ticker, data_period)

    results = apply_rsi_strategy(hist, period)
    metrics = calculate_metrics(results)
    chart_df = results.copy()
    chart_df['Date_Str'] = chart_df.index.astype(str)
    chart_data = chart_df[['Date_Str', 'Close', 'RSI']].to_dict(orient="list")

    return {
        "ticker": ticker,
        "strategy": f"RSI Mean Reversion ({period})",
        "performance": {
            "market_return_percent": round((results['Cumulative_Market'].iloc[-1] - 1) * 100, 2),
            "strategy_return_percent": round((results['Cumulative_Strategy'].iloc[-1] - 1) * 100, 2),
            "total_trades": metrics["total_trades"],
            "win_rate_percent": metrics["win_rate_percent"],
            "max_drawdown_percent": metrics["max_drawdown_percent"],
            "sharpe_ratio": metrics["sharpe_ratio"]
        },
        "chart_data": chart_data
    }


@app.get("/backtest/composite/{ticker}")
def run_composite_backtest(
    ticker: Annotated[str, Path(
        min_length=1,
        max_length=20,
        pattern=r'^[A-Z0-9\.\-]+$',
        description='Stock ticker symbol',
        examples=['GOOG', 'TSLA', 'RELIANCE.NS']
    )],
    fast: Annotated[int, Query(ge=1, le=200)] = 10,
    slow: Annotated[int, Query(ge=1, le=500)] = 50,
    rsi: Annotated[int, Query(ge=1, le=100)] = 14,
    period: Annotated[str, Query(pattern="^(1d|5d|1mo|3mo|6mo|1y|2y|5y|10y|ytd|max)$")] = "max"
):
    if fast >= slow:
        raise HTTPException(status_code=422, detail='Fast SMA must be less than Slow SMA')

    ticker = ticker.strip().upper()
    hist = validate_ticker_exists(ticker, period)

    results = apply_composite_strategy(hist, fast, slow, rsi)
    metrics = calculate_metrics(results)
    chart_df = results.copy()
    chart_df['Date_Str'] = chart_df.index.astype(str)
    chart_data = chart_df[['Date_Str', 'Close', 'Fast_SMA', 'Slow_SMA', 'RSI']].to_dict(orient="list")

    return {
        "ticker": ticker,
        "strategy": f"Composite SMA+RSI",
        "performance": {
            "market_return_percent": round((results['Cumulative_Market'].iloc[-1] - 1) * 100, 2),
            "strategy_return_percent": round((results['Cumulative_Strategy'].iloc[-1] - 1) * 100, 2),
            "total_trades": metrics["total_trades"],
            "win_rate_percent": metrics["win_rate_percent"],
            "max_drawdown_percent": metrics["max_drawdown_percent"],
            "sharpe_ratio": metrics["sharpe_ratio"]
        },
        "chart_data": chart_data
    }


# Alternative: POST endpoint using Pydantic model for request body
@app.post("/backtest")
def run_backtest(request: TickerRequest):
    ticker = request.ticker  # Already validated & normalized
    hist = validate_ticker_exists(ticker, request.period)

    has_sma = request.fast is not None and request.slow is not None
    has_rsi = request.rsi is not None

    if has_sma and has_rsi:
        # Composite
        results = apply_composite_strategy(hist, request.fast, request.slow, request.rsi)
        strategy_name = f"Composite SMA+RSI ({request.fast}/{request.slow}/{request.rsi})"
        chart_fields = ['Date_Str', 'Close', 'Fast_SMA', 'Slow_SMA', 'RSI']

    elif has_sma:
        # SMA only
        results = apply_sma_crossover(hist, request.fast, request.slow)
        strategy_name = f"SMA Crossover ({request.fast}/{request.slow})"
        chart_fields = ['Date_Str', 'Close', 'Fast_SMA', 'Slow_SMA']

    else:
        # RSI only
        results = apply_rsi_strategy(hist, request.rsi)
        strategy_name = f"RSI Mean Reversion ({request.rsi})"
        chart_fields = ['Date_Str', 'Close', 'RSI']

    metrics = calculate_metrics(results)
    chart_df = results.copy()
    chart_df['Date_Str'] = chart_df.index.astype(str)
    chart_data = chart_df[chart_fields].to_dict(orient="list")

    return {
        "ticker": ticker,
        "strategy": strategy_name,
        "performance": {
            "market_return_percent": round((results['Cumulative_Market'].iloc[-1] - 1) * 100, 2),
            "strategy_return_percent": round((results['Cumulative_Strategy'].iloc[-1] - 1) * 100, 2),
            "total_trades": metrics["total_trades"],
            "win_rate_percent": metrics["win_rate_percent"],
            "max_drawdown_percent": metrics["max_drawdown_percent"],
            "sharpe_ratio": metrics["sharpe_ratio"]
        },
        "chart_data": chart_data
    }