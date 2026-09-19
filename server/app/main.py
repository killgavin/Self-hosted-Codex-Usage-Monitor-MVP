"""Minimal FastAPI application entry point for the MVP server."""

from fastapi import FastAPI

from app.api.login import router as login_router
from app.codex.adapter import CodexAppServerAdapter
from app.services.auth import AuthService


def create_app(auth_service: AuthService | None = None) -> FastAPI:
    """Create the server without starting Codex or making network requests."""

    application = FastAPI(title="Self-hosted Codex Usage Monitor")
    application.state.auth_service = (
        auth_service if auth_service is not None else AuthService(CodexAppServerAdapter())
    )
    application.include_router(login_router)

    @application.get("/health")
    async def health() -> dict[str, str]:
        """Return the basic process health contract for the Stage 0 smoke test."""

        return {"status": "ok"}

    return application


app = create_app()
