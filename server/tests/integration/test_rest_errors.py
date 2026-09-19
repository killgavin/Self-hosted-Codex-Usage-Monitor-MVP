"""ASGI integration coverage for fixed sanitized REST errors."""

import asyncio
import json
from typing import Any

import pytest

from app.codex.exceptions import (
    AdapterStateError,
    ExecutableNotFound,
    ProcessCommunicationFailed,
    ProcessStartFailed,
    ProcessStopFailed,
)
from app.config import Settings
from app.main import create_app


SERVER_TOKEN = "error-test-monitor-token"
PRIVATE_MARKER = "private-auth-payload-and-trace-marker"


class FailingAccountService:
    def __init__(self, failure: Exception) -> None:
        self.failure = failure

    async def get_status(self):
        raise self.failure


class FailingRateLimitService:
    def __init__(self, failure: Exception) -> None:
        self.failure = failure

    async def get_rate_limits(self):
        raise self.failure


def request(
    failure: Exception,
    path: str = "/api/v1/account",
) -> tuple[int, dict[str, Any]]:
    messages: list[dict[str, Any]] = []

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
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": [(b"authorization", f"Bearer {SERVER_TOKEN}".encode())],
        "client": ("testclient", 12345),
        "server": ("testserver", 80),
    }
    app = create_app(
        settings=Settings(server_api_token=SERVER_TOKEN),
        account_service=FailingAccountService(failure),
        rate_limit_service=FailingRateLimitService(failure),
    )
    asyncio.run(app(scope, receive, send))
    start = next(message for message in messages if message["type"] == "http.response.start")
    body = next(message for message in messages if message["type"] == "http.response.body")
    return start["status"], json.loads(body["body"])


@pytest.mark.parametrize(
    ("failure", "expected_status", "expected_code", "expected_message"),
    (
        (ExecutableNotFound(PRIVATE_MARKER), 503, "CODEX_NOT_INSTALLED", "Codex is not installed"),
        (ProcessStartFailed(PRIVATE_MARKER), 503, "CODEX_START_FAILED", "Codex failed to start"),
        (AdapterStateError(PRIVATE_MARKER), 503, "UPSTREAM_UNAVAILABLE", "Codex is unavailable"),
        (ProcessCommunicationFailed(PRIVATE_MARKER), 502, "CODEX_PROTOCOL_ERROR", "Codex protocol error"),
        (ProcessStopFailed(PRIVATE_MARKER), 502, "CODEX_PROTOCOL_ERROR", "Codex protocol error"),
        (RuntimeError(PRIVATE_MARKER), 500, "INTERNAL_ERROR", "Internal error"),
    ),
)
def test_service_failures_use_fixed_sanitized_errors(
    failure: Exception,
    expected_status: int,
    expected_code: str,
    expected_message: str,
) -> None:
    status, body = request(failure)

    assert status == expected_status
    assert body == {
        "error": {
            "code": expected_code,
            "message": expected_message,
        }
    }
    serialized = json.dumps(body)
    assert PRIVATE_MARKER not in serialized
    assert SERVER_TOKEN not in serialized
    assert all(
        forbidden not in serialized.lower()
        for forbidden in ("traceback", "authorization", "cookie", "access_token", "refresh_token")
    )


def test_rate_limit_failure_uses_the_same_sanitized_mapper() -> None:
    status, body = request(
        ProcessCommunicationFailed(PRIVATE_MARKER),
        path="/api/v1/rate-limits",
    )

    assert status == 502
    assert body == {
        "error": {
            "code": "CODEX_PROTOCOL_ERROR",
            "message": "Codex protocol error",
        }
    }
    assert PRIVATE_MARKER not in json.dumps(body)
