"""ASGI integration coverage for the authenticated account endpoint."""

import asyncio
import json
from typing import Any

from app.config import Settings
from app.main import create_app
from app.models.account import AccountStatus


SERVER_TOKEN = "account-test-monitor-token"


class FakeAccountService:
    def __init__(self, status: AccountStatus) -> None:
        self.status = status
        self.calls = 0

    async def get_status(self) -> AccountStatus:
        self.calls += 1
        return self.status


def request(
    service: FakeAccountService,
    authorization: str | None,
) -> tuple[int, dict[str, Any]]:
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
        "path": "/api/v1/account",
        "raw_path": b"/api/v1/account",
        "query_string": b"",
        "headers": headers,
        "client": ("testclient", 12345),
        "server": ("testserver", 80),
    }
    app = create_app(
        settings=Settings(server_api_token=SERVER_TOKEN),
        account_service=service,
    )
    asyncio.run(app(scope, receive, send))
    start = next(message for message in messages if message["type"] == "http.response.start")
    body = next(message for message in messages if message["type"] == "http.response.body")
    return start["status"], json.loads(body["body"])


def test_authenticated_account_schema_contains_no_credential_fields() -> None:
    service = FakeAccountService(AccountStatus(True, "chatgpt", "test-plan"))

    status, body = request(service, f"Bearer {SERVER_TOKEN}")

    assert status == 200
    assert body == {
        "authenticated": True,
        "authMode": "chatgpt",
        "planType": "test-plan",
    }
    serialized = json.dumps(body).lower()
    assert all(
        forbidden not in serialized
        for forbidden in ("token", "authorization", "cookie", "email", "credential")
    )
    assert service.calls == 1


def test_unauthenticated_account_preserves_nulls() -> None:
    service = FakeAccountService(AccountStatus(False, None, None))

    status, body = request(service, f"Bearer {SERVER_TOKEN}")

    assert status == 200
    assert body == {
        "authenticated": False,
        "authMode": None,
        "planType": None,
    }
    assert service.calls == 1


def test_missing_server_token_does_not_call_account_service() -> None:
    service = FakeAccountService(AccountStatus(True, "chatgpt", "test-plan"))

    status, body = request(service, None)

    assert status == 401
    assert body["error"]["code"] == "INVALID_SERVER_TOKEN"
    assert service.calls == 0
