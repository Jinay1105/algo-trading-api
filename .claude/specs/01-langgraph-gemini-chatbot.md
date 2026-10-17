# Spec: LangGraph Gemini Chatbot

## Overview
The goal is to implement an AI-powered chatbot that serves as an intelligent interface for the Algorithmic Trading Backtesting Engine. Instead of manually interacting with API endpoints or the Streamlit dashboard, users can converse with the chatbot to run backtests, analyze stock performance, and get strategy recommendations.

The chatbot will be built using **LangGraph** for stateful orchestration and **Google Gemini** models for reasoning. It will act as a "Quant Assistant" that can translate natural language requests (e.g., "How would a 10/50 SMA strategy perform on Apple over the last year?") into specific tool calls to the existing backend engine.

## Requirements
- **Functional**:
    - Understand natural language requests for stock backtesting.
    - Dynamically call backtesting functions (SMA, RSI, Composite) based on user input.
    - Retrieve and present performance metrics (Win Rate, Sharpe Ratio, etc.) in a conversational format.
    - Maintain conversation state to allow follow-up questions (e.g., "Now try it with a 20/100 SMA").
    - Handle invalid tickers or parameter combinations gracefully.
- **Non-Functional**:
    - Low latency responses.
    - Modular tool design to allow easy addition of new strategies.
    - Secure handling of API keys for Gemini.

## Technical Design
- **Logic Flow**:
    - **Input Node**: Receives user query $\rightarrow$ Gemini LLM decides if a tool call is needed.
    - **Tool Node**: Executes the corresponding backend logic (via the FastAPI routes or direct engine calls).
    - **Synthesis Node**: Gemini takes the tool output and formats it into a user-friendly response.
    - **Edge Logic**: Conditional routing between reasoning and tool execution.
- **Data Model**:
    - **LangGraph State**: A Pydantic schema containing `messages` (history), `current_ticker`, `current_strategy`, and `last_results`.
- **API Changes**:
    - New `/chat` endpoint in `main.py` to interface the frontend with the LangGraph agent.
- **Engine Changes**:
    - No changes to core calculation logic, but wrapping existing functions in LangChain/LangGraph tools.

## Implementation Plan
1. **Environment Setup**: Install `langgraph`, `langchain-google-genai`, and configure Gemini API keys.
2. **Tool Definition**: Create a `tools.py` file that wraps `apply_sma_crossover`, `apply_rsi_strategy`, and `apply_composite_strategy` as LangChain tools.
3. **State Schema**: Define the `AgentState` using Pydantic.
4. **Graph Construction**:
    - Define the `call_model` node.
    - Define the `execute_tools` node.
    - Set up conditional edges for tool routing.
5. **API Integration**: Add a FastAPI endpoint to `main.py` that invokes the graph.
6. **Frontend Integration**: (Optional/Future) Add a chat interface to `dashboard.py`.
7. **Testing**: Verify end-to-end flow from natural language $\rightarrow$ backtest $\rightarrow$ response.

## Definition of Done
- [ ] Chatbot correctly identifies the requested strategy and ticker from natural language.
- [ ] Chatbot successfully invokes backend backtesting logic and returns correct metrics.
- [ ] Chatbot maintains context across multiple turns of conversation.
- [ ] Invalid inputs are handled with helpful error messages instead of crashes.
- [ ] All implementation follows the project's architectural standards defined in `CLAUDE.md`.
