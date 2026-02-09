"""Tests for the channel_handler.main module."""

import os
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

# Set environment variables BEFORE importing app
os.environ["VERIFY_TOKEN"] = "test_token"
if "LANGGRAPH_URL" not in os.environ:
    os.environ["LANGGRAPH_URL"] = "http://mock-langgraph.url"
if "LANGGRAPH_API_KEY" not in os.environ:
    os.environ["LANGGRAPH_API_KEY"] = "test_api_key"

from channel_handler.main import app, forward_to_langgraph

client = TestClient(app)

# --- Webhook Tests ---


def test_verify_webhook() -> None:
    """Test verification with correct token."""
    response = client.get(
        "/",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "test_token",
            "hub.challenge": "12345",
        },
    )
    assert response.status_code == 200
    assert response.text == "12345"


def test_verify_webhook_invalid_token() -> None:
    """Test verification with incorrect token."""
    response = client.get(
        "/",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong_token",
            "hub.challenge": "12345",
        },
    )
    assert response.status_code == 403


@patch("httpx.AsyncClient.post", new_callable=AsyncMock)
def test_webhook_message_processing(mock_post: AsyncMock) -> None:
    """Test processing of a webhook message."""
    # Mock successful response from LangGraph
    mock_post.return_value = httpx.Response(200, json={"status": "success"})

    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "12345",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "1234567890",
                                "phone_number_id": "9876543210",
                            },
                            "contacts": [
                                {"profile": {"name": "Test User"}, "wa_id": "16315551234"}
                            ],
                            "messages": [
                                {
                                    "from": "16315551234",
                                    "id": "wamid.HBgLM...",
                                    "timestamp": "1679999999",
                                    "text": {"body": "Hello World"},
                                    "type": "text",
                                }
                            ],
                        },
                        "field": "messages",
                    }
                ],
            }
        ],
    }

    response = client.post("/", json=payload)
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_webhook_invalid_payload() -> None:
    """Test processing of an invalid webhook payload."""
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "12345",
                # Missing 'changes' field
            }
        ],
    }

    response = client.post("/", json=payload)
    # Pydantic validation checks happen before the handler body is executed
    # Invalid payload should result in 422 Unprocessable Entity
    assert response.status_code == 422


# --- Forward to LangGraph Tests ---


@pytest.mark.asyncio
async def test_forward_to_langgraph() -> None:
    """Test that forward_to_langgraph sends the correct payload."""
    # Mock environment variables to ensure URL is set
    with (
        patch.dict(os.environ, {"LANGGRAPH_URL": "http://mock-url", "LANGGRAPH_API_KEY": "secret"}),
        # Mock httpx.AsyncClient
        patch("httpx.AsyncClient") as mock_client,
    ):
        mock_post = AsyncMock()
        mock_post.return_value.json.return_value = {"run_id": "123", "status": "success"}
        mock_post.return_value.raise_for_status = lambda: None
        mock_post.return_value.status_code = 200

        # Setup the context manager mock correctly
        mock_instance = AsyncMock()
        mock_instance.post = mock_post
        mock_client.return_value.__aenter__.return_value = mock_instance
        mock_client.return_value.post = mock_post

        await forward_to_langgraph("Hello World", "user123")

        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args

        # Verify URL
        assert "/runs" in args[0]

        # Verify headers - Authorization is handled by Client init, not per request
        # assert kwargs["headers"]["Authorization"] == "Bearer secret"

        # Verify payload
        if "json" in kwargs:
            payload = kwargs["json"]
        elif "content" in kwargs:
            import json

            payload = json.loads(kwargs["content"])
        else:
            pytest.fail(f"No json or content in kwargs: {kwargs.keys()}")
        assert payload["assistant_id"] == "agent"
        assert payload["input"]["messages"][0]["content"] == "Hello World"
        assert payload["input"]["messages"][0]["role"] == "user"
        assert payload["config"]["configurable"]["thread_id"] == "user123"
