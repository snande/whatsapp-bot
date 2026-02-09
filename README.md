# WhatsApp Bot

A simple WhatsApp bot using FastAPI and ngrok for local development, integrated with LangGraph.

## Prerequisites

-   **Python 3.12+**: Ensure you have Python installed.
-   **Poetry**: Dependency management tool. Install via `pip install poetry`.
-   **Ngrok**: Tool to expose your local server to the internet. [Download and install ngrok](https://ngrok.com/download).
-   **WhatsApp Business API Account**: You need a Meta for Developers account and a WhatsApp app set up.

## Configuration

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/snande/whatsapp-bot.git
    cd whatsapp-bot
    ```

2.  **Install dependencies:**
    ```bash
    poetry install
    ```

3.  **Set up environment variables:**
    Copy the example environment file:
    ```bash
    cp .env.example .env
    ```
    Open `.env` and fill in the following values:
    -   `VERIFY_TOKEN`: A random string you verify in your WhatsApp App configuration.
    -   `LANGGRAPH_URL`: The URL of your deployed LangGraph graph (or local if running locally).
    -   `LANGGRAPH_API_KEY`: (Optional) If your graph is protected.

## Running the Application

### 1. Start the LangGraph Server (Optional - if running locally)

If you are developing the graph locally:

```bash
# Ensure you have the langgraph-cli installed or use python module
# For this project, we can use the langgraph cli if installed, or rely on deployed graphs.
# If you want to test the graph logic in isolation:
poetry run langgraph dev
```
*Note: The project is configured to use a deployed graph via `LANGGRAPH_URL`.*

### 2. Start the FastApi Webhook Handler

Run the main application server:

```bash
poetry run python src/channel_handler/main.py
```
Or using `uvicorn` with hot reload:
```bash
poetry run uvicorn channel_handler.main:app --reload
```
The server will start on `http://localhost:3000` (or the port defined in `PORT` env var).

### 3. Expose Local Server via Ngrok

In a new terminal window, start ngrok to expose port 3000:

```bash
ngrok http 3000
```
Copy the Forwarding URL (e.g., `https://<random-id>.ngrok-free.app`).

### 4. Configure WhatsApp Webhook

1.  Go to your app dashboard on [Meta for Developers](https://developers.facebook.com/).
2.  Navigate to **WhatsApp** > **Configuration**.
3.  Click **Edit** under **Webhook**.
4.  **Callback URL**: Paste your ngrok URL (e.g., `https://<random-id>.ngrok-free.app/`).
5.  **Verify Token**: Enter the `VERIFY_TOKEN` you set in your `.env` file.
6.  Click **Verify and Save**.
7.  Under **Webhook fields**, click **Manage** and subscribe to `messages`.



## Testing

Send a message to your WhatsApp test number. The bot should receive it and forward it to the LangGraph agent.

## Development

### Running Tests

To run the tests, use the following command:

```bash
poetry run pytest
```

### Code Style

This project follows Google-style docstrings and uses Pydantic for data validation.
