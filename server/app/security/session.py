"""Guard dashboard APIs with the server-side Codex login state."""

from fastapi import Request
from fastapi.responses import JSONResponse


async def session_guard(request: Request, call_next):
    """Allow login lifecycle routes; require completed Codex login for data APIs."""
    path = request.url.path
    login_routes = {
        "/api/v1/login", "/api/v1/login/status",
        "/api/v1/login/cancel", "/api/v1/logout",
    }
    if path.startswith("/api/") and path not in login_routes:
        status = request.app.state.auth_service.status
        if status.state.value != "COMPLETED":
            return JSONResponse(
                status_code=401,
                content={"error": {"code": "AUTH_REQUIRED", "message": "ChatGPT login required"}},
            )
    return await call_next(request)
