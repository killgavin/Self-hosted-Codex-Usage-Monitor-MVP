"""Subprocess start boundary for the Codex app-server.

This module intentionally does not implement stopping, transport, or protocol
behavior. Those lifecycle and communication concerns belong to later tasks.
"""

import asyncio
import os
import signal

from app.config import Settings, get_settings, resolve_codex_executable
from app.codex.exceptions import (
    ExecutableNotFound,
    ProcessExited,
    ProcessStartFailed,
    ProcessStopFailed,
)


class CodexProcess:
    """Start one Codex app-server child with pipes for future stdio transport."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings if settings is not None else get_settings()
        self._process: asyncio.subprocess.Process | None = None
        self._argv: tuple[str, str] | None = None
        self._process_group_id: int | None = None

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

    def ensure_alive(self) -> None:
        """Raise a controlled error if a started child has already exited.

        The process boundary deliberately does not inspect or include child
        stdout/stderr.  Callers can therefore distinguish an unavailable
        upstream from a protocol payload without exposing process details.
        """

        if self._process is not None and not self.is_alive:
            raise ProcessExited("Codex app-server process exited")

    async def start(self) -> asyncio.subprocess.Process:
        """Start ``<resolved executable> app-server`` without invoking a shell."""

        if self._process is not None:
            raise ProcessStartFailed("Codex process has already been started")

        executable = resolve_codex_executable(self._settings)
        if executable is None:
            raise ExecutableNotFound("Configured Codex executable was not found")

        argv = (executable, "app-server")
        spawn_kwargs: dict[str, object] = {
            "stdin": asyncio.subprocess.PIPE,
            "stdout": asyncio.subprocess.PIPE,
            "stderr": asyncio.subprocess.PIPE,
        }
        if os.name == "posix":
            # The npm executable is a wrapper around a native child. Keep both
            # processes in an owned session so shutdown cannot strand a child
            # holding the transport pipes open.
            spawn_kwargs["start_new_session"] = True

        try:
            process = await asyncio.create_subprocess_exec(
                *argv,
                **spawn_kwargs,
            )
        except (OSError, ValueError) as exc:
            raise ProcessStartFailed("Codex app-server process could not be started") from exc

        self._argv = argv
        self._process = process
        if os.name == "posix":
            try:
                process_group_id = os.getpgid(process.pid)
            except ProcessLookupError:
                process_group_id = None
            self._process_group_id = process_group_id
        return process

    def _signal_for_stop(self, process: asyncio.subprocess.Process, *, terminate: bool) -> None:
        """Signal the owned process group, with a direct-process fallback."""

        if os.name == "posix" and self._process_group_id is not None:
            # A fresh session must never point at the pytest/server group. If
            # the invariant is not available, prefer a direct signal to avoid
            # affecting unrelated processes.
            if self._process_group_id != os.getpgrp():
                signum = signal.SIGTERM if terminate else signal.SIGKILL
                try:
                    os.killpg(self._process_group_id, signum)
                    return
                except ProcessLookupError:
                    if process.returncode is not None:
                        return

        try:
            if terminate:
                process.terminate()
            else:
                process.kill()
        except ProcessLookupError:
            pass

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
                    self._signal_for_stop(process, terminate=True)
                    try:
                        await asyncio.wait_for(process.wait(), timeout)
                    except asyncio.TimeoutError:
                        self._signal_for_stop(process, terminate=False)
                        try:
                            await asyncio.wait_for(process.wait(), timeout)
                        except asyncio.TimeoutError as exc:
                            raise ProcessStopFailed("Codex app-server did not exit") from exc
        finally:
            if process.returncode is not None:
                self._process = None
                self._argv = None
                self._process_group_id = None
