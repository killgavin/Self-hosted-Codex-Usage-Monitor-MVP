"""Synthetic protocol-to-domain mapping tests for TASK-0505."""

import os
import time
from decimal import Decimal

import pytest

from app.codex.protocol import (
    GetAccountRateLimitsResponse,
    RateLimitResetCreditProtocol,
    RateLimitResetCreditsProtocol,
    RateLimitSnapshotProtocol,
    RateLimitWindowProtocol,
)
from app.codex.rate_limit_mapper import (
    map_rate_limit_snapshot,
    map_rate_limit_window,
    map_rate_limits_response,
    map_reset_credits,
)


def test_window_mapping_preserves_decimal_clamps_and_utc() -> None:
    result = map_rate_limit_window(
        RateLimitWindowProtocol(usedPercent="101.25", windowDurationMins=300, resetsAt=0)
    )
    assert result.used_percent == Decimal("101.25")
    assert result.remaining_percent == Decimal("0")
    assert result.reset_at == "1970-01-01T00:00:00Z"


@pytest.mark.parametrize(
    ("used", "expected"),
    [("25", "75"), ("0", "100"), ("100", "0"), ("-1", "100"), ("101", "0")],
)
def test_t01_t05_clamping_is_proven_through_mapping(used: str, expected: str) -> None:
    result = map_rate_limit_window(RateLimitWindowProtocol(usedPercent=used))
    assert result.used_percent == Decimal(used)
    assert result.remaining_percent == Decimal(expected)


def test_t06_long_decimal_precision_is_preserved_through_mapping() -> None:
    used = "12." + "34567890" * 8
    result = map_rate_limit_window(RateLimitWindowProtocol(usedPercent=used))
    assert result.used_percent == Decimal(used)
    assert result.remaining_percent == Decimal(
        "87.6543210965432109654321096543210965432109654321096543210965432110"
    )


def test_snapshot_mapping_preserves_nullable_fields_unknown_type_and_extras() -> None:
    dto = RateLimitSnapshotProtocol.model_validate(
        {
            "limitId": None,
            "limitName": None,
            "rateLimitReachedType": "future-type",
            "primary": None,
            "secondary": None,
            "futureRateField": {"safe": True},
        }
    )
    result = map_rate_limit_snapshot(dto, fallback_id="opaque-key")
    assert result.id == "opaque-key"
    assert result.name is None
    assert result.primary is None and result.secondary is None
    assert result.reached_type == "future-type"
    assert result.raw_metadata == {"futureRateField": {"safe": True}}


def test_future_top_level_response_field_is_ignored_but_nested_window_is_safe() -> None:
    response = GetAccountRateLimitsResponse.model_validate(
        {
            "rateLimits": {
                "limitId": "id",
                "primary": {"usedPercent": 25, "futureWindow": "ignored-by-domain"},
            },
            "futureTopLevel": {"mustNotBecomeRateMetadata": True},
        }
    )
    limits, _ = map_rate_limits_response(response)
    assert limits[0].raw_metadata is None
    assert limits[0].primary.used_percent == Decimal("25")


def test_t16_t17_mapping_timestamp_is_timezone_independent() -> None:
    if not hasattr(time, "tzset"):
        raise AssertionError("tzset is required in this validation environment")
    original = os.environ.get("TZ")
    try:
        outputs = []
        for zone in ("UTC", "Asia/Taipei"):
            os.environ["TZ"] = zone
            time.tzset()
            dto = GetAccountRateLimitsResponse.model_validate(
                {"rateLimits": {"primary": {"usedPercent": 25, "resetsAt": 1_700_000_000}}}
            )
            outputs.append(map_rate_limits_response(dto)[0][0].primary.reset_at)
        assert outputs == ["2023-11-14T22:13:20Z"] * 2
    finally:
        if original is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = original
        time.tzset()


def test_explicit_id_takes_precedence_over_key() -> None:
    dto = RateLimitSnapshotProtocol(limitId="explicit", limitName="name")
    assert map_rate_limit_snapshot(dto, fallback_id="key").id == "explicit"


def test_keyed_mapping_preserves_order_and_does_not_duplicate_legacy() -> None:
    response = GetAccountRateLimitsResponse.model_validate(
        {
            "rateLimits": {"limitId": "legacy"},
            "rateLimitsByLimitId": {
                "first-key": {"limitId": None},
                "second-key": {"limitId": "explicit"},
            },
        }
    )
    limits, credits = map_rate_limits_response(response)
    assert [limit.id for limit in limits] == ["first-key", "explicit"]
    assert credits is None


def test_empty_or_missing_keyed_mapping_falls_back_to_legacy_once() -> None:
    response = GetAccountRateLimitsResponse(
        rateLimits=RateLimitSnapshotProtocol(limitId="legacy"),
        rateLimitsByLimitId={},
    )
    limits, _ = map_rate_limits_response(response)
    assert [limit.id for limit in limits] == ["legacy"]


def test_reset_mapping_preserves_count_null_empty_and_details() -> None:
    detail = RateLimitResetCreditProtocol(
        id="opaque",
        status="future-status",
        grantedAt=0,
        resetType="future-reset",
        expiresAt=1700000100,
        title="title",
        description="description",
    )
    mapped = map_reset_credits(
        RateLimitResetCreditsProtocol(availableCount=2, credits=[detail])
    )
    assert mapped.available_count == 2
    assert mapped.credits[0].id == "opaque"
    assert mapped.credits[0].status == "future-status"
    assert mapped.credits[0].granted_at == "1970-01-01T00:00:00Z"
    assert mapped.credits[0].expires_at == "2023-11-14T22:15:00Z"
    assert mapped.credits[0].title == "title"
    assert mapped.credits[0].description == "description"
    assert not hasattr(mapped.credits[0], "reset_type")
    null_details = map_reset_credits(
        RateLimitResetCreditsProtocol(availableCount=2, credits=None)
    )
    empty_details = map_reset_credits(
        RateLimitResetCreditsProtocol(availableCount=2, credits=[])
    )
    assert null_details.credits is None
    assert empty_details.credits == ()
    assert map_reset_credits(None) is None
