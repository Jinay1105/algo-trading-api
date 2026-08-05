import pandas as pd
import numpy as np

def calculate_metrics(df: pd.DataFrame) -> dict:
    strategy_returns = df['Strategy_Return'].dropna()
    market_returns = df['Market_Return'].dropna()
    
    total_trades = int((df['Signal'].diff() != 0).sum() / 2)
    if total_trades == 0:
        total_trades = int((df['Signal'] == 1).sum() > 0)
    
    winning_trades = 0
    losing_trades = 0
    trade_returns = []
    
    in_position = False
    entry_price = 0
    for i in range(len(df)):
        if not in_position and df['Signal'].iloc[i] == 1:
            in_position = True
            entry_price = df['Close'].iloc[i]
        elif in_position and df['Signal'].iloc[i] == 0:
            in_position = False
            exit_price = df['Close'].iloc[i]
            ret = (exit_price - entry_price) / entry_price
            trade_returns.append(ret)
            if ret > 0:
                winning_trades += 1
            else:
                losing_trades += 1
    
    if in_position:
        exit_price = df['Close'].iloc[-1]
        ret = (exit_price - entry_price) / entry_price
        trade_returns.append(ret)
        if ret > 0:
            winning_trades += 1
        else:
            losing_trades += 1
    
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    
    cum_strat = (1 + strategy_returns).cumprod()
    running_max = cum_strat.expanding().max()
    drawdown = (cum_strat - running_max) / running_max
    max_drawdown = abs(drawdown.min()) * 100
    
    sharpe = 0
    if len(strategy_returns) > 1 and strategy_returns.std() > 0:
        sharpe = (strategy_returns.mean() / strategy_returns.std()) * np.sqrt(252)
    
    return {
        "total_trades": total_trades,
        "winning_trades": winning_trades,
        "losing_trades": losing_trades,
        "win_rate_percent": round(win_rate, 2),
        "max_drawdown_percent": round(max_drawdown, 2),
        "sharpe_ratio": round(sharpe, 2),
        "avg_trade_return_percent": round(np.mean(trade_returns) * 100, 2) if trade_returns else 0
    }

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