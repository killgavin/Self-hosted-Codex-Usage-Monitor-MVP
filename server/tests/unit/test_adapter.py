"""Automated tests for the Codex adapter lifecycle boundary."""

import asyncio
import json

import pytest

from app.codex.adapter import AdapterState, CodexAppServerAdapter
from app.codex.exceptions import AdapterStateError


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
