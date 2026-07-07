import pandas as pd
import numpy as np

def apply_sma_crossover(df: pd.DataFrame, fast: int = 10, slow: int = 50):
    df = df.copy()
    df['Fast_SMA'] = df['Close'].rolling(window=fast).mean()
    df['Slow_SMA'] = df['Close'].rolling(window=slow).mean()
    
    df['Signal'] = 0 
    df.loc[df['Fast_SMA'] > df['Slow_SMA'], 'Signal'] = 1 
    
    df['Market_Return'] = df['Close'].pct_change()
    df['Strategy_Return'] = df['Signal'].shift(1) * df['Market_Return']
    
    df = df.dropna().copy()
    df['Cumulative_Market'] = (1 + df['Market_Return']).cumprod()
    df['Cumulative_Strategy'] = (1 + df['Strategy_Return']).cumprod()
    return df

def apply_rsi_strategy(df: pd.DataFrame, period: int = 14):
    df = df.copy()
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    df['Signal'] = 0 
    df.loc[df['RSI'] < 30, 'Signal'] = 1 
    df['Signal'] = df['Signal'].replace(0, pd.NA).ffill().fillna(0)
    df.loc[df['RSI'] > 70, 'Signal'] = 0 
    
    df['Market_Return'] = df['Close'].pct_change()
    df['Strategy_Return'] = df['Signal'].shift(1) * df['Market_Return']
    
    df = df.dropna().copy()
    df['Cumulative_Market'] = (1 + df['Market_Return']).cumprod()
    df['Cumulative_Strategy'] = (1 + df['Strategy_Return']).cumprod()
    return df

def apply_composite_strategy(df: pd.DataFrame, fast: int = 10, slow: int = 50, rsi_period: int = 14):
    """
    The Hedge Fund Strategy: 
    Only buys when the trend is UP (Fast > Slow) AND the stock dips (RSI < 40).
    Sells immediately if the trend breaks OR the stock gets overbought (RSI > 70).
    """
    df = df.copy()
    
    # Calculate SMA
    df['Fast_SMA'] = df['Close'].rolling(window=fast).mean()
    df['Slow_SMA'] = df['Close'].rolling(window=slow).mean()
    
    # Calculate RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # The Composite Vectorized Logic
    df['Signal'] = 0
    # Buy condition: Uptrend + Dip
    df.loc[(df['Fast_SMA'] > df['Slow_SMA']) & (df['RSI'] < 40), 'Signal'] = 1
    
    # Hold the position
    df['Signal'] = df['Signal'].replace(0, pd.NA).ffill().fillna(0)
    
    # Sell condition: Downtrend + Overbought
    df.loc[(df['Fast_SMA'] < df['Slow_SMA']) | (df['RSI'] > 70), 'Signal'] = 0
    
    df['Market_Return'] = df['Close'].pct_change()
    df['Strategy_Return'] = df['Signal'].shift(1) * df['Market_Return']
    
    df = df.dropna().copy()
    df['Cumulative_Market'] = (1 + df['Market_Return']).cumprod()
    df['Cumulative_Strategy'] = (1 + df['Strategy_Return']).cumprod()
    return df