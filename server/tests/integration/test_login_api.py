"""ASGI integration coverage for the minimal login REST contract."""

import asyncio
import json
from typing import Any

import pytest

from app.main import create_app
from app.codex.exceptions import AdapterStateError, ProcessCommunicationFailed
from app.services.auth import (
    LoginAlreadyPending,
    LoginCancellationFailed,
    LoginNotPending,
    LoginState,
    LoginStatus,
)


class FakeAuthService:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.wait_timeouts: list[float] = []
        self.failure: Exception | None = None

    async def start_login(self):
        self.calls.append("start_login")
        if self.failure:
            raise self.failure
        return LoginStatus(LoginState.PENDING, "synthetic-login-id", "https://example.invalid", "synthetic-code")

    async def get_status(self, wait_timeout=0.05):
        self.calls.append("get_status")
        self.wait_timeouts.append(wait_timeout)
        if self.failure:
            raise self.failure
        return LoginStatus(LoginState.COMPLETED)

    async def cancel_login(self):
        self.calls.append("cancel_login")
        if self.failure:
            raise self.failure
        return LoginStatus(LoginState.CANCELED)

    async def logout(self):
        self.calls.append("logout")
        if self.failure:
            raise self.failure
        return LoginStatus(LoginState.IDLE)


def request(app, method: str, path: str) -> tuple[int, dict[str, Any]]:
    messages: list[dict[str, Any]] = []

    async def receive() -> dict[str, Any]:
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message: dict[str, Any]) -> None:
        messages.append(message)

    scope = {
        "type": "http", "asgi": {"version": "3.0", "spec_version": "2.0"},
        "http_version": "1.1", "method": method, "scheme": "http", "path": path,
        "raw_path": path.encode(), "query_string": b"", "headers": [],
        "client": ("testclient", 12345), "server": ("testserver", 80),
    }
    asyncio.run(app(scope, receive, send))
    start = next(message for message in messages if message["type"] == "http.response.start")
    body = next(message for message in messages if message["type"] == "http.response.body")
    return start["status"], json.loads(body["body"])


def test_login_routes_have_safe_success_shapes_and_exact_service_calls() -> None:
    service = FakeAuthService()
    app = create_app(service)
    for method, path, call in (
        ("POST", "/api/v1/login", "start_login"),
        ("GET", "/api/v1/login/status", "get_status"),
        ("POST", "/api/v1/login/cancel", "cancel_login"),
        ("POST", "/api/v1/logout", "logout"),
    ):
        status, body = request(app, method, path)
        assert status == 200
        assert set(body) == {"state", "verificationUrl", "userCode"}
        assert "loginId" not in body and "synthetic-login-id" not in json.dumps(body)
        assert service.calls[-1] == call
    assert service.wait_timeouts == [0.05]


@pytest.mark.parametrize(
    ("failure", "status", "code", "message"),
    [
        (LoginAlreadyPending("private"), 409, "CODEX_LOGIN_PENDING", "Login is already pending"),
        (LoginNotPending("private"), 409, "CODEX_NOT_AUTHENTICATED", "Login is not pending"),
        (LoginCancellationFailed("private"), 502, "CODEX_PROTOCOL_ERROR", "Login cancellation failed"),
        (AdapterStateError("private"), 503, "UPSTREAM_UNAVAILABLE", "Codex is unavailable"),
        (ProcessCommunicationFailed("private"), 502, "CODEX_PROTOCOL_ERROR", "Codex protocol error"),
    ],
)
def test_login_errors_are_fixed_and_sanitized(failure, status, code, message) -> None:
    service = FakeAuthService()
    service.failure = failure
    app = create_app(service)
    response_status, body = request(app, "POST", "/api/v1/login")
    assert response_status == status
    assert body == {"error": {"code": code, "message": message}}
    assert "private" not in json.dumps(body)


def test_health_unknown_path_and_method_remain_normal() -> None:
    app = create_app(FakeAuthService())
    status, body = request(app, "GET", "/health")
    assert status == 200 and body == {"status": "ok"}
    status, _ = request(app, "GET", "/not-found")
    assert status == 404
    status, _ = request(app, "GET", "/api/v1/login")
    assert status == 405
    status, _ = request(app, "POST", "/api/v1/login/logout")
    assert status == 404


def test_global_app_creation_does_not_start_a_process() -> None:
    from app.main import app

    assert app.state.auth_service._adapter._process.process is None
