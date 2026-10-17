from fastapi import HTTPException
import sqlite3
import pandas as pd
import yfinance as yf
import requests
import time
import os

DB_NAME = os.getenv("DB_PATH", "market_data.db")
VALID_PERIODS = {"1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"}
YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"

CURRENCY_SYMBOLS = {
    "INR": "₹",
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "JPY": "¥",
    "CNY": "¥",
    "KRW": "₩",
    "SGD": "S$",
    "HKD": "HK$",
    "CAD": "C$",
    "AUD": "A$",
    "CHF": "CHF",
}

def get_currency_symbol(currency_code: str | None) -> str:
    """Map currency code to display symbol. Returns empty string if unknown."""
    if not currency_code:
        return ""
    return CURRENCY_SYMBOLS.get(currency_code.upper(), "")

def currency_from_history_meta(stock) -> str | None:
    """Currency from the chart meta block yfinance already downloaded with the prices."""
    try:
        meta = getattr(stock, "history_metadata", None) or {}
        code = meta.get("currency")
        if code:
            return str(code).strip().upper()
    except Exception:
        pass
    return None

def currency_from_chart_api(ticker: str, session=None) -> str | None:
    """Currency from Yahoo's chart API meta block - crumb-free and independent of yfinance."""
    try:
        s = session or requests.Session()
        s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        resp = s.get(YAHOO_CHART_URL.format(ticker=ticker),
                     params={'range': '1d', 'interval': '1d'}, timeout=15)
        if resp.status_code != 200:
            return None
        meta = resp.json()["chart"]["result"][0]["meta"]
        code = meta.get("currency")
        if code:
            return str(code).strip().upper()
    except Exception:
        pass
    return None

def currency_from_info(stock) -> str | None:
    """Currency from yfinance quoteSummary metadata (rate-limited, so last resort)."""
    try:
        code = (stock.info or {}).get("currency")
        if code:
            return str(code).strip().upper()
    except Exception:
        pass
    return None

def fetch_ticker_currency(ticker: str) -> str | None:
    """Resolve a ticker's currency without assuming anything from the symbol's suffix."""
    code = currency_from_chart_api(ticker)
    if code:
        return code
    try:
        stock = yf.Ticker(ticker)
        stock.history(period="5d")  # populates history_metadata
        code = currency_from_history_meta(stock) or currency_from_info(stock)
        if code:
            return code
    except Exception:
        pass
    return None

def fetch_or_cache_data(ticker: str, period: str = "1y") -> tuple[pd.DataFrame, str | None]:
    """Fetch data from cache or yfinance/yahooquery with retries and fallback. Returns (dataframe, currency_code)."""
    if period not in VALID_PERIODS:
        period = "1y"

    conn = sqlite3.connect(DB_NAME)
    table_name = ticker.replace(".", "_")
    cache_key = f"{table_name}_{period}"

    # 1. Try cache FIRST
    try:
        df = pd.read_sql(f"SELECT * FROM {cache_key}", conn, parse_dates=['Date'])
        df.set_index('Date', inplace=True)

        # Try to get currency from cached metadata table
        currency = None
        try:
            meta_df = pd.read_sql(f"SELECT currency FROM {cache_key}_meta", conn)
            if not meta_df.empty:
                currency = meta_df['currency'].iloc[0]
        except Exception:
            pass

        if not currency:
            currency = fetch_ticker_currency(ticker)
            if currency:
                pd.DataFrame([{"currency": currency}]).to_sql(f"{cache_key}_meta", conn, if_exists='replace')

        conn.close()
        return df, currency
    except Exception:
        pass  # Cache miss, will fetch

    # 2. Try yfinance with retries
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

    currency = None
    for attempt in range(3):
        try:
            stock = yf.Ticker(ticker, session=session)
            df = stock.history(period=period)
            if not df.empty:
                currency = (currency_from_history_meta(stock)
                            or currency_from_chart_api(ticker, session)
                            or currency_from_info(stock))

                df.to_sql(cache_key, conn, if_exists='replace')
                if currency:
                    pd.DataFrame([{"currency": currency}]).to_sql(f"{cache_key}_meta", conn, if_exists='replace')
                conn.close()
                return df, currency
        except Exception as e:
            pass

        if attempt < 2:
            time.sleep(2 ** attempt)

    # 3. Fallback: yahooquery
    try:
        from yahooquery import Ticker as YQTicker
        ticker_obj = YQTicker(ticker, session=session)
        df = ticker_obj.history(period=period)

        if not df.empty and 'close' in df.columns:
            df = df.reset_index()
            df = df.rename(columns={
                'date': 'Date', 'close': 'Close', 'open': 'Open',
                'high': 'High', 'low': 'Low', 'volume': 'Volume'
            })
            df.set_index('Date', inplace=True)
            df.to_sql(cache_key, conn, if_exists='replace')

            try:
                summary = ticker_obj.summary_detail
                if ticker in summary and summary[ticker].get('currency'):
                    currency = str(summary[ticker]['currency']).strip().upper()
            except Exception:
                pass
            if not currency:
                currency = currency_from_chart_api(ticker, session)
            if currency:
                pd.DataFrame([{"currency": currency}]).to_sql(f"{cache_key}_meta", conn, if_exists='replace')
            conn.close()
            return df, currency
    except Exception as e:
        pass

    conn.close()
    return pd.DataFrame(), None

def validate_ticker_exists(ticker: str, period: str = "1y") -> tuple[pd.DataFrame, str | None]:
    """Fetch data and raise 404 if ticker not found. Returns (dataframe, currency_code)."""
    hist, currency = fetch_or_cache_data(ticker, period)
    if hist.empty:
        # We raise a generic Exception here because the FastAPI HTTPException
        # is better handled in the route layer.
        raise ValueError(f"Ticker '{ticker}' not found or no data available for period '{period}'")
    return hist, currency
