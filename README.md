# Self-hosted Codex Usage Monitor

This repository contains the self-hosted MVP server and web dashboard for
reading Codex account status and rate limits through the official Codex
app-server interface. The monitor is intended to run on a machine you control;
OpenAI credentials remain on that server and are never sent to the browser or
returned by the monitor API.

## Architecture and security boundary

The FastAPI monitor starts the official Codex app-server as a local process and
exposes a same-origin REST API plus dashboard. The browser talks only to the
monitor. The monitor's separate `CODEX_MONITOR_API_TOKEN` protects data routes;
it is not an OpenAI credential. The Compose setup publishes to loopback by
default, drops Linux capabilities, and runs the image as its dedicated runtime
user. Remote access should use an HTTPS reverse proxy, Tailscale, or another
equivalent protected path—not direct public exposure.

## Quick start

Docker Engine with Compose v2 is required. The complete, copyable setup,
configuration, login, persistence, and troubleshooting instructions are in
[`docs/deployment.md`](docs/deployment.md). The short path is:

```sh
umask 077
printf 'CODEX_MONITOR_API_TOKEN=%s\n' "$(openssl rand -hex 32)" > .env
chmod 600 .env
docker compose up -d --build
```

The monitor token must be non-blank for the protected data endpoints; follow
the [token setup instructions](docs/deployment.md#configure-the-monitor-token)
before running Compose.

Then open `http://127.0.0.1:8080/` and use the dashboard's official
Codex/ChatGPT device-code login flow.

This repository has static, automated, and real runtime evidence for the
documented contracts. T-64 through T-68 were verified on a Debian 13 Docker runner
during Stage 10, covering image build, healthy Compose startup, clean-volume
unauthenticated behavior, restart persistence, and rebuild/recreate persistence.
The real Chrome 360px validation T-63 is PASS, completing the Final MVP Gate.
Overall status: `OVERALL: PASS` — `MVP COMPLETE`.

## Canonical documentation

- [`docs/specification.md`](docs/specification.md) — requirements and security invariants
- [`docs/design.md`](docs/design.md) — architecture and implementation design
- [`docs/test-plan.md`](docs/test-plan.md) — test matrix and evidence rules
- [`docs/implementation-plan.md`](docs/implementation-plan.md) — staged task plan
- [`docs/implementation-status.md`](docs/implementation-status.md) — current implementation evidence
- [`docs/deployment.md`](docs/deployment.md) — operational deployment guide
