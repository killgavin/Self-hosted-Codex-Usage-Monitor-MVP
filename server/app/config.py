"""Environment-backed server configuration without runtime side effects."""

from dataclasses import dataclass
import math
import os
import shutil


DEFAULT_CODEX_EXECUTABLE = "codex"
DEFAULT_CACHE_TTL_SECONDS = 60.0
DEFAULT_MONITOR_HOST = "127.0.0.1"
DEFAULT_MONITOR_PORT = 8080
DEFAULT_LOG_LEVEL = "info"
VALID_LOG_LEVELS = frozenset({"critical", "error", "warning", "info", "debug", "trace"})

INVALID_PORT_MESSAGE = "CODEX_MONITOR_PORT must be an integer between 1 and 65535"
INVALID_LOG_LEVEL_MESSAGE = (
    "LOG_LEVEL must be one of: critical, error, warning, info, debug, trace"
)


@dataclass(frozen=True)
class Settings:
    """Runtime settings needed by the server and Codex process boundary."""

    codex_executable: str = DEFAULT_CODEX_EXECUTABLE
    cache_ttl_seconds: float = DEFAULT_CACHE_TTL_SECONDS
    host: str = DEFAULT_MONITOR_HOST
    port: int = DEFAULT_MONITOR_PORT
    log_level: str = DEFAULT_LOG_LEVEL

    @classmethod
    def from_environment(cls) -> "Settings":
        """Build settings from environment variables without starting a process."""

        configured_executable = os.getenv("CODEX_EXECUTABLE")
        if configured_executable is None:
            executable = DEFAULT_CODEX_EXECUTABLE
        else:
            # An empty or whitespace-only override falls back explicitly to
            # the safe command default instead of becoming ambiguous.
            executable = configured_executable.strip() or DEFAULT_CODEX_EXECUTABLE

        configured_ttl = os.getenv("CACHE_TTL_SECONDS")
        if configured_ttl is None:
            cache_ttl_seconds = DEFAULT_CACHE_TTL_SECONDS
        else:
            try:
                cache_ttl_seconds = float(configured_ttl)
            except ValueError as error:
                raise ValueError("CACHE_TTL_SECONDS must be a positive finite number") from error
            if not math.isfinite(cache_ttl_seconds) or cache_ttl_seconds <= 0:
                raise ValueError("CACHE_TTL_SECONDS must be a positive finite number")

        configured_host = os.getenv("CODEX_MONITOR_HOST")
        host = configured_host.strip() if configured_host is not None else ""
        host = host or DEFAULT_MONITOR_HOST

        configured_port = os.getenv("CODEX_MONITOR_PORT")
        if configured_port is None:
            port = DEFAULT_MONITOR_PORT
        else:
            try:
                port = int(configured_port.strip())
            except ValueError as error:
                raise ValueError(INVALID_PORT_MESSAGE) from error
            if not 1 <= port <= 65535:
                raise ValueError(INVALID_PORT_MESSAGE)

        configured_log_level = os.getenv("LOG_LEVEL")
        log_level = configured_log_level.strip().lower() if configured_log_level else ""
        if not log_level:
            log_level = DEFAULT_LOG_LEVEL
        elif log_level not in VALID_LOG_LEVELS:
            raise ValueError(INVALID_LOG_LEVEL_MESSAGE)

        return cls(
            codex_executable=executable,
            cache_ttl_seconds=cache_ttl_seconds,
            host=host,
            port=port,
            log_level=log_level,
        )


def get_settings() -> Settings:
    """Return settings loaded from the current process environment."""

    return Settings.from_environment()


def resolve_codex_executable(settings: Settings | None = None) -> str | None:
    """Resolve the configured executable through ``PATH`` without launching it."""

    active_settings = settings if settings is not None else get_settings()
    return shutil.which(active_settings.codex_executable)
