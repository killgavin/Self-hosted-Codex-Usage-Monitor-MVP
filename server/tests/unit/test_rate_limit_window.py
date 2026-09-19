"""Pure RateLimitWindow domain tests for T-01–T-06 and T-16–T-17."""

import os
import time
from dataclasses import FrozenInstanceError, fields
from decimal import Decimal

import pytest

from app.models.rate_limit import RateLimitWindow


@pytest.mark.parametrize(("used", "remaining"), [(25, "75"), (0, "100"), (100, "0")])
def test_t01_t03_remaining_percent(used, remaining) -> None:
    window = RateLimitWindow.from_values(used)
    assert window.remaining_percent == Decimal(remaining)


@pytest.mark.parametrize(("used", "remaining"), [(-1, "100"), (101, "0")])
def test_t04_t05_remaining_clamps_without_clamping_used(used, remaining) -> None:
    window = RateLimitWindow.from_values(used)
    assert window.used_percent == Decimal(str(used))
    assert window.remaining_percent == Decimal(remaining)


def test_t06_decimal_precision_is_preserved() -> None:
    window = RateLimitWindow.from_values("12.345678901234567890")
    assert window.used_percent == Decimal("12.345678901234567890")
    assert window.remaining_percent == Decimal("87.654321098765432110")


def test_t06_long_decimal_is_not_rounded_by_default_context() -> None:
    used = "12." + "34567890" * 8
    window = RateLimitWindow.from_values(used)
    assert window.used_percent == Decimal(used)
    assert window.remaining_percent == Decimal(
        "87.6543210965432109654321096543210965432109654321096543210965432110"
    )


def test_t16_unix_timestamp_is_canonical_utc_iso() -> None:
    window = RateLimitWindow.from_values(25, 300, 0)
    assert window.window_duration_minutes == 300
    assert window.reset_at == "1970-01-01T00:00:00Z"


def test_t17_timestamp_is_timezone_independent_and_optional_fields_are_none() -> None:
    if not hasattr(time, "tzset"):
        raise AssertionError("T-17 requires tzset in this validation environment")
    original = os.environ.get("TZ")
    try:
        outputs = []
        for zone in ("Asia/Taipei", "UTC"):
            os.environ["TZ"] = zone
            time.tzset()
            outputs.append(RateLimitWindow.from_values(25, reset_at=1_700_000_000).reset_at)
        assert outputs == ["2023-11-14T22:13:20Z", "2023-11-14T22:13:20Z"]
    finally:
        if original is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = original
        time.tzset()
    empty = RateLimitWindow.from_values("0")
    assert empty.window_duration_minutes is None
    assert empty.reset_at is None


def test_model_has_exact_order_and_is_immutable() -> None:
    assert [field.name for field in fields(RateLimitWindow)] == [
        "used_percent", "remaining_percent", "window_duration_minutes", "reset_at"
    ]
    window = RateLimitWindow.from_values(25)
    with pytest.raises(FrozenInstanceError):
        window.used_percent = Decimal("30")


def test_direct_construction_computes_remaining_and_rejects_caller_value() -> None:
    window = RateLimitWindow(Decimal("25"))
    assert window.remaining_percent == Decimal("75")
    with pytest.raises(TypeError):
        RateLimitWindow(Decimal("25"), remaining_percent=Decimal("1"))


@pytest.mark.parametrize("value", ["nan", "inf", "-inf", "not-a-number"])
def test_invalid_or_non_finite_percentages_are_controlled(value) -> None:
    with pytest.raises(ValueError):
        RateLimitWindow.from_values(value)


@pytest.mark.parametrize("value", ["nan", "inf", "bad", 10**1000])
def test_invalid_timestamps_are_controlled(value) -> None:
    with pytest.raises(ValueError):
        RateLimitWindow.from_values(25, reset_at=value)
