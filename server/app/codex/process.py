"""Subprocess start boundary for the Codex app-server.

This module intentionally does not implement stopping, transport, or protocol
behavior. Those lifecycle and communication concerns belong to later tasks.
"""

import asyncio

from app.config import Settings, get_settings, resolve_codex_executable
from app.codex.exceptions import ExecutableNotFound, ProcessStartFailed


class CodexProcess:
    """Start one Codex app-server child with pipes for future stdio transport."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings if settings is not None else get_settings()
        self._process: asyncio.subprocess.Process | None = None
        self._argv: tuple[str, str] | None = None

    @property
    def process(self) -> asyncio.subprocess.Process | None:
        """Expose the child handle for controlled callers and test teardown."""

        return self._process

    @property
    def argv(self) -> tuple[str, str] | None:
        """Return the exact command tuple selected for the child, if started."""

        return self._argv

    @property
    def is_alive(self) -> bool:
        """Report whether the started child has not exited."""

        return self._process is not None and self._process.returncode is None

    async def start(self) -> asyncio.subprocess.Process:
        """Start ``<resolved executable> app-server`` without invoking a shell."""

        if self._process is not None:
            raise ProcessStartFailed("Codex process has already been started")

        executable = resolve_codex_executable(self._settings)
        if executable is None:
            raise ExecutableNotFound("Configured Codex executable was not found")

        argv = (executable, "app-server")
        try:
            process = await asyncio.create_subprocess_exec(
                *argv,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except (OSError, ValueError) as exc:
            raise ProcessStartFailed("Codex app-server process could not be started") from exc

        self._argv = argv
        self._process = process
        return process
