"""Application service orchestration for account status."""

from typing import Protocol

from app.codex.account_mapper import account_status_from_protocol
from app.codex.protocol import GetAccountResponse
from app.models.account import AccountStatus


class AccountReader(Protocol):
    """Minimal injected adapter boundary required by AccountService."""

    async def read_account(self) -> GetAccountResponse:
        """Read one account DTO using the adapter's safe defaults."""


class AccountService:
    """Map one adapter account read into the pure domain status model."""

    def __init__(self, adapter: AccountReader) -> None:
        self._adapter = adapter

    async def get_status(self) -> AccountStatus:
        """Read exactly once and map without changing adapter failures."""

        response = await self._adapter.read_account()
        return account_status_from_protocol(response)
