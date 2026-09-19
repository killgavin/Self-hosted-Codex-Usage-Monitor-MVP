"""ASGI and dependency-free behavior checks for the minimal login UI."""

import asyncio
import json
import os
import subprocess
from pathlib import Path

from app.main import create_app


def request(app, method: str, path: str) -> tuple[int, bytes, str]:
    messages = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        messages.append(message)

    scope = {
        "type": "http", "asgi": {"version": "3.0", "spec_version": "2.0"},
        "http_version": "1.1", "method": method, "scheme": "http", "path": path,
        "raw_path": path.encode(), "query_string": b"", "headers": [],
        "client": ("testclient", 12345), "server": ("testserver", 80),
    }
    asyncio.run(app(scope, receive, send))
    start = next(item for item in messages if item["type"] == "http.response.start")
    body = next(item for item in messages if item["type"] == "http.response.body")
    content_type = dict(start["headers"]).get(b"content-type", b"").decode()
    return start["status"], body["body"], content_type


def test_dashboard_shell_assets_and_rest_remain_reachable() -> None:
    app = create_app()
    status, body, content_type = request(app, "GET", "/")
    html = body.decode()
    assert status == 200 and "text/html" in content_type
    for required in (
        "dashboard-shell", "server-token", "connect-button", "connection-status",
        "account-summary", "rate-limit-list", "reset-credit-summary", "last-updated",
        "login-button", "login-state", "verification-link", "user-code", "cancel-button",
        "logout-button", "/assets/app.mjs",
    ):
        assert required in html
    assert 'id="server-token"' in html and 'type="password"' in html
    assert 'id="server-token"' in html and 'value=' not in html
    assert all(value not in html for value in ("usedPercent", "remainingPercent", "windowDurationMinutes"))
    status, body, content_type = request(app, "GET", "/assets/app.mjs")
    assert status == 200 and "javascript" in content_type
    assert all(value not in body for value in (b"localStorage", b"sessionStorage", b"document.cookie"))
    status, _, _ = request(app, "GET", "/health")
    assert status == 200
    status, _, _ = request(app, "GET", "/assets/missing.txt")
    assert status == 404


def test_dependency_free_node_behavior() -> None:
    node = os.environ.get("NODE", "node")
    fixture = Path(__file__).resolve().parents[1] / "fixtures" / "login_ui_behavior.mjs"
    result = subprocess.run([node, str(fixture)], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr or result.stdout
    assert "login-ui-behavior: PASS" in result.stdout
