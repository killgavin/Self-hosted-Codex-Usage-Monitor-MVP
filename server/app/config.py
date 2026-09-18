"""Small configuration boundary for the Codex executable.

This module only reads configuration and resolves an executable name. Process
startup and lifecycle management belong to a later task.
"""

from dataclasses import dataclass
import os
import shutil


DEFAULT_CODEX_EXECUTABLE = "codex"


@dataclass(frozen=True)
class Settings:
    """Runtime settings needed by the Codex process boundary."""

    codex_executable: str = DEFAULT_CODEX_EXECUTABLE

    @classmethod
    def from_environment(cls) -> "Settings":
        """Build settings from environment variables without starting a process."""

        configured = os.getenv("CODEX_EXECUTABLE")
        if configured is None:
            return cls()

        # An empty or whitespace-only override falls back explicitly to the
        # safe command default instead of becoming an ambiguous executable.
        executable = configured.strip()
        return cls(executable or DEFAULT_CODEX_EXECUTABLE)


def get_settings() -> Settings:
    """Return settings loaded from the current process environment."""

    return Settings.from_environment()


def resolve_codex_executable(settings: Settings | None = None) -> str | None:
    """Resolve the configured executable through ``PATH`` without launching it."""

    active_settings = settings if settings is not None else get_settings()
    return shutil.which(active_settings.codex_executable)
