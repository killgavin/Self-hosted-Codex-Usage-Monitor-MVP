"""Authenticated rate-limit REST endpoint and stable serializers."""

from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, Request

from app.models.rate_limit import RateLimit, RateLimitWindow, ResetCredit, ResetCredits
from app.security.server_token import ServerTokenAuth
from app.services.rate_limits import RateLimitService


def _decimal_text(value: Decimal) -> str:
    """Preserve decimal precision without binary JSON-number conversion."""

    return format(value, "f")


def serialize_window(window: RateLimitWindow | None) -> dict[str, Any] | None:
    if window is None:
        return None
    return {
        "usedPercent": _decimal_text(window.used_percent),
        "remainingPercent": _decimal_text(window.remaining_percent),
        "windowDurationMinutes": window.window_duration_minutes,
        "resetAt": window.reset_at,
    }


def serialize_limit(limit: RateLimit) -> dict[str, Any]:
    """Serialize canonical fields while excluding compatibility metadata."""

    return {
        "id": limit.id,
        "name": limit.name,
        "primary": serialize_window(limit.primary),
        "secondary": serialize_window(limit.secondary),
        "reachedType": limit.reached_type,
    }


def serialize_credit(credit: ResetCredit) -> dict[str, Any]:
    return {
        "id": credit.id,
        "status": credit.status,
        "grantedAt": credit.granted_at,
        "expiresAt": credit.expires_at,
        "title": credit.title,
        "description": credit.description,
    }


def serialize_reset_credits(reset: ResetCredits | None) -> dict[str, Any] | None:
    if reset is None:
        return None
    return {
        "availableCount": reset.available_count,
        "credits": (
            None
            if reset.credits is None
            else [serialize_credit(credit) for credit in reset.credits]
        ),
    }


def create_rate_limits_router(server_api_token: str | None) -> APIRouter:
    """Build the rate-limit router with its monitor-token boundary."""

    router = APIRouter(
        prefix="/api/v1",
        tags=["rate-limits"],
        dependencies=[Depends(ServerTokenAuth(server_api_token))],
    )

    @router.get("/rate-limits")
    async def rate_limits(request: Request) -> dict[str, Any]:
        service: RateLimitService = request.app.state.rate_limit_service
        limits, reset_credits = await service.get_rate_limits()
        return {
            "limits": [serialize_limit(limit) for limit in limits],
            "resetCredits": serialize_reset_credits(reset_credits),
        }

    return router
