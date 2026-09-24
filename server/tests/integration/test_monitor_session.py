"""Monitor owner password and sliding session boundary checks."""
import asyncio
import json

from app.config import Settings
from app.main import create_app
from app.security.session import COOKIE_NAME, IDLE_SECONDS, issue, valid


async def request(app, path, method="GET", headers=(), body=b""):
    messages = []
    sent = False

    async def receive():
        nonlocal sent
        if sent:
            return {"type": "http.disconnect"}
        sent = True
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(message):
        messages.append(message)

    await app({
        "type": "http", "asgi": {"version": "3.0", "spec_version": "2.0"},
        "http_version": "1.1", "method": method, "scheme": "http",
        "path": path, "raw_path": path.encode(), "query_string": b"",
        "headers": list(headers), "client": ("testclient", 12345),
        "server": ("testserver", 80),
    }, receive, send)
    start = next(message for message in messages if message["type"] == "http.response.start")
    payload = next(message for message in messages if message["type"] == "http.response.body")
    return start["status"], dict(start["headers"]), json.loads(payload["body"])


def test_password_session_cookie_and_logout_contract():
    async def scenario():
        app = create_app(settings=Settings(monitor_password="private-pass", session_secret="private-secret"))
        headers = [
            (b"origin", b"https://monitor.example.com"),
            (b"host", b"monitor.example.com"),
            (b"x-forwarded-proto", b"https"),
            (b"cf-ray", b"synthetic-ray"),
            (b"content-type", b"application/json"),
        ]
        status, response_headers, body = await request(
            app, "/api/v1/session", "POST", headers, b'{"password":"wrong"}'
        )
        assert status == 401 and body["error"]["code"] == "INVALID_PASSWORD"
        assert "private-pass" not in json.dumps(body)

        status, response_headers, body = await request(
            app, "/api/v1/session", "POST", headers, b'{"password":"private-pass"}'
        )
        assert status == 200 and body == {"authenticated": True}
        cookie = response_headers[b"set-cookie"].decode()
        assert cookie.startswith(f"{COOKIE_NAME}=")
        for attribute in ("HttpOnly", "Secure", "SameSite=lax", "Path=/", f"Max-Age={IDLE_SECONDS}"):
            assert attribute in cookie
        cookie_pair = cookie.split(";", 1)[0].encode()
        status, refresh_headers, _ = await request(app, "/api/v1/status", headers=[(b"cookie", cookie_pair)])
        assert status == 200 and b"set-cookie" in refresh_headers
        assert (await request(app, "/api/v1/status"))[0] == 401

        status, logout_headers, _ = await request(app, "/api/v1/session/logout", "POST", [
            (b"origin", b"https://monitor.example.com"),
            (b"host", b"monitor.example.com"),
            (b"x-forwarded-proto", b"https"), (b"cf-ray", b"synthetic-ray"),
            (b"cookie", cookie_pair),
        ])
        assert status == 200
        assert COOKIE_NAME.encode() in logout_headers[b"set-cookie"] and b"Max-Age=0" in logout_headers[b"set-cookie"]

    asyncio.run(scenario())


def test_session_rejects_idle_expiry_and_configuration_changes():
    token = issue("secret", "password", now=1000)
    assert valid(token, "secret", "password", now=1000 + IDLE_SECONDS - 1)
    assert not valid(token, "secret", "password", now=1000 + IDLE_SECONDS)
    assert not valid(token, "changed", "password", now=1001)
    assert not valid(token, "secret", "changed", now=1001)


def test_http_lan_cookie_works_without_disabling_https_cookie_security():
    async def scenario():
        app = create_app(settings=Settings(monitor_password="password", session_secret="secret"))
        status, headers, _ = await request(app, "/api/v1/session", "POST", [
            (b"origin", b"http://testserver"), (b"content-type", b"application/json"),
        ], b'{"password":"password"}')
        assert status == 200
        # Plain HTTP LAN access needs a non-Secure cookie, while proxied HTTPS
        # requests still get Secure (covered by the Cloudflare test above).
        assert b"Secure" not in headers[b"set-cookie"]
        assert b"HttpOnly" in headers[b"set-cookie"]

    asyncio.run(scenario())


def test_state_change_rejects_foreign_or_missing_origin():
    async def scenario():
        app = create_app(settings=Settings(monitor_password="password", session_secret="secret"))
        for headers in ([], [(b"origin", b"https://attacker.invalid")]):
            status, _, body = await request(app, "/api/v1/session", "POST", headers,
                                            b'{"password":"password"}')
            assert status == 403 and body["error"]["code"] == "INVALID_ORIGIN"

        # Cloudflare terminates browser HTTPS, then forwards HTTP to the app.
        cf_headers = [
            (b"host", b"monitor.example.com"),
            (b"origin", b"https://monitor.example.com"),
            (b"x-forwarded-proto", b"https"),
            (b"cf-ray", b"synthetic-ray"),
            (b"content-type", b"application/json"),
        ]
        status, _, body = await request(
            app, "/api/v1/session", "POST", cf_headers, b'{"password":"password"}'
        )
        assert status == 200 and body == {"authenticated": True}

        # Forwarded headers alone are not trusted for direct, non-Cloudflare requests.
        spoofed = [
            (b"origin", b"https://testserver"),
            (b"x-forwarded-proto", b"https"),
            (b"content-type", b"application/json"),
        ]
        status, _, body = await request(
            app, "/api/v1/session", "POST", spoofed, b'{"password":"password"}'
        )
        assert status == 403 and body["error"]["code"] == "INVALID_ORIGIN"

    asyncio.run(scenario())
