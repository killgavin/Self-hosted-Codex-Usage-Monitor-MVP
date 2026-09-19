"""Privacy-safe real Codex rate-limit validation."""

import asyncio
import os
from decimal import Decimal

import pytest

from app.config import Settings
from app.codex.adapter import AdapterState, CodexAppServerAdapter
from app.codex.process import CodexProcess
from app.codex.rate_limit_mapper import map_rate_limits_response
from app.models.rate_limit import RateLimit, RateLimitWindow, ResetCredits
from app.services.rate_limits import RateLimitService


def _executable() -> str:
    executable = os.environ.get("REAL_CODEX_EXECUTABLE")
    if not executable:
        raise AssertionError("REAL_CODEX_EXECUTABLE is required")
    return executable


def test_real_rate_limits_read() -> None:
    executable = _executable()

    async def scenario() -> None:
        process = CodexProcess(Settings(executable))
        adapter = CodexAppServerAdapter(process)
        child = None
        try:
            await adapter.initialize()
            child = process.process
            result = await RateLimitService(adapter).get_rate_limits()
            assert adapter.state is AdapterState.READY
            limits, reset_credits = result
            assert limits
            assert all(isinstance(limit, RateLimit) for limit in limits)
            assert all(
                window is None or isinstance(window, RateLimitWindow)
                for limit in limits
                for window in (limit.primary, limit.secondary)
            )
            assert all(
                isinstance(window.used_percent, Decimal) and window.used_percent.is_finite()
                and Decimal("0") <= window.remaining_percent <= Decimal("100")
                for limit in limits
                for window in (limit.primary, limit.secondary)
                if window is not None
            )
            assert reset_credits is None or isinstance(reset_credits, ResetCredits)
        finally:
            await adapter.shutdown()
        assert adapter.state is AdapterState.STOPPED
        assert process.process is None
        assert child is not None and child.returncode is not None

    asyncio.run(scenario())


def test_real_multiple_rate_limits_when_available() -> None:
    executable = _executable()

    async def scenario() -> None:
        process = CodexProcess(Settings(executable))
        adapter = CodexAppServerAdapter(process)
        child = None
        try:
            await adapter.initialize()
            child = process.process
            response = await adapter.read_rate_limits()
            keyed = response.rate_limits_by_limit_id
            if keyed is None or len(keyed) <= 1:
                pytest.skip("current account does not expose multiple keyed rate-limit buckets")
            mapped, _ = map_rate_limits_response(response)
            assert len(mapped) == len(keyed)
            assert [limit.id for limit in mapped] == [
                snapshot.limit_id or key for key, snapshot in keyed.items()
            ]
        finally:
            await adapter.shutdown()
        assert adapter.state is AdapterState.STOPPED
        assert process.process is None
        assert child is not None and child.returncode is not None

    asyncio.run(scenario())
