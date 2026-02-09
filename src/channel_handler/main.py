"""Main entry point for the WhatsApp Bot."""

import logging
import os

import httpx
import uvicorn
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request

from channel_handler.schemas.langgraph import (
    LangGraphConfig,
    LangGraphConfigurable,
    LangGraphInput,
    LangGraphMessage,
    LangGraphPayload,
)
from channel_handler.schemas.whatsapp import WhatsAppWebhook

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI()

# Load environment variables
load_dotenv()

# Set port and verify_token
port = int(os.environ.get("PORT", 3000))
verify_token = os.environ.get("VERIFY_TOKEN")
langgraph_url = os.environ.get("LANGGRAPH_URL")
langgraph_api_key = os.environ.get("LANGGRAPH_API_KEY")


# --- Functions ---


async def forward_to_langgraph(message_body: str, sender_id: str) -> None:
    """Forwards the message to the LangGraph deployment.

    Args:
        message_body: The content of the message.
        sender_id: The ID of the sender (phone number).

    Returns:
        None
    """
    if not langgraph_url:
        logger.error("LANGGRAPH_URL is not set. Cannot forward message.")
        return

    headers = {
        "Content-Type": "application/json",
    }
    if langgraph_api_key:
        headers["Authorization"] = f"Bearer {langgraph_api_key}"

    # Construct the payload for LangGraph using Pydantic models
    payload_model = LangGraphPayload(
        input=LangGraphInput(
            messages=[
                LangGraphMessage(
                    role="user",
                    content=message_body,
                    additional_kwargs={"sender_id": sender_id},
                )
            ]
        ),
        config=LangGraphConfig(configurable=LangGraphConfigurable(thread_id=sender_id)),
    )
    payload = payload_model.model_dump()

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(langgraph_url, json=payload, headers=headers)
            response.raise_for_status()
            logger.info(f"LangGraph response: {response.json()}")
    except httpx.HTTPStatusError as e:
        logger.error(
            f"LangGraph request failed with status {e.response.status_code}: {e.response.text}"
        )
    except Exception:
        logger.exception("Error forwarding to LangGraph")


@app.get("/")
async def verify_webhook(request: Request) -> int:
    """Verify the webhook with WhatsApp.

    Args:
        request: The incoming request object.

    Returns:
        The challenge string cast to an integer, if verification is successful.

    Raises:
        HTTPException: If verification fails or challenge is missing.
    """
    mode = request.query_params.get("hub.mode")
    challenge = request.query_params.get("hub.challenge")
    token = request.query_params.get("hub.verify_token")

    if mode == "subscribe" and token == verify_token:
        if not challenge:
            raise HTTPException(status_code=400, detail="Missing challenge")
        logger.info("Webhook verified successfully")
        return int(challenge)
    else:
        raise HTTPException(status_code=403, detail="Forbidden")


@app.post("/")
async def receive_webhook(
    body: WhatsAppWebhook, background_tasks: BackgroundTasks
) -> dict[str, str]:
    """Receive and process webhook messages.

    Args:
        body: The parsed WhatsApp webhook payload.
        background_tasks: FastAPI background tasks handler.

    Returns:
        A status dictionary.
    """
    try:
        # Check if this is a message from WhatsApp
        if body.object == "whatsapp_business_account":
            for entry in body.entry:
                for change in entry.changes:
                    value = change.value
                    if value.messages:
                        for message in value.messages:
                            if message.type == "text" and message.text:
                                message_body = message.text.body
                                sender_id = message.from_
                                logger.info(f"Received message from {sender_id}: {message_body}")

                                # Forward to LangGraph in background to respond quickly to WhatsApp
                                background_tasks.add_task(
                                    forward_to_langgraph, message_body, sender_id
                                )

        return {"status": "ok"}
    except Exception:
        logger.exception("Error processing webhook")
        # Return 200 anyway to prevent WhatsApp from retrying indefinitely on bad logic
        return {"status": "error", "message": "Internal Server Error"}


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Check the health of the application.

    Returns:
        A status dictionary.
    """
    return {"status": "ok"}


if __name__ == "__main__":
    logger.info(f"Listening on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
