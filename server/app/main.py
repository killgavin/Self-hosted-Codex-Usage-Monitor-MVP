"""Minimal FastAPI application entry point for the MVP server."""

from fastapi import FastAPI


app = FastAPI(title="Self-hosted Codex Usage Monitor")


@app.get("/health")
async def health() -> dict[str, str]:
    """Return the basic process health contract for the Stage 0 smoke test."""

    return {"status": "ok"}
