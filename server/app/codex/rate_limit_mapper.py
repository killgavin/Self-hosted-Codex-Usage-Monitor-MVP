"""Pure mapping from rate-limit protocol DTOs into immutable domain models."""

from app.codex.protocol import (
    GetAccountRateLimitsResponse,
    RateLimitResetCreditProtocol,
    RateLimitResetCreditsProtocol,
    RateLimitSnapshotProtocol,
    RateLimitWindowProtocol,
)
from app.models.rate_limit import RateLimit, RateLimitWindow, ResetCredit, ResetCredits


def map_rate_limit_window(dto: RateLimitWindowProtocol) -> RateLimitWindow:
    """Map one wire window; the domain computes and clamps remaining percent."""

    return RateLimitWindow.from_values(
        dto.used_percent,
        window_duration_minutes=dto.window_duration_minutes,
        reset_at=dto.resets_at,
    )


def map_rate_limit_snapshot(
    dto: RateLimitSnapshotProtocol,
    fallback_id: str | None = None,
) -> RateLimit:
    """Map one generic snapshot, retaining only its internal unknown extras."""

    raw_metadata = dict(dto.model_extra) if dto.model_extra else None
    return RateLimit(
        id=dto.limit_id if dto.limit_id is not None else fallback_id,
        name=dto.limit_name,
        primary=map_rate_limit_window(dto.primary) if dto.primary is not None else None,
        secondary=map_rate_limit_window(dto.secondary) if dto.secondary is not None else None,
        reached_type=dto.rate_limit_reached_type,
        raw_metadata=raw_metadata,
    )


def map_reset_credit(dto: RateLimitResetCreditProtocol) -> ResetCredit:
    """Map canonical reset-credit fields, intentionally omitting resetType."""

    return ResetCredit(
        id=dto.id,
        status=dto.status,
        granted_at=dto.granted_at,
        expires_at=dto.expires_at,
        title=dto.title,
        description=dto.description,
    )


def map_reset_credits(dto: RateLimitResetCreditsProtocol | None) -> ResetCredits | None:
    """Map an optional summary while preserving null versus empty details."""

    if dto is None:
        return None
    credits = (
        None
        if dto.credits is None
        else tuple(map_reset_credit(item) for item in dto.credits)
    )
    return ResetCredits(available_count=dto.available_count, credits=credits)


def map_rate_limits_response(
    dto: GetAccountRateLimitsResponse,
) -> tuple[tuple[RateLimit, ...], ResetCredits | None]:
    """Map keyed buckets in insertion order, or the single legacy bucket once."""

    if dto.rate_limits_by_limit_id:
        limits = tuple(
            map_rate_limit_snapshot(snapshot, fallback_id=key)
            for key, snapshot in dto.rate_limits_by_limit_id.items()
        )
    else:
        limits = (map_rate_limit_snapshot(dto.rate_limits),)
    return limits, map_reset_credits(dto.rate_limit_reset_credits)
