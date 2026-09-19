"""Authenticated process-status REST endpoint."""

from fastapi import APIRouter, Depends

from app.security.server_token import ServerTokenAuth


def create_status_router(server_api_token: str | None) -> APIRouter:
    """Build the status router with its server-owned credential boundary."""

    router = APIRouter(
        prefix="/api/v1",
        tags=["status"],
        dependencies=[Depends(ServerTokenAuth(server_api_token))],
    )

    @router.get("/status")
    async def status() -> dict[str, str]:
        """Report that the HTTP process is available without starting Codex."""

        return {"status": "ok"}

    return router
