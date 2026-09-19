"""Automated tests for version-specific initialization DTOs."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.codex.protocol import (
    AccountLoginCompletedNotification,
    CancelLoginParams,
    CancelLoginResponse,
    ClientInfo,
    DeviceCodeLoginParams,
    DeviceCodeLoginResponse,
    GetAccountRateLimitsResponse,
    InitializeCapabilities,
    InitializeParams,
    InitializeResponse,
    InitializedNotification,
    LogoutAccountResponse,
    RateLimitResetCreditProtocol,
    RateLimitResetCreditsProtocol,
    RateLimitSnapshotProtocol,
    RateLimitWindowProtocol,
    to_wire,
)


def test_minimal_initialize_params_serialize_with_wire_aliases() -> None:
    params = InitializeParams(clientInfo={"name": "usage-monitor", "version": "0.1"})

    assert to_wire(params) == {
        "clientInfo": {"name": "usage-monitor", "version": "0.1"}
    }


def test_capabilities_aliases_and_defaults() -> None:
    capabilities = InitializeCapabilities(
        experimentalApi=True,
        mcpServerOpenaiFormElicitation=True,
        optOutNotificationMethods=["example/event"],
        requestAttestation=True,
    )

    assert to_wire(capabilities) == {
        "experimentalApi": True,
        "mcpServerOpenaiFormElicitation": True,
        "optOutNotificationMethods": ["example/event"],
        "requestAttestation": True,
    }
    assert InitializeCapabilities().experimental_api is False
    assert InitializeCapabilities().request_attestation is False


def test_initialize_response_parsing_uses_camel_case_wire_names() -> None:
    response = InitializeResponse.model_validate(
        {
            "codexHome": "synthetic-codex-home",
            "platformFamily": "unix",
            "platformOs": "linux",
            "userAgent": "codex-cli-test",
        }
    )

    assert response.platform_family == "unix"
    assert to_wire(response)["codexHome"] == "synthetic-codex-home"


def test_unknown_fields_are_preserved_at_protocol_boundary() -> None:
    client = ClientInfo.model_validate(
        {"name": "usage-monitor", "version": "0.1", "futureField": {"safe": True}}
    )
    params = InitializeParams.model_validate(
        {
            "clientInfo": {"name": "usage-monitor", "version": "0.1"},
            "futureParam": "preserved",
        }
    )

    assert client.model_extra == {"futureField": {"safe": True}}
    assert params.model_extra == {"futureParam": "preserved"}
    assert to_wire(client)["futureField"] == {"safe": True}
    assert to_wire(params)["futureParam"] == "preserved"


def test_missing_optional_fields_are_accepted_as_none() -> None:
    params = InitializeParams(clientInfo=ClientInfo(name="usage-monitor", version="0.1"))

    assert params.capabilities is None
    assert InitializeCapabilities().extensions is None


def test_missing_required_fields_are_rejected() -> None:
    with pytest.raises(ValidationError):
        InitializeParams.model_validate({})
    with pytest.raises(ValidationError):
        InitializeResponse.model_validate({"platformFamily": "unix"})


def test_initialized_notification_wire_shape() -> None:
    notification = InitializedNotification()

    assert to_wire(notification) == {"method": "initialized"}


def test_device_code_login_shapes_and_unknown_fields() -> None:
    response = DeviceCodeLoginResponse.model_validate(
        {
            "type": "chatgptDeviceCode",
            "loginId": "synthetic-id",
            "userCode": "synthetic-code",
            "verificationUrl": "https://example.invalid/verify",
            "futureField": True,
        }
    )

    assert to_wire(DeviceCodeLoginParams()) == {"type": "chatgptDeviceCode"}
    assert to_wire(response)["loginId"] == "synthetic-id"
    assert response.model_extra == {"futureField": True}


def test_device_code_login_required_fields_and_literal() -> None:
    with pytest.raises(ValidationError):
        DeviceCodeLoginResponse.model_validate({"type": "chatgptDeviceCode"})
    with pytest.raises(ValidationError):
        DeviceCodeLoginResponse.model_validate(
            {
                "type": "unsupported",
                "loginId": "id",
                "userCode": "code",
                "verificationUrl": "url",
            }
        )


def test_login_completed_notification_aliases_and_unknown_fields() -> None:
    notification = AccountLoginCompletedNotification.model_validate(
        {"success": False, "loginId": "synthetic-id", "error": "synthetic", "future": True}
    )

    assert notification.login_id == "synthetic-id"
    assert notification.model_extra == {"future": True}


def test_login_completed_success_is_required_and_optional_fields_are_nullable() -> None:
    notification = AccountLoginCompletedNotification.model_validate(
        {"success": False, "future": "kept"}
    )

    assert notification.success is False
    assert notification.login_id is None
    assert notification.error is None
    assert notification.model_extra == {"future": "kept"}

    with pytest.raises(ValidationError):
        AccountLoginCompletedNotification.model_validate({"loginId": "id"})


def test_cancel_login_dtos_use_aliases_and_preserve_unknown_fields() -> None:
    params = CancelLoginParams.model_validate({"loginId": "synthetic-id", "future": True})
    response = CancelLoginResponse.model_validate({"status": "future-status", "future": {"x": 1}})

    assert to_wire(params) == {"loginId": "synthetic-id", "future": True}
    assert response.status == "future-status"
    assert response.model_extra == {"future": {"x": 1}}
    assert to_wire(response)["status"] == "future-status"

    with pytest.raises(ValidationError):
        CancelLoginParams.model_validate({})
    with pytest.raises(ValidationError):
        CancelLoginResponse.model_validate({})


def test_logout_response_accepts_empty_or_future_fields() -> None:
    assert to_wire(LogoutAccountResponse()) == {}
    assert LogoutAccountResponse.model_validate({"future": True}).model_extra == {"future": True}


def test_rate_limit_protocol_aliases_decimals_nullability_and_unknown_fields() -> None:
    response = GetAccountRateLimitsResponse.model_validate(
        {
            "rateLimits": {
                "limitId": None,
                "limitName": None,
                "planType": "future-plan",
                "rateLimitReachedType": "future-reached",
                "primary": {"usedPercent": "12.345678901234567890", "futureWindow": True},
                "secondary": None,
                "futureSnapshot": {"safe": True},
            },
            "rateLimitsByLimitId": {
                "future-limit-key": {"limitId": "opaque-key", "primary": None, "secondary": None}
            },
            "futureTopLevel": "preserved",
        }
    )
    assert response.rate_limits.plan_type == "future-plan"
    assert response.rate_limits.rate_limit_reached_type == "future-reached"
    assert response.rate_limits.primary.used_percent == Decimal("12.345678901234567890")
    assert response.rate_limits.secondary is None
    assert response.rate_limits_by_limit_id["future-limit-key"].limit_id == "opaque-key"
    assert response.rate_limits_by_limit_id["future-limit-key"].primary is None
    assert response.rate_limits_by_limit_id["future-limit-key"].secondary is None
    assert response.rate_limits.primary.model_extra == {"futureWindow": True}
    assert response.rate_limits.model_extra == {"futureSnapshot": {"safe": True}}
    assert response.model_extra == {"futureTopLevel": "preserved"}
    assert to_wire(response)["rateLimits"]["primary"]["usedPercent"] == Decimal("12.345678901234567890")
    null_windows = RateLimitSnapshotProtocol.model_validate({"primary": None, "secondary": None})
    assert null_windows.primary is None and null_windows.secondary is None


def test_rate_limit_protocol_required_fields_and_optional_defaults() -> None:
    with pytest.raises(ValidationError):
        RateLimitWindowProtocol.model_validate({})
    with pytest.raises(ValidationError):
        GetAccountRateLimitsResponse.model_validate({})
    with pytest.raises(ValidationError):
        RateLimitResetCreditProtocol.model_validate({"id": "id", "status": "status"})
    assert RateLimitWindowProtocol(usedPercent=1).window_duration_minutes is None
    assert RateLimitSnapshotProtocol().limit_id is None
    assert RateLimitResetCreditsProtocol(availableCount=2).credits is None


def test_reset_credit_protocol_aliases_null_empty_and_unknown_detail_fields() -> None:
    detail = RateLimitResetCreditProtocol.model_validate(
        {
            "id": "opaque",
            "status": "future-status",
            "grantedAt": 1700000000,
            "resetType": "future-type",
            "expiresAt": 1700000100,
            "title": "future-title",
            "description": "future-description",
            "futureDetail": {"safe": True},
        }
    )
    response = GetAccountRateLimitsResponse.model_validate(
        {
            "rateLimits": {"primary": None, "secondary": None},
            "rateLimitResetCredits": {"availableCount": 2, "credits": [detail.model_dump(by_alias=True)]},
        }
    )
    assert response.rate_limit_reset_credits.available_count == 2
    assert response.rate_limit_reset_credits.credits[0].id == "opaque"
    assert response.rate_limit_reset_credits.credits[0].status == "future-status"
    assert response.rate_limit_reset_credits.credits[0].reset_type == "future-type"
    assert response.rate_limit_reset_credits.credits[0].granted_at == 1700000000
    assert response.rate_limit_reset_credits.credits[0].expires_at == 1700000100
    assert response.rate_limit_reset_credits.credits[0].title == "future-title"
    assert response.rate_limit_reset_credits.credits[0].description == "future-description"
    assert detail.model_extra == {"futureDetail": {"safe": True}}
    assert RateLimitResetCreditsProtocol(availableCount=2, credits=None).credits is None
    assert RateLimitResetCreditsProtocol(availableCount=0, credits=[]).credits == []
    assert to_wire(detail)["grantedAt"] == 1700000000
