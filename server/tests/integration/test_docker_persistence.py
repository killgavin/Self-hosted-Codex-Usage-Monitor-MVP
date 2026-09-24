"""Static safety checks for the TASK-0903 Compose persistence contract."""

from pathlib import Path
import re


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
COMPOSE = REPOSITORY_ROOT / "docker-compose.yml"
DOCKERFILE = REPOSITORY_ROOT / "Dockerfile"

VOLUME_NAME_EXPRESSION = "${CODEX_MONITOR_HOME_VOLUME:-codex_monitor_home}"
VOLUME_NAME_DEFAULT = "codex_monitor_home"
VOLUME_KEY = "codex_monitor_home"
HOME_TARGET = "/home/codex-monitor"


def _compose() -> str:
    return COMPOSE.read_text(encoding="utf-8")


def _dockerfile() -> str:
    return DOCKERFILE.read_text(encoding="utf-8")


def _volume_block(compose: str) -> str:
    match = re.search(r"(?ms)^volumes:\n(?P<body>.*)\Z", compose)
    assert match is not None
    return match.group("body")


def _service_volume_block(compose: str) -> str:
    match = re.search(r"(?ms)^    volumes:\n(?P<body>.*?)(?=^  [a-zA-Z0-9_-]+:\n|^volumes:)", compose)
    assert match is not None
    return match.group("body")


def _volume_name_expression(compose: str) -> str:
    volume_block = _volume_block(compose)
    match = re.search(
        r"(?m)^  codex_monitor_home:\n    name: [\"'](?P<name>[^\"']+)[\"']$",
        volume_block,
    )
    assert match is not None
    return match.group("name")


def _resolve_volume_name(expression: str, override: str | None = None) -> str:
    match = re.fullmatch(r"\$\{CODEX_MONITOR_HOME_VOLUME:-([^}]+)\}", expression)
    assert match is not None
    return override or match.group(1)


def test_compose_mounts_one_named_volume_to_the_complete_non_root_home() -> None:
    compose = _compose()

    mounts = re.findall(
        r"(?m)^      - (?P<source>[^\s:]+):(?P<target>[^\s]+)$",
        _service_volume_block(compose),
    )
    assert mounts == [(VOLUME_KEY, HOME_TARGET)]
    service_volumes = _service_volume_block(compose)
    assert not re.search(r"(?m)^      - (?:/|\./|\.\./|[A-Za-z]:[\\/])", service_volumes)
    assert not re.search(r"(?m)^      - [^\s:]+$", service_volumes)


def test_compose_volume_target_matches_dockerfile_home_contract() -> None:
    dockerfile = _dockerfile()

    assert f"--home-dir {HOME_TARGET}" in dockerfile
    assert f"HOME={HOME_TARGET}" in dockerfile
    assert re.search(r"^USER codex-monitor$", dockerfile, re.MULTILINE)
    assert re.search(r"--uid 10001 --gid 10001", dockerfile)
    assert re.search(
        rf"(?m)^      - {re.escape(VOLUME_KEY)}:{re.escape(HOME_TARGET)}$", _compose()
    )


def test_compose_volume_has_stable_explicit_identity_with_optional_override() -> None:
    compose = _compose()

    expression = _volume_name_expression(compose)
    assert expression == VOLUME_NAME_EXPRESSION
    assert _resolve_volume_name(expression) == VOLUME_NAME_DEFAULT
    assert (
        _resolve_volume_name(expression, "team_codex_monitor_home")
        == "team_codex_monitor_home"
    )


def test_reconstruction_resolves_to_the_same_volume_identity() -> None:
    expression = _volume_name_expression(_compose())

    initial = _resolve_volume_name(expression)
    reconstructed = _resolve_volume_name(_volume_name_expression(_compose()))
    assert initial == VOLUME_NAME_DEFAULT
    assert reconstructed == initial

    override = "shared_codex_monitor_home"
    assert _resolve_volume_name(expression, override) == override
    assert _resolve_volume_name(_volume_name_expression(_compose()), override) == override


def test_persistence_contract_does_not_add_credential_or_volume_lifecycle_behavior() -> None:
    compose = _compose()

    for forbidden in (
        ".codex",
        "auth.json",
        "/backend-api/wham",
        "nocopy",
        "volume-nocopy",
        "docker volume rm",
        "docker compose down -v",
    ):
        assert forbidden not in compose.lower()

    assert not re.search(r"(?i)\b(?:credential|credentials|parser|seed)\b", compose)
    assert not re.search(r"(?i)\b(?:copy|parse)\b.*(?:auth|credential)", compose)
    assert not re.search(
        r"(?i)\b(?:rm|remove|delete|deletion)\b.*(?:volume|home)", compose
    )
