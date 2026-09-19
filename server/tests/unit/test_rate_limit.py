"""Generic RateLimit domain tests for T-07–T-11 and T-72–T-74."""

from dataclasses import FrozenInstanceError, fields

import pytest

from app.models.rate_limit import RateLimit, RateLimitWindow


def test_t07_opaque_id_and_t08_null_name_are_preserved() -> None:
    limit = RateLimit(id="vendor-specific-limit", name=None, primary=None, secondary=None, reached_type=None)
    assert limit.id == "vendor-specific-limit"
    assert limit.name is None


@pytest.mark.parametrize("field", ["primary", "secondary"])
def test_t09_t10_nullable_windows(field: str) -> None:
    limit = RateLimit(id=None, name="Example", primary=None, secondary=None, reached_type=None)
    assert getattr(limit, field) is None


def test_t11_unknown_generic_field_is_preserved_safely() -> None:
    source = {"futureGenericField": "opaque"}
    limit = RateLimit(None, None, None, None, None, source)
    source["futureGenericField"] = "changed"
    assert limit.raw_metadata["futureGenericField"] == "opaque"


def test_t72_future_top_level_metadata_is_read_only() -> None:
    source = {"futureTopLevel": {"enabled": True}}
    limit = RateLimit(
        id=None,
        name=None,
        primary=RateLimitWindow.from_values("25.5"),
        secondary=None,
        reached_type=None,
        raw_metadata=source,
    )
    source["futureTopLevel"]["enabled"] = False
    assert limit.raw_metadata["futureTopLevel"]["enabled"] is True
    with pytest.raises(TypeError):
        limit.raw_metadata["futureTopLevel"] = {}


def test_t73_nested_future_rate_metadata_is_read_only() -> None:
    source = {"futureRate": {"newRateField": ["opaque", {"nested": True}]}}
    limit = RateLimit(None, None, None, None, None, source)
    source["futureRate"]["newRateField"].append("changed")
    assert limit.raw_metadata["futureRate"]["newRateField"][0] == "opaque"
    with pytest.raises(TypeError):
        limit.raw_metadata["futureRate"]["newRateField"][1]["nested"] = False


@pytest.mark.parametrize("metadata", [{1: "bad"}, {"bad": object()}, {"bad": float("nan")}])
def test_invalid_metadata_is_rejected(metadata) -> None:
    with pytest.raises((TypeError, ValueError)):
        RateLimit(None, None, None, None, None, metadata)


def test_t74_unknown_reached_type_is_preserved_as_raw_string() -> None:
    limit = RateLimit(None, None, None, None, "future-reached-type")
    assert limit.reached_type == "future-reached-type"


def test_rate_limit_has_canonical_order_and_is_frozen() -> None:
    assert [item.name for item in fields(RateLimit)] == [
        "id", "name", "primary", "secondary", "reached_type", "raw_metadata"
    ]
    limit = RateLimit(None, None, None, None, None)
    with pytest.raises(FrozenInstanceError):
        limit.name = "changed"
