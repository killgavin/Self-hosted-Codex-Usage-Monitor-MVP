"""Minimal login REST routes over the application AuthService boundary."""

from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.api.errors import error_response
from app.services.auth import (
    AuthService,
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
