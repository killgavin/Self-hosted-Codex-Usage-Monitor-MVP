"""Automated tests for the Codex adapter lifecycle state guard."""

import pytest

from app.codex.adapter import AdapterState, CodexAppServerAdapter
from app.codex.exceptions import AdapterStateError


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
