"""Authenticated process-status REST endpoint."""

from fastapi import APIRouter, Request


def create_status_router() -> APIRouter:
    """Build the status router; the application session middleware protects it."""

    router = APIRouter(
        prefix="/api/v1",
        tags=["status"],
    )

    @router.get("/status")
    async def status(request: Request) -> dict[str, str]:
        """Report the sanitized application/runtime availability status."""

        adapter = getattr(request.app.state, "adapter", None)
        runtime_status = getattr(request.app.state, "runtime_status", "ok")
        runtime_started = getattr(request.app.state, "runtime_started", False)
        if runtime_started and runtime_status == "ok" and adapter is not None:
            is_available = getattr(adapter, "is_available", None)
            if callable(is_available) and not is_available():
                request.app.state.runtime_status = "degraded"
                runtime_status = "degraded"
        return {"status": "degraded" if runtime_status == "degraded" else "ok"}

    return router
