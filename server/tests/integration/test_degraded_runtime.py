"""Automated degraded-runtime coverage for T-69 through T-71."""

import asyncio
import json

from app.codex.adapter import CodexAppServerAdapter
from app.codex.exceptions import AdapterStateError, ProcessExited
from app.config import Settings
from app.main import create_app


SERVER_TOKEN = "degraded-runtime-test-token"
PRIVATE_MARKER = "synthetic-private-process-output"


class _FakeWriter:
    def __init__(self) -> None:
        self.messages: list[bytes] = []

    def write(self, data: bytes) -> None:
        self.messages.append(data)

    async def drain(self) -> None:
        return None

    def close(self) -> None:
        return None

    async def wait_closed(self) -> None:
        return None


class _FakeReader:
    def __init__(self) -> None:
        self.lines: asyncio.Queue[bytes] = asyncio.Queue()

    async def readline(self) -> bytes:
        return await self.lines.get()


class _FakeChild:
    def __init__(self) -> None:
        self.stdin = _FakeWriter()
        self.stdout = _FakeReader()


class _ExitableProcess:
    """Deterministic process boundary with a controllable child exit."""

    def __init__(self) -> None:
        self.child = _FakeChild()
        self.started = False
        self.exited = False
        self.stopped = False

    @property
    def process(self):
        return self.child if self.started and not self.stopped else None

    @property
    def is_alive(self) -> bool:
        return self.started and not self.exited and not self.stopped

    def ensure_alive(self) -> None:
        if self.exited:
            raise ProcessExited(PRIVATE_MARKER)

    async def start(self) -> None:
        self.started = True

    async def stop(self) -> None:
        self.stopped = True


async def _request(app, path: str) -> tuple[int, dict]:
    messages: list[dict] = []

    async def receive() -> dict:
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message: dict) -> None:
        messages.append(message)

    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": [(b"authorization", f"Bearer {SERVER_TOKEN}".encode())],
        "client": ("testclient", 12345),
        "server": ("testserver", 80),
    }
    await app(scope, receive, send)
    start = next(message for message in messages if message["type"] == "http.response.start")
    body = next(message for message in messages if message["type"] == "http.response.body")
    return start["status"], json.loads(body["body"])


def test_t69_missing_codex_keeps_lifespan_available_and_reports_degraded() -> None:
    async def scenario() -> None:
        app = create_app(
            settings=Settings(
                codex_executable="definitely-missing-task-0804",
                server_api_token=SERVER_TOKEN,
            )
        )
        async with app.router.lifespan_context(app):
            assert await _request(app, "/health") == (200, {"status": "ok"})
            assert await _request(app, "/api/v1/status") == (200, {"status": "degraded"})

    asyncio.run(scenario())


def test_t70_unexpected_exit_is_controlled_and_shutdown_reaps() -> None:
    async def scenario() -> None:
        process = _ExitableProcess()
        adapter = CodexAppServerAdapter(process)
        await process.child.stdout.lines.put(
            (
                json.dumps(
                    {
                        "id": 1,
                        "result": {
                            "codexHome": "/synthetic",
                            "platformFamily": "synthetic",
                            "platformOs": "synthetic",
                            "userAgent": "synthetic",
                        },
                    }
                )
                + "\n"
            ).encode()
        )
        app = create_app(
            settings=Settings(server_api_token=SERVER_TOKEN),
            adapter=adapter,
        )
        async with app.router.lifespan_context(app):
            assert adapter.state.value == "READY"
            assert adapter.is_available() is True
            process.exited = True
            status, body = await _request(app, "/api/v1/account")
            assert status == 503
            assert body == {
                "error": {"code": "UPSTREAM_UNAVAILABLE", "message": "Codex is unavailable"}
            }
            assert adapter.state.value == "FAILED"
            assert adapter.is_available() is False
            assert await _request(app, "/api/v1/status") == (200, {"status": "degraded"})
        assert process.stopped is True

    asyncio.run(scenario())


def test_t71_unavailable_error_is_exact_and_sanitized() -> None:
    async def scenario() -> None:
        process = _ExitableProcess()
        adapter = CodexAppServerAdapter(process)
        await process.child.stdout.lines.put(
            (
                json.dumps(
                    {
                        "id": 1,
                        "result": {
                            "codexHome": "/synthetic",
                            "platformFamily": "synthetic",
                            "platformOs": "synthetic",
                            "userAgent": "synthetic",
                        },
                    }
                )
                + "\n"
            ).encode()
        )
        app = create_app(
            settings=Settings(server_api_token=SERVER_TOKEN),
            adapter=adapter,
        )
        async with app.router.lifespan_context(app):
            process.exited = True
            status, body = await _request(app, "/api/v1/account")
            assert status == 503
            assert body == {
                "error": {"code": "UPSTREAM_UNAVAILABLE", "message": "Codex is unavailable"}
            }
            assert PRIVATE_MARKER not in json.dumps(body)

    asyncio.run(scenario())


def test_lifespan_does_not_swallow_unexpected_startup_errors() -> None:
    class RaisingAdapter:
        async def initialize(self) -> None:
            raise RuntimeError(PRIVATE_MARKER)

        async def shutdown(self) -> None:
            raise AssertionError("shutdown should not run when startup never yielded")

    async def scenario() -> None:
        app = create_app(adapter=RaisingAdapter())
        try:
            async with app.router.lifespan_context(app):
                raise AssertionError("lifespan unexpectedly yielded")
        except RuntimeError as error:
            assert str(error) == PRIVATE_MARKER
        else:
            raise AssertionError("unexpected startup error was swallowed")

    asyncio.run(scenario())


def test_lifespan_awaits_shutdown_to_completion() -> None:
    class LifecycleAdapter:
        def __init__(self) -> None:
            self.shutdown_started = False
            self.shutdown_finished = False

        async def initialize(self) -> None:
            return None

        async def shutdown(self) -> None:
            self.shutdown_started = True
            self.shutdown_finished = True

        def is_available(self) -> bool:
            return True

    async def scenario() -> None:
        adapter = LifecycleAdapter()
        app = create_app(adapter=adapter)
        async with app.router.lifespan_context(app):
            assert app.state.runtime_started is True
        assert adapter.shutdown_started is True
        assert adapter.shutdown_finished is True

    asyncio.run(scenario())
