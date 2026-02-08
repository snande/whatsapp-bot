"""Main entry point for the WhatsApp Bot."""

import logging
import os

import httpx
import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Set port and verify_token
port = int(os.environ.get("PORT", 3000))
verify_token = os.environ.get("VERIFY_TOKEN")
langgraph_url = os.environ.get("LANGGRAPH_URL")
langgraph_api_key = os.environ.get("LANGGRAPH_API_KEY")


async def forward_to_langgraph(message_body: str, sender_id: str) -> None:
    """Forwards the message to the LangGraph deployment."""
    if not langgraph_url:
        logger.error("LANGGRAPH_URL is not set. Cannot forward message.")
        return

    headers = {
        "Content-Type": "application/json",
    }
    if langgraph_api_key:
        headers["Authorization"] = f"Bearer {langgraph_api_key}"

    # Construct the payload for LangGraph
    # Assuming a standard graph that accepts "messages" or "input"
    payload = {
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": message_body,
                    "additional_kwargs": {"sender_id": sender_id},
                }
            ]
        },
        "config": {
            "configurable": {
                "thread_id": sender_id  # Use sender_id as thread_id for continuity
            }
        },
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(langgraph_url, json=payload, headers=headers)
            response.raise_for_status()
            logger.info(f"LangGraph response: {response.json()}")
    except httpx.HTTPStatusError as e:
        logger.error(
            f"LangGraph request failed with status {e.response.status_code}: {e.response.text}"
        )
    except Exception as e:
        logger.error(f"Error forwarding to LangGraph: {str(e)}")


# Route for GET requests (verification)
@app.get("/")
async def verify_webhook(request: Request) -> int:
    """Verify the webhook with WhatsApp."""
    mode = request.query_params.get("hub.mode")
    challenge = request.query_params.get("hub.challenge")
    token = request.query_params.get("hub.verify_token")

    if mode == "subscribe" and token == verify_token:
        if not challenge:
            raise HTTPException(status_code=400, detail="Missing challenge")
        print("WEBHOOK VERIFIED")
        return int(challenge)
    else:
        raise HTTPException(status_code=403, detail="Forbidden")


# Route for POST requests (receive webhook)
@app.post("/")
async def receive_webhook(request: Request, background_tasks: BackgroundTasks) -> dict[str, str]:
    """Receive and process webhook messages."""
    # timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        body = await request.json()

        # Log the full incoming payload for debugging
        # print(f"\n\nWebhook received {timestamp}\n")
        # print(json.dumps(body, indent=2))

        # Check if this is a message from WhatsApp
        if body.get("object") == "whatsapp_business_account":
            for entry in body.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    if "messages" in value:
                        for message in value["messages"]:
                            if message.get("type") == "text":
                                message_body = message["text"]["body"]
                                sender_id = message["from"]
                                logger.info(f"Received message from {sender_id}: {message_body}")

                                # Forward to LangGraph in background to respond quickly to WhatsApp
                                background_tasks.add_task(
                                    forward_to_langgraph, message_body, sender_id
                                )

        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        # Return 200 anyway to prevent WhatsApp from retrying indefinitely on bad logic
        return {"status": "error", "message": str(e)}


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Check the health of the application."""
    return {"status": "ok"}


# Start the server
if __name__ == "__main__":
    print(f"\nListening on port {port}\n")
    uvicorn.run(app, host="0.0.0.0", port=port)
