"""Automated tests for the pure AccountStatus domain model."""

from dataclasses import FrozenInstanceError

import pytest

from app.models.account import AccountStatus


def test_authenticated_status_preserves_values() -> None:
    status = AccountStatus(authenticated=True, auth_mode="chatgpt", plan_type="Plus")

    assert status.authenticated is True
    assert status.auth_mode == "chatgpt"
    assert status.plan_type == "Plus"


def test_unauthenticated_status_preserves_values() -> None:
    status = AccountStatus(authenticated=False, auth_mode=None, plan_type=None)

    assert status.authenticated is False
    assert status.auth_mode is None
    assert status.plan_type is None


def test_missing_plan_is_not_inferred() -> None:
    status = AccountStatus(authenticated=True, auth_mode="chatgpt", plan_type=None)

    assert status.plan_type is None


def test_domain_model_is_immutable() -> None:
    status = AccountStatus(authenticated=False, auth_mode=None, plan_type=None)

    with pytest.raises(FrozenInstanceError):
        status.authenticated = True
