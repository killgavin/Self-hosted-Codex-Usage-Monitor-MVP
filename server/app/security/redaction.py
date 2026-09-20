"""Small logging boundary for authentication and token material.

The functions in this module deliberately return copies.  Logging should not
alter a request, exception, or other object which the caller may still use.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Mapping
from typing import Any

REDACTED = "[REDACTED]"

# Values are terminated at common structured-log delimiters.  The expression
# is intentionally case-insensitive: header and JSON naming conventions vary.
_VALUE = r"[^\s,;&}\]>)%]+"
_AUTH_VALUE = r"[^,;&}\]>)%\"']+"
_STRING_PATTERNS = (
    # Headers and their values (including non-Bearer Authorization schemes).
    (re.compile(rf"(?i)(\bauthorization\b[\"']?\s*[:=]\s*[\"']?){_AUTH_VALUE}"), r"\1" + REDACTED),
    # Token-like key/value pairs found in query strings, JSON-ish text, and
    # ordinary log messages.
    (re.compile(rf"(?i)(\b(?:access[_-]?token|refresh[_-]?token)\b[\"']?\s*[:=]\s*[\"']?){_VALUE}"), r"\1" + REDACTED),
    (re.compile(rf"(?i)(\b(?:api[_-]?token|server[_-]?monitor[_-]?token|monitor[_-]?api[_-]?token|server[_-]?api[_-]?token)\b[\"']?\s*[:=]\s*[\"']?){_VALUE}"), r"\1" + REDACTED),
    # Also catch a credential when a caller logs only the Authorization value.
    (re.compile(rf"(?i)\bbearer\s+{_VALUE}"), "Bearer " + REDACTED),
)


def _sensitive_key(key: object) -> bool:
    """Return whether a structured field name denotes secret material."""

    if not isinstance(key, str):
        return False
    normalized = re.sub(r"[^a-z0-9]", "", key.casefold())
    return normalized in {
        "authorization",
        "accesstoken",
        "refreshtoken",
        "cookie",
        "apitoken",
        "serverapitoken",
        "servermonitortoken",
        "monitorapitoken",
    }


def _redact_string(value: str) -> str:
    # Cookies are a header containing multiple name/value pairs.  Preserve
    # %-format placeholders, but discard everything else in the header.
    cookie = re.compile(r"(?i)(\bcookie\b[\"']?\s*[:=]\s*)(.*)")
    def replace_cookie(match: re.Match[str]) -> str:
        placeholders = re.findall(r"%(?:\([^)]+\))?[#0 +\-]?(?:\d+|\*)?(?:\.\d+)?[a-zA-Z]", match.group(2))
        return match.group(1) + REDACTED + "".join(placeholders)
    value = cookie.sub(replace_cookie, value)
    for pattern, replacement in _STRING_PATTERNS:
        value = pattern.sub(replacement, value)
    return value


def _redact_all_strings(value: Any) -> Any:
    """Redact a value used by a format string naming a secret field."""

    if isinstance(value, str):
        return REDACTED
    if isinstance(value, Mapping):
        return {key: _redact_all_strings(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return tuple(_redact_all_strings(item) for item in value)
    if isinstance(value, list):
        return [_redact_all_strings(item) for item in value]
    if isinstance(value, set):
        return {_redact_all_strings(item) for item in value}
    return value


def redact_sensitive(value: Any, *, _key_context: bool = False) -> Any:
    """Return *value* with authentication material replaced by ``[REDACTED]``.

    Strings are sanitized for common header/key-value forms.  Mappings and
    sequences are copied recursively, including nested values.  Other values
    are returned unchanged, so this is safe to apply to arbitrary log args.
    """

    if _key_context:
        return REDACTED
    if isinstance(value, str):
        return _redact_string(value)
    if isinstance(value, Mapping):
        return {
            key: redact_sensitive(item, _key_context=_sensitive_key(key))
            for key, item in value.items()
        }
    if isinstance(value, tuple):
        return tuple(redact_sensitive(item) for item in value)
    if isinstance(value, list):
        return [redact_sensitive(item) for item in value]
    if isinstance(value, set):
        return {redact_sensitive(item) for item in value}
    return value


class RedactionFilter(logging.Filter):
    """A standard-library filter suitable for any handler or logger."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact_sensitive(record.msg)
        record.args = redact_sensitive(record.args)
        # A common logging form is ``"access_token=%s", token``.  The token
        # is not visible until %-formatting, so redact arguments when the
        # format string explicitly identifies a credential field.
        if isinstance(record.msg, str) and re.search(
            r"(?i)\b(?:authorization|bearer|access[_-]?token|refresh[_-]?token|cookie|api[_-]?token|server[_-]?monitor[_-]?token)\b",
            record.msg,
        ):
            record.args = _redact_all_strings(record.args)
        # Formatter.format() appends exception text after filters have run.
        # Populate a sanitized copy so the original exception remains intact.
        if record.exc_info:
            exception_text = logging.Formatter().formatException(record.exc_info)
            record.exc_text = _redact_string(exception_text)
        elif getattr(record, "exc_text", None):
            record.exc_text = _redact_string(record.exc_text)
        return True


# Descriptive alias for callers that prefer the longer name.
SensitiveDataFilter = RedactionFilter


__all__ = ["REDACTED", "RedactionFilter", "SensitiveDataFilter", "redact_sensitive"]
