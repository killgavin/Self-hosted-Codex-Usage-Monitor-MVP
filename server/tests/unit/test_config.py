"""Unit tests for environment-backed server configuration and executable detection."""

import os
import sys

import pytest

from app.config import Settings, get_settings, resolve_codex_executable


def test_default_executable(monkeypatch) -> None:
    monkeypatch.delenv("CODEX_EXECUTABLE", raising=False)

    assert get_settings().codex_executable == "codex"


def test_default_server_bind_configuration(monkeypatch) -> None:
    for name in ("CODEX_MONITOR_HOST", "CODEX_MONITOR_PORT", "LOG_LEVEL"):
        monkeypatch.delenv(name, raising=False)

    settings = get_settings()

    assert settings.host == "127.0.0.1"
    assert settings.port == 8080
    assert settings.log_level == "info"


def test_explicit_server_bind_overrides(monkeypatch) -> None:
    monkeypatch.setenv("CODEX_MONITOR_HOST", " 0.0.0.0 ")
    monkeypatch.setenv("CODEX_MONITOR_PORT", " 18080 ")
    monkeypatch.setenv("LOG_LEVEL", " DEBUG ")

    settings = get_settings()

    assert settings.host == "0.0.0.0"
    assert settings.port == 18080
    assert settings.log_level == "debug"


def test_blank_host_falls_back_to_loopback(monkeypatch) -> None:
    monkeypatch.setenv("CODEX_MONITOR_HOST", "  \t")

    assert get_settings().host == "127.0.0.1"


@pytest.mark.parametrize("configured_port", ("", "0", "65536", "not-a-port", "8080.5"))
def test_invalid_port_raises_sanitized_error(monkeypatch, configured_port: str) -> None:
    monkeypatch.setenv("CODEX_MONITOR_PORT", configured_port)

    with pytest.raises(
        ValueError,
        match=r"^CODEX_MONITOR_PORT must be an integer between 1 and 65535$",
    ) as raised:
        get_settings()

    assert str(raised.value) == "CODEX_MONITOR_PORT must be an integer between 1 and 65535"


def test_invalid_log_level_raises_sanitized_error(monkeypatch) -> None:
    monkeypatch.setenv("LOG_LEVEL", "verbose")

    with pytest.raises(
        ValueError,
        match=r"^LOG_LEVEL must be one of: critical, error, warning, info, debug, trace$",
    ) as raised:
        get_settings()

    assert str(raised.value) == (
        "LOG_LEVEL must be one of: critical, error, warning, info, debug, trace"
    )


def test_blank_log_level_uses_info(monkeypatch) -> None:
    monkeypatch.setenv("LOG_LEVEL", " \t")

    assert get_settings().log_level == "info"


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
