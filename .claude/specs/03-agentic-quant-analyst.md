# Spec: Agentic Quant Analyst with Market Intelligence

## Overview
Transform the current chatbot from a simple parameter-orchestrator into a sophisticated **Agentic Quant Analyst**. This feature integrates multi-step reasoning (Plan-and-Execute) with real-time market intelligence (RAG) to provide high-confidence trading signals.

Instead of just running a backtest, the agent will now act as a researcher: it will fetch real-time news, analyze current sentiment, validate quantitative signals via backtesting, and synthesize a final investment thesis.

## Requirements
- **Functional**:
    - **Multi-Step Reasoning**: The agent must be able to plan a sequence of actions (e.g., "Search news" $\rightarrow$ "Run backtest" $\rightarrow$ "Analyze risk") before responding.
    - **Real-time Intelligence**: Integration with a web search tool to fetch current market sentiment and news.
    - **Quantitative Validation**: Ability to use existing backtesting tools to verify if a natural language signal is supported by historical data.
    - **Investment Thesis**: The final output must be a structured analysis (Sentiment + Quantitative Data + Conclusion) rather than just a bot response.
- **Non-Functional**:
    - **Latency**: Use async tool calls where possible to prevent the UI from freezing.
    - **Traceability**: The agent should explicitly state its reasoning steps (e.g., "Searching for news on AAPL...", "Running SMA backtest...").

## Technical Design
- **Logic Flow**:
    - **Orchestration**: Refactor `backend/chatbot/graph.py` from a simple loop to a **Plan-and-Execute** pattern.
    - **Nodes**:
        - `Planner`: Analyzes the prompt and creates a task list.
        - `Executor`: Calls tools based on the plan.
        - `Synthesizer`: Combines tool outputs into a final professional report.
    - **Tool Integration**:
        - Add a `web_search` tool using an API like Tavily or Brave Search.
        - Reuse `run_backtest` as a quantitative validation tool.
- **Data Model**:
    - No changes to SQLite required, but `AgentState` in `backend/chatbot/state.py` will be expanded to track the current plan and intermediate research findings.
- **API Changes**:
    - `/chat` endpoint remains the same, but the underlying LangGraph logic will be more complex.

## Implementation Plan
1. **Search Tool Integration**: Implement a `web_search` tool in `backend/chatbot/tools.py` and test it independently.
2. **LangGraph Refactor**:
    - Update `AgentState` to include `plan: List[str]` and `research_notes: List[str]`.
    - Implement the `Planner` node to generate a step-by-step research plan.
    - Implement the `Synthesizer` node to create the final investment thesis.
3. **Reasoning Loop**: Connect the nodes in `backend/chatbot/graph.py` to create the Plan $\rightarrow$ Execute $\rightarrow$ Synthesize loop.
4. **UI Enhancement**: Update `frontend/dashboard.py` to display the agent's "thinking process" (the steps it's currently executing).
5. **Verification**: Test with a complex query like "Should I buy TSLA based on current news and a 20/100 SMA strategy?".

## Definition of Done
- [ ] Agent can successfully perform a multi-step research process (Search $\rightarrow$ Backtest $\rightarrow$ Synthesis).
- [ ] Final response includes both qualitative (news) and quantitative (backtest) evidence.
- [ ] Agent explicitly shows its reasoning steps in the chat.
- [ ] The `web_search` tool returns relevant, current market data.
- [ ] The system handles cases where news is contradictory to quantitative signals.
