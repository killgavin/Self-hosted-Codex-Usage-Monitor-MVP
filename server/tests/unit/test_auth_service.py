"""Automated tests for the minimal AuthService state boundary."""

from dataclasses import FrozenInstanceError, fields

import pytest

from app.services.auth import AuthService, LoginState, LoginStatus


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
    service = AuthService()

    assert service.status == LoginStatus(state=LoginState.IDLE)
    assert service.status.login_id is None
    assert service.status.verification_url is None
    assert service.status.user_code is None


def test_auth_service_status_property_is_read_only() -> None:
    service = AuthService()

    with pytest.raises(AttributeError):
        service.status = LoginStatus(state=LoginState.PENDING)
