"""Automated tests for the Codex adapter lifecycle boundary."""

import asyncio
import json

import pytest

from app.codex.adapter import AdapterState, CodexAppServerAdapter
from app.codex.exceptions import AdapterStateError, ProcessCommunicationFailed
from app.codex.protocol import GetAccountResponse


class _FakeWriter:
    def write(self, data: bytes) -> None:
        return None

    async def drain(self) -> None:
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


class _FakeProcess:
    def __init__(self) -> None:
        self.child = _FakeChild()
        self.started = False
        self.stopped = False

    @property
    def process(self):
        return self.child if self.started and not self.stopped else None

    async def start(self) -> None:
        self.started = True

    async def stop(self) -> None:
        self.stopped = True


def test_initial_state_and_canonical_states() -> None:
    adapter = CodexAppServerAdapter()

    assert adapter.state is AdapterState.STOPPED
    assert {state.value for state in AdapterState} == {
        "STOPPED",
        "STARTING",
        "INITIALIZING",
        "READY",
        "FAILED",
    }


def test_valid_start_and_ready_lifecycle() -> None:
    adapter = CodexAppServerAdapter()

    adapter._transition(AdapterState.STARTING)
    adapter._transition(AdapterState.INITIALIZING)
    adapter._transition(AdapterState.READY)

    assert adapter.state is AdapterState.READY


def test_valid_failure_and_recovery_transitions() -> None:
    adapter = CodexAppServerAdapter()

    adapter._transition(AdapterState.STARTING)
    adapter._transition(AdapterState.FAILED)
    adapter._transition(AdapterState.STARTING)
    adapter._transition(AdapterState.STOPPED)
    adapter._transition(AdapterState.STARTING)
    adapter._transition(AdapterState.INITIALIZING)
    adapter._transition(AdapterState.FAILED)
    adapter._transition(AdapterState.STOPPED)

    assert adapter.state is AdapterState.STOPPED


def test_valid_stop_transitions_from_active_states() -> None:
    for active_state in (
        AdapterState.STARTING,
        AdapterState.INITIALIZING,
        AdapterState.READY,
        AdapterState.FAILED,
    ):
        adapter = CodexAppServerAdapter()
        adapter._transition(AdapterState.STARTING)
        if active_state is AdapterState.INITIALIZING:
            adapter._transition(active_state)
        elif active_state is AdapterState.READY:
            adapter._transition(AdapterState.INITIALIZING)
            adapter._transition(active_state)
        elif active_state is AdapterState.FAILED:
            adapter._transition(active_state)
        adapter._transition(AdapterState.STOPPED)
        assert adapter.state is AdapterState.STOPPED


def test_invalid_and_repeated_transitions_are_controlled() -> None:
    adapter = CodexAppServerAdapter()

    with pytest.raises(AdapterStateError):
        adapter._transition(AdapterState.READY)
    adapter._transition(AdapterState.STARTING)
    with pytest.raises(AdapterStateError):
        adapter._transition(AdapterState.STARTING)
    assert adapter.state is AdapterState.STARTING


def test_requests_are_guarded_before_ready() -> None:
    for state in (
        AdapterState.STOPPED,
        AdapterState.STARTING,
        AdapterState.INITIALIZING,
        AdapterState.FAILED,
    ):
        adapter = CodexAppServerAdapter()
        if state is AdapterState.STARTING:
            adapter._transition(AdapterState.STARTING)
        elif state is AdapterState.INITIALIZING:
            adapter._transition(AdapterState.STARTING)
            adapter._transition(AdapterState.INITIALIZING)
        elif state is AdapterState.FAILED:
            adapter._transition(AdapterState.STARTING)
            adapter._transition(AdapterState.FAILED)
        with pytest.raises(AdapterStateError, match="not ready"):
            adapter._require_ready()


def test_initialize_failure_enters_failed_and_cleans_up() -> None:
    async def scenario() -> None:
        process = _FakeProcess()
        adapter = CodexAppServerAdapter(process)
        initialize = asyncio.create_task(adapter.initialize())
        await asyncio.sleep(0)
        await process.child.stdout.lines.put(
            (json.dumps({"id": 1, "result": {"privateFake": "do-not-leak"}}) + "\n").encode()
        )

        with pytest.raises(AdapterStateError) as error:
            await initialize
        assert "do-not-leak" not in str(error.value)
        assert adapter.state is AdapterState.FAILED
        assert process.stopped is True

    asyncio.run(scenario())


def test_read_account_uses_default_refresh_and_returns_dto() -> None:
    class FakeTransport:
        def __init__(self) -> None:
            self.calls = []

        async def request(self, method, params):
            self.calls.append((method, params))
            return {"requiresOpenaiAuth": False, "account": None}

    async def scenario() -> None:
        adapter = CodexAppServerAdapter()
        adapter._transition(AdapterState.STARTING)
        adapter._transition(AdapterState.INITIALIZING)
        adapter._transition(AdapterState.READY)
        transport = FakeTransport()
        adapter._transport = transport

        response = await adapter.read_account()

        assert isinstance(response, GetAccountResponse)
        assert transport.calls == [("account/read", {"refreshToken": False})]

    asyncio.run(scenario())


def test_read_account_invalid_response_is_generic() -> None:
    class FakeTransport:
        async def request(self, method, params):
            return {"requiresOpenaiAuth": "private-invalid-marker", "account": None}

    async def scenario() -> None:
        adapter = CodexAppServerAdapter()
        adapter._transition(AdapterState.STARTING)
        adapter._transition(AdapterState.INITIALIZING)
        adapter._transition(AdapterState.READY)
        adapter._transport = FakeTransport()

        with pytest.raises(ProcessCommunicationFailed) as error:
            await adapter.read_account()
        assert "private-invalid-marker" not in str(error.value)

    asyncio.run(scenario())


def test_read_account_preserves_transport_communication_error() -> None:
    sentinel = ProcessCommunicationFailed("transport unavailable")

    class FakeTransport:
        async def request(self, method, params):
            raise sentinel

    async def scenario() -> None:
        adapter = CodexAppServerAdapter()
        adapter._transition(AdapterState.STARTING)
        adapter._transition(AdapterState.INITIALIZING)
        adapter._transition(AdapterState.READY)
        adapter._transport = FakeTransport()

        with pytest.raises(ProcessCommunicationFailed) as error:
            await adapter.read_account()
        assert error.value is sentinel

    asyncio.run(scenario())


def test_start_login_uses_exact_method_and_params() -> None:
    class FakeTransport:
        def __init__(self) -> None:
            self.calls = []

        async def request(self, method, params):
            self.calls.append((method, params))
            return {
                "type": "chatgptDeviceCode",
                "loginId": "synthetic-id",
                "userCode": "synthetic-code",
                "verificationUrl": "https://example.invalid/verify",
            }

    async def scenario() -> None:
        adapter = CodexAppServerAdapter()
        adapter._transition(AdapterState.STARTING)
        adapter._transition(AdapterState.INITIALIZING)
        adapter._transition(AdapterState.READY)
        transport = FakeTransport()
        adapter._transport = transport
        response = await adapter.start_login()
        assert response.login_id == "synthetic-id"
        assert transport.calls == [("account/login/start", {"type": "chatgptDeviceCode"})]

    asyncio.run(scenario())


def test_start_login_invalid_response_is_sanitized() -> None:
    class FakeTransport:
        async def request(self, method, params):
            return {"type": "chatgptDeviceCode", "loginId": "private-marker"}

    async def scenario() -> None:
        adapter = CodexAppServerAdapter()
        adapter._transition(AdapterState.STARTING)
        adapter._transition(AdapterState.INITIALIZING)
        adapter._transition(AdapterState.READY)
        adapter._transport = FakeTransport()
        with pytest.raises(ProcessCommunicationFailed) as error:
            await adapter.start_login()
        assert "private-marker" not in str(error.value)

    asyncio.run(scenario())


def test_start_login_requires_ready_without_request() -> None:
    adapter = CodexAppServerAdapter()

    async def scenario() -> None:
        with pytest.raises(AdapterStateError, match="not ready"):
            await adapter.start_login()

    asyncio.run(scenario())


def test_start_login_preserves_transport_failure_identity() -> None:
    sentinel = ProcessCommunicationFailed("controlled login transport failure")

    class FakeTransport:
        async def request(self, method, params):
            raise sentinel

    async def scenario() -> None:
        adapter = CodexAppServerAdapter()
        adapter._transition(AdapterState.STARTING)
        adapter._transition(AdapterState.INITIALIZING)
        adapter._transition(AdapterState.READY)
        adapter._transport = FakeTransport()
        with pytest.raises(ProcessCommunicationFailed) as error:
            await adapter.start_login()
        assert error.value is sentinel

    asyncio.run(scenario())


def test_wait_login_completion_filters_and_correlates_notifications() -> None:
    class FakeTransport:
        def __init__(self) -> None:
            self.notifications = iter(
                [
                    {"method": "other/event", "params": {}},
                    {"method": "account/login/completed", "params": {"success": True, "loginId": "other"}},
                    {"method": "account/login/completed", "params": {"success": True}},
                ]
            )

        async def next_notification(self):
            return next(self.notifications)

    async def scenario() -> None:
        adapter = CodexAppServerAdapter()
        adapter._transition(AdapterState.STARTING)
        adapter._transition(AdapterState.INITIALIZING)
        adapter._transition(AdapterState.READY)
        adapter._transport = FakeTransport()
        result = await adapter.wait_login_completion("expected", timeout=0.2)
        assert result.success is True
        assert result.login_id is None

    asyncio.run(scenario())


def test_wait_login_completion_failure_dto_is_preserved_at_boundary() -> None:
    class FakeTransport:
        async def next_notification(self):
            return {"method": "account/login/completed", "params": {"success": False, "error": "private-marker"}}

    async def scenario() -> None:
        adapter = CodexAppServerAdapter()
        adapter._transition(AdapterState.STARTING)
        adapter._transition(AdapterState.INITIALIZING)
        adapter._transition(AdapterState.READY)
        adapter._transport = FakeTransport()
        result = await adapter.wait_login_completion("expected")
        assert result.success is False
        assert result.error == "private-marker"

    asyncio.run(scenario())


def test_wait_login_completion_timeout_is_bounded() -> None:
    class FakeTransport:
        async def next_notification(self):
            await asyncio.sleep(1)

    async def scenario() -> None:
        adapter = CodexAppServerAdapter()
        adapter._transition(AdapterState.STARTING)
        adapter._transition(AdapterState.INITIALIZING)
        adapter._transition(AdapterState.READY)
        adapter._transport = FakeTransport()
        with pytest.raises(ProcessCommunicationFailed, match="timed out"):
            await adapter.wait_login_completion("expected", timeout=0.01)

    asyncio.run(scenario())


def test_wait_login_completion_invalid_params_are_sanitized() -> None:
    class FakeTransport:
        async def next_notification(self):
            return {
                "method": "account/login/completed",
                "params": {"success": "private-marker"},
            }

    async def scenario() -> None:
        adapter = CodexAppServerAdapter()
        adapter._transition(AdapterState.STARTING)
        adapter._transition(AdapterState.INITIALIZING)
        adapter._transition(AdapterState.READY)
        adapter._transport = FakeTransport()
        with pytest.raises(ProcessCommunicationFailed) as error:
            await adapter.wait_login_completion("expected")
        assert "private-marker" not in str(error.value)

    asyncio.run(scenario())


def test_wait_login_completion_uses_one_overall_deadline() -> None:
    class FakeTransport:
        def __init__(self) -> None:
            self.calls = 0

        async def next_notification(self):
            self.calls += 1
            if self.calls == 1:
                return {"method": "unrelated", "params": {}}
            await asyncio.sleep(1)

    async def scenario() -> None:
        adapter = CodexAppServerAdapter()
        adapter._transition(AdapterState.STARTING)
        adapter._transition(AdapterState.INITIALIZING)
        adapter._transition(AdapterState.READY)
        transport = FakeTransport()
        adapter._transport = transport
        with pytest.raises(ProcessCommunicationFailed, match="timed out"):
            await adapter.wait_login_completion("expected", timeout=0.02)
        assert transport.calls == 2

    asyncio.run(scenario())


def test_wait_login_completion_preserves_transport_failure() -> None:
    sentinel = ProcessCommunicationFailed("completion transport failure")

    class FakeTransport:
        async def next_notification(self):
            raise sentinel

    async def scenario() -> None:
        adapter = CodexAppServerAdapter()
        adapter._transition(AdapterState.STARTING)
        adapter._transition(AdapterState.INITIALIZING)
        adapter._transition(AdapterState.READY)
        adapter._transport = FakeTransport()
        with pytest.raises(ProcessCommunicationFailed) as error:
            await adapter.wait_login_completion("expected")
        assert error.value is sentinel

    asyncio.run(scenario())


def test_wait_login_completion_requires_ready_without_consuming_notification() -> None:
    class FakeTransport:
        def __init__(self) -> None:
            self.consumed = False

        async def next_notification(self):
            self.consumed = True
            return {"method": "account/login/completed", "params": {"success": True}}

    async def scenario() -> None:
        adapter = CodexAppServerAdapter()
        transport = FakeTransport()
        adapter._transport = transport
        with pytest.raises(AdapterStateError, match="not ready"):
            await adapter.wait_login_completion("expected")
        assert transport.consumed is False

    asyncio.run(scenario())


def test_wait_login_completion_rejects_non_positive_timeout() -> None:
    async def scenario() -> None:
        adapter = CodexAppServerAdapter()
        adapter._transition(AdapterState.STARTING)
        adapter._transition(AdapterState.INITIALIZING)
        adapter._transition(AdapterState.READY)
        adapter._transport = object()
        with pytest.raises(ValueError, match="positive"):
            await adapter.wait_login_completion("expected", timeout=0)

    asyncio.run(scenario())
