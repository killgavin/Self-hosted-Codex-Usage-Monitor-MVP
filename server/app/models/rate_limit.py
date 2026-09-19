"""Pure immutable rate-limit window domain model."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, localcontext
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


def _reset_iso(reset_at: Any) -> str | None:
    """Normalize Unix seconds to an explicit UTC ISO-8601 value."""

    if reset_at is None:
        return None
    try:
        timestamp = Decimal(str(reset_at))
        if not timestamp.is_finite():
            raise ValueError
        return datetime.fromtimestamp(float(timestamp), tz=UTC).isoformat().replace("+00:00", "Z")
    except (InvalidOperation, ValueError, TypeError, OverflowError, OSError) as exc:
        raise ValueError("reset_at must be a valid Unix timestamp") from exc


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
            object.__setattr__(self, "reset_at", _reset_iso(self.reset_at))

    @classmethod
    def from_values(
        cls,
        used_percent: Any,
        window_duration_minutes: int | None = None,
        reset_at: Any = None,
    ) -> "RateLimitWindow":
        """Build a window, clamping only the computed remaining percentage."""

        used = _decimal_percent(used_percent)
        return cls(used, window_duration_minutes, _reset_iso(reset_at))
