"""Synthetic adapter and service tests for TASK-0506."""

import asyncio

import pytest

from app.codex.adapter import AdapterState, CodexAppServerAdapter
from app.codex.exceptions import AdapterStateError, ProcessCommunicationFailed
from app.codex.protocol import GetAccountRateLimitsResponse, RateLimitSnapshotProtocol
from app.services.rate_limits import RateLimitService


def _ready_adapter() -> CodexAppServerAdapter:
    adapter = CodexAppServerAdapter()
    adapter._transition(AdapterState.STARTING)
    adapter._transition(AdapterState.INITIALIZING)
    adapter._transition(AdapterState.READY)
    return adapter


def test_adapter_read_rate_limits_exact_method_without_params() -> None:
    class FakeTransport:
        def __init__(self):
            self.calls = []

        async def request(self, *args, **kwargs):
            self.calls.append((args, kwargs))
            return {"rateLimits": {"limitId": "synthetic"}}

    async def scenario() -> None:
        adapter = _ready_adapter()
        transport = FakeTransport()
        adapter._transport = transport
        response = await adapter.read_rate_limits()
        assert response.rate_limits.limit_id == "synthetic"
        assert transport.calls == [(("account/rateLimits/read",), {})]

    asyncio.run(scenario())


def test_adapter_read_rate_limits_ready_guard_and_no_request() -> None:
    adapter = CodexAppServerAdapter()

    async def scenario() -> None:
        class CountingTransport:
            calls = 0

            async def request(self, *args, **kwargs):
                self.calls += 1

        transport = CountingTransport()
        adapter._transport = transport
        with pytest.raises(AdapterStateError, match="not ready"):
            await adapter.read_rate_limits()
        assert transport.calls == 0

    asyncio.run(scenario())


def test_adapter_read_rate_limits_ready_without_transport_is_controlled() -> None:
    adapter = _ready_adapter()

    async def scenario() -> None:
        with pytest.raises(AdapterStateError, match="transport"):
            await adapter.read_rate_limits()

    asyncio.run(scenario())


def test_adapter_read_rate_limits_invalid_response_is_sanitized() -> None:
    class FakeTransport:
        async def request(self, *args, **kwargs):
            return {"private": "marker"}

    async def scenario() -> None:
        adapter = _ready_adapter()
        adapter._transport = FakeTransport()
        with pytest.raises(ProcessCommunicationFailed) as error:
            await adapter.read_rate_limits()
        assert "marker" not in str(error.value)

    asyncio.run(scenario())


def test_adapter_read_rate_limits_preserves_transport_identity() -> None:
    sentinel = ProcessCommunicationFailed("controlled read failure")

    class FakeTransport:
        async def request(self, *args, **kwargs):
            raise sentinel

    async def scenario() -> None:
        adapter = _ready_adapter()
        adapter._transport = FakeTransport()
        with pytest.raises(ProcessCommunicationFailed) as error:
            await adapter.read_rate_limits()
        assert error.value is sentinel

    asyncio.run(scenario())


class FakeReader:
    def __init__(self, response=None, failure=None):
        self.response = response
        self.failure = failure
        self.calls = 0

    async def read_rate_limits(self):
        self.calls += 1
        if self.failure is not None:
            raise self.failure
        return self.response


def test_service_maps_once_and_preserves_multiple_and_reset_semantics() -> None:
    response = GetAccountRateLimitsResponse(
        rateLimits=RateLimitSnapshotProtocol(limitId="legacy"),
        rateLimitsByLimitId={"first": RateLimitSnapshotProtocol(limitId=None)},
        rateLimitResetCredits={"availableCount": 2, "credits": None},
    )

    async def scenario() -> None:
        reader = FakeReader(response)
        result = await RateLimitService(reader).get_rate_limits()
        assert reader.calls == 1
        assert [item.id for item in result[0]] == ["first"]
        assert result[1].available_count == 2
        assert result[1].credits is None

    asyncio.run(scenario())


def test_service_preserves_reader_failure_identity_without_retry() -> None:
    sentinel = ProcessCommunicationFailed("service read failure")

    async def scenario() -> None:
        reader = FakeReader(failure=sentinel)
        with pytest.raises(ProcessCommunicationFailed) as error:
            await RateLimitService(reader).get_rate_limits()
        assert error.value is sentinel
        assert reader.calls == 1

    asyncio.run(scenario())


def test_service_maps_legacy_single_limit_without_reset_summary() -> None:
    response = GetAccountRateLimitsResponse(
        rateLimits=RateLimitSnapshotProtocol(limitId="legacy")
    )

    async def scenario() -> None:
        result = await RateLimitService(FakeReader(response)).get_rate_limits()
        assert tuple(item.id for item in result[0]) == ("legacy",)
        assert result[1] is None

    asyncio.run(scenario())
