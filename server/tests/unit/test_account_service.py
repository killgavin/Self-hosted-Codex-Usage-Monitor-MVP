"""Focused tests for AccountService orchestration and propagation."""

import asyncio

import pytest

from app.codex.exceptions import ProcessCommunicationFailed
from app.codex.protocol import AccountProtocol, GetAccountResponse
from app.services.account import AccountService


class FakeAdapter:
    def __init__(self, response=None, failure=None) -> None:
        self.response = response
        self.failure = failure
        self.calls = 0

    async def read_account(self):
        self.calls += 1
        if self.failure is not None:
            raise self.failure
        return self.response


def test_authenticated_status_at_service_boundary() -> None:
    async def scenario() -> None:
        adapter = FakeAdapter(
            GetAccountResponse(
                requiresOpenaiAuth=False,
                account=AccountProtocol(type="chatgpt", planType="Plus"),
            )
        )

        status = await AccountService(adapter).get_status()

        assert status.authenticated is True
        assert status.auth_mode == "chatgpt"
        assert status.plan_type == "Plus"
        assert adapter.calls == 1

    asyncio.run(scenario())


def test_unauthenticated_status_at_service_boundary() -> None:
    async def scenario() -> None:
        adapter = FakeAdapter(GetAccountResponse(requiresOpenaiAuth=True, account=None))

        status = await AccountService(adapter).get_status()

        assert status.authenticated is False
        assert status.auth_mode is None
        assert status.plan_type is None
        assert adapter.calls == 1

    asyncio.run(scenario())


def test_null_plan_is_preserved_without_inference() -> None:
    async def scenario() -> None:
        adapter = FakeAdapter(
            GetAccountResponse(
                requiresOpenaiAuth=False,
                account=AccountProtocol(type="chatgpt", planType=None),
            )
        )

        status = await AccountService(adapter).get_status()

        assert status.plan_type is None
        assert adapter.calls == 1

    asyncio.run(scenario())


def test_unknown_and_missing_account_type_are_preserved() -> None:
    async def scenario() -> None:
        unknown_adapter = FakeAdapter(
            GetAccountResponse(
                requiresOpenaiAuth=False,
                account=AccountProtocol(type="futureType", planType="FuturePlan"),
            )
        )
        missing_adapter = FakeAdapter(
            GetAccountResponse(
                requiresOpenaiAuth=False,
                account=AccountProtocol(type=None, planType=None),
            )
        )

        unknown_status = await AccountService(unknown_adapter).get_status()
        missing_status = await AccountService(missing_adapter).get_status()

        assert unknown_status.auth_mode == "futureType"
        assert unknown_status.plan_type == "FuturePlan"
        assert missing_status.authenticated is True
        assert missing_status.auth_mode is None

    asyncio.run(scenario())


def test_adapter_failure_propagates_unchanged() -> None:
    async def scenario() -> None:
        failure = ProcessCommunicationFailed("controlled transport failure")
        adapter = FakeAdapter(failure=failure)

        with pytest.raises(ProcessCommunicationFailed) as error:
            await AccountService(adapter).get_status()

        assert error.value is failure
        assert adapter.calls == 1

    asyncio.run(scenario())
