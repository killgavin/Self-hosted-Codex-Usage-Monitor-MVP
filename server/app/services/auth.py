"""Local login state plus typed device-code start orchestration.

The service exposes only UI-safe state and delegates device-code start to an
injected adapter. Completion and cancellation remain deferred.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from app.codex.protocol import DeviceCodeLoginResponse


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


class LoginStarter(Protocol):
    """Minimal injected adapter boundary for login start."""

    async def start_login(self) -> DeviceCodeLoginResponse:
        """Start device-code login through the adapter."""


class AuthService:
    """Expose immutable local state and the device-code start operation."""

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
