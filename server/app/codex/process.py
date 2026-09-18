"""Subprocess start boundary for the Codex app-server.

This module intentionally does not implement stopping, transport, or protocol
behavior. Those lifecycle and communication concerns belong to later tasks.
"""

import asyncio

from app.config import Settings, get_settings, resolve_codex_executable
from app.codex.exceptions import ExecutableNotFound, ProcessStartFailed, ProcessStopFailed


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

    async def stop(self, timeout: float = 2.0) -> None:
        """Gracefully stop and reap the child using bounded escalation.

        Closing stdin provides EOF for a cooperative app-server. If it remains
        alive, terminate is attempted, followed by kill as a final fallback.
        Every wait is bounded and awaited so the child is reaped before state
        is cleared. Calling stop before start or after stop is harmless.
        """

        if timeout <= 0:
            raise ValueError("stop timeout must be positive")

        process = self._process
        if process is None:
            return

        try:
            if process.returncode is None and process.stdin is not None:
                # Closing the pipe sends EOF; no payload is read or logged here.
                process.stdin.close()
                try:
                    await asyncio.wait_for(process.stdin.wait_closed(), timeout)
                except (asyncio.TimeoutError, ConnectionError):
                    pass

            if process.returncode is None:
                try:
                    await asyncio.wait_for(process.wait(), timeout)
                except asyncio.TimeoutError:
                    # Escalate only after the bounded graceful wait.
                    process.terminate()
                    try:
                        await asyncio.wait_for(process.wait(), timeout)
                    except asyncio.TimeoutError:
                        process.kill()
                        try:
                            await asyncio.wait_for(process.wait(), timeout)
                        except asyncio.TimeoutError as exc:
                            raise ProcessStopFailed("Codex app-server did not exit") from exc
        finally:
            if process.returncode is not None:
                self._process = None
                self._argv = None
