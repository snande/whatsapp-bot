"""Simple echo graph implementation."""

from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, MessagesState, StateGraph


def echo_node(state: MessagesState) -> dict[str, list[HumanMessage]]:
    """Echoes the last message.

    Args:
        state: The current state of the conversation.

    Returns:
        A dictionary containing the echoed message.
    """
    last_message = state["messages"][-1]
    # Create a new HumanMessage with "Echo: " prefix as the response
    return {"messages": [HumanMessage(content=f"Echo: {last_message.content}")]}


builder = StateGraph(MessagesState)
builder.add_node("echo", echo_node)
builder.add_edge(START, "echo")
builder.add_edge("echo", END)

graph = builder.compile()
