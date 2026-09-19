"""Pure immutable generic rate-limit domain models."""

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, localcontext
from types import MappingProxyType
from typing import Any


def _decimal_percent(value: Any) -> Decimal:
    """Convert numeric input without introducing binary float artifacts."""

    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError("used_percent must be a finite decimal") from exc
    if not result.is_finite():
        raise ValueError("used_percent must be a finite decimal")
    return result


def _timestamp_iso(value: Any, field_name: str) -> str | None:
    """Normalize Unix seconds to an explicit UTC ISO-8601 value."""

    if value is None:
        return None
    try:
        timestamp = Decimal(str(value))
        if not timestamp.is_finite():
            raise ValueError
        return datetime.fromtimestamp(float(timestamp), tz=UTC).isoformat().replace("+00:00", "Z")
    except (InvalidOperation, ValueError, TypeError, OverflowError, OSError) as exc:
        raise ValueError(f"{field_name} must be a valid Unix timestamp") from exc


@dataclass(frozen=True)
class RateLimitWindow:
    """Preserve usage and normalize its derived remaining percentage."""

    used_percent: Decimal
    remaining_percent: Decimal = field(init=False)
    window_duration_minutes: int | None = None
    reset_at: str | None = None

    def __post_init__(self) -> None:
        used = _decimal_percent(self.used_percent)
        with localcontext() as context:
            context.prec = max(context.prec, len(used.as_tuple().digits) + 16)
            remaining = max(Decimal("0"), min(Decimal("100"), Decimal("100") - used))
        object.__setattr__(self, "used_percent", used)
        object.__setattr__(self, "remaining_percent", remaining)
        if self.reset_at is not None and not isinstance(self.reset_at, str):
            object.__setattr__(self, "reset_at", _timestamp_iso(self.reset_at, "reset_at"))

    @classmethod
    def from_values(
        cls,
        used_percent: Any,
        window_duration_minutes: int | None = None,
        reset_at: Any = None,
    ) -> "RateLimitWindow":
        """Build a window, clamping only the computed remaining percentage."""

        used = _decimal_percent(used_percent)
        return cls(used, window_duration_minutes, _timestamp_iso(reset_at, "reset_at"))


def _readonly_metadata(value: Any) -> Any:
    """Freeze JSON-compatible compatibility metadata recursively."""

    if isinstance(value, Mapping):
        frozen = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("raw_metadata keys must be strings")
            frozen[key] = _readonly_metadata(item)
        return MappingProxyType(frozen)
    if isinstance(value, list):
        return tuple(_readonly_metadata(item) for item in value)
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float) and math.isfinite(value):
        return value
    raise TypeError("raw_metadata must contain only JSON-compatible values")


@dataclass(frozen=True)
class RateLimit:
    """Generic quota identity preserving unknown upstream values unchanged."""

    id: str | None
    name: str | None
    primary: RateLimitWindow | None
    secondary: RateLimitWindow | None
    reached_type: str | None
    # This is a read-only internal compatibility bag, not a raw protocol payload.
    raw_metadata: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.raw_metadata is not None:
            object.__setattr__(self, "raw_metadata", _readonly_metadata(self.raw_metadata))


@dataclass(frozen=True)
class ResetCredit:
    """One opaque reset credit detail with canonical UTC timestamps."""

    id: str
    status: str
    granted_at: str
    expires_at: str | None = None
    title: str | None = None
    description: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.granted_at, str):
            object.__setattr__(self, "granted_at", _timestamp_iso(self.granted_at, "granted_at"))
        if self.expires_at is not None and not isinstance(self.expires_at, str):
            object.__setattr__(self, "expires_at", _timestamp_iso(self.expires_at, "expires_at"))


@dataclass(frozen=True)
class ResetCredits:
    """Present reset-credit summary; absent summaries remain Python ``None``."""

    available_count: int
    credits: tuple[ResetCredit, ...] | None

    def __post_init__(self) -> None:
        if isinstance(self.available_count, bool) or not isinstance(self.available_count, int):
            raise TypeError("available_count must be an integer")
        if self.credits is None:
            return
        if isinstance(self.credits, (str, bytes, Mapping)):
            raise TypeError("credits must be an iterable of ResetCredit values")
        try:
            credits = tuple(self.credits)
        except TypeError as exc:
            raise TypeError("credits must be an iterable of ResetCredit values") from exc
        if any(not isinstance(credit, ResetCredit) for credit in credits):
            raise TypeError("credits must contain only ResetCredit values")
        object.__setattr__(self, "credits", credits)
