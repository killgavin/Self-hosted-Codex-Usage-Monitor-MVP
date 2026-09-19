"""ASGI integration coverage for monitor-owned Bearer authentication."""

import asyncio
import json
from typing import Any

from fastapi import Depends, FastAPI
import pytest

from app.config import Settings
from app.security.server_token import (
    InvalidServerToken,
    ServerTokenAuth,
    invalid_server_token_handler,
)


SERVER_TOKEN = "monitor-test-token"
OPENAI_STYLE_TOKEN = "sk-test-not-a-real-credential"


def protected_app() -> FastAPI:
    app = FastAPI()
    app.add_exception_handler(InvalidServerToken, invalid_server_token_handler)

    @app.get("/protected", dependencies=[Depends(ServerTokenAuth(SERVER_TOKEN))])
    async def protected() -> dict[str, str]:
        return {"status": "ok"}

    return app


def request(authorization: str | None = None) -> tuple[int, dict[str, Any], dict[bytes, bytes]]:
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
        "path": "/protected",
        "raw_path": b"/protected",
        "query_string": b"",
        "headers": headers,
        "client": ("testclient", 12345),
        "server": ("testserver", 80),
    }
    asyncio.run(protected_app()(scope, receive, send))
    start = next(message for message in messages if message["type"] == "http.response.start")
    body = next(message for message in messages if message["type"] == "http.response.body")
    return start["status"], json.loads(body["body"]), dict(start["headers"])


def assert_invalid(response: tuple[int, dict[str, Any], dict[bytes, bytes]]) -> None:
    status, body, headers = response
    assert status == 401
    assert body == {
        "error": {
            "code": "INVALID_SERVER_TOKEN",
            "message": "Invalid server token",
        }
    }
    assert headers[b"www-authenticate"] == b"Bearer"
    serialized = json.dumps(body)
    assert SERVER_TOKEN not in serialized
    assert OPENAI_STYLE_TOKEN not in serialized


def test_valid_server_token_reaches_protected_route() -> None:
    status, body, _ = request(f"Bearer {SERVER_TOKEN}")
    assert status == 200
    assert body == {"status": "ok"}


def test_missing_server_token_is_rejected() -> None:
    assert_invalid(request())


@pytest.mark.parametrize(
    "authorization",
    ("Bearer wrong-monitor-token", "Basic monitor-test-token", "Bearer"),
)
def test_invalid_server_token_is_rejected_without_echo(authorization: str) -> None:
    assert_invalid(request(authorization))


def test_openai_style_token_is_not_implicitly_accepted() -> None:
    assert_invalid(request(f"Bearer {OPENAI_STYLE_TOKEN}"))


def test_settings_loads_only_the_monitor_token(monkeypatch) -> None:
    monkeypatch.setenv("CODEX_MONITOR_API_TOKEN", SERVER_TOKEN)
    monkeypatch.setenv("OPENAI_API_KEY", OPENAI_STYLE_TOKEN)

    settings = Settings.from_environment()
    assert settings.server_api_token == SERVER_TOKEN
    assert SERVER_TOKEN not in repr(settings)
