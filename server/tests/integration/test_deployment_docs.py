"""Static documentation-contract checks for reconciled deployment guidance."""

from pathlib import Path
import re


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
README = REPOSITORY_ROOT / "README.md"
DEPLOYMENT = REPOSITORY_ROOT / "docs" / "deployment.md"
COMPOSE = REPOSITORY_ROOT / "docker-compose.yml"
DOCKERFILE = REPOSITORY_ROOT / "Dockerfile"
GITIGNORE = REPOSITORY_ROOT / ".gitignore"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_readme_describes_the_mvp_and_links_the_operational_guide() -> None:
    readme = _read(README)

    assert "MVP server and web dashboard" in readme
    assert "project skeleton" not in readme.lower()
    assert "CODEX_MONITOR_PASSWORD" in readme
    assert "openssl rand -hex 32" in readme
    assert "docker compose up -d --build" in readme
    assert "docs/deployment.md#configure-monitor-password-and-session-secret" in readme
    assert "docs/deployment.md" in readme
    assert "OpenAI credentials remain on that server" in readme
    assert "loopback" in readme
    for canonical_doc in (
        "docs/specification.md",
        "docs/design.md",
        "docs/test-plan.md",
        "docs/implementation-plan.md",
        "docs/implementation-status.md",
    ):
        assert canonical_doc in readme
    assert "Stage 10" in readme
    assert "T-64 through T-68 were verified" in readme
    assert "Debian 13 Docker runner" in readme
    assert "real Chrome 360px validation T-63 is PASS" in readme
    assert "`OVERALL: PASS` — `MVP COMPLETE`" in readme


def test_relative_markdown_links_resolve() -> None:
    for document in (README, DEPLOYMENT):
        for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", _read(document)):
            if target.startswith(("#", "http://", "https://", "mailto:")):
                continue
            assert (document.parent / target.split("#", 1)[0]).exists(), (document, target)


def test_guide_has_copyable_password_setup_and_health_commands() -> None:
    guide = _read(DEPLOYMENT)

    for command in (
        "git clone <repository-url> Self-hosted-Codex-Usage-Monitor-MVP",
        "docker compose up -d --build",
        "docker compose ps",
        "curl --fail http://127.0.0.1:8080/health",
    ):
        assert command in guide
    assert "openssl rand -hex 32" in guide
    assert "chmod 600 .env" in guide
    assert ".env" in guide and "private and uncommitted" in guide
    assert "fail closed" in guide or "fail-closed" in guide
    for endpoint in ("/api/v1/status", "/api/v1/account", "/api/v1/rate-limits"):
        assert endpoint in guide
    assert "expected response is `{\"status\":\"ok\"}`" in guide


def test_guide_states_the_safe_binding_and_exposure_boundary() -> None:
    guide = _read(DEPLOYMENT)

    assert "CODEX_MONITOR_BIND_HOST=127.0.0.1" in guide
    assert "CODEX_MONITOR_BIND_HOST=0.0.0.0" in guide
    assert "private, access-controlled LAN" in guide
    normalized = " ".join(guide.split())
    assert "Do not publish this service directly to the public internet" in normalized
    for protected_access in ("HTTPS", "Tailscale", "reverse proxy"):
        assert protected_access in guide
    assert "internal server bind is intentionally separate" in normalized


def test_guide_describes_the_official_login_boundary_without_private_paths() -> None:
    guide = _read(DEPLOYMENT)

    assert "official Codex/ChatGPT" in guide
    assert "device-code" in guide
    assert "verification URL" in guide
    assert "Do not use custom OAuth" in guide
    assert "OpenAI credentials in environment variables" in guide
    assert "direct browser-to-OpenAI requests" in guide
    assert "internal credential path" in guide
    forbidden = ("auth.json", ".codex", "/backend-api/", "OPENAI_API_KEY", "OPENAI_TOKEN")
    for marker in forbidden:
        assert marker.lower() not in guide.lower()


def test_guide_matches_compose_defaults_and_classifies_supported_variables() -> None:
    compose = _read(COMPOSE)
    guide = _read(DEPLOYMENT)
    expected_defaults = {
        "CODEX_VERSION": "0.155.1",
        "CODEX_MONITOR_IMAGE": "self-hosted-codex-usage-monitor:0.155.1",
        "CODEX_MONITOR_BIND_HOST": "127.0.0.1",
        "CODEX_MONITOR_PORT": "8080",
        "CODEX_MONITOR_PASSWORD": "required",
        "CODEX_MONITOR_SESSION_SECRET": "required",
        "CODEX_MONITOR_COOKIE_SECURE": "true",
        "CLOUDFLARE_TUNNEL_TOKEN": "unset",
        "CACHE_TTL_SECONDS": "60",
        "LOG_LEVEL": "info",
        "CODEX_MONITOR_HOME_VOLUME": "codex_monitor_home",
    }
    for variable, default in expected_defaults.items():
        assert f"`{variable}`" in guide
        if default in {"blank", "required", "unset"}:
            assert f"| {default} |" in guide
        else:
            assert f"`{default}`" in guide
        assert variable in compose

    assert 'CODEX_VERSION: "${CODEX_VERSION:-0.155.1}"' in compose
    assert 'image: "${CODEX_MONITOR_IMAGE:-self-hosted-codex-usage-monitor:0.155.1}"' in compose
    assert '"${CODEX_MONITOR_BIND_HOST:-127.0.0.1}:${CODEX_MONITOR_PORT:-8080}' in compose
    assert 'CODEX_MONITOR_PASSWORD: "${CODEX_MONITOR_PASSWORD:?Set CODEX_MONITOR_PASSWORD in your private .env}"' in compose
    assert 'CODEX_MONITOR_SESSION_SECRET: "${CODEX_MONITOR_SESSION_SECRET:?Set CODEX_MONITOR_SESSION_SECRET in your private .env}"' in compose
    assert 'CODEX_MONITOR_COOKIE_SECURE: "${CODEX_MONITOR_COOKIE_SECURE:-true}"' in compose
    assert 'CACHE_TTL_SECONDS: "${CACHE_TTL_SECONDS:-60}"' in compose
    assert 'LOG_LEVEL: "${LOG_LEVEL:-info}"' in compose
    assert 'name: "${CODEX_MONITOR_HOME_VOLUME:-codex_monitor_home}"' in compose
    assert "Build-time" in guide
    assert "Runtime" in guide
    assert "Host publish" in guide
    assert "Volume identity" in guide


def test_guide_matches_the_whole_home_persistence_contract() -> None:
    compose = _read(COMPOSE)
    dockerfile = _read(DOCKERFILE)
    guide = _read(DEPLOYMENT)

    assert "codex_monitor_home:/home/codex-monitor" in compose
    assert "codex_monitor_home` at the complete home" in guide
    assert "/home/codex-monitor" in guide
    assert "CODEX_MONITOR_HOME_VOLUME" in guide
    assert "docker compose down -v" in guide
    assert "delete" in guide.lower() and "credential state" in guide.lower()
    assert "internal credential path" in guide
    assert "runtime validation used only sanitized authenticated/unauthenticated state" in guide
    assert "USER codex-monitor" in dockerfile
    assert "HOME=/home/codex-monitor" in dockerfile
    assert "designed to preserve" in guide
    assert "Real Docker validation confirmed persistence" in guide


def test_private_compose_environment_files_are_ignored() -> None:
    gitignore = _read(GITIGNORE)

    assert re.search(r"(?m)^\.env$", gitignore)
    assert re.search(r"(?m)^\.env\.\*$", gitignore)


def test_guide_has_safe_lifecycle_troubleshooting_and_no_destructive_fix() -> None:
    guide = _read(DEPLOYMENT)

    for command in (
        "docker compose stop",
        "docker compose start",
        "docker compose restart",
        "docker compose up -d --build",
        "docker compose down",
        "docker compose logs --tail=100 monitor",
    ):
        assert command in guide
    assert "Do not delete the volume as a troubleshooting step" in " ".join(guide.split())
    assert "Do not manually seed or copy" in guide


def test_validation_status_records_real_docker_runtime_evidence() -> None:
    guide = _read(DEPLOYMENT)

    assert "## Validation status" in guide
    for test_id in ("T-64", "T-65", "T-66", "T-67", "T-68"):
        assert test_id in guide
        assert re.search(rf"{test_id} PASS", guide)
    assert "Debian 13 Docker runner" in guide
    assert "authenticated=false" in guide
    assert "authenticated=true" in guide
    assert "no-cache rebuild and forced container recreation" in guide
    assert "named volume remained `codex_monitor_home`" in guide
    assert "T-63 PASS — real installed Google Chrome at a 360px viewport" in guide
    assert "checked-in\n  mobile layout fixture reported PASS" in guide
    assert "The Final MVP Gate is complete" in guide
    assert "`OVERALL: PASS`" in guide
    assert "`MVP COMPLETE`" in guide


def test_documentation_does_not_add_private_endpoint_or_credential_provisioning() -> None:
    material = _read(README) + "\n" + _read(DEPLOYMENT)

    for marker in ("/backend-api/", "auth.json", ".codex", "OPENAI_API_KEY", "OPENAI_TOKEN"):
        assert marker.lower() not in material.lower()
    assert "direct browser-to-OpenAI" in material
    assert "OpenAI credentials remain on that server" in material
