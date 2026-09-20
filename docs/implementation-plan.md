# Self-hosted Codex Usage Monitor — Implementation Plan

- Version: 0.3
- Status: READY
- Primary Coding Model: GPT-5.6 Luna
- Escalation Model: GPT-5.6 Sol

Canonical: specification → design → test-plan → implementation-plan。

## Execution Rules

一次只執行 ONE TASK。狀態 NOT_STARTED / READY / IN_PROGRESS / BLOCKED / HUMAN_REQUIRED / DONE。DONE = Implementation + Tests + Validation + Required Documentation Sync。

禁止 unrelated refactor、framework replacement、DB、central SaaS、Browser/Android→OpenAI、private /wham、direct auth.json dependency、custom OAuth、credential leakage、降低 acceptance criteria。Protocol/architecture/security/canonical conflict/undocumented upstream behavior/cross-stage redesign → HUMAN_REQUIRED。

## Stage 0 — Repository Foundation

- TASK-0001 Create Project Skeleton：Allowed server/, README.md, .gitignore；建立 server/app/main.py、config.py、api/codex/models/services/security、tests/unit/integration/fixtures；不得 Codex/Login/Rate/Web/Docker。
- TASK-0002 Python Dependencies：FastAPI、uvicorn、Pydantic、pytest；不得預加 ORM/Redis/Celery/大型 frontend。
- TASK-0003 FastAPI Skeleton：GET /health → {"status":"ok"} + test。

## Stage 1 — Codex Process / Transport

TASK-0101 executable config；0102 start T-37/T-38；0103 stop T-39；0104 JSON-RPC transport；0105 notifications T-40–42；0106 malformed/timeout T-43–44。

## Stage 2 — Protocol Initialization

TASK-0201 initialization DTO；0202 Adapter states；0203 initialize/initialized T-45/T-46。Mismatch → HUMAN_REQUIRED。

## Stage 3 — Account Read

TASK-0301 AccountStatus T-18–20；0302 account/read mapping；0303 AccountService；0304 real validation T-47/T-48。

## Stage 4 — ChatGPT Login

TASK-0401 AuthService state；0402 device code T-49；0403 completion T-50；0404 cancel T-51；0405 minimal login REST；0406 minimal login UI T-59。

## Stage 5 — Rate Limit Domain

TASK-0501 RateLimitWindow T-01–06/T-16–17；0502 generic RateLimit T-07–11/T-72–74；0503 ResetCredits T-12–15；0504 protocol DTO；0505 mapping；0506 service；0507 real T-52/T-53。

## Stage 6 — REST API

TASK-0601 server API token T-25–28；0602 status T-54；0603 account T-33/T-55；0604 rate limits T-34/T-56/T-57/T-75/T-76；0605 errors T-35；0606 TTL cache T-21–24。

## Stage 7 — Web

TASK-0701 shell；0702 Generic RateLimitCard T-60/T-61；0703 time T-62；0704 360px implementation/static prerequisites；0705 E2E T-58–62。By explicit Human decision on 2026-09-20，real-browser T-63 is deferred to Stage10 because the current ChatGPT Work workspace cannot provide a browser that can access repository localhost. T-63 remains required and must stay BLOCKED/NOT_RUN until actual execution evidence exists；it cannot be inferred from static tests or counted PASS for Stage10.

## Stage 8 — Security

TASK-0801 redaction T-29–32；0802 sanitization T-33–35/T-76；0803 default 127.0.0.1；0804 degraded T-69–71。

## Stage 9 — Docker

TASK-0901 Dockerfile implementation/static prerequisites；0902 compose implementation/static prerequisites；0903 persistence implementation/static prerequisites；0904 deployment docs。By explicit Human decision on 2026-09-20，real Docker T-64–68 execution is deferred to Stage10 because the current workspace has no usable container builder. TASK-0901～TASK-0904 may advance only after their implementation/static evidence passes；T-64–68 remain BLOCKED/NOT_RUN，must not be counted PASS，and remain mandatory Final Gate tests.

## Stage 10 — Final MVP Validation

No new features。TASK-1001 automated sweep；1002 real Codex；1003 real login；1004 deferred real Docker T-64–68 E2E；1005 security；1006 docs reconciliation；1007 deferred real-browser T-63 plus final report。T-63 or any T-64–68 BLOCKED/NOT_RUN prevents `OVERALL: PASS`。只有 OVERALL: PASS → MVP COMPLETE。

## Luna Task Contract

每次給 Luna：TASK ID、Goal、Sources、Allowed Files、Required Changes、Forbidden Changes、Test IDs、Validation、Output Contract。一次不得多個不相關 Task。Real tests 無法執行 → NOT_RUN。

## Planner Rule

Luna 是 implementation agent，不是 planner。Sol/Human review evidence 後才決定 CONTINUE / HUMAN_REQUIRED / GOAL_COMPLETE。

## Commit Strategy

One bounded Task ≈ one logical commit；不得跨 Stage 混 commit。

## Context Optimization

新 Session 先讀 implementation-status.md，再讀 current task 的 canonical sections/source files；不得重做 DONE task 或重規劃 architecture。
