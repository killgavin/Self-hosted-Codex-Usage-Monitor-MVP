"""Codex app-server lifecycle and initialization boundary.

This module owns process startup, the initialize/initialized handshake,
adapter state transitions, account reads, and device-code login lifecycle.
Rate-limit reads are exposed through the typed app-server boundary.
"""

import asyncio
import time
from enum import Enum

from app.codex.process import CodexProcess
from app.codex.exceptions import (
    AdapterStateError,
    LoginCompletionTimeout,
    ProcessExited,
    ProcessCommunicationFailed,
)
from app.codex.protocol import (
    ClientInfo,
    AccountLoginCompletedNotification,
    CancelLoginParams,
    CancelLoginResponse,
    DeviceCodeLoginParams,
    DeviceCodeLoginResponse,
    GetAccountParams,
    GetAccountRateLimitsResponse,
    GetAccountResponse,
    InitializeParams,
    InitializeResponse,
    LogoutAccountResponse,
    to_wire,
)
from app.codex.transport import CodexTransport
from pydantic import ValidationError


DEVICE_CODE_LOGIN_START_TIMEOUT = 30.0


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
    """Own the Codex lifecycle and initialization method boundary."""

    def __init__(self, process: CodexProcess | None = None) -> None:
        self._state = AdapterState.STOPPED
        self._process = process if process is not None else CodexProcess()
        self._transport: CodexTransport | None = None

    @property
    def state(self) -> AdapterState:
        """Read-only current lifecycle state."""

        return self._state

    async def initialize(self) -> InitializeResponse:
        """Start, initialize, and mark the adapter ready after ``initialized``."""

        if self._state not in {AdapterState.STOPPED, AdapterState.FAILED}:
            raise AdapterStateError("Codex adapter is not ready to initialize")
        self._transition(AdapterState.STARTING)
        try:
            await self._process.start()
            self._transport = CodexTransport(self._process)
            self._transition(AdapterState.INITIALIZING)
            params = InitializeParams(
                clientInfo=ClientInfo(
                    name="self-hosted-codex-usage-monitor",
                    version="0.1",
                )
            )
            result = await self._transport.request("initialize", to_wire(params))
            response = InitializeResponse.model_validate(result)
            await self._transport.send_notification("initialized")
            self._transition(AdapterState.READY)
            return response
        except Exception as exc:
            self._transition(AdapterState.FAILED)
            await self._cleanup_resources()
            raise AdapterStateError("Codex initialize failed") from exc

    async def shutdown(self) -> None:
        """Boundedly close transport and stop the child, returning to STOPPED."""

        try:
            await self._cleanup_resources()
        finally:
            if self._state is not AdapterState.STOPPED:
                self._transition(AdapterState.STOPPED)

    async def read_account(self, refresh_token: bool = False) -> GetAccountResponse:
        """Read account status through the ready Codex protocol boundary."""

        self._require_ready()
        if self._transport is None:
            raise AdapterStateError("Codex adapter transport is unavailable")
        try:
            result = await self._transport.request(
                "account/read",
                to_wire(GetAccountParams(refresh_token=refresh_token)),
            )
        except ProcessCommunicationFailed:
            raise
        try:
            return GetAccountResponse.model_validate(result)
        except ValidationError:
            raise ProcessCommunicationFailed("Codex account response validation failed") from None

    async def read_rate_limits(self) -> GetAccountRateLimitsResponse:
        """Read rate limits through the ready official Codex boundary."""

        self._require_ready()
        if self._transport is None:
            raise AdapterStateError("Codex adapter transport is unavailable")
        try:
            result = await self._transport.request("account/rateLimits/read")
        except ProcessCommunicationFailed:
            raise
        try:
            return GetAccountRateLimitsResponse.model_validate(result)
        except ValidationError:
            raise ProcessCommunicationFailed("Codex rate limits response validation failed") from None

    async def start_login(self) -> DeviceCodeLoginResponse:
        """Start the supported device-code login flow after initialization."""

        self._require_ready()
        if self._transport is None:
            raise AdapterStateError("Codex adapter transport is unavailable")
        try:
            result = await self._transport.request(
                "account/login/start",
                to_wire(DeviceCodeLoginParams()),
                timeout=DEVICE_CODE_LOGIN_START_TIMEOUT,
            )
        except ProcessCommunicationFailed:
            raise
        try:
            return DeviceCodeLoginResponse.model_validate(result)
        except ValidationError:
            raise ProcessCommunicationFailed("Codex login response validation failed") from None

    async def wait_login_completion(
        self, login_id: str, timeout: float = 10.0
    ) -> AccountLoginCompletedNotification:
        """Wait for one correlated completion notification within one deadline."""

        self._require_ready()
        if self._transport is None:
            raise AdapterStateError("Codex adapter transport is unavailable")
        if timeout <= 0:
            raise ValueError("login completion timeout must be positive")
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise LoginCompletionTimeout("Codex login completion timed out")
            try:
                notification = await asyncio.wait_for(
                    self._transport.next_notification(), remaining
                )
            except asyncio.TimeoutError as exc:
                raise LoginCompletionTimeout("Codex login completion timed out") from exc
            if notification.get("method") != "account/login/completed":
                continue
            try:
                params = AccountLoginCompletedNotification.model_validate(
                    notification.get("params", {})
                )
            except ValidationError:
                raise ProcessCommunicationFailed(
                    "Codex login completion was invalid"
                ) from None
            if params.login_id is not None and params.login_id != login_id:
                continue
            return params

    async def cancel_login(self, login_id: str) -> CancelLoginResponse:
        """Cancel one pending device-code login through the ready boundary."""

        self._require_ready()
        if self._transport is None:
            raise AdapterStateError("Codex adapter transport is unavailable")
        try:
            result = await self._transport.request(
                "account/login/cancel",
                to_wire(CancelLoginParams(loginId=login_id)),
            )
        except ProcessCommunicationFailed:
            raise
        try:
            return CancelLoginResponse.model_validate(result)
        except ValidationError:
            raise ProcessCommunicationFailed("Codex login cancellation response validation failed") from None

    async def logout(self) -> LogoutAccountResponse:
        """Log out through the ready Codex protocol boundary."""

        self._require_ready()
        if self._transport is None:
            raise AdapterStateError("Codex adapter transport is unavailable")
        try:
            result = await self._transport.request("account/logout")
        except ProcessCommunicationFailed:
            raise
        try:
            return LogoutAccountResponse.model_validate(result)
        except ValidationError:
            raise ProcessCommunicationFailed("Codex logout response validation failed") from None

    def _require_ready(self) -> None:
        """Guard future adapter requests until initialization completed."""

        if self._state is not AdapterState.READY:
            raise AdapterStateError("Codex adapter is not ready")
        # A child may exit after the initialize handshake.  Detect that
        # condition at the process boundary before writing any protocol data,
        # while retaining the canonical adapter state machine.
        try:
            self._ensure_process_alive()
        except ProcessExited:
            self._transition(AdapterState.FAILED)
            raise

    def is_available(self) -> bool:
        """Return whether a ready adapter still has a live child process.

        The application lifespan gates calls to this method for request-only
        ASGI tests.  At the adapter boundary only READY with a live child is
        available; all other canonical states are unavailable.
        """

        if self._state is not AdapterState.READY:
            return False
        # READY without a child handle is not an available runtime.  This
        # also keeps injected process boundaries honest while request-only
        # ASGI tests remain gated by application.state.runtime_started.
        if getattr(self._process, "process", None) is None:
            return False
        try:
            self._ensure_process_alive()
        except ProcessExited:
            self._transition(AdapterState.FAILED)
            return False
        return True

    def _ensure_process_alive(self) -> None:
        """Normalize the production and injected process liveness contracts."""

        ensure_alive = getattr(self._process, "ensure_alive", None)
        if callable(ensure_alive):
            ensure_alive()
            return
        is_alive = getattr(self._process, "is_alive", None)
        if callable(is_alive):
            is_alive = is_alive()
        if is_alive is False:
            raise ProcessExited("Codex app-server process exited")

    def _transition(self, target: AdapterState) -> None:
        """Apply one explicitly allowed transition or raise a state error."""

        if target not in _ALLOWED_TRANSITIONS[self._state]:
            raise AdapterStateError("Invalid Codex adapter state transition")
        self._state = target

    async def _cleanup_resources(self) -> None:
        transport = self._transport
        self._transport = None
        if transport is not None:
            await transport.close()
        await self._process.stop()
