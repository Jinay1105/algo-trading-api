from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Annotated, Optional
from typing_extensions import Self
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from backend.engine import apply_sma_crossover, apply_rsi_strategy, apply_composite_strategy, calculate_metrics
from backend.api.services.market_data import (
    get_currency_symbol,
    validate_ticker_exists
)
from backend.chatbot.graph import app as chatbot_graph
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver

# Pydantic model for query/body validation
class TickerRequest(BaseModel):
    ticker: Annotated[str, Field(
        min_length=1,
        max_length=20,
        pattern=r'^[A-Z0-9\.\-]+$',
        description='Stock ticker symbol (e.g., GOOG, TSLA, RELIANCE.NS)',
        examples=['GOOG', 'TSLA', 'RELIANCE.NS']
    )]
    fast: Optional[Annotated[int, Field(ge=1, le=500)]] = None
    slow: Optional[Annotated[int, Field(ge=1, le=1000)]] = None
    rsi: Optional[Annotated[int, Field(ge=1, le=500)]] = None
    period: Annotated[str, Field(pattern="^(1d|5d|1mo|3mo|6mo|1y|2y|5y|10y|ytd|max)$")] = "1y"

    @field_validator('ticker')
    @classmethod
    def validate_ticker_format(cls, v: str) -> str:
        v = v.strip().upper()
        if not v:
            raise ValueError('Ticker cannot be empty')
        if not all(c.isalnum() or c in '.-' for c in v):
            raise ValueError('Ticker can only contain letters, numbers, dots, and hyphens')
        return v

    @model_validator(mode='after')
    def validate_combination(self) -> Self:
        has_sma = self.fast is not None and self.slow is not None
        has_rsi = self.rsi is not None
        if not has_sma and not has_rsi:
            raise ValueError('Provide either (fast + slow) for SMA, rsi for RSI, or all three for Composite')
        if has_sma and self.fast >= self.slow:
            raise ValueError('Fast SMA must be less than Slow SMA')
        return self

app = FastAPI(title="Algo Trading Backtest API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

memory = MemorySaver()
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
    config = {"configurable": {"thread_id": request.session_id}}
    try:
        final_state = chatbot_graph.invoke(
            {"messages": [HumanMessage(content=request.message)]},
            config=config
        )
        last_message = final_state["messages"][-1]
        content = last_message.content
        if isinstance(content, list):
            text_parts = [block["text"] for block in content if isinstance(block, dict) and "text" in block]
            response_text = " ".join(text_parts)
        else:
            response_text = str(content)

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
    return {"detail": "Hello, Welcome to Algo Backtesting Engine"}

@app.get("/health")
def health():
    return {"status": "healthy", "service": "api"}

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

@app.post("/backtest")
def run_backtest(request: TickerRequest):
    ticker = request.ticker
    hist, currency = validate_ticker_exists(ticker, request.period)
    has_sma = request.fast is not None and request.slow is not None
    has_sma_rsi = has_sma and request.rsi is not None
    has_rsi = request.rsi is not None

    if has_sma_rsi:
        results = apply_composite_strategy(hist, request.fast, request.slow, request.rsi)
        strategy_name = f"Composite SMA+RSI ({request.fast}/{request.slow}/{request.rsi})"
        chart_fields = ['Date_Str', 'Close', 'Fast_SMA', 'Slow_SMA', 'RSI']
    elif has_sma:
        results = apply_sma_crossover(hist, request.fast, request.slow)
        strategy_name = f"SMA Crossover ({request.fast}/{request.slow})"
        chart_fields = ['Date_Str', 'Close', 'Fast_SMA', 'Slow_SMA']
    else:
        results = apply_rsi_strategy(hist, request.rsi)
        strategy_name = f"RSI Mean Reversion ({request.rsi})"
        chart_fields = ['Date_Str', 'Close', 'RSI']

    metrics = calculate_metrics(results)
    chart_df = results.copy()
    chart_df['Date_Str'] = chart_df.index.astype(str)
    chart_data = chart_df[chart_fields].to_dict(orient="list")

    return {
        "ticker": ticker,
        "currency": currency,
        "currency_symbol": get_currency_symbol(currency),
        "strategy": strategy_name,
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
