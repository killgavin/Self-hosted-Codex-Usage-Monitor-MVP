"""Unit tests for executable configuration and detection."""

import os
import sys

from app.config import Settings, get_settings, resolve_codex_executable


def test_default_executable(monkeypatch) -> None:
    monkeypatch.delenv("CODEX_EXECUTABLE", raising=False)

    assert get_settings().codex_executable == "codex"


def test_environment_override_trims_only_outer_whitespace(monkeypatch) -> None:
    configured = "  command with internal spaces  "
    monkeypatch.setenv("CODEX_EXECUTABLE", configured)

    assert get_settings().codex_executable == "command with internal spaces"


def test_blank_environment_override_uses_default(monkeypatch) -> None:
    monkeypatch.setenv("CODEX_EXECUTABLE", "   ")

    assert get_settings().codex_executable == "codex"


def test_existing_executable_detection() -> None:
    resolved = resolve_codex_executable(Settings(codex_executable=sys.executable))

    assert resolved is not None
    assert os.path.samefile(resolved, sys.executable)


def test_missing_executable_returns_none() -> None:
    assert resolve_codex_executable(Settings(codex_executable="definitely-missing-codex-test")) is None
