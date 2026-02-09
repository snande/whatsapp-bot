"""Tests for the simple graph."""

from langchain_core.messages import HumanMessage

from intelligence.graphs.simple_graph import graph


def test_echo_graph() -> None:
    """Test the echo graph with a simple message."""
    initial_state = {"messages": [HumanMessage(content="Hello")]}
    result = graph.invoke(initial_state)  # type: ignore[arg-type]
    assert len(result["messages"]) == 2
    assert result["messages"][1].content == "Echo: Hello"
