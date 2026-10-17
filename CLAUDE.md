# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

### Backend Development
- Run API: `cd backend && uvicorn main:app --reload`
- Install dependencies: `pip install -r backend/requirements.txt`

### Frontend Development
- Run Dashboard: `streamlit run frontend/dashboard.py`

### Infrastructure
- Build & Start all services: `docker compose up -d --build`
- Stop services: `docker compose down`

## Architecture Overview

The project is structured as a decoupled monorepo splitting the API (Backend) from the UI (Frontend).

### Backend (`/backend`)
- **Framework**: FastAPI.
- **Engine**: `engine.py` contains the core quantitative logic for SMA and RSI strategies.
- **Services**: `api/services/market_data.py` handles data acquisition with a multi-stage fallback (yfinance $\rightarrow$ yahooquery $\rightarrow$ cache).
- **Persistence**: SQLite is used via `api/db/database.py` to cache historical price data and currency metadata to minimize API rate limits.
- **Flow**: `main.py` (Routes) $\rightarrow$ `market_data.py` (Data) $\rightarrow$ `engine.py` (Logic) $\rightarrow$ `main.py` (Response).

### Frontend (`/frontend`)
- **Framework**: Streamlit.
- **Communication**: Consumes the Backend API via HTTP requests.
- **Visualization**: Plotly for interactive stock charts and performance metrics.

### Deployment
- **API**: Deployed on Render.
- **Dashboard**: Deployed on AWS EC2 via Docker and Nginx reverse proxy.

## AI Agent Development Framework

When tasked with building or extending AI Agents, follow this strict spec-driven workflow:

### 1. Research & Analysis
- **Reference Patterns**: Study RAG, Self-RAG, and LangGraph patterns. Focus on state management, conditional edges, and tool-calling (`bind_tools`).
- **Tool Inventory**: Inventory all existing functions in `backend/` that can be converted into tools. Map agent goals to existing tool contracts.
- **Integration Points**: Identify where the agent fits into the existing FastAPI/Streamlit flow.

### 2. Spec-Driven Design (Mandatory)
Before writing implementation code, propose a specification in `.claude/specs/`:
- **Requirements**: Problem statement, user stories, and explicit success criteria.
- **Design**: LangGraph node/edge definitions, state schema, and tool-routing logic.
- **Human-in-the-Loop**: Explicitly define where `interrupt` or approval is required for consequential actions.
- **Task List**: Break implementation into small, independently verifiable steps.

### 3. Implementation Rules
- **State Management**: Use typed Pydantic schemas for LangGraph state.
- **Tooling**: Keep tool execution logic separate from reasoning logic.
- **Error Handling**: Implement bounded retries and clear failure paths for LLM tool-calls.
- **Incremental Build**: Implement one task from the spec at a time, verifying each with tests before proceeding.
- **Approval Gate**: Wait for user approval of the spec before modifying application code.
