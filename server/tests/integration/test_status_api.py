"""ASGI integration coverage for the authenticated status endpoint."""

import asyncio
import json
from typing import Any

from app.config import Settings
from app.main import create_app


SERVER_TOKEN = "status-test-monitor-token"


def request(authorization: str | None) -> tuple[int, dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    headers = [] if authorization is None else [(b"authorization", authorization.encode())]

    async def receive() -> dict[str, Any]:
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message: dict[str, Any]) -> None:
        messages.append(message)

    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/api/v1/status",
        "raw_path": b"/api/v1/status",
        "query_string": b"",
        "headers": headers,
        "client": ("testclient", 12345),
        "server": ("testserver", 80),
    }
    app = create_app(settings=Settings(server_api_token=SERVER_TOKEN))
    asyncio.run(app(scope, receive, send))
    start = next(message for message in messages if message["type"] == "http.response.start")
    body = next(message for message in messages if message["type"] == "http.response.body")
    return start["status"], json.loads(body["body"])


def test_status_endpoint_has_stable_authenticated_schema() -> None:
    status, body = request(f"Bearer {SERVER_TOKEN}")

    assert status == 200
    assert body == {"status": "ok"}


def test_status_endpoint_requires_server_token_without_echo() -> None:
    status, body = request(None)

    assert status == 401
    assert body == {
        "error": {
            "code": "INVALID_SERVER_TOKEN",
            "message": "Invalid server token",
        }
    }
    assert SERVER_TOKEN not in json.dumps(body)
