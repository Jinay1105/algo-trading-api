from typing import Annotated, List, Optional
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(BaseModel):
    # Standard LangGraph message history
    messages: Annotated[List[BaseMessage], add_messages] = Field(
        default_factory=list,
        description="The conversation history"
    )

    # Contextual state to avoid asking user for the same info repeatedly
    current_ticker: Optional[str] = Field(
        None,
        description="The stock ticker currently being analyzed"
    )
    current_strategy: Optional[str] = Field(
        None,
        description="The active strategy (SMA, RSI, or Composite)"
    )
    strategy_params: dict = Field(
        default_factory=dict,
        description="Parameters like fast, slow, rsi, and period"
    )
