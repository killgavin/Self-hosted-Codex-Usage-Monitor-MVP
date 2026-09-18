"""Real Codex coverage for the public process stop lifecycle."""

import asyncio
import os
from pathlib import Path

from app.config import Settings
from app.codex.process import CodexProcess


def test_stop_before_start_is_idempotent() -> None:
    async def scenario() -> None:
        codex_process = CodexProcess()
        await codex_process.stop()
        await codex_process.stop()
        assert codex_process.process is None

    asyncio.run(scenario())


def test_real_codex_app_server_stops_and_is_reaped() -> None:
    executable = os.environ.get("REAL_CODEX_EXECUTABLE")
    if not executable:
        raise AssertionError("REAL_CODEX_EXECUTABLE is required for the real-process validation")
    assert Path(executable).is_file()

    async def scenario() -> None:
        codex_process = CodexProcess(Settings(executable))
        child = await codex_process.start()
        pid = child.pid
        assert pid is not None
        assert codex_process.is_alive

        await codex_process.stop()

        assert child.returncode is not None
        assert not codex_process.is_alive
        assert codex_process.process is None
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            pass
        else:
            raise AssertionError("stopped Codex child still exists")

    asyncio.run(scenario())
