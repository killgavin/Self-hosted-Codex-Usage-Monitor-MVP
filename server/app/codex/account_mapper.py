"""Mapping from account protocol DTOs to the pure account domain model."""

from app.models.account import AccountStatus
from app.codex.protocol import GetAccountResponse


def account_status_from_protocol(response: GetAccountResponse) -> AccountStatus:
    """Map only stable account type and plan fields into domain status."""

    account = response.account
    if account is None:
        return AccountStatus(authenticated=False, auth_mode=None, plan_type=None)
    return AccountStatus(
        authenticated=True,
        auth_mode=account.type,
        plan_type=account.plan_type,
    )
