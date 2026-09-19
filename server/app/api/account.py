"""Authenticated account-status REST endpoint."""

from typing import Any

from fastapi import APIRouter, Depends, Request

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

    @router.get("/account")
    async def account(request: Request) -> dict[str, Any]:
        """Return one AccountService result without protocol metadata."""

        service: AccountService = request.app.state.account_service
        return serialize_account(await service.get_status())

    return router
