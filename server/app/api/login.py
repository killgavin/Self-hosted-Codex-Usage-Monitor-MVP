"""Minimal login REST routes over the application AuthService boundary."""

from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.codex.exceptions import AdapterStateError, ProcessCommunicationFailed
from app.services.auth import (
    AuthService,
    LoginAlreadyPending,
    LoginCancellationFailed,
    LoginNotPending,
    LoginStatus,
)


router = APIRouter(prefix="/api/v1", tags=["login"])


def serialize_status(status: LoginStatus) -> dict[str, Any]:
    """Serialize only the stable, UI-safe login response fields."""

    return {
        "state": status.state.value,
        "verificationUrl": status.verification_url,
        "userCode": status.user_code,
    }


def error_response(error: Exception) -> JSONResponse:
    """Map known failures to fixed sanitized REST errors."""

    if isinstance(error, LoginAlreadyPending):
        code, message, status = "CODEX_LOGIN_PENDING", "Login is already pending", 409
    elif isinstance(error, LoginNotPending):
        code, message, status = "CODEX_NOT_AUTHENTICATED", "Login is not pending", 409
    elif isinstance(error, LoginCancellationFailed):
        code, message, status = "CODEX_PROTOCOL_ERROR", "Login cancellation failed", 502
    elif isinstance(error, AdapterStateError):
        code, message, status = "UPSTREAM_UNAVAILABLE", "Codex is unavailable", 503
    elif isinstance(error, ProcessCommunicationFailed):
        code, message, status = "CODEX_PROTOCOL_ERROR", "Codex protocol error", 502
    else:
        code, message, status = "INTERNAL_ERROR", "Internal error", 500
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


def _service(request: Request) -> AuthService:
    """Return the request application's injected authentication service."""

    return request.app.state.auth_service


async def _call(request: Request, operation: Callable[[AuthService], Awaitable[LoginStatus]]) -> JSONResponse:
    """Invoke one service operation and map failures to the REST envelope."""

    try:
        return JSONResponse(serialize_status(await operation(_service(request))))
    except Exception as error:
        return error_response(error)


@router.post("/login")
async def login(request: Request) -> JSONResponse:
    """Start a device-code login."""

    return await _call(request, lambda service: service.start_login())


@router.get("/login/status")
async def login_status(request: Request) -> JSONResponse:
    """Return current login status with a bounded completion poll."""

    return await _call(request, lambda service: service.get_status(wait_timeout=0.05))


@router.post("/login/cancel")
async def login_cancel(request: Request) -> JSONResponse:
    """Cancel the current pending device-code login."""

    return await _call(request, lambda service: service.cancel_login())


@router.post("/logout")
async def logout(request: Request) -> JSONResponse:
    """Log out through the authentication service."""

    return await _call(request, lambda service: service.logout())
