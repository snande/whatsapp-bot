"""Simple echo graph implementation."""

from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, MessagesState, StateGraph


def echo_node(state: MessagesState) -> dict[str, list[HumanMessage]]:
    """Echoes the last message."""
    last_message = state["messages"][-1]
    # Simple echo logic
    return {"messages": [HumanMessage(content=f"Echo: {last_message.content}")]}


builder = StateGraph(MessagesState)
builder.add_node("echo", echo_node)
builder.add_edge(START, "echo")
builder.add_edge("echo", END)

graph = builder.compile()
