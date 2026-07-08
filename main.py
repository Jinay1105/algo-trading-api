from fastapi import FastAPI
import yfinance as yf
import sqlite3
import pandas as pd
from engine import apply_sma_crossover, apply_rsi_strategy, apply_composite_strategy

app = FastAPI(title="Algo Trading Backtest API")
DB_NAME = "market_data.db"

def fetch_or_cache_data(ticker: str):
    conn = sqlite3.connect(DB_NAME)
    table_name = ticker.replace(".", "_")
    try:
        df = pd.read_sql(f"SELECT * FROM {table_name}", conn, parse_dates=['Date'])
        df.set_index('Date', inplace=True)
        print(f"Loaded {ticker} from Database Cache!")
    except Exception:
        print(f"Downloading {ticker} from Yahoo Finance...")
        stock = yf.Ticker(ticker)
        df = stock.history(period="1y")
        if not df.empty:
            df.to_sql(table_name, conn, if_exists='replace')
    conn.close()
    return df

@app.get("/backtest/{ticker}")
def run_sma_backtest(ticker: str, fast: int = 10, slow: int = 50):
    try:
        hist = fetch_or_cache_data(ticker)
        if hist.empty:
            return {"error": "No data found"}
        results = apply_sma_crossover(hist, fast, slow)
        chart_df = results.tail(200).copy()
        chart_df['Date_Str'] = chart_df.index.astype(str) 
        chart_data = chart_df[['Date_Str', 'Close', 'Fast_SMA', 'Slow_SMA']].to_dict(orient="list")
        
        return {
            "ticker": ticker.upper(),
            "strategy": f"SMA Crossover ({fast}/{slow})",
            "performance": {
                "market_return_percent": round((results['Cumulative_Market'].iloc[-1] - 1) * 100, 2),
                "strategy_return_percent": round((results['Cumulative_Strategy'].iloc[-1] - 1) * 100, 2)
            },
            "chart_data": chart_data 
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/backtest/rsi/{ticker}")
def run_rsi_backtest(ticker: str, period: int = 14):
    try:
        hist = fetch_or_cache_data(ticker)
        if hist.empty:
            return {"error": "No data found"}
        results = apply_rsi_strategy(hist, period)
        chart_df = results.tail(200).copy()
        chart_df['Date_Str'] = chart_df.index.astype(str) 
        chart_data = chart_df[['Date_Str', 'Close', 'RSI']].to_dict(orient="list")
        return {
            "ticker": ticker.upper(),
            "strategy": f"RSI Mean Reversion ({period})",
            "performance": {
                "market_return_percent": round((results['Cumulative_Market'].iloc[-1] - 1) * 100, 2),
                "strategy_return_percent": round((results['Cumulative_Strategy'].iloc[-1] - 1) * 100, 2)
            },
            "chart_data": chart_data # Send it to Streamlit
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/backtest/composite/{ticker}")
def run_composite_backtest(ticker: str, fast: int = 10, slow: int = 50, rsi: int = 14):
    try:
        hist = fetch_or_cache_data(ticker)
        if hist.empty:
            return {"error": "No data found"}
            
        results = apply_composite_strategy(hist, fast, slow, rsi)
        
        chart_df = results.tail(200).copy()
        chart_df['Date_Str'] = chart_df.index.astype(str) 
        chart_data = chart_df[['Date_Str', 'Close', 'Fast_SMA', 'Slow_SMA', 'RSI']].to_dict(orient="list")
        
        return {
            "ticker": ticker.upper(),
            "strategy": f"Composite SMA+RSI",
            "performance": {
                "market_return_percent": round((results['Cumulative_Market'].iloc[-1] - 1) * 100, 2),
                "strategy_return_percent": round((results['Cumulative_Strategy'].iloc[-1] - 1) * 100, 2)
            },
            "chart_data": chart_data 
        }
    except Exception as e:
        return {"error": str(e)}