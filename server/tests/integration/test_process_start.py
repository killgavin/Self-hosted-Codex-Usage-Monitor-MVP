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
        pytest.skip("REAL_CODEX_EXECUTABLE is not configured")
    assert Path(executable).is_file()

    async def scenario() -> None:
        codex_process = CodexProcess(Settings(executable))
        await codex_process.start()
        try:
            await asyncio.sleep(2.1)
            assert codex_process.is_alive
            assert codex_process.argv == (executable, "app-server")
        finally:
            await codex_process.stop()

    asyncio.run(scenario())
