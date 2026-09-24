"""Deterministic dashboard connect-flow evidence (not real-browser evidence)."""

import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
APP = ROOT.parent / "web" / "assets" / "app.mjs"
FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "dashboard_e2e_behavior.mjs"


def test_dashboard_connect_flow_node_fixture() -> None:
    node = os.environ.get("NODE", "node")
    result = subprocess.run([node, str(FIXTURE)], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr or result.stdout
    assert "dashboard-e2e-behavior: PASS" in result.stdout


def test_dashboard_connect_is_same_origin_and_does_not_persist_token() -> None:
    source = APP.read_text()
    assert '"/api/v1/status"' in source
    assert '"/api/v1/account"' in source
    assert '"/api/v1/rate-limits"' in source
    assert '"/api/v1/session"' in source and "Authorization" not in source and "Bearer ${token}" not in source
    assert "localStorage" not in source and "sessionStorage" not in source
    assert "document.cookie" not in source
    assert "/backend-api/" not in source and "console.log" not in source


def test_dashboard_shell_has_safe_connection_targets() -> None:
    html = (ROOT.parent / "web" / "index.html").read_text()
    for required in ("server-token", "monitor-logout-button", "connect-button", "connection-status", "account-summary", "reset-credit-summary", "rate-limit-list", "last-updated"):
        assert required in html
    assert 'id="server-token"' in html and 'type="password"' in html
    assert 'id="server-token"' in html and 'value=' not in html


def test_dashboard_summary_headings_preserve_aria_targets() -> None:
    source = APP.read_text()
    assert 'heading.id = "account-title"' in source
    assert 'heading.id = "reset-credit-title"' in source
