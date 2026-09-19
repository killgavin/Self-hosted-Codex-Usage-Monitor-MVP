"""Authenticated account-status REST endpoint."""

from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from app.api.errors import error_response
from app.models.account import AccountStatus
from app.security.server_token import ServerTokenAuth
from app.services.account import AccountService


def serialize_account(status: AccountStatus) -> dict[str, Any]:
    """Expose only the stable credential-free account contract."""

    return {
        "authenticated": status.authenticated,
        "authMode": status.auth_mode,
        "planType": status.plan_type,
    }


def create_account_router(server_api_token: str | None) -> APIRouter:
    """Build the account router with its monitor-token boundary."""

    router = APIRouter(
        prefix="/api/v1",
        tags=["account"],
        dependencies=[Depends(ServerTokenAuth(server_api_token))],
    )

    @router.get("/account", response_model=None)
    async def account(request: Request) -> dict[str, Any] | JSONResponse:
        """Return one AccountService result without protocol metadata."""

        service: AccountService = request.app.state.account_service
        try:
            return serialize_account(await service.get_status())
        except Exception as error:
            return error_response(error)

    return router
