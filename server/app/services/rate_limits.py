"""Minimal typed rate-limit read orchestration."""

from typing import Protocol, TypeAlias

from app.codex.protocol import GetAccountRateLimitsResponse
from app.codex.rate_limit_mapper import map_rate_limits_response
from app.models.rate_limit import RateLimit, ResetCredits


RateLimitResult: TypeAlias = tuple[tuple[RateLimit, ...], ResetCredits | None]


class RateLimitReader(Protocol):
    """Injected typed boundary for one official rate-limit read."""

    async def read_rate_limits(self) -> GetAccountRateLimitsResponse:
        """Read one typed response without lifecycle or retry behavior."""


class RateLimitService:
    """Read and map rate limits exactly once per service call."""

    def __init__(self, reader: RateLimitReader) -> None:
        self._reader = reader

    async def get_rate_limits(self) -> RateLimitResult:
        """Return the immutable mapped result, propagating controlled failures."""

        response = await self._reader.read_rate_limits()
        return map_rate_limits_response(response)
