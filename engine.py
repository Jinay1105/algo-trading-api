import pandas as pd
import numpy as np

def apply_sma_crossover(df: pd.DataFrame, fast_period: int = 10, slow_period: int = 50):
    """
    Applies a Simple Moving Average (SMA) crossover strategy.
    Returns the dataframe with signals and calculated strategy returns.
    """
    # 1. Calculate the Moving Averages
    df['SMA_Fast'] = df['Close'].rolling(window=fast_period).mean()
    df['SMA_Slow'] = df['Close'].rolling(window=slow_period).mean()

    # 2. Generate the Signal (1 = Buy/Hold, 0 = Sell/Flat)
    # If the fast average is above the slow average, we want to be in the market.
    df['Signal'] = np.where(df['SMA_Fast'] > df['SMA_Slow'], 1, 0)
    
    # 3. Calculate Daily Market Returns
    df['Market_Return'] = df['Close'].pct_change()
    
    # 4. Calculate Strategy Returns (CRITICAL STEP)
    # We use .shift(1) because we can only trade TODAY based on YESTERDAY'S closing signal.
    # If you don't shift, you are using future data to trade, which is "look-ahead bias".
    df['Strategy_Return'] = df['Signal'].shift(1) * df['Market_Return']
    
    # 5. Clean up missing data caused by the rolling windows
    df = df.dropna().copy()
    
    # 6. Calculate cumulative returns to see how much money we made
    df['Cumulative_Market'] = (1 + df['Market_Return']).cumprod()
    df['Cumulative_Strategy'] = (1 + df['Strategy_Return']).cumprod()
    
    return df