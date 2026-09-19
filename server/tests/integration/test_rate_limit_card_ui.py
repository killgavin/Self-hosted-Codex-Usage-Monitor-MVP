"""Dependency-free browser-component behavior checks for rate-limit cards."""

import os
from pathlib import Path
import subprocess


def test_generic_rate_limit_card_behavior() -> None:
    node = os.environ.get("NODE", "node")
    fixture = Path(__file__).resolve().parents[1] / "fixtures" / "rate_limit_card_behavior.mjs"
    result = subprocess.run([node, str(fixture)], capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr or result.stdout
    assert "rate-limit-card-behavior: PASS" in result.stdout


def test_card_renderer_avoids_html_injection_and_hard_coded_limit_ids() -> None:
    script = Path(__file__).resolve().parents[3] / "web" / "assets" / "app.mjs"
    source = script.read_text()

    assert "innerHTML" not in source
    assert "future-limit" not in source and "known-id" not in source
    assert "createRateLimitCard" in source and "renderRateLimitCards" in source
