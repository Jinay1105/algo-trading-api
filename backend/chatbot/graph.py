from typing import Literal
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from backend.chatbot.state import AgentState
from backend.chatbot.tools import run_backtest
from langchain_core.messages import HumanMessage, AIMessage

# Load Gemini Model
model = ChatGoogleGenerativeAI(model="gemini-3.5-flash")
tools = [run_backtest]
model_with_tools = model.bind_tools(tools)

# Simple tool-calling agent logic (Return to original loop)
def call_model(state: AgentState):
    """Decides whether to call a tool or respond to the user."""
    messages = state.messages
    response = model_with_tools.invoke(messages)
    return {"messages": [response]}

def route_tools(state: AgentState) -> Literal["tools", "__end__"]:
    """Routes to the tool node if tool calls are present."""
    last_message = state.messages[-1]
    if last_message.tool_calls:
        return "tools"
    return "__end__"

# Construct Graph
workflow = StateGraph(AgentState)

workflow.add_node("agent", call_model)
workflow.add_node("tools", ToolNode(tools))

workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", route_tools)
workflow.add_edge("tools", "agent")

# Compile Graph with Memory
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)
