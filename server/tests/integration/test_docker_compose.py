"""Deterministic static safety checks for the TASK-0902 compose file."""

from pathlib import Path
import re


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
COMPOSE = REPOSITORY_ROOT / "docker-compose.yml"


def _compose() -> str:
    return COMPOSE.read_text(encoding="utf-8")


def _environment_block(compose: str) -> str:
    match = re.search(
        r"(?ms)^    environment:\n(?P<body>.*?)(?=^    [a-zA-Z_]|^\s*\Z)",
        compose,
    )
    assert match is not None
    return match.group("body")


def test_compose_defines_one_monitor_service_with_pinned_local_image() -> None:
    compose = _compose()

    assert re.search(r"(?m)^services:\n  monitor:\n", compose)
    service_body = re.search(r"(?ms)^  monitor:\n(?P<body>.*?)(?=^volumes:)", compose)
    assert service_body is not None
    assert not re.search(r"(?m)^  [a-zA-Z0-9_-]+:\n", service_body.group("body"))
    assert "context: ." in service_body.group("body")
    assert "dockerfile: Dockerfile" in service_body.group("body")
    assert 'CODEX_VERSION: "${CODEX_VERSION:-0.155.1}"' in compose
    assert 'image: "${CODEX_MONITOR_IMAGE:-self-hosted-codex-usage-monitor:0.155.1}"' in compose


def test_compose_publishes_loopback_by_default_and_synchronizes_port() -> None:
    compose = _compose()
    environment = _environment_block(compose)

    assert 'CODEX_MONITOR_HOST: "0.0.0.0"' in environment
    assert 'CODEX_MONITOR_PORT: "${CODEX_MONITOR_PORT:-8080}"' in environment
    assert (
        '"${CODEX_MONITOR_BIND_HOST:-127.0.0.1}:${CODEX_MONITOR_PORT:-8080}:'
        '${CODEX_MONITOR_PORT:-8080}"'
    ) in compose
    assert "0.0.0.0:${CODEX_MONITOR_PORT" not in compose


def test_compose_passes_only_monitor_configuration_and_fails_closed() -> None:
    compose = _compose()
    environment = _environment_block(compose)

    assert set(re.findall(r"(?m)^      ([A-Z][A-Z0-9_]+):", environment)) == {
        "CODEX_MONITOR_HOST",
        "CODEX_MONITOR_PORT",
        "CODEX_MONITOR_API_TOKEN",
        "CACHE_TTL_SECONDS",
        "LOG_LEVEL",
    }
    assert 'CODEX_MONITOR_API_TOKEN: "${CODEX_MONITOR_API_TOKEN:-}"' in environment
    assert re.search(r"CODEX_MONITOR_API_TOKEN:\s*\"\$\{[^}]+:-\}\"", environment)
    assert "OPENAI_API_KEY" not in environment
    assert "OPENAI_TOKEN" not in environment
    assert "CODEX_AUTH" not in environment


def test_compose_healthcheck_is_local_credential_free_and_bounded() -> None:
    compose = _compose()
    healthcheck = re.search(r"(?ms)^    healthcheck:\n(?P<body>.*?)(?=^    volumes:)", compose)
    assert healthcheck is not None
    body = healthcheck.group("body")

    assert "- CMD" in body
    assert "- python" in body
    assert "urllib.request" in body
    assert "http://127.0.0.1:{port}/health" in body
    assert 'os.environ["CODEX_MONITOR_PORT"]' in body
    assert "timeout=3" in body
    assert re.search(r"(?m)^      interval: (?:[1-9]|[1-5][0-9])s$", body)
    assert re.search(r"(?m)^      timeout: (?:[1-9]|[1-5][0-9])s$", body)
    assert re.search(r"(?m)^      retries: [1-9][0-9]*$", body)
    assert re.search(r"(?m)^      start_period: (?:[1-9]|[1-5][0-9])s$", body)
    assert "Authorization" not in body
    assert "CODEX_MONITOR_API_TOKEN" not in body


def test_compose_enforces_non_privileged_runtime() -> None:
    compose = _compose()

    assert "init: true" in compose
    assert "restart: unless-stopped" in compose
    assert "no-new-privileges:true" in compose
    assert re.search(r"(?m)^    cap_drop:\n      - ALL$", compose)
    assert re.search(r"(?m)^    stop_grace_period: [1-9][0-9]*s$", compose)
    assert "privileged:" not in compose
    assert "network_mode:" not in compose
    assert "pid:" not in compose
    assert "ipc:" not in compose
    assert "user:" not in compose
    assert "/var/run/docker.sock" not in compose


def test_compose_uses_named_whole_home_volume_and_no_sensitive_paths() -> None:
    compose = _compose()

    assert "      - codex_monitor_home:/home/codex-monitor" in compose
    assert re.search(r"(?m)^volumes:\n  codex_monitor_home:\s*$", compose)
    for forbidden in ("auth.json", "/backend-api/wham", "OPENAI_API_KEY", "OPENAI_TOKEN"):
        assert forbidden not in compose
