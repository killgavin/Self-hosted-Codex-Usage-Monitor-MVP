"""Pure domain model for account authentication status.

The domain object intentionally contains no credential, protocol, or raw
metadata fields and has no dependency on transport or web frameworks.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class AccountStatus:
    """Preserve account status values without inferring plan semantics."""

    authenticated: bool
    auth_mode: str | None
    plan_type: str | None
