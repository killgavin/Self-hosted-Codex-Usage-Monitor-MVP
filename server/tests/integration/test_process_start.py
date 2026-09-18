"""Integration coverage for the Codex subprocess start boundary."""

import asyncio
import os
from pathlib import Path

import pytest

from app.config import Settings
from app.codex.exceptions import ExecutableNotFound
from app.codex.process import CodexProcess


def test_missing_executable_is_controlled() -> None:
    async def scenario() -> None:
        process = CodexProcess(Settings("definitely-missing-codex-test"))
        with pytest.raises(ExecutableNotFound):
            await process.start()

    asyncio.run(scenario())


def test_real_codex_app_server_starts_and_stays_alive() -> None:
    executable = os.environ.get("REAL_CODEX_EXECUTABLE")
    if not executable:
        pytest.fail("REAL_CODEX_EXECUTABLE is required for the real-process validation")
    assert Path(executable).is_file()

    async def scenario() -> None:
        codex_process = CodexProcess(Settings(executable))
        child = await codex_process.start()
        try:
            await asyncio.sleep(2.1)
            assert codex_process.is_alive
            assert codex_process.argv == (executable, "app-server")
            assert child.stdin is not None
            assert child.stdout is not None
            assert child.stderr is not None
        finally:
            # TASK-0102 deliberately has no public stop API. This teardown is
            # scoped to the child created by this test only.
            child.kill()
            await child.wait()

    asyncio.run(scenario())
