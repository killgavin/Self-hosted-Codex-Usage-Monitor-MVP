"""Static safety and structure checks for the TASK-0901 container image."""

from pathlib import Path
import re


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCKERFILE = REPOSITORY_ROOT / "Dockerfile"
DOCKERIGNORE = REPOSITORY_ROOT / ".dockerignore"


def _dockerfile() -> str:
    return DOCKERFILE.read_text(encoding="utf-8")


def _dockerignore() -> str:
    return DOCKERIGNORE.read_text(encoding="utf-8")


def test_dockerfile_uses_named_non_latest_debian_stages_and_pinned_codex() -> None:
    dockerfile = _dockerfile()

    assert re.search(r"^FROM node:[^\s]+-bookworm-slim AS codex-builder$", dockerfile, re.MULTILINE)
    assert re.search(r"^FROM python:3\.12-[^\s]+-bookworm AS runtime$", dockerfile, re.MULTILINE)
    assert "ARG CODEX_VERSION=0.155.1" in dockerfile
    assert 'npm install --global --prefix /opt/codex --omit=dev --no-audit --no-fund "@openai/codex@${CODEX_VERSION}"' in dockerfile
    assert "/opt/codex/bin/codex --version" in dockerfile
    assert "latest" not in dockerfile.lower()


def test_dockerfile_copies_only_required_codex_runtime_and_cleans_apt() -> None:
    dockerfile = _dockerfile()

    assert "COPY --from=codex-builder /usr/local/bin/node /usr/local/bin/node" in dockerfile
    assert "COPY --from=codex-builder /opt/codex /opt/codex" in dockerfile
    assert "npm" not in dockerfile.split("FROM python:", 1)[1]
    assert "apt-get install --no-install-recommends" in dockerfile
    assert "rm -rf /var/lib/apt/lists/*" in dockerfile


def test_dockerfile_preserves_runtime_layout_and_docker_defaults() -> None:
    dockerfile = _dockerfile()

    assert "COPY server/requirements.txt" in dockerfile
    assert "requirements-dev.txt" not in dockerfile
    assert "COPY --chown=codex-monitor:codex-monitor server/app /opt/codex-monitor/server/app" in dockerfile
    assert "COPY --chown=codex-monitor:codex-monitor web /opt/codex-monitor/web" in dockerfile
    assert "PYTHONPATH=/opt/codex-monitor/server" in dockerfile
    assert "CODEX_MONITOR_HOST=0.0.0.0" in dockerfile
    assert "CODEX_MONITOR_PORT=8080" in dockerfile
    assert "CODEX_EXECUTABLE=/opt/codex/bin/codex" in dockerfile
    assert "EXPOSE 8080" in dockerfile
    assert 'CMD ["python", "-m", "app"]' in dockerfile


def test_dockerfile_runs_as_dedicated_user_with_writable_home() -> None:
    dockerfile = _dockerfile()

    assert "useradd --create-home --home-dir /home/codex-monitor" in dockerfile
    assert "groupadd --gid 10001 codex-monitor" in dockerfile
    assert "--uid 10001 --gid 10001" in dockerfile
    assert "HOME=/home/codex-monitor" in dockerfile
    assert "PYTHONDONTWRITEBYTECODE=1" in dockerfile
    assert re.search(r"^USER codex-monitor$", dockerfile, re.MULTILINE)
    assert not re.search(r"^USER\s+root\s*$", dockerfile, re.MULTILINE | re.IGNORECASE)


def test_dockerfile_contains_no_credential_or_private_endpoint_instructions() -> None:
    dockerfile = _dockerfile()

    private_endpoint = "/backend-api/" + "wham"
    assert private_endpoint not in dockerfile
    assert "auth.json" not in dockerfile.lower()
    assert not re.search(
        r"^(?:ARG|ENV)\s+.*(?:TOKEN|PASSWORD|SECRET|CREDENTIAL|COOKIE|API_KEY)",
        dockerfile,
        re.MULTILINE | re.IGNORECASE,
    )
    assert "CODEX_MONITOR_API_TOKEN" not in dockerfile
    assert "--mount=type=secret" not in dockerfile


def test_dockerignore_excludes_sensitive_and_unneeded_context_but_not_runtime_inputs() -> None:
    dockerignore = _dockerignore()

    for pattern in (".git", ".codex", "**/.codex", ".env", "auth.json", "__pycache__/", "server/tests/", "docs/", "build/"):
        assert pattern in dockerignore
    assert "server/requirements.txt" not in dockerignore
    assert "server/app" not in dockerignore
    assert "web" not in dockerignore
