"""Minimal FastAPI application entry point for the MVP server."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.account import create_account_router
from app.api.login import router as login_router
from app.api.status import create_status_router
from app.codex.adapter import CodexAppServerAdapter
from app.config import Settings, get_settings
from app.security.server_token import InvalidServerToken, invalid_server_token_handler
from app.services.account import AccountService
from app.services.auth import AuthService


def create_app(
    auth_service: AuthService | None = None,
    settings: Settings | None = None,
    account_service: AccountService | None = None,
) -> FastAPI:
    """Create the server without starting Codex or making network requests."""

    application = FastAPI(title="Self-hosted Codex Usage Monitor")
    active_settings = settings if settings is not None else get_settings()
    adapter = CodexAppServerAdapter()
    application.state.settings = active_settings
    application.state.auth_service = (
        auth_service if auth_service is not None else AuthService(adapter)
    )
    application.state.account_service = (
        account_service if account_service is not None else AccountService(adapter)
    )
    application.add_exception_handler(InvalidServerToken, invalid_server_token_handler)
    application.include_router(login_router)
    application.include_router(create_status_router(active_settings.server_api_token))
    application.include_router(create_account_router(active_settings.server_api_token))
    web_root = Path(__file__).resolve().parents[2] / "web"
    application.mount("/assets", StaticFiles(directory=web_root / "assets"), name="assets")

    @application.get("/")
    async def index() -> FileResponse:
        """Serve the server-hosted login page."""

        return FileResponse(web_root / "index.html", media_type="text/html")

    @application.get("/health")
    async def health() -> dict[str, str]:
        """Return the basic process health contract for the Stage 0 smoke test."""

        return {"status": "ok"}

    return application


app = create_app()
