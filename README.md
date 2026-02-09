# WhatsApp Bot

A simple WhatsApp bot using FastAPI and ngrok for local development, integrated with LangGraph.

## Setup

1.  **Install dependencies:**
    This project uses [Poetry](https://python-poetry.org/) for dependency management.
    ```bash
    poetry install
    ```

2.  **Run the server:**
    ```bash
    poetry run python src/channel_handler/main.py
    ```
    Or using uvicorn directly:
    ```bash
    poetry run uvicorn channel_handler.main:app --reload
    ```

3.  **Expose the server with ngrok:**
    ```bash
    ngrok http 3000
    ```

## Configuration

Set the following environment variables:

```bash
export VERIFY_TOKEN="your_token_here"
export LANGGRAPH_URL="your_langgraph_url_here"
export LANGGRAPH_API_KEY="your_langgraph_api_key_here" # Optional, if required
```

## Usage

-   **Webhook URL:** `http://<ngrok-url>/`
-   **Verify Token:** The value of `VERIFY_TOKEN`

## Development

### Running Tests

To run the tests, use the following command:

```bash
poetry run pytest
```

### Code Style

This project follows Google-style docstrings and uses Pydantic for data validation.

