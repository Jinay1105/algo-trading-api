from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

from backend.chatbot.graph import app as chatbot_graph
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from services.market_data import (
    fetch_or_cache_data,
    validate_ticker_exists,
    get_currency_symbol,
    VALID_PERIODS
)
from engine import apply_sma_crossover, apply_rsi_strategy, apply_composite_strategy, calculate_metrics
import pandas as pd
import os
import time
import requests
import sqlite3

# Initialize FastAPI app
app = FastAPI(title="Algo Trading Backtest API")

# CORS middleware for cross-origin requests
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize memory for the chatbot
memory = MemorySaver()
# In newer langgraph versions, checkpointing is passed during compile()
# instead of using .with_checkpoint() on the compiled app.
# However, we can just import the compiled graph and use it.
# If the graph in graph.py is already compiled, we can't simply 'add' memory here.
# We will handle the memory integration inside graph.py instead.
chatbot_graph = chatbot_graph

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    response: str
    chart_data: Optional[dict] = None
    performance: Optional[dict] = None
    ticker: Optional[str] = None
    currency: Optional[str] = None
    currency_symbol: Optional[str] = None
    strategy: Optional[str] = None

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Chat endpoint for the Quant Assistant.
    """
    config = {"configurable": {"thread_id": request.session_id}}

    try:
        # Invoke the graph with the user message
        final_state = chatbot_graph.invoke(
            {"messages": [HumanMessage(content=request.message)]},
            config=config
        )

        # The last message in the state is the AI's final response
        last_message = final_state["messages"][-1]
        content = last_message.content

        # If content is a list of blocks (Gemini multimodal format), extract the text
        if isinstance(content, list):
            text_parts = [block["text"] for block in content if isinstance(block, dict) and "text" in block]
            response_text = " ".join(text_parts)
        else:
            response_text = str(content)

        # Extract performance and chart data from the state if available
        perf = final_state.get("performance")
        chart = final_state.get("chart_data")
        ticker = final_state.get("current_ticker")
        currency = final_state.get("currency")
        curr_sym = get_currency_symbol(currency)
        strat = final_state.get("current_strategy")

        return ChatResponse(
            response=response_text,
            chart_data=chart,
            performance=perf,
            ticker=ticker,
            currency=currency,
            currency_symbol=curr_sym,
            strategy=strat
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chatbot error: {str(e)}")

@app.get("/")
def landing():
    return {"detail": "Hello,Welcome to Algo Backtesting Engine"}

@app.get("/health")
def health():
    return {"status": "healthy", "service": "api"}

# --- Existing Backtest Endpoints (Refactored to use services.market_data) ---

@app.get("/backtest/sma/{ticker}")
def run_sma_backtest(ticker: str, fast: int = 10, slow: int = 50, period: str = "1y"):
    if fast >= slow:
        raise HTTPException(status_code=422, detail='Fast SMA must be less than Slow SMA')
    ticker = ticker.strip().upper()
    hist, currency = validate_ticker_exists(ticker, period)
    results = apply_sma_crossover(hist, fast, slow)
    metrics = calculate_metrics(results)
    chart_df = results.copy()
    chart_df['Date_Str'] = chart_df.index.astype(str)
    chart_data = chart_df[['Date_Str', 'Close', 'Fast_SMA', 'Slow_SMA']].to_dict(orient="list")
    return {
        "ticker": ticker,
        "currency": currency,
        "currency_symbol": get_currency_symbol(currency),
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
def run_rsi_backtest(ticker: str, rsi: int = 14, period: str = "1y"):
    ticker = ticker.strip().upper()
    hist, currency = validate_ticker_exists(ticker, period)
    results = apply_rsi_strategy(hist, rsi)
    metrics = calculate_metrics(results)
    chart_df = results.copy()
    chart_df['Date_Str'] = chart_df.index.astype(str)
    chart_data = chart_df[['Date_Str', 'Close', 'RSI']].to_dict(orient="list")
    return {
        "ticker": ticker,
        "currency": currency,
        "currency_symbol": get_currency_symbol(currency),
        "strategy": f"RSI Mean Reversion ({rsi})",
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
def run_composite_backtest(ticker: str, fast: int = 10, slow: int = 50, rsi: int = 14, period: str = "1y"):
    if fast >= slow:
        raise HTTPException(status_code=422, detail='Fast SMA must be less than Slow SMA')
    ticker = ticker.strip().upper()
    hist, currency = validate_ticker_exists(ticker, period)
    results = apply_composite_strategy(hist, fast, slow, rsi)
    metrics = calculate_metrics(results)
    chart_df = results.copy()
    chart_df['Date_Str'] = chart_df.index.astype(str)
    chart_data = chart_df[['Date_Str', 'Close', 'Fast_SMA', 'Slow_SMA', 'RSI']].to_dict(orient="list")
    return {
        "ticker": ticker,
        "currency": currency,
        "currency_symbol": get_currency_symbol(currency),
        "strategy": "Composite SMA+RSI",
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
