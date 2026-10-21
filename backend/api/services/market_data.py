import pandas as pd
import requests
import yfinance as yf
from backend.api.config import YAHOO_CHART_URL, CURRENCY_SYMBOLS
from backend.api.db.database import load_from_cache, load_meta_from_cache, save_to_cache, save_meta_to_cache

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

def fetch_or_cache_data(ticker: str, period: str = "1y") -> tuple:
    """Fetch data from cache or yfinance/yahooquery with retries and fallback. Returns (dataframe, currency_code)."""
    from api.config import VALID_PERIODS
    if period not in VALID_PERIODS:
        period = "1y"

    table_name = ticker.replace(".", "_")
    cache_key = f"{table_name}_{period}"

    # 1. Try cache FIRST
    df = load_from_cache(cache_key)
    if df is not None:
        print(f"Loaded {ticker} from Database Cache (period={period})!")
        currency = load_meta_from_cache(cache_key)
        if not currency:
            currency = fetch_ticker_currency(ticker)
            if currency:
                save_meta_to_cache(cache_key, currency)
        return df, currency

    # 2. Try yfinance with retries
    import time
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

    currency = None
    for attempt in range(3):
        try:
            print(f"Fetching {ticker} via yfinance (attempt {attempt+1})...")
            stock = yf.Ticker(ticker, session=session)
            df = stock.history(period=period)
            if not df.empty:
                currency = (currency_from_history_meta(stock)
                            or currency_from_chart_api(ticker, session)
                            or currency_from_info(stock))

                save_to_cache(cache_key, df)
                if currency:
                    save_meta_to_cache(cache_key, currency)
                print(f"yfinance success: {len(df)} rows for {ticker}, currency={currency}")
                return df, currency
            else:
                print(f"yfinance returned empty (attempt {attempt+1})")
        except Exception as e:
            print(f"yfinance error: {e} (attempt {attempt+1})")

        if attempt < 2:
            time.sleep(2 ** attempt)

    # 3. Fallback: yahooquery
    try:
        print(f"Trying yahooquery for {ticker}...")
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
            save_to_cache(cache_key, df)

            try:
                summary = ticker_obj.summary_detail
                if ticker in summary and summary[ticker].get('currency'):
                    currency = str(summary[ticker]['currency']).strip().upper()
            except Exception:
                pass
            if not currency:
                currency = currency_from_chart_api(ticker, session)
            if currency:
                save_meta_to_cache(cache_key, currency)
            print(f"yahooquery success: {len(df)} rows for {ticker}, currency={currency}")
            return df, currency
    except Exception as e:
        print(f"yahooquery failed: {e}")

    return pd.DataFrame(), None
