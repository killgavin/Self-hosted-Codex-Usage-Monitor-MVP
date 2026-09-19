"""Server-owned Bearer authentication for monitor REST routes."""

from hmac import compare_digest
from typing import Annotated

from fastapi import Header, Request
from fastapi.responses import JSONResponse


class InvalidServerToken(Exception):
    """Indicate missing or invalid monitor credentials without retaining them."""


class ServerTokenAuth:
    """Reusable FastAPI dependency for exact server-token authentication."""

    def __init__(self, expected_token: str | None) -> None:
        self._expected_token = expected_token

    async def __call__(
        self,
        authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    ) -> None:
        """Accept only an exact Bearer credential configured by this server."""

        if self._expected_token is None or authorization is None:
            raise InvalidServerToken

        scheme, separator, credential = authorization.partition(" ")
        if separator != " " or scheme.lower() != "bearer" or not credential:
            raise InvalidServerToken

        if not compare_digest(
            credential.encode("utf-8"),
            self._expected_token.encode("utf-8"),
        ):
            raise InvalidServerToken


async def invalid_server_token_handler(
    _request: Request,
    _error: InvalidServerToken,
) -> JSONResponse:
    """Return the fixed public error without echoing authorization input."""

    return JSONResponse(
        status_code=401,
        content={
            "error": {
                "code": "INVALID_SERVER_TOKEN",
                "message": "Invalid server token",
            }
        },
        headers={"WWW-Authenticate": "Bearer"},
    )
