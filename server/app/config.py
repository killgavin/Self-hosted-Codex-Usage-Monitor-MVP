"""Small configuration boundary for the Codex executable.

This module only reads configuration and resolves an executable name. Process
startup and lifecycle management belong to a later task.
"""

from dataclasses import dataclass, field
import os
import shutil


DEFAULT_CODEX_EXECUTABLE = "codex"


@dataclass(frozen=True)
class Settings:
    """Runtime settings needed by the server and Codex process boundary."""

    codex_executable: str = DEFAULT_CODEX_EXECUTABLE
    server_api_token: str | None = field(default=None, repr=False)

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
        return cls(
            codex_executable=executable,
            server_api_token=configured_token or None,
        )


def get_settings() -> Settings:
    """Return settings loaded from the current process environment."""

    return Settings.from_environment()


def resolve_codex_executable(settings: Settings | None = None) -> str | None:
    """Resolve the configured executable through ``PATH`` without launching it."""

    active_settings = settings if settings is not None else get_settings()
    return shutil.which(active_settings.codex_executable)
