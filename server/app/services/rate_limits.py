"""Typed rate-limit read orchestration with a bounded in-memory TTL cache."""

import math
import time
from collections.abc import Callable
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
    """Read, map, and briefly cache immutable rate-limit domain results."""

    def __init__(
        self,
        reader: RateLimitReader,
        ttl_seconds: float = 60.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if not math.isfinite(ttl_seconds) or ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be a positive finite number")
        self._reader = reader
        self._ttl_seconds = ttl_seconds
        self._clock = clock
        self._cached: RateLimitResult | None = None
        self._expires_at = 0.0

    async def get_rate_limits(self) -> RateLimitResult:
        """Return an unexpired result or populate the cache after one read."""

        if self._cached is not None and self._clock() < self._expires_at:
            return self._cached
        response = await self._reader.read_rate_limits()
        result = map_rate_limits_response(response)
        self._cached = result
        self._expires_at = self._clock() + self._ttl_seconds
        return result
