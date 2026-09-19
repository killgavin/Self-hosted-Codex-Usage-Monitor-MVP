"""T-62 evidence that UTC reset values render in the client timezone."""

import json
import os
from pathlib import Path
import subprocess


FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "local_time_behavior.mjs"


def run_in_timezone(timezone: str) -> dict[str, str]:
    environment = os.environ.copy()
    environment["TZ"] = timezone
    result = subprocess.run(
        [environment.get("NODE", "node"), str(FIXTURE)],
        capture_output=True,
        text=True,
        check=False,
        env=environment,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    return json.loads(result.stdout)


def test_utc_timestamp_renders_differently_in_browser_timezones() -> None:
    utc = run_in_timezone("UTC")
    taipei = run_in_timezone("Asia/Taipei")

    assert utc["output"] != taipei["output"]
    assert utc["invalid"] == taipei["invalid"] == "Unknown reset time"


def test_formatter_does_not_fix_a_timezone() -> None:
    script = Path(__file__).resolve().parents[3] / "web" / "assets" / "app.mjs"
    source = script.read_text()

    assert 'timeZone:' not in source
    assert 'timeZone =' not in source
    assert "Asia/Taipei" not in source
