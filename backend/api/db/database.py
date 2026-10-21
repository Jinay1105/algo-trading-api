import sqlite3
import pandas as pd
from backend.api.config import DB_NAME

def get_db_connection():
    """Returns a connection to the SQLite database."""
    return sqlite3.connect(DB_NAME)

def save_to_cache(table_name: str, df: pd.DataFrame):
    """Saves a dataframe to the SQLite cache."""
    with get_db_connection() as conn:
        df.to_sql(table_name, conn, if_exists='replace')

def save_meta_to_cache(table_name: str, currency: str):
    """Saves currency metadata to the SQLite cache."""
    with get_db_connection() as conn:
        pd.DataFrame([{"currency": currency}]).to_sql(f"{table_name}_meta", conn, if_exists='replace')

def load_from_cache(table_name: str):
    """Loads data from the SQLite cache. Returns None if not found."""
    try:
        with get_db_connection() as conn:
            df = pd.read_sql(f"SELECT * FROM {table_name}", conn, parse_dates=['Date'])
            df.set_index('Date', inplace=True)
            return df
    except Exception:
        return None

def load_meta_from_cache(table_name: str):
    """Loads currency metadata from the SQLite cache."""
    try:
        with get_db_connection() as conn:
            meta_df = pd.read_sql(f"SELECT currency FROM {table_name}_meta", conn)
            if not meta_df.empty:
                return meta_df['currency'].iloc[0]
    except Exception:
        pass
    return None
