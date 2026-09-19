"""Automated tests for the minimal AuthService state boundary."""

import asyncio
from dataclasses import FrozenInstanceError, fields

import pytest

from app.codex.exceptions import LoginCompletionTimeout, ProcessCommunicationFailed
from app.codex.protocol import (
    AccountLoginCompletedNotification,
    CancelLoginResponse,
    DeviceCodeLoginResponse,
)
from app.services.auth import (
    AuthService,
    LoginAlreadyPending,
    LoginCancellationFailed,
    LoginNotPending,
    LoginState,
    LoginStatus,
)


class FakeLoginStarter:
    def __init__(self, response=None, failure=None) -> None:
        self.response = response
        self.failure = failure
        self.calls = 0
        self.cancel_calls = []
        self.logout_calls = 0

    async def start_login(self):
        self.calls += 1
        if self.failure is not None:
            raise self.failure
        return self.response

    async def wait_login_completion(self, login_id, timeout=10.0):
        self.calls += 1
        if self.failure is not None:
            raise self.failure
        return self.response

    async def cancel_login(self, login_id):
        self.cancel_calls.append(login_id)
        if self.failure is not None:
            raise self.failure
        return self.response

    async def logout(self):
        self.logout_calls += 1
        if self.failure is not None:
            raise self.failure
        return self.response


def test_login_state_has_exact_values() -> None:
    assert {state.value for state in LoginState} == {
        "IDLE",
        "PENDING",
        "COMPLETED",
        "FAILED",
        "CANCELED",
    }


def test_login_status_has_exact_immutable_fields_and_defaults() -> None:
    assert [field.name for field in fields(LoginStatus)] == [
        "state",
        "login_id",
        "verification_url",
        "user_code",
    ]
    status = LoginStatus(state=LoginState.IDLE)
    assert status.login_id is None
    assert status.verification_url is None
    assert status.user_code is None
    with pytest.raises(FrozenInstanceError):
        status.state = LoginState.PENDING


def test_auth_service_initial_status_is_idle_and_empty() -> None:
    service = AuthService(FakeLoginStarter())

    assert service.status == LoginStatus(state=LoginState.IDLE)
    assert service.status.login_id is None
    assert service.status.verification_url is None
    assert service.status.user_code is None


def test_auth_service_status_property_is_read_only() -> None:
    service = AuthService(FakeLoginStarter())

    with pytest.raises(AttributeError):
        service.status = LoginStatus(state=LoginState.PENDING)


def test_start_login_publishes_pending_status_and_calls_once() -> None:
    async def scenario() -> None:
        starter = FakeLoginStarter(
            DeviceCodeLoginResponse(
                type="chatgptDeviceCode",
                loginId="synthetic-id",
                userCode="synthetic-code",
                verificationUrl="https://example.invalid/verify",
            )
        )
        service = AuthService(starter)
        status = await service.start_login()
        assert status.state is LoginState.PENDING
        assert status.login_id == "synthetic-id"
        assert status.verification_url == "https://example.invalid/verify"
        assert status.user_code == "synthetic-code"
        assert starter.calls == 1

    asyncio.run(scenario())


def test_second_start_is_rejected_without_second_adapter_call() -> None:
    async def scenario() -> None:
        starter = FakeLoginStarter(
            DeviceCodeLoginResponse(
                type="chatgptDeviceCode",
                loginId="id",
                userCode="code",
                verificationUrl="url",
            )
        )
        service = AuthService(starter)
        await service.start_login()
        with pytest.raises(LoginAlreadyPending):
            await service.start_login()
        assert starter.calls == 1

    asyncio.run(scenario())


def test_start_failure_preserves_prior_status_and_error() -> None:
    async def scenario() -> None:
        failure = ProcessCommunicationFailed("controlled failure")
        starter = FakeLoginStarter(failure=failure)
        service = AuthService(starter)
        with pytest.raises(ProcessCommunicationFailed) as error:
            await service.start_login()
        assert error.value is failure
        assert service.status.state is LoginState.IDLE
        assert starter.calls == 1

    asyncio.run(scenario())


def test_completion_transitions_to_completed_and_clears_fields() -> None:
    async def scenario() -> None:
        starter = FakeLoginStarter(
            DeviceCodeLoginResponse(type="chatgptDeviceCode", loginId="id", userCode="code", verificationUrl="url")
        )
        service = AuthService(starter)
        await service.start_login()
        starter.response = AccountLoginCompletedNotification(success=True, loginId="id")
        status = await service.wait_for_completion(timeout=0.1)
        assert status == LoginStatus(state=LoginState.COMPLETED)

    asyncio.run(scenario())


def test_failed_completion_transitions_to_failed_and_clears_fields() -> None:
    async def scenario() -> None:
        starter = FakeLoginStarter(
            DeviceCodeLoginResponse(type="chatgptDeviceCode", loginId="id", userCode="code", verificationUrl="url")
        )
        service = AuthService(starter)
        await service.start_login()
        starter.response = AccountLoginCompletedNotification(success=False, loginId="id", error="private")
        status = await service.wait_for_completion()
        assert status == LoginStatus(state=LoginState.FAILED)

    asyncio.run(scenario())


def test_completion_requires_pending_and_failure_preserves_pending() -> None:
    async def scenario() -> None:
        idle_starter = FakeLoginStarter()
        idle_service = AuthService(idle_starter)
        with pytest.raises(LoginNotPending):
            await idle_service.wait_for_completion(timeout=0.1)
        assert idle_starter.calls == 0

        failure = ProcessCommunicationFailed("completion failed")
        starter = FakeLoginStarter(
            DeviceCodeLoginResponse(type="chatgptDeviceCode", loginId="id", userCode="code", verificationUrl="url")
        )
        service = AuthService(starter)
        await service.start_login()
        starter.failure = failure
        pending = service.status
        with pytest.raises(ProcessCommunicationFailed) as error:
            await service.wait_for_completion()
        assert error.value is failure
        assert service.status == pending

    asyncio.run(scenario())


def test_cancel_success_clears_pending_fields() -> None:
    async def scenario() -> None:
        starter = FakeLoginStarter(
            DeviceCodeLoginResponse(type="chatgptDeviceCode", loginId="id", userCode="code", verificationUrl="url")
        )
        service = AuthService(starter)
        await service.start_login()
        starter.response = CancelLoginResponse(status="canceled")
        status = await service.cancel_login()
        assert status == LoginStatus(state=LoginState.CANCELED)
        assert starter.cancel_calls == ["id"]

    asyncio.run(scenario())


def test_cancel_requires_pending_and_does_not_call_adapter() -> None:
    async def scenario() -> None:
        starter = FakeLoginStarter()
        service = AuthService(starter)
        with pytest.raises(LoginNotPending):
            await service.cancel_login()
        assert starter.cancel_calls == []

    asyncio.run(scenario())


@pytest.mark.parametrize("status", ["notFound", "future-status"])
def test_cancel_non_success_is_generic_and_preserves_pending(status: str) -> None:
    async def scenario() -> None:
        starter = FakeLoginStarter(
            DeviceCodeLoginResponse(type="chatgptDeviceCode", loginId="id", userCode="code", verificationUrl="url")
        )
        service = AuthService(starter)
        await service.start_login()
        pending = service.status
        starter.response = CancelLoginResponse(status=status)
        with pytest.raises(LoginCancellationFailed) as error:
            await service.cancel_login()
        assert str(error.value) == "Login cancellation failed"
        assert service.status == pending

    asyncio.run(scenario())


def test_cancel_transport_failure_preserves_pending_and_identity() -> None:
    async def scenario() -> None:
        starter = FakeLoginStarter(
            DeviceCodeLoginResponse(type="chatgptDeviceCode", loginId="id", userCode="code", verificationUrl="url")
        )
        service = AuthService(starter)
        await service.start_login()
        failure = ProcessCommunicationFailed("cancel transport failure")
        starter.failure = failure
        pending = service.status
        with pytest.raises(ProcessCommunicationFailed) as error:
            await service.cancel_login()
        assert error.value is failure
        assert service.status == pending

    asyncio.run(scenario())


def test_get_status_terminal_does_not_call_adapter() -> None:
    async def scenario() -> None:
        starter = FakeLoginStarter()
        service = AuthService(starter)
        status = await service.get_status()
        assert status == LoginStatus(state=LoginState.IDLE)
        assert starter.calls == 0

    asyncio.run(scenario())


def test_get_status_consumes_arrived_completion() -> None:
    async def scenario() -> None:
        starter = FakeLoginStarter(
            DeviceCodeLoginResponse(type="chatgptDeviceCode", loginId="id", userCode="code", verificationUrl="url")
        )
        service = AuthService(starter)
        await service.start_login()
        starter.response = AccountLoginCompletedNotification(success=True, loginId="id")
        status = await service.get_status()
        assert status.state is LoginState.COMPLETED

    asyncio.run(scenario())


def test_get_status_timeout_preserves_pending_and_other_failure_propagates() -> None:
    async def scenario() -> None:
        starter = FakeLoginStarter(
            DeviceCodeLoginResponse(type="chatgptDeviceCode", loginId="id", userCode="code", verificationUrl="url")
        )
        service = AuthService(starter)
        await service.start_login()
        pending = service.status
        original = service.wait_for_completion

        async def timeout(*, timeout):
            raise LoginCompletionTimeout("timed out")

        service.wait_for_completion = timeout
        assert await service.get_status() == pending
        service.wait_for_completion = original
        failure = ProcessCommunicationFailed("private marker")
        starter.failure = failure
        with pytest.raises(ProcessCommunicationFailed) as error:
            await service.get_status()
        assert error.value is failure
        assert service.status == pending

    asyncio.run(scenario())


def test_logout_success_clears_state_and_pending_is_rejected() -> None:
    async def scenario() -> None:
        starter = FakeLoginStarter(
            response=DeviceCodeLoginResponse(
                type="chatgptDeviceCode", loginId="id", userCode="code", verificationUrl="url"
            )
        )
        service = AuthService(starter)
        status = await service.logout()
        assert status == LoginStatus(state=LoginState.IDLE)
        assert starter.logout_calls == 1
        await service.start_login()
        with pytest.raises(LoginAlreadyPending):
            await service.logout()
        assert starter.logout_calls == 1

    asyncio.run(scenario())


def test_logout_failure_preserves_prior_state_and_identity() -> None:
    async def scenario() -> None:
        failure = ProcessCommunicationFailed("logout failure")
        starter = FakeLoginStarter(
            response=DeviceCodeLoginResponse(
                type="chatgptDeviceCode", loginId="id", userCode="code", verificationUrl="url"
            )
        )
        service = AuthService(starter)
        await service.start_login()
        starter.response = AccountLoginCompletedNotification(success=True, loginId="id")
        await service.wait_for_completion()
        before = service.status
        starter.failure = failure
        with pytest.raises(ProcessCommunicationFailed) as error:
            await service.logout()
        assert error.value is failure
        assert service.status == before

    asyncio.run(scenario())
