"""Lifecycle state boundary for the Codex app-server adapter.

This task defines state and transition guards only. Process startup,
initialization, and protocol method calls are intentionally deferred.
"""

from enum import Enum

from app.codex.exceptions import AdapterStateError


class AdapterState(str, Enum):
    """Canonical lifecycle states for the single Codex method boundary."""

    STOPPED = "STOPPED"
    STARTING = "STARTING"
    INITIALIZING = "INITIALIZING"
    READY = "READY"
    FAILED = "FAILED"


_ALLOWED_TRANSITIONS: dict[AdapterState, frozenset[AdapterState]] = {
    AdapterState.STOPPED: frozenset({AdapterState.STARTING}),
    AdapterState.STARTING: frozenset(
        {AdapterState.INITIALIZING, AdapterState.FAILED, AdapterState.STOPPED}
    ),
    AdapterState.INITIALIZING: frozenset(
        {AdapterState.READY, AdapterState.FAILED, AdapterState.STOPPED}
    ),
    AdapterState.READY: frozenset({AdapterState.FAILED, AdapterState.STOPPED}),
    AdapterState.FAILED: frozenset({AdapterState.STARTING, AdapterState.STOPPED}),
}


class CodexAppServerAdapter:
    """Hold adapter lifecycle state with a private guarded transition primitive."""

    def __init__(self) -> None:
        self._state = AdapterState.STOPPED

    @property
    def state(self) -> AdapterState:
        """Read-only current lifecycle state."""

        return self._state

    def _transition(self, target: AdapterState) -> None:
        """Apply one explicitly allowed transition or raise a state error."""

        if target not in _ALLOWED_TRANSITIONS[self._state]:
            raise AdapterStateError("Invalid Codex adapter state transition")
        self._state = target
