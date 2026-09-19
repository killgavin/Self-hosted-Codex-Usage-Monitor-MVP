"""ASGI integration coverage for the authenticated rate-limit endpoint."""

import asyncio
from decimal import Decimal
import json
from typing import Any

from app.config import Settings
from app.main import create_app
from app.models.rate_limit import RateLimit, RateLimitWindow, ResetCredit, ResetCredits


SERVER_TOKEN = "rate-test-monitor-token"
PRIVATE_MARKER = "must-not-cross-rest-boundary"


class FakeRateLimitService:
    def __init__(self, result) -> None:
        self.result = result
        self.calls = 0

    async def get_rate_limits(self):
        self.calls += 1
        return self.result


def request(
    service: FakeRateLimitService,
    authorization: str | None,
) -> tuple[int, dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    headers = [] if authorization is None else [(b"authorization", authorization.encode())]

    async def receive() -> dict[str, Any]:
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message: dict[str, Any]) -> None:
        messages.append(message)

    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/api/v1/rate-limits",
        "raw_path": b"/api/v1/rate-limits",
        "query_string": b"",
        "headers": headers,
        "client": ("testclient", 12345),
        "server": ("testserver", 80),
    }
    app = create_app(
        settings=Settings(server_api_token=SERVER_TOKEN),
        rate_limit_service=service,
    )
    asyncio.run(app(scope, receive, send))
    start = next(message for message in messages if message["type"] == "http.response.start")
    body = next(message for message in messages if message["type"] == "http.response.body")
    return start["status"], json.loads(body["body"])


def test_rate_limit_endpoint_has_stable_precise_schema_without_raw_leakage() -> None:
    limit = RateLimit(
        id="future-limit",
        name=None,
        primary=RateLimitWindow.from_values(
            Decimal("12.345678901234567890"),
            window_duration_minutes=321,
            reset_at=0,
        ),
        secondary=None,
        reached_type="future-reached-type",
        raw_metadata={"futureProtocolField": PRIVATE_MARKER},
    )
    credit = ResetCredit(
        id="credit-id",
        status="available",
        granted_at="1970-01-01T00:00:00Z",
        expires_at=None,
        title=None,
        description=None,
    )
    service = FakeRateLimitService(((limit,), ResetCredits(2, (credit,))))

    status, body = request(service, f"Bearer {SERVER_TOKEN}")

    assert status == 200
    assert body == {
        "limits": [
            {
                "id": "future-limit",
                "name": None,
                "primary": {
                    "usedPercent": "12.345678901234567890",
                    "remainingPercent": "87.654321098765432110",
                    "windowDurationMinutes": 321,
                    "resetAt": "1970-01-01T00:00:00Z",
                },
                "secondary": None,
                "reachedType": "future-reached-type",
            }
        ],
        "resetCredits": {
            "availableCount": 2,
            "credits": [
                {
                    "id": "credit-id",
                    "status": "available",
                    "grantedAt": "1970-01-01T00:00:00Z",
                    "expiresAt": None,
                    "title": None,
                    "description": None,
                }
            ],
        },
    }
    serialized = json.dumps(body)
    assert PRIVATE_MARKER not in serialized
    assert "raw_metadata" not in serialized and "rawMetadata" not in serialized
    assert all(
        forbidden not in serialized.lower()
        for forbidden in ("authorization", "cookie", "access_token", "refresh_token")
    )
    assert service.calls == 1


def test_unknown_limit_with_null_windows_is_preserved() -> None:
    limit = RateLimit("opaque-new-limit", None, None, None, "unknown-kind")
    service = FakeRateLimitService(((limit,), None))

    status, body = request(service, f"Bearer {SERVER_TOKEN}")

    assert status == 200
    assert body == {
        "limits": [
            {
                "id": "opaque-new-limit",
                "name": None,
                "primary": None,
                "secondary": None,
                "reachedType": "unknown-kind",
            }
        ],
        "resetCredits": None,
    }


def test_reset_credit_count_survives_null_details() -> None:
    service = FakeRateLimitService(((), ResetCredits(2, None)))

    status, body = request(service, f"Bearer {SERVER_TOKEN}")

    assert status == 200
    assert body == {
        "limits": [],
        "resetCredits": {"availableCount": 2, "credits": None},
    }


def test_missing_server_token_does_not_call_rate_limit_service() -> None:
    service = FakeRateLimitService(((), None))

    status, body = request(service, None)

    assert status == 401
    assert body["error"]["code"] == "INVALID_SERVER_TOKEN"
    assert service.calls == 0
