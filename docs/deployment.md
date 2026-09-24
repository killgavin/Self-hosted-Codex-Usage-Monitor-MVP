# Deployment guide

This guide deploys the self-hosted MVP with the checked-in `Dockerfile` and
`docker-compose.yml`. It covers the supported Compose contract and the
sanitized real runtime evidence recorded in [Validation Status](#validation-status).

## Prerequisites

- Docker Engine with Docker Compose v2 (`docker compose version`).
- Git, to clone the repository.
- OpenSSL on the host if you use the token-generation command below.
- A host that can keep the named Docker volume and reach the official Codex
  device-code login service from the Codex app-server process.

Clone the repository and enter it:

```sh
git clone <repository-url> Self-hosted-Codex-Usage-Monitor-MVP
cd Self-hosted-Codex-Usage-Monitor-MVP
```

Replace `<repository-url>` with the repository URL. Do not put a real token or
other credential in this document or in a shell history that will be shared.

## Build and start

From the repository root, build the pinned Codex CLI image and start the
monitor in the background:

```sh
docker compose up -d --build
docker compose ps
```

The default browser URL is <http://127.0.0.1:8080/>. A direct health check is:

```sh
curl --fail http://127.0.0.1:8080/health
```

The expected response is `{"status":"ok"}`. The Compose healthcheck performs
the same local request inside the container with a short timeout; it does not
send a monitor token.

## Binding and exposure

Compose publishes to loopback by default with
`CODEX_MONITOR_BIND_HOST=127.0.0.1`. This is the safe default for a single
machine. To publish on all host interfaces for a private LAN, set the
host-publish override explicitly:

```sh
CODEX_MONITOR_BIND_HOST=0.0.0.0 docker compose up -d
```

This binds the published port on every host interface, so use it only on a
private, access-controlled LAN or equivalent protected network. Do not publish
this service directly to the public internet. If access from outside the host
is required, use HTTPS, Tailscale, or a properly configured reverse proxy with
its own access controls and network policy. The container's internal server
bind is intentionally separate from the host-publish setting; the latter
controls which host interface is reachable.

Compose fixes the container's internal `CODEX_MONITOR_HOST` to `0.0.0.0` so
the service can receive traffic from the published port. That internal bind is
not a recommendation to expose the host publicly and is not the host interface
selected by `CODEX_MONITOR_BIND_HOST`.

### Cloudflare Tunnel

For remote browser access without opening an inbound router port, use a named
Cloudflare Tunnel. Add the intended hostname as a Cloudflare Access
self-hosted application first and create an Allow policy for your own email;
Cloudflare warns that a public hostname route without Access is available to
anyone on the internet. Then create a Tunnel and configure its published
hostname route to `http://monitor:8080`.

In the tunnel setup, choose Docker and copy its tunnel token into the private
`.env` file as `CLOUDFLARE_TUNNEL_TOKEN=...`. Start the optional connector:

```sh
docker compose up -d
docker compose --profile cloudflare up -d cloudflared
```

The connector shares the Compose network with `monitor`, so its origin target
is the service name `http://monitor:8080`. Keep the host-published Monitor port
bound to `127.0.0.1`; do not use Cloudflare Tunnel Funnel or create an
unauthenticated public hostname. Browse to the HTTPS hostname configured in
Cloudflare after Access has allowed your account.

## Official login flow

Open the dashboard and select **Log in**. Complete the official Codex/ChatGPT
device-code flow using the verification URL and user code shown by the
dashboard. The Codex app-server owns the upstream authentication lifecycle;
the browser talks only to the monitor's same-origin login routes.

Do not use custom OAuth, put OpenAI credentials in environment variables, make
direct browser-to-OpenAI requests, or manually copy/seed credential files.
This guide intentionally does not name or depend on an internal credential
path, file layout, or UID/permission assumption. Those details belong to the
Codex app-server and must be verified at runtime rather than guessed.

## Configuration contract

The following are the supported Compose variables. Defaults below are taken
from the checked-in Compose/Dockerfile contract.

| Variable | Default | Where it applies | Purpose |
| --- | --- | --- | --- |
| `CODEX_VERSION` | `0.155.1` | Build-time | Official Codex CLI version passed as the Docker build argument. |
| `CODEX_MONITOR_IMAGE` | `self-hosted-codex-usage-monitor:0.155.1` | Image identity | Local image name/tag used by Compose. |
| `CODEX_MONITOR_BIND_HOST` | `127.0.0.1` | Host publish | Host interface/address on the left side of the port mapping. |
| `CODEX_MONITOR_PORT` | `8080` | Runtime + host publish | Container listening port and the published host port. |
| `CLOUDFLARE_TUNNEL_TOKEN` | unset | Optional Cloudflare profile | Private connector token; only needed when running the `cloudflared` profile. |
| `CACHE_TTL_SECONDS` | `60` | Runtime | In-memory rate-limit cache TTL. |
| `LOG_LEVEL` | `info` | Runtime | Application log level (`critical`, `error`, `warning`, `info`, `debug`, or `trace`). |
| `CODEX_MONITOR_HOME_VOLUME` | `codex_monitor_home` | Volume identity | Optional stable named-volume override. |

For example, this changes only the host-published port while retaining the
same container port contract:

```sh
CODEX_MONITOR_PORT=9090 docker compose up -d --build
```

When changing `CODEX_VERSION`, rebuild the image. Runtime variables are read
when the container is created or recreated; use `docker compose up -d` after
changing them.

## Persistence and updates

Compose mounts the named volume `codex_monitor_home` at the complete home
directory `/home/codex-monitor`. The volume's stable identity is
`codex_monitor_home` unless `CODEX_MONITOR_HOME_VOLUME` supplies an explicit
override. This is designed to preserve the Codex app-server's configuration and
credential state across a normal stop, restart, container recreation, or image
rebuild. Real Docker validation confirmed persistence across restart and across
no-cache rebuild with forced container recreation.

The application owns the contents of that whole-home volume. Do not infer an
internal credential path or change ownership based on an example; the runtime validation used only sanitized authenticated/unauthenticated state and did not inspect credential details.

Normal lifecycle and update commands:

```sh
docker compose stop
docker compose start
docker compose restart
docker compose up -d --build
docker compose down
```

To update, pull the desired repository revision, review any `CODEX_VERSION`
change, and run `docker compose up -d --build`. `docker compose down` removes
the container and network but keeps the named volume. **Do not run
`docker compose down -v` unless you intentionally want to delete
`codex_monitor_home` and all persisted configuration and credential state.**

## Basic troubleshooting

- Check state and health with `docker compose ps` and
  `curl --fail http://127.0.0.1:8080/health` (adjust the port if configured).
- If a protected dashboard request returns `401`, check that the private `.env` is in the compose project directory and both required
  settings are present. Do not disclose either value while diagnosing the issue.
- If the browser cannot connect, verify the configured
  `CODEX_MONITOR_BIND_HOST`, `CODEX_MONITOR_PORT`, host firewall, and any port
  conflict with `docker compose ps`. Keep the listener on loopback unless a
  private LAN or protected HTTPS/Tailscale/reverse-proxy path is intentional.
- Inspect bounded service output with `docker compose logs --tail=100 monitor`.
  Do not paste logs containing private configuration into a public report.
- If health is `ok` but the dashboard reports degraded Codex availability,
  use the dashboard's official login flow and check that the Codex CLI image
  was rebuilt after a `CODEX_VERSION` change. Do not manually seed or copy
  credentials.
- If a restart or rebuild appears not to retain state, confirm that the same
  `CODEX_MONITOR_HOME_VOLUME` value is being used. Do not delete the volume as
  a troubleshooting step.

## Validation status

Static and automated documentation prerequisites pass when the deployment-doc
contract suite and existing Dockerfile/Compose/persistence static suites pass.
In addition, a Debian 13 Docker runner supplied the following sanitized Stage
10 runtime evidence:

- T-64 PASS — Docker Compose image build.
- T-65 PASS — Compose startup and healthy container.
- T-66 PASS — clean named-volume first start reported `authenticated=false`.
- T-67 PASS — container restart retained `authenticated=true`.
- T-68 PASS — no-cache rebuild and forced container recreation retained
  `authenticated=true`.

Real browser validation also passed:

- T-63 PASS — real installed Google Chrome at a 360px viewport; the checked-in
  mobile layout fixture reported PASS with no required horizontal overflow.

The named volume remained `codex_monitor_home` and the container remained
healthy. No account identity, token, quota, credential path, or raw protocol
payload is recorded here. The Final MVP Gate is complete: `OVERALL: PASS` and
`MVP COMPLETE`.

See the [implementation status ledger](implementation-status.md) and the
[test plan](test-plan.md) for the evidence rules and final validation record.
