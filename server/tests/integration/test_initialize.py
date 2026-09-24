"""Real Codex initialization handshake and cleanup coverage."""

import asyncio
import os

import pytest

from app.config import Settings
from app.codex.adapter import AdapterState, CodexAppServerAdapter
from app.codex.process import CodexProcess


def test_real_initialize_reaches_ready_and_cleans_up() -> None:
    executable = os.environ.get("REAL_CODEX_EXECUTABLE")
    if not executable:
        pytest.skip("REAL_CODEX_EXECUTABLE is not configured")

    async def scenario() -> None:
        process = CodexProcess(Settings(executable))
        adapter = CodexAppServerAdapter(process)
        child = None
        try:
            response = await adapter.initialize()
            child = process.process
            assert adapter.state is AdapterState.READY
            assert response.codex_home
            assert response.platform_family
            assert response.platform_os
            assert response.user_agent
            assert child is not None
            pid = child.pid
        finally:
            await adapter.shutdown()

        assert adapter.state is AdapterState.STOPPED
        assert process.process is None
        assert child is not None
        assert child.returncode is not None
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            pass
        else:
            raise AssertionError("stopped Codex child still exists")

    asyncio.run(scenario())
