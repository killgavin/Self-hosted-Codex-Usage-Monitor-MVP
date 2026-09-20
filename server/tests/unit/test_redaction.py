"""Deterministic evidence for the logging redaction boundary (T-29--T-32)."""

from __future__ import annotations

import logging
from io import StringIO

from app.security.redaction import REDACTED, RedactionFilter, redact_sensitive


SENTINEL = "synthetic-secret-marker"


def _formatted(message: object, *args: object) -> str:
    record = logging.LogRecord("test", logging.INFO, __file__, 1, message, args, None)
    RedactionFilter().filter(record)
    return record.getMessage()


def test_t29_authorization_and_bearer_are_redacted() -> None:
    output = _formatted(
        "Authorization: Bearer %s; standalone bearer=%s",
        SENTINEL,
        "Bearer " + SENTINEL,
    )
    assert SENTINEL not in output
    assert output.count(REDACTED) >= 2


def test_t30_access_token_is_redacted() -> None:
    output = _formatted("payload access_token=%s", SENTINEL)
    assert SENTINEL not in output
    assert REDACTED in output


def test_t31_refresh_token_is_redacted() -> None:
    output = _formatted("payload refresh_token=%s", SENTINEL)
    assert SENTINEL not in output
    assert REDACTED in output


def test_t32_cookie_is_redacted() -> None:
    output = _formatted("Cookie: session=%s; other=value", SENTINEL)
    assert SENTINEL not in output
    assert "other=value" not in output
    assert REDACTED in output


def test_nested_structured_args_are_copied_and_redacted() -> None:
    original = {
        "access_token": SENTINEL,
        "nested": [{"refreshToken": SENTINEL}, ("Cookie: " + SENTINEL, "safe")],
        "ordinary": "keep me",
    }
    sanitized = redact_sensitive(original)
    assert sanitized["access_token"] == REDACTED
    assert sanitized["nested"][0]["refreshToken"] == REDACTED
    assert sanitized["nested"][1][0] == "Cookie: " + REDACTED
    assert sanitized["ordinary"] == original["ordinary"]
    assert original["access_token"] == SENTINEL
    assert original["nested"][0]["refreshToken"] == SENTINEL


def test_filter_preserves_non_sensitive_formatting_and_structured_values() -> None:
    values = {"name": "example", "count": 3}
    record = logging.LogRecord("test", logging.INFO, __file__, 1, "user=%s count=%d", (values["name"], values["count"]), None)
    assert RedactionFilter().filter(record)
    assert record.getMessage() == "user=example count=3"

    output = _formatted("%s", {"server-monitor-token": SENTINEL, "ok": "yes"})
    assert SENTINEL not in output
    assert "'ok': 'yes'" in output


def test_formatted_json_like_text_redacts_quoted_keys() -> None:
    output = _formatted(
        '{"access_token":"%s", "refresh_token": "%s", "cookie":"session=%s", "Authorization":"Basic %s"}',
        SENTINEL,
        SENTINEL,
        SENTINEL,
        SENTINEL,
    )
    assert SENTINEL not in output
    assert output.count(REDACTED) >= 4


def test_preformatted_sensitive_strings_redact_entire_values() -> None:
    output = _formatted("Authorization: Basic " + SENTINEL)
    output += _formatted('{"Authorization":"Basic ' + SENTINEL + '"}')
    output += _formatted("access_token=" + SENTINEL)
    output += _formatted("refresh_token=" + SENTINEL)
    output += _formatted("Cookie: session=" + SENTINEL)
    assert SENTINEL not in output


def test_final_formatter_output_redacts_exception_text() -> None:
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    handler.addFilter(RedactionFilter())
    logger = logging.getLogger("redaction-final-format")
    logger.handlers = [handler]
    logger.propagate = False
    try:
        try:
            raise RuntimeError("refresh_token=" + SENTINEL)
        except RuntimeError:
            logger.exception("request failed")
    finally:
        logger.handlers.clear()
        logger.propagate = True

    output = stream.getvalue()
    assert SENTINEL not in output
    assert REDACTED in output
