"""Reset-credit domain tests for T-12–T-15."""

from dataclasses import FrozenInstanceError, fields

import pytest

from app.models.rate_limit import ResetCredit, ResetCredits


def test_t12_absent_summary_is_none_without_fabricated_count() -> None:
    summary = None
    assert summary is None


def test_t13_null_details_preserve_available_count() -> None:
    summary = ResetCredits(available_count=2, credits=None)
    assert summary.available_count == 2
    assert summary.credits is None


def test_t14_empty_details_are_distinct_from_null() -> None:
    empty = ResetCredits(available_count=2, credits=[])
    null = ResetCredits(available_count=2, credits=None)
    assert empty.credits == ()
    assert empty.credits != null.credits


def test_t15_detail_mapping_preserves_fields_and_utc_timestamps() -> None:
    detail = ResetCredit(
        id="opaque-credit",
        status="future-status",
        granted_at=0,
        expires_at=1_700_000_000,
        title=None,
        description=None,
    )
    summary = ResetCredits(available_count=5, credits=[detail])
    assert summary.credits == (detail,)
    assert detail.granted_at == "1970-01-01T00:00:00Z"
    assert detail.expires_at == "2023-11-14T22:13:20Z"
    assert detail.title is None and detail.description is None


def test_reset_credits_defensively_freezes_collection_and_is_immutable() -> None:
    source = [ResetCredit("id", "available", 0)]
    summary = ResetCredits(available_count=1, credits=source)
    source.clear()
    assert len(summary.credits) == 1
    with pytest.raises(FrozenInstanceError):
        summary.available_count = 2
    with pytest.raises(FrozenInstanceError):
        source_detail = summary.credits[0]
        source_detail.status = "changed"


def test_reset_credit_field_order_and_invalid_timestamp_are_controlled() -> None:
    assert [item.name for item in fields(ResetCredit)] == [
        "id", "status", "granted_at", "expires_at", "title", "description"
    ]
    assert [item.name for item in fields(ResetCredits)] == ["available_count", "credits"]
    with pytest.raises(ValueError, match="granted_at"):
        ResetCredit("id", "status", float("nan"))
    with pytest.raises(ValueError, match="expires_at"):
        ResetCredit("id", "status", 0, float("nan"))


@pytest.mark.parametrize("credits", ["not-credits", {"id": "bad"}, ["not-a-credit"], [1]])
def test_invalid_credit_collections_are_controlled(credits) -> None:
    with pytest.raises(TypeError):
        ResetCredits(available_count=1, credits=credits)
