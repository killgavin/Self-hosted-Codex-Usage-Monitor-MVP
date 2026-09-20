# Build the official Codex CLI separately so the runtime image contains only
# the Node runtime and the installed CLI package that the server needs.
FROM node:22-bookworm-slim AS codex-builder

ARG CODEX_VERSION=0.155.1

RUN npm install --global --prefix /opt/codex --omit=dev --no-audit --no-fund "@openai/codex@${CODEX_VERSION}" \
    && /opt/codex/bin/codex --version

# The application runtime does not need npm, the Node headers, or the builder
# image's global modules.  The prefix retains the executable wrapper and its
# package layout so the wrapper can resolve @openai/codex at runtime.
FROM python:3.12-slim-bookworm AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    CODEX_MONITOR_HOST=0.0.0.0 \
    CODEX_MONITOR_PORT=8080 \
    CODEX_EXECUTABLE=/opt/codex/bin/codex \
    PYTHONPATH=/opt/codex-monitor/server \
    HOME=/home/codex-monitor \
    PATH=/opt/codex/bin:/usr/local/bin:${PATH}

RUN apt-get update \
    && apt-get install --no-install-recommends --yes ca-certificates libgcc-s1 libstdc++6 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 codex-monitor \
    && useradd --create-home --home-dir /home/codex-monitor --uid 10001 --gid 10001 --shell /usr/sbin/nologin codex-monitor \
    && install --directory --owner codex-monitor --group codex-monitor /opt/codex-monitor

COPY --from=codex-builder /usr/local/bin/node /usr/local/bin/node
COPY --from=codex-builder /opt/codex /opt/codex

WORKDIR /opt/codex-monitor

COPY server/requirements.txt /tmp/codex-monitor-requirements.txt
RUN python -m pip install --no-cache-dir --disable-pip-version-check \
    --requirement /tmp/codex-monitor-requirements.txt \
    && rm -f /tmp/codex-monitor-requirements.txt

COPY --chown=codex-monitor:codex-monitor server/app /opt/codex-monitor/server/app
COPY --chown=codex-monitor:codex-monitor web /opt/codex-monitor/web

EXPOSE 8080

USER codex-monitor

CMD ["python", "-m", "app"]
