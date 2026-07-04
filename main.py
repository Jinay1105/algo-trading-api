from fastapi import FastAPI
import yfinance as yf
import pandas as pd
import sqlite3
from engine import apply_sma_crossover

app = FastAPI(title="Algo Trading Backtest API", version="2.0")

# --- DATABASE SETUP ---
DB_NAME = "market_data.db"

def init_db():
    """Ensures the database exists."""
    conn = sqlite3.connect(DB_NAME)
    conn.close()

init_db() # Run once on startup

def fetch_or_cache_data(ticker: str):
    """
    Checks the database for the stock data. If missing, downloads and saves it.
    """
    conn = sqlite3.connect(DB_NAME)
    table_name = ticker.replace(".", "_") # SQLite doesn't like dots in table names
    
    try:
        # Try to read from the database first
        df = pd.read_sql(f"SELECT * FROM {table_name}", conn, parse_dates=['Date'])
        df.set_index('Date', inplace=True)
        print(f"Loaded {ticker} from Database Cache!")
        
    except Exception: # <--- THE FIX: Catch any exception (like Pandas DatabaseError)
        # If it fails (table doesn't exist), fetch from Yahoo Finance
        print(f"Downloading {ticker} from Yahoo Finance...")
        stock = yf.Ticker(ticker)
        df = stock.history(period="1y")
        
        if not df.empty:
            # Save it to the database for next time
            df.to_sql(table_name, conn, if_exists='replace')
            
    conn.close()
    return df

# --- API ENDPOINTS ---
@app.get("/")
def read_root():
    return {"status": "online", "message": "Enterprise Trading Engine is running."}

@app.get("/backtest/{ticker}")
def run_backtest(ticker: str, fast: int = 10, slow: int = 50):
    try:
        # 1. Use the new caching layer
        hist = fetch_or_cache_data(ticker)
        
        if hist.empty:
            return {"error": "No data found for this ticker."}

        # 2. Run the engine
        backtest_results = apply_sma_crossover(hist, fast_period=fast, slow_period=slow)
        
        # 3. Calculate Returns
        final_market = (backtest_results['Cumulative_Market'].iloc[-1] - 1) * 100
        final_strategy = (backtest_results['Cumulative_Strategy'].iloc[-1] - 1) * 100
        
        return {
            "ticker": ticker.upper(),
            "strategy": f"SMA Crossover ({fast}/{slow})",
            "performance": {
                "market_return_percent": round(final_market, 2),
                "strategy_return_percent": round(final_strategy, 2)
            }
        }
    except Exception as e:
        return {"error": str(e)}