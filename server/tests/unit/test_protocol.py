"""Automated tests for version-specific initialization DTOs."""

import pytest
from pydantic import ValidationError

from app.codex.protocol import (
    ClientInfo,
    DeviceCodeLoginParams,
    DeviceCodeLoginResponse,
    AccountLoginCompletedNotification,
    CancelLoginParams,
    CancelLoginResponse,
    InitializeCapabilities,
    InitializeParams,
    InitializeResponse,
    InitializedNotification,
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
