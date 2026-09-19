"""Deterministic T-21 through T-24 coverage for the rate-limit TTL cache."""

import asyncio
from dataclasses import FrozenInstanceError

import pytest

from app.codex.protocol import GetAccountRateLimitsResponse, RateLimitSnapshotProtocol
from app.config import DEFAULT_CACHE_TTL_SECONDS, Settings
from app.services.rate_limits import RateLimitService


class FakeClock:
    def __init__(self) -> None:
        self.now = 100.0

    def __call__(self) -> float:
        return self.now


class FakeReader:
    def __init__(self) -> None:
        self.calls = 0

    async def read_rate_limits(self) -> GetAccountRateLimitsResponse:
        self.calls += 1
        return GetAccountRateLimitsResponse(
            rateLimits=RateLimitSnapshotProtocol(limitId=f"limit-{self.calls}")
        )


def test_cache_miss_reads_once_and_populates() -> None:
    async def scenario() -> None:
        reader = FakeReader()
        service = RateLimitService(reader, ttl_seconds=60, clock=FakeClock())

        result = await service.get_rate_limits()

        assert reader.calls == 1
        assert result[0][0].id == "limit-1"
        assert service._cached is result

    asyncio.run(scenario())


def test_cache_hit_does_not_call_reader() -> None:
    async def scenario() -> None:
        reader = FakeReader()
        service = RateLimitService(reader, ttl_seconds=60, clock=FakeClock())
        first = await service.get_rate_limits()

        second = await service.get_rate_limits()

        assert second is first
        assert reader.calls == 1

    asyncio.run(scenario())


def test_expired_cache_refreshes_once() -> None:
    async def scenario() -> None:
        clock = FakeClock()
        reader = FakeReader()
        service = RateLimitService(reader, ttl_seconds=60, clock=clock)
        first = await service.get_rate_limits()
        clock.now += 60

        second = await service.get_rate_limits()

        assert reader.calls == 2
        assert first[0][0].id == "limit-1"
        assert second[0][0].id == "limit-2"
        assert service._cached is second

    asyncio.run(scenario())


def test_cached_domain_data_remains_immutable_and_unchanged() -> None:
    async def scenario() -> None:
        reader = FakeReader()
        service = RateLimitService(reader, ttl_seconds=60, clock=FakeClock())
        first = await service.get_rate_limits()
        second = await service.get_rate_limits()

        assert second is first
        assert isinstance(second[0], tuple)
        with pytest.raises(FrozenInstanceError):
            second[0][0].id = "changed"
        assert first[0][0].id == "limit-1"

    asyncio.run(scenario())


def test_cache_ttl_configuration_default_and_override(monkeypatch) -> None:
    monkeypatch.delenv("CACHE_TTL_SECONDS", raising=False)
    assert Settings.from_environment().cache_ttl_seconds == DEFAULT_CACHE_TTL_SECONDS

    monkeypatch.setenv("CACHE_TTL_SECONDS", "12.5")
    assert Settings.from_environment().cache_ttl_seconds == 12.5


@pytest.mark.parametrize("value", ("0", "-1", "nan", "inf", "invalid"))
def test_invalid_cache_ttl_configuration_is_rejected(monkeypatch, value: str) -> None:
    monkeypatch.setenv("CACHE_TTL_SECONDS", value)

    with pytest.raises(ValueError, match="positive finite"):
        Settings.from_environment()
