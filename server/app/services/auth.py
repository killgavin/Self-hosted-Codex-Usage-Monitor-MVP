"""Minimal local authentication lifecycle state representation.

This module deliberately contains no upstream protocol, adapter, credential,
token, or transition behavior; later tasks own login operations.
"""

from dataclasses import dataclass
from enum import Enum


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


class AuthService:
    """Expose the initial immutable local login status only."""

    def __init__(self) -> None:
        self._status = LoginStatus(state=LoginState.IDLE)

    @property
    def status(self) -> LoginStatus:
        """Return the current immutable status snapshot read-only."""

        return self._status
