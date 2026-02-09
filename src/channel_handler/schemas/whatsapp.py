"""Pydantic models for WhatsApp Webhooks."""

from typing import Any

from pydantic import BaseModel, Field


class WhatsAppMessageText(BaseModel):
    """Represents the text content of a WhatsApp message."""

    body: str


class WhatsAppMessage(BaseModel):
    """Represents a single WhatsApp message."""

    from_: str = Field(..., alias="from")
    id: str
    timestamp: str
    text: WhatsAppMessageText | None = None
    type: str


class WhatsAppValue(BaseModel):
    """Represents the value field in a WhatsApp webhook change."""

    messaging_product: str
    metadata: dict[str, Any]
    contacts: list[dict[str, Any]] | None = None
    messages: list[WhatsAppMessage] | None = None


class WhatsAppChange(BaseModel):
    """Represents a change object in the WhatsApp webhook entry."""

    value: WhatsAppValue
    field: str


class WhatsAppEntry(BaseModel):
    """Represents an entry in the WhatsApp webhook payload."""

    id: str
    changes: list[WhatsAppChange]


class WhatsAppWebhook(BaseModel):
    """Represents the top-level WhatsApp webhook payload."""

    object: str
    entry: list[WhatsAppEntry]
