"""Local login state plus typed device-code start/completion orchestration.

The service exposes only UI-safe state and delegates device-code lifecycle
operations to an injected adapter.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from app.codex.protocol import (
    AccountLoginCompletedNotification,
    CancelLoginResponse,
    DeviceCodeLoginResponse,
)


class LoginState(str, Enum):
    """Local application states for the future login UI lifecycle."""

    IDLE = "IDLE"
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"


@dataclass(frozen=True)
class LoginStatus:
    """Immutable UI-safe login snapshot with no secret-bearing fields."""

    state: LoginState
    login_id: str | None = None
    verification_url: str | None = None
    user_code: str | None = None


class LoginAlreadyPending(Exception):
    """A login start was requested while another login is pending."""


class LoginNotPending(Exception):
    """A login operation was requested without a pending login."""


class LoginCancellationFailed(Exception):
    """The Codex server did not confirm cancellation of a pending login."""


class LoginStarter(Protocol):
    """Minimal injected adapter boundary for the login lifecycle."""

    async def start_login(self) -> DeviceCodeLoginResponse:
        """Start device-code login through the adapter."""

    async def wait_login_completion(
        self, login_id: str, timeout: float = 10.0
    ) -> AccountLoginCompletedNotification:
        """Wait for the correlated completion notification."""

    async def cancel_login(self, login_id: str) -> CancelLoginResponse:
        """Cancel one pending login and return its typed protocol response."""


class AuthService:
    """Expose immutable local state and device-code login operations."""

    def __init__(self, adapter: LoginStarter) -> None:
        self._status = LoginStatus(state=LoginState.IDLE)
        self._adapter = adapter

    @property
    def status(self) -> LoginStatus:
        """Return the current immutable status snapshot read-only."""

        return self._status

    async def start_login(self) -> LoginStatus:
        """Start device-code login and atomically publish a pending snapshot."""

        if self._status.state is LoginState.PENDING:
            raise LoginAlreadyPending("Login is already pending")
        response = await self._adapter.start_login()
        self._status = LoginStatus(
            state=LoginState.PENDING,
            login_id=response.login_id,
            verification_url=response.verification_url,
            user_code=response.user_code,
        )
        return self._status

    async def wait_for_completion(self, timeout: float = 10.0) -> LoginStatus:
        """Apply a correlated completion to the local pending snapshot."""

        if self._status.state is not LoginState.PENDING or self._status.login_id is None:
            raise LoginNotPending("Login is not pending")
        completion = await self._adapter.wait_login_completion(self._status.login_id, timeout)
        self._status = LoginStatus(
            state=LoginState.COMPLETED if completion.success else LoginState.FAILED
        )
        return self._status

    async def cancel_login(self) -> LoginStatus:
        """Cancel the pending login, publishing CANCELED only on exact success."""

        if self._status.state is not LoginState.PENDING or self._status.login_id is None:
            raise LoginNotPending("Login is not pending")
        response = await self._adapter.cancel_login(self._status.login_id)
        if response.status != "canceled":
            raise LoginCancellationFailed("Login cancellation failed")
        self._status = LoginStatus(state=LoginState.CANCELED)
        return self._status
