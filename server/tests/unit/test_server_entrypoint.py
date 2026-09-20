"""Unit tests for the side-effect-free uvicorn server entry point."""

import importlib

import app.__main__ as server_entrypoint


def test_import_does_not_start_uvicorn(monkeypatch) -> None:
    # Reloading is an import operation; importing the module must not start a listener.
    calls = []
    monkeypatch.setattr(server_entrypoint.uvicorn, "run", calls.append)

    importlib.reload(server_entrypoint)

    assert calls == []


def test_main_uses_default_safe_bind_values(monkeypatch) -> None:
    calls = []
    monkeypatch.setattr(
        server_entrypoint.uvicorn,
        "run",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )
    monkeypatch.delenv("CODEX_MONITOR_HOST", raising=False)
    monkeypatch.delenv("CODEX_MONITOR_PORT", raising=False)
    monkeypatch.delenv("LOG_LEVEL", raising=False)

    server_entrypoint.main()

    assert calls == [
        (
            ("app.main:app",),
            {"host": "127.0.0.1", "port": 8080, "log_level": "info"},
        )
    ]


def test_main_uses_explicit_overrides(monkeypatch) -> None:
    calls = []
    monkeypatch.setattr(
        server_entrypoint.uvicorn,
        "run",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )
    monkeypatch.setenv("CODEX_MONITOR_HOST", "0.0.0.0")
    monkeypatch.setenv("CODEX_MONITOR_PORT", "9090")
    monkeypatch.setenv("LOG_LEVEL", "WARNING")

    server_entrypoint.main()

    assert calls == [
        (
            ("app.main:app",),
            {"host": "0.0.0.0", "port": 9090, "log_level": "warning"},
        )
    ]
