"""Run the Usage Monitor HTTP server with environment-backed settings."""

import uvicorn

from app.config import get_settings


def main() -> None:
    """Start uvicorn using the current process environment configuration."""

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level,
    )


if __name__ == "__main__":
    main()
