from langchain_core.tools import tool
from services.market_data import validate_ticker_exists
from engine import apply_sma_crossover, apply_rsi_strategy, apply_composite_strategy, calculate_metrics
import pandas as pd

@tool
def run_backtest(
    ticker: str,
    strategy: str,
    fast: int = 10,
    slow: int = 50,
    rsi: int = 14,
    period: str = "1y"
) -> str:
    """
    Run a backtest for a given stock ticker and strategy.

    Args:
        ticker: The stock ticker symbol (e.g., 'AAPL', 'TSLA').
        strategy: The strategy to use. Must be one of 'SMA', 'RSI', or 'Composite'.
        fast: Fast SMA window (used for SMA and Composite).
        slow: Slow SMA window (used for SMA and Composite).
        rsi: RSI window (used for RSI and Composite).
        period: Data period (e.g., '1y', '5y', 'max').
    """
    ticker = ticker.strip().upper()
    try:
        # 1. Validate ticker and get data
        hist, currency = validate_ticker_exists(ticker, period)

        # 2. Validate SMA parameters: Fast must be less than Slow
        strategy_upper = strategy.upper()
        if strategy_upper in ["SMA", "COMPOSITE"]:
            if fast >= slow:
                return f"Error: Fast SMA ({fast}) must be smaller than Slow SMA ({slow}). Please correct the parameters and try again."

        # 3. Execute strategy
        if strategy_upper == "SMA":
            results = apply_sma_crossover(hist, fast, slow)
        elif strategy_upper == "RSI":
            results = apply_rsi_strategy(hist, rsi)
        elif strategy_upper == "COMPOSITE":
            results = apply_composite_strategy(hist, fast, slow, rsi)
        else:
            return f"Error: Invalid strategy '{strategy}'. Choose SMA, RSI, or Composite."

        # 4. Calculate metrics
        metrics = calculate_metrics(results)

        # 5. Format result for LLM
        result_str = (
            f"Backtest results for {ticker} using {strategy} strategy:\n"
            f"Currency: {currency}\n"
            f"Market Return: {round((results['Cumulative_Market'].iloc[-1] - 1) * 100, 2)}%\n"
            f"Strategy Return: {round((results['Cumulative_Strategy'].iloc[-1] - 1) * 100, 2)}%\n"
            f"Total Trades: {metrics['total_trades']}\n"
            f"Win Rate: {metrics['win_rate_percent']}%\n"
            f"Max Drawdown: {metrics['max_drawdown_percent']}%\n"
            f"Sharpe Ratio: {metrics['sharpe_ratio']}\n"
            f"Avg Trade Return: {metrics['avg_trade_return_percent']}%"
        )
        return result_str

    except ValueError as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"
