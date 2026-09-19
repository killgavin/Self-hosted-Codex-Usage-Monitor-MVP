"""Environment-backed server configuration without runtime side effects."""

from dataclasses import dataclass, field
import math
import os
import shutil


DEFAULT_CODEX_EXECUTABLE = "codex"
DEFAULT_CACHE_TTL_SECONDS = 60.0


@dataclass(frozen=True)
class Settings:
    """Runtime settings needed by the server and Codex process boundary."""

    codex_executable: str = DEFAULT_CODEX_EXECUTABLE
    server_api_token: str | None = field(default=None, repr=False)
    cache_ttl_seconds: float = DEFAULT_CACHE_TTL_SECONDS

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

        configured_token = os.getenv("CODEX_MONITOR_API_TOKEN")
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
        return cls(
            codex_executable=executable,
            server_api_token=configured_token or None,
            cache_ttl_seconds=cache_ttl_seconds,
        )


def get_settings() -> Settings:
    """Return settings loaded from the current process environment."""

    return Settings.from_environment()


def resolve_codex_executable(settings: Settings | None = None) -> str | None:
    """Resolve the configured executable through ``PATH`` without launching it."""

    active_settings = settings if settings is not None else get_settings()
    return shutil.which(active_settings.codex_executable)
