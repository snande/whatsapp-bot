"""Tests for the webhook module."""

import os
from unittest.mock import AsyncMock, patch

import httpx
from fastapi.testclient import TestClient

# Set environment variables BEFORE importing app
os.environ["VERIFY_TOKEN"] = "test_token"
if "LANGGRAPH_URL" not in os.environ:
    os.environ["LANGGRAPH_URL"] = "http://mock-langgraph.url"
if "LANGGRAPH_API_KEY" not in os.environ:
    os.environ["LANGGRAPH_API_KEY"] = "test_api_key"

from channel_handler.main import app

client = TestClient(app)


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

    # Verify LangGraph was called
    # Note: BackgroundTasks might not execute immediately in TestClient depending on async setup.
    # However, Starlette/FastAPI TestClient typically executes background tasks synchronously.
    # Let's verify mock_post calls.

    assert mock_post.called
    assert mock_post.call_count == 1

    args, kwargs = mock_post.call_args
    # Check URL
    assert args[0] == "http://mock-langgraph.url"

    # Check Payload
    sent_payload = kwargs["json"]
    assert sent_payload["input"]["messages"][0]["content"] == "Hello World"
    assert sent_payload["input"]["messages"][0]["additional_kwargs"]["sender_id"] == "16315551234"
    assert sent_payload["config"]["configurable"]["thread_id"] == "16315551234"

    # Check Headers
    assert kwargs["headers"]["Authorization"] == "Bearer test_api_key"


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


if __name__ == "__main__":
    # If run directly as a script
    try:
        test_verify_webhook()
        test_verify_webhook_invalid_token()
        print("Verification tests passed!")
        # test_webhook_message_processing needs mocking which is easier with pytest
    except Exception as e:
        print(f"Tests failed: {e}")
