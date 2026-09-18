"""Minimal JSONL request/response transport over a started Codex child.

This boundary owns wire serialization, request IDs, and one response reader.
Process lifecycle remains with :class:`CodexProcess`; notifications,
concurrent request guarantees, malformed-message policy, and request timeouts
are intentionally deferred to later tasks.
"""

import asyncio
import json
from typing import Any

from app.codex.exceptions import ProcessCommunicationFailed


class CodexTransport:
    """Correlate basic JSONL requests with responses from a child stdout pipe."""

    def __init__(self, process_or_child: Any) -> None:
        child = getattr(process_or_child, "process", process_or_child)
        self._stdin = getattr(child, "stdin", None)
        self._stdout = getattr(child, "stdout", None)
        self._next_id = 1
        self._pending: dict[int, asyncio.Future[Any]] = {}
        self._notifications: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()
        self._reader_task: asyncio.Task[None] | None = None
        self._closed = False

    async def request(self, method: str, params: Any = None) -> Any:
        """Write one request and await its correlated result or controlled error."""

        if self._closed or self._stdin is None or self._stdout is None:
            raise ProcessCommunicationFailed("Codex transport is not available")

        if self._reader_task is None:
            self._reader_task = asyncio.create_task(self._read_responses())

        request_id = self._next_id
        self._next_id += 1
        loop = asyncio.get_running_loop()
        future: asyncio.Future[Any] = loop.create_future()
        self._pending[request_id] = future

        message: dict[str, Any] = {"method": method, "id": request_id}
        if params is not None:
            message["params"] = params

        try:
            wire_message = (json.dumps(message, separators=(",", ":")) + "\n").encode()
            self._stdin.write(wire_message)
            await self._stdin.drain()
        except (OSError, RuntimeError, AttributeError) as exc:
            self._pending.pop(request_id, None)
            raise ProcessCommunicationFailed("Codex request write failed") from exc

        try:
            return await future
        finally:
            self._pending.pop(request_id, None)

    async def next_notification(self) -> dict[str, Any]:
        """Deliver the next generic notification without interpreting its method."""

        if self._closed and self._notifications.empty():
            raise ProcessCommunicationFailed("Codex transport closed")
        notification = await self._notifications.get()
        if notification is None:
            raise ProcessCommunicationFailed("Codex transport closed")
        return notification

    async def close(self, timeout: float = 1.0) -> None:
        """Boundedly cancel reader work and fail pending requests.

        Closing this transport does not stop the Codex child; that remains the
        process lifecycle owner's responsibility.
        """

        if timeout <= 0:
            raise ValueError("transport close timeout must be positive")
        if self._closed:
            return
        self._closed = True
        self._notifications.put_nowait(None)
        error = ProcessCommunicationFailed("Codex transport closed")
        for future in self._pending.values():
            if not future.done():
                future.set_exception(error)

        reader_task = self._reader_task
        if reader_task is not None:
            reader_task.cancel()
            try:
                await asyncio.wait_for(asyncio.shield(reader_task), timeout)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass

    async def _read_responses(self) -> None:
        """Read newline-delimited responses and complete matching futures."""

        try:
            while True:
                line = await self._stdout.readline()
                if not line:
                    self._fail_pending("Codex stdout closed")
                    return
                message = json.loads(line)
                response_id = message.get("id")
                if not isinstance(response_id, int):
                    # Keep notification semantics generic; domain dispatch is
                    # deliberately outside this transport boundary.
                    if isinstance(message, dict):
                        self._notifications.put_nowait(message)
                    continue
                future = self._pending.get(response_id)
                if future is None or future.done():
                    continue
                if "error" in message:
                    future.set_exception(ProcessCommunicationFailed("Codex response returned an error"))
                else:
                    future.set_result(message.get("result"))
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            self._fail_pending("Codex response read failed")
            raise ProcessCommunicationFailed("Codex response read failed") from exc

    def _fail_pending(self, message: str) -> None:
        error = ProcessCommunicationFailed(message)
        for future in self._pending.values():
            if not future.done():
                future.set_exception(error)
