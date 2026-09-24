"""Real Codex account/read validation through production boundaries."""

import asyncio
import os

import pytest

from app.config import Settings
from app.codex.account_mapper import account_status_from_protocol
from app.codex.adapter import AdapterState, CodexAppServerAdapter
from app.codex.process import CodexProcess


def _required_executable() -> str:
    executable = os.environ.get("REAL_CODEX_EXECUTABLE")
    if not executable:
        pytest.skip("REAL_CODEX_EXECUTABLE is not configured")
    return executable


def test_real_authenticated_account_read() -> None:
    executable = _required_executable()

    async def scenario() -> None:
        process = CodexProcess(Settings(executable))
        adapter = CodexAppServerAdapter(process)
        child = None
        try:
            await adapter.initialize()
            child = process.process
            status = account_status_from_protocol(await adapter.read_account())
            assert adapter.state is AdapterState.READY
            assert status.authenticated is True
            assert status.auth_mode is None or isinstance(status.auth_mode, str)
        finally:
            await adapter.shutdown()

        assert adapter.state is AdapterState.STOPPED
        assert process.process is None
        assert child is not None
        assert child.returncode is not None

    asyncio.run(scenario())


def test_real_empty_codex_home_is_unauthenticated(tmp_path, monkeypatch) -> None:
    executable = _required_executable()
    monkeypatch.setenv("CODEX_HOME", str(tmp_path))

    async def scenario() -> None:
        process = CodexProcess(Settings(executable))
        adapter = CodexAppServerAdapter(process)
        child = None
        try:
            await adapter.initialize()
            child = process.process
            status = account_status_from_protocol(await adapter.read_account())
            assert adapter.state is AdapterState.READY
            assert status.authenticated is False
            assert status.auth_mode is None
            assert status.plan_type is None
        finally:
            await adapter.shutdown()

        assert adapter.state is AdapterState.STOPPED
        assert process.process is None
        assert child is not None
        assert child.returncode is not None

    asyncio.run(scenario())
