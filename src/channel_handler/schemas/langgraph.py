"""Pydantic models for LangGraph interaction."""

from typing import Any

from pydantic import BaseModel


class LangGraphMessage(BaseModel):
    """Represents a message in the LangGraph payload."""

    role: str
    content: str
    additional_kwargs: dict[str, Any] | None = None


class LangGraphInput(BaseModel):
    """Represents the input structure for LangGraph."""

    messages: list[LangGraphMessage]


class LangGraphConfigurable(BaseModel):
    """Represents the configurable options for LangGraph."""

    thread_id: str


class LangGraphConfig(BaseModel):
    """Represents the configuration for LangGraph."""

    configurable: LangGraphConfigurable


class LangGraphPayload(BaseModel):
    """Represents the complete payload sent to LangGraph."""

    input: LangGraphInput
    config: LangGraphConfig
