"""Automated account DTO and domain mapping tests."""

from app.codex.account_mapper import account_status_from_protocol
from app.codex.protocol import AccountProtocol, GetAccountParams, GetAccountResponse, to_wire


def test_account_params_default_and_wire_alias() -> None:
    assert to_wire(GetAccountParams()) == {"refreshToken": False}
    assert to_wire(GetAccountParams(refreshToken=True)) == {"refreshToken": True}


def test_chatgpt_account_maps_to_domain() -> None:
    response = GetAccountResponse.model_validate(
        {
            "requiresOpenaiAuth": False,
            "account": {
                "type": "chatgpt",
                "email": "private@example.invalid",
                "planType": "Plus",
            },
        }
    )

    status = account_status_from_protocol(response)

    assert status.authenticated is True
    assert status.auth_mode == "chatgpt"
    assert status.plan_type == "Plus"
    assert "email" not in status.__dict__


def test_null_account_maps_to_unauthenticated() -> None:
    response = GetAccountResponse(requiresOpenaiAuth=True, account=None)

    assert account_status_from_protocol(response).authenticated is False


def test_null_plan_remains_none() -> None:
    response = GetAccountResponse(
        requiresOpenaiAuth=False,
        account=AccountProtocol(type="chatgpt", planType=None),
    )

    assert account_status_from_protocol(response).plan_type is None


def test_account_without_type_remains_authenticated_without_inference() -> None:
    response = GetAccountResponse.model_validate(
        {"requiresOpenaiAuth": False, "account": {"planType": "Unknown"}}
    )

    status = account_status_from_protocol(response)
    assert status.authenticated is True
    assert status.auth_mode is None


def test_unknown_account_type_and_fields_are_preserved_at_protocol_boundary() -> None:
    response = GetAccountResponse.model_validate(
        {
            "requiresOpenaiAuth": False,
            "futureResponse": {"enabled": True},
            "account": {
                "type": "futureAccountType",
                "planType": "FuturePlan",
                "futureAccountField": "preserved",
            },
        }
    )

    assert response.model_extra == {"futureResponse": {"enabled": True}}
    assert response.account is not None
    assert response.account.model_extra == {"futureAccountField": "preserved"}
    status = account_status_from_protocol(response)
    assert status.auth_mode == "futureAccountType"
    assert status.plan_type == "FuturePlan"
