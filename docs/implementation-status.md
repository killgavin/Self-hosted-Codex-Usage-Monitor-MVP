# Self-hosted Codex Usage Monitor — Implementation Status

- Version: 0.1
- Status: ACTIVE
- Purpose: Implementation Progress Ledger
- Primary Coding Model: GPT-5.6 Luna

> 本文件只記錄 Implementation 狀態與 Validation Evidence，不是 Requirement / Design / Test Source of Truth。

## Current Project Status

```text
PROJECT_STATUS: IN_PROGRESS
CURRENT_PHASE: MVP
CURRENT_STAGE: Stage 5 — Rate Limit Domain
CURRENT_TASK: TASK-0503 — ResetCredits
LAST_COMPLETED_TASK: TASK-0502 — Generic RateLimit
BLOCKED: NO
HUMAN_REQUIRED: NO
```

## Status Rules

Task: NOT_STARTED / READY / IN_PROGRESS / BLOCKED / HUMAN_REQUIRED / DONE。
Validation: PASS / FAIL / NOT_RUN / NOT_APPLICABLE / BLOCKED。
DONE 必須有 Implementation + Test + Validation evidence。

## Stage Summary

| Stage | Status |
|---|---|
| Stage 0 Repository Foundation | DONE |
| Stage 1 Codex Process / Transport | DONE |
| Stage 2 Protocol Initialization | DONE |
| Stage 3 Account Read | DONE |
| Stage 4 ChatGPT Login | IN_PROGRESS |
| Stage 5 Rate Limit Domain | IN_PROGRESS |
| Stage 6 REST API | NOT_STARTED |
| Stage 7 Web Dashboard | NOT_STARTED |
| Stage 8 Security Hardening | NOT_STARTED |
| Stage 9 Docker Deployment | NOT_STARTED |
| Stage 10 Final MVP Validation | NOT_STARTED |

## Task Ledger

TASK-0001～TASK-0003、TASK-0101～TASK-0106、TASK-0201～TASK-0203、TASK-0301～TASK-0304、TASK-0401～TASK-0406、TASK-0501～TASK-0502 DONE。TASK-0503 READY。TASK-0504～TASK-1007 依 implementation-plan.md 為 NOT_STARTED。

## Real Runtime Validation Ledger

Codex executable：PASS（Real Codex Verified, latest rerun `codex-cli 0.155.1`）。app-server startup：PASS（Real Codex Verified）。app-server stop/no orphan：PASS（Real Codex Verified）。protocol initialize：PASS（Real Codex Verified）。account/read：PASS（Real Codex Verified；authenticated current environment and unauthenticated isolated clean environment）。device-code login start：PASS（Real Codex Verified in isolated clean environment）。login cancel：PASS（Real Codex Verified）。login completion、rateLimits/read、Docker startup、credential persistence：NOT_RUN。

## Security Validation Ledger

Authorization redaction、Access Token、Refresh Token、Cookie、Account API isolation、Rate Limit API isolation、Error sanitization、Raw protocol isolation：全部 NOT_RUN。

## Known Blockers

NONE.

## Human Decisions

NONE.

## Known Limitations

Stages 0–3 are complete. Stage 4 implementation tasks are complete but the stage remains IN_PROGRESS because real completion T-50 is NOT_RUN. T-59 is Automated/Mock Verified only；real browser、real logout and default app runtime initialization remain NOT_RUN/deferred. Stage 5 has verified pure RateLimitWindow and generic RateLimit domain models；T-72/T-73 are Domain-level Automated Verified only，while ResetCredits、Codex protocol/mapping/service and real `account/rateLimits/read` remain NOT_RUN.

## Completed Task Record

### TASK-0001 — Create Project Skeleton

- STATUS: DONE
- COMPLETED: 2026-09-18
- CHANGED_FILES: `.gitignore`, `README.md`, `server/app/**`, `server/tests/**`
- TESTS: T-xx NOT_APPLICABLE；Structural validation PASS；Python compile validation PASS
- VALIDATION: `python3 -m compileall -q server/app` PASS；`git diff --check` PASS；required paths and allowed-file scope PASS
- RUNTIME_EVIDENCE: NONE；all real runtime ledger entries remain NOT_RUN
- SECURITY_EVIDENCE: New-file credential keyword scan PASS；no credential material found
- KNOWN_UNKNOWNS: NONE within TASK-0001；runtime behavior intentionally deferred
- NEXT_TASK: TASK-0002 — Python Dependencies

### TASK-0002 — Python Dependencies

- STATUS: DONE
- COMPLETED: 2026-09-18
- CHANGED_FILES: `server/requirements.txt`, `server/requirements-dev.txt`
- TESTS: T-xx NOT_APPLICABLE；Dependency manifest validation PASS；pip resolver dry-run PASS
- VALIDATION: `python3 -m pip install --dry-run -r server/requirements-dev.txt` PASS；runtime manifest contains only FastAPI, uvicorn, Pydantic；dev adds only pytest；`git diff --check` PASS
- RUNTIME_EVIDENCE: NONE；dependency resolution is not Codex or feature runtime evidence
- SECURITY_EVIDENCE: Dependency manifest credential keyword scan PASS；no credential material found
- KNOWN_UNKNOWNS: NONE within TASK-0002
- NEXT_TASK: TASK-0003 — FastAPI Skeleton

### TASK-0003 — FastAPI Skeleton

- STATUS: DONE
- COMPLETED: 2026-09-18
- CHANGED_FILES: `server/app/main.py`, `server/tests/integration/test_health.py`
- TESTS: Stage 0 health smoke PASS（Automated Verified）；T-54 subset PASS（Automated Verified）；full T-54 `/api/v1/status` NOT_RUN
- VALIDATION: Fresh temporary venv install PASS；`PYTHONPATH=server python -m pytest -q server/tests/integration/test_health.py` PASS (`1 passed`)；`python -m compileall -q server/app server/tests` PASS；`git diff --check` PASS
- RUNTIME_EVIDENCE: Local FastAPI ASGI request returned HTTP 200 and exact JSON `{"status":"ok"}`；Codex runtime evidence NONE
- SECURITY_EVIDENCE: Changed-file credential keyword scan PASS；no credential material found
- KNOWN_UNKNOWNS: Full T-54 and Codex runtime remain NOT_RUN by task scope
- NEXT_TASK: TASK-0101 — Executable Config

### TASK-0101 — Executable Config

- STATUS: DONE
- COMPLETED: 2026-09-18
- CHANGED_FILES: `server/app/config.py`, `server/tests/unit/test_config.py`
- TESTS: T-36 PASS（Automated Verified with harmless executable）；Real Codex detection NOT_RUN；T-37～T-39 NOT_RUN
- VALIDATION: `PYTHONPATH=server python -m pytest -q server/tests/unit/test_config.py` PASS (`5 passed`)；`python -m compileall -q server/app server/tests` PASS；`git diff --check` PASS
- RUNTIME_EVIDENCE: Harmless executable path resolution only；Real Codex evidence NONE
- SECURITY_EVIDENCE: Changed-file credential keyword scan PASS；no credential material found
- KNOWN_UNKNOWNS: Real Codex detection and process startup/stop remain unverified
- NEXT_TASK: TASK-0102 — Process Start

### TASK-0102 — Process Start

- STATUS: DONE
- COMPLETED: 2026-09-18
- CHANGED_FILES: `server/app/codex/exceptions.py`, `server/app/codex/process.py`, `server/tests/integration/test_process_start.py`
- TESTS: T-37 PASS（Automated Verified）；T-38 PASS（Real Codex Verified）；T-39 NOT_RUN
- VALIDATION: `PYTHONPATH=server REAL_CODEX_EXECUTABLE=/tmp/codex-task-runtime-0.155.0/bin/codex python -m pytest -q server/tests/integration/test_process_start.py` PASS (`2 passed`)；app-server remained alive 2.1 seconds；post-test orphan check PASS；compile and diff checks PASS
- RUNTIME_EVIDENCE: Official `codex-cli 0.155.0` executable started `app-server` with stdin/stdout/stderr pipes；no raw payload inspected or printed
- SECURITY_EVIDENCE: Exact argv/no shell；no raw stdout/stderr logging；credential keyword scan PASS
- KNOWN_UNKNOWNS: Formal stop/lifecycle cleanup remains NOT_RUN
- NEXT_TASK: TASK-0103 — Process Stop

### TASK-0103 — Process Stop

- STATUS: DONE
- COMPLETED: 2026-09-18
- CHANGED_FILES: `server/app/codex/process.py`, `server/app/codex/exceptions.py`, `server/tests/integration/test_process_start.py`, `server/tests/integration/test_process_stop.py`
- TESTS: T-37 PASS；T-38 PASS（Real Codex Verified）；T-39 PASS（Real Codex Verified）
- VALIDATION: Real Codex integration suite PASS (`4 passed`)；production stop completed bounded EOF/terminate/kill escalation and reaped child；post-test process check found no orphan；compile and diff checks PASS
- RUNTIME_EVIDENCE: Official `codex-cli 0.155.0` app-server stopped through production `stop()`；child exit observed and reaped
- SECURITY_EVIDENCE: No shell, raw process-output logging, credential access, or `auth.json` access；credential scan PASS
- KNOWN_UNKNOWNS: NONE within TASK-0103
- NEXT_TASK: TASK-0104 — JSON-RPC Transport

### TASK-0104 — JSON-RPC Transport

- STATUS: DONE
- COMPLETED: 2026-09-18
- CHANGED_FILES: `server/app/codex/transport.py`, `server/app/codex/exceptions.py`, `server/tests/unit/test_transport.py`
- TESTS: Basic request serialization/correlation PASS；controlled error response PASS；close-fails-pending PASS（Automated Verified）；T-40～T-44 NOT_RUN
- VALIDATION: `PYTHONPATH=server python -m pytest -q server/tests/unit/test_transport.py` PASS (`3 passed`)；compile and diff checks PASS
- RUNTIME_EVIDENCE: NONE；Real Codex transport/protocol not exercised in this Task
- SECURITY_EVIDENCE: No shell, raw payload logging, credential access, or `auth.json` access；credential scan PASS
- KNOWN_UNKNOWNS: Notification dispatch, out-of-order concurrency, malformed JSON, and request timeout remain NOT_RUN
- NEXT_TASK: TASK-0105 — Notifications and Concurrent Correlation

### TASK-0105 — Notifications and Concurrent Correlation

- STATUS: DONE
- COMPLETED: 2026-09-18
- CHANGED_FILES: `server/app/codex/transport.py`, `server/tests/unit/test_transport.py`
- TESTS: TASK-0104 regression PASS；T-40 PASS；T-41 PASS；T-42 PASS（Automated Verified）；T-43～T-44 NOT_RUN
- VALIDATION: `PYTHONPATH=server python -m pytest -q server/tests/unit/test_transport.py` PASS (`6 passed`)；compile and diff checks PASS
- RUNTIME_EVIDENCE: NONE；in-memory transport evidence only，Real Codex protocol NOT_RUN
- SECURITY_EVIDENCE: Notifications retained only in transport memory；no raw payload logging, credential access, or `auth.json` access；scan PASS
- KNOWN_UNKNOWNS: Malformed JSON and request timeout behavior remain NOT_RUN
- NEXT_TASK: TASK-0106 — Malformed JSON and Timeout Handling

### TASK-0106 — Malformed JSON and Timeout Handling

- STATUS: DONE
- COMPLETED: 2026-09-18
- CHANGED_FILES: `server/app/codex/transport.py`, `server/tests/unit/test_transport.py`
- TESTS: TASK-0104/TASK-0105 regression PASS；T-43 PASS；T-44 PASS（Automated Verified）
- VALIDATION: `PYTHONASYNCIODEBUG=1 PYTHONPATH=server python -m pytest -q server/tests/unit/test_transport.py` PASS (`8 passed`)；malformed input boundedly failed pending request and blocked notification waiter；no unretrieved task warnings；compile and diff checks PASS
- RUNTIME_EVIDENCE: NONE；in-memory transport evidence only，Real Codex protocol NOT_RUN
- SECURITY_EVIDENCE: Malformed raw line excluded from exceptions/logs；no credential access or `auth.json` access；scan PASS
- KNOWN_UNKNOWNS: Real Codex protocol initialization remains NOT_RUN
- NEXT_TASK: TASK-0201 — Initialization DTO

### TASK-0201 — Initialization DTO

- STATUS: DONE
- COMPLETED: 2026-09-18
- CHANGED_FILES: `server/app/codex/protocol.py`, `server/tests/unit/test_protocol.py`
- TESTS: Initialization DTO unit suite PASS (`7 passed`, Automated Verified)；T-45～T-46 NOT_RUN
- VALIDATION: DTO fields reconciled with official `codex-cli 0.155.0` generated schema；camelCase aliases, required/optional validation, and unknown-field preservation PASS；compile and diff checks PASS
- RUNTIME_EVIDENCE: NONE；initialize request was not sent
- SECURITY_EVIDENCE: Synthetic protocol path only；no real home/auth path, credential access, or raw payload logging；scan PASS
- KNOWN_UNKNOWNS: Adapter state transitions and real initialization remain NOT_RUN
- NEXT_TASK: TASK-0202 — Adapter States

### TASK-0202 — Adapter States

- STATUS: DONE
- COMPLETED: 2026-09-18
- CHANGED_FILES: `server/app/codex/adapter.py`, `server/app/codex/exceptions.py`, `server/tests/unit/test_adapter.py`
- TESTS: Adapter state unit suite PASS (`5 passed`, Automated Verified)；T-45～T-46 NOT_RUN
- VALIDATION: Canonical STOPPED/STARTING/INITIALIZING/READY/FAILED states and guarded legal/illegal transitions PASS；compile and diff checks PASS
- RUNTIME_EVIDENCE: NONE；no process or protocol request executed
- SECURITY_EVIDENCE: No subprocess startup, credential/auth access, or raw payload logging；scan PASS
- KNOWN_UNKNOWNS: Adapter lifecycle integration and real initialize handshake remain NOT_RUN
- NEXT_TASK: TASK-0203 — Initialize Handshake

### TASK-0203 — Initialize Handshake

- STATUS: DONE
- COMPLETED: 2026-09-18
- CHANGED_FILES: `server/app/codex/adapter.py`, `server/app/codex/transport.py`, `server/tests/unit/test_adapter.py`, `server/tests/unit/test_transport.py`, `server/tests/integration/test_initialize.py`
- TESTS: Adapter/transport regression PASS (`16 passed`)；T-45 PASS（Real Codex Verified）；T-46 PASS（Automated Verified）
- VALIDATION: Official `codex-cli 0.155.0` completed production initialize/initialized handshake and reached READY；production shutdown returned STOPPED and left no orphan；failure path reached FAILED and cleaned process；compile and diff checks PASS
- RUNTIME_EVIDENCE: Real app-server initialize response validated without printing values or `codexHome`；initialized notification sent；READY observed
- SECURITY_EVIDENCE: No raw response, path, stdout/stderr, credential, or auth payload logging；generic failure omitted synthetic private marker；scan PASS
- KNOWN_UNKNOWNS: account/read and later protocol flows remain NOT_RUN
- NEXT_TASK: TASK-0301 — AccountStatus Domain Model

### TASK-0301 — AccountStatus Domain Model

- STATUS: DONE
- COMPLETED: 2026-09-18
- CHANGED_FILES: `server/app/models/account.py`, `server/app/models/__init__.py`, `server/tests/unit/test_account_model.py`
- TESTS: T-18 PASS；T-19 PASS；T-20 PASS；immutability PASS（Automated Verified, `4 passed`）
- VALIDATION: Pure standard-library frozen dataclass with exactly authenticated/auth_mode/plan_type；compile and diff checks PASS
- RUNTIME_EVIDENCE: NONE；no account/read request executed
- SECURITY_EVIDENCE: Domain contains no credential, token, raw metadata, protocol, web, or process dependency；scan PASS
- KNOWN_UNKNOWNS: Protocol DTO/mapping, service, and real account/read remain NOT_RUN
- NEXT_TASK: TASK-0302 — Account Read Mapping

### TASK-0302 — Account Read Mapping

- STATUS: DONE
- COMPLETED: 2026-09-18
- CHANGED_FILES: `server/app/codex/protocol.py`, `server/app/codex/adapter.py`, `server/app/codex/account_mapper.py`, `server/tests/unit/test_adapter.py`, `server/tests/unit/test_account_mapping.py`
- TESTS: T-18 PASS；T-19 PASS；T-20 PASS；account/read DTO、mapping、adapter request、invalid-response sanitization、transport-error propagation PASS（Automated Verified, `20 passed`）；T-47～T-48 NOT_RUN
- VALIDATION: `PYTHONPATH=server /tmp/task0003-review.C5k26h/bin/python -m pytest -q server/tests/unit/test_account_model.py server/tests/unit/test_account_mapping.py server/tests/unit/test_adapter.py` PASS (`20 passed`)；compile and diff checks PASS
- RUNTIME_EVIDENCE: NONE；no real account/read request executed
- SECURITY_EVIDENCE: Mapper deliberately excludes email and protocol metadata；validation error is generic and omits raw response；no credential/auth file access or raw payload logging；scan PASS
- KNOWN_UNKNOWNS: AccountService and real authenticated/unauthenticated account/read behavior remain NOT_RUN
- NEXT_TASK: TASK-0303 — AccountService

### TASK-0303 — AccountService

- STATUS: DONE
- COMPLETED: 2026-09-18
- CHANGED_FILES: `server/app/services/account.py`, `server/app/services/__init__.py`, `server/tests/unit/test_account_service.py`
- TESTS: T-18 PASS；T-19 PASS；T-20 PASS；exactly-one adapter call、unknown/missing type preservation、unchanged failure propagation PASS（Automated Verified）；T-47～T-48 NOT_RUN
- VALIDATION: `PYTHONPATH=server /tmp/task0003-review.C5k26h/bin/python -m pytest -q server/tests/unit` PASS (`46 passed`)；compile and diff checks PASS
- RUNTIME_EVIDENCE: NONE；service tests use injected DTO-returning fake only，no real account/read request executed
- SECURITY_EVIDENCE: Service accepts typed DTO boundary and returns only pure `AccountStatus`；no subprocess、JSON-RPC wire handling、raw response logging、credential/auth file access；scan PASS
- KNOWN_UNKNOWNS: Real authenticated and clean-environment unauthenticated account/read behavior remain NOT_RUN
- NEXT_TASK: TASK-0304 — Real Account Validation

### TASK-0304 — Real Account Validation

- STATUS: DONE
- COMPLETED: 2026-09-18
- CHANGED_FILES: `server/tests/integration/test_account_read.py`
- TESTS: T-47 PASS（Real Codex Verified）；T-48 PASS（Real Codex Verified）；account regression suite PASS（Automated Verified, `25 passed`）
- VALIDATION: `REAL_CODEX_EXECUTABLE=/tmp/codex-task-runtime-0.155.0/bin/codex PYTHONPATH=server /tmp/task0003-review.C5k26h/bin/python -m pytest -q server/tests/integration/test_account_read.py` PASS (`2 passed in 4.47s`)；compile、diff、allowed-scope and post-test orphan checks PASS
- RUNTIME_EVIDENCE: Production process/adapter/account mapper returned authenticated `AccountStatus` in the current real environment；a separate real app-server with an empty temporary `CODEX_HOME` returned unauthenticated status with null auth mode and plan；both children were shut down and reaped
- SECURITY_EVIDENCE: No auth file inspection、refresh request、raw DTO/init payload、email、path、stdout/stderr or credential output；only domain-safe facts were asserted
- KNOWN_UNKNOWNS: NONE for T-47/T-48；login start/completion/cancel remains NOT_RUN
- NEXT_TASK: TASK-0401 — AuthService State

### TASK-0401 — AuthService State

- STATUS: DONE
- COMPLETED: 2026-09-18
- CHANGED_FILES: `server/app/services/auth.py`, `server/app/services/__init__.py`, `server/tests/unit/test_auth_service.py`
- TESTS: TASK-0401 local state unit tests PASS（Automated Verified, `4 passed`）；full unit regression PASS (`50 passed`)；T-49～T-51、T-59 NOT_RUN
- VALIDATION: `PYTHONPATH=server /tmp/task0003-review.C5k26h/bin/python -m pytest -q server/tests/unit` PASS (`50 passed`)；compile and diff checks PASS
- RUNTIME_EVIDENCE: NONE；no Codex login method or UI executed
- SECURITY_EVIDENCE: Immutable status has exactly state、login_id、verification_url、user_code；no credential、token、error payload、raw protocol field or logging
- KNOWN_UNKNOWNS: Device-code start、completion、cancel and UI behavior remain NOT_RUN
- NEXT_TASK: TASK-0402 — Device Code Login Start

### TASK-0402 — Device Code Login Start

- STATUS: DONE
- COMPLETED: 2026-09-18
- CHANGED_FILES: `server/app/codex/protocol.py`, `server/app/codex/adapter.py`, `server/app/services/auth.py`, `server/tests/unit/test_protocol.py`, `server/tests/unit/test_adapter.py`, `server/tests/unit/test_auth_service.py`, `server/tests/integration/test_login.py`
- TESTS: T-49 PASS（Real Codex Verified）；focused protocol/adapter/service tests PASS (`30 passed`)；full unit regression PASS (`59 passed`)；T-50、T-51、T-59 NOT_RUN
- VALIDATION: `REAL_CODEX_EXECUTABLE=/tmp/codex-task-runtime-0.155.0/bin/codex PYTHONPATH=server /tmp/task0003-review.C5k26h/bin/python -m pytest -q server/tests/integration/test_login.py` PASS (`1 passed in 8.41s`)；unit、compile、diff、allowed-scope and post-test orphan checks PASS
- RUNTIME_EVIDENCE: Real `codex-cli 0.155.0` in an empty temporary `CODEX_HOME` completed production initialize and `account/login/start` through adapter/service；PENDING and all required structural fields were observed；child shut down/reaped with no orphan
- SECURITY_EVIDENCE: Runtime login ID、verification URL、user code、raw response、paths、stdout/stderr and credentials were neither printed nor compared literally；no auth file/token access
- KNOWN_UNKNOWNS: Completion notification T-50、cancel T-51 and UI T-59 remain NOT_RUN
- NEXT_TASK: TASK-0403 — Login Completion

### TASK-0403 — Login Completion

- STATUS: DONE
- COMPLETED: 2026-09-19
- CHANGED_FILES: `server/app/codex/protocol.py`, `server/app/codex/adapter.py`, `server/app/services/auth.py`, `server/tests/unit/test_protocol.py`, `server/tests/unit/test_adapter.py`, `server/tests/unit/test_auth_service.py`
- TESTS: TASK-0403 completion DTO/adapter/service suite PASS（Automated Verified, `43 passed`）；full unit regression PASS (`72 passed`)；T-49 regression PASS（Real Codex Verified）；T-50、T-51、T-59 NOT_RUN
- VALIDATION: `PYTHONPATH=server /tmp/codex-review.lTnq3j/bin/python -m pytest -q server/tests/unit` PASS (`72 passed`)；`REAL_CODEX_EXECUTABLE=/tmp/codex-task-runtime-0.155.1/bin/codex ... server/tests/integration/test_login.py` PASS (`1 passed in 9.01s`)；compile、diff、scope、security and orphan checks PASS
- RUNTIME_EVIDENCE: Completion behavior is Automated Verified only；no real completion occurred。T-49 device-code start was reverified with official `codex-cli 0.155.1` and the child was shut down/reaped
- SECURITY_EVIDENCE: Upstream completion error remains boundary-only and is never stored in UI-safe state；invalid payload/timeout errors are generic；no runtime login values、raw notification、auth file、token or credential output
- KNOWN_UNKNOWNS: Real human login completion T-50、cancel T-51 and UI T-59 remain NOT_RUN
- NEXT_TASK: TASK-0404 — Login Cancel

### TASK-0404 — Login Cancel

- STATUS: DONE
- COMPLETED: 2026-09-19
- CHANGED_FILES: `server/app/codex/protocol.py`, `server/app/codex/adapter.py`, `server/app/services/auth.py`, `server/tests/unit/test_protocol.py`, `server/tests/unit/test_adapter.py`, `server/tests/unit/test_auth_service.py`, `server/tests/integration/test_login.py`
- TESTS: TASK-0404 cancel DTO/adapter/service suite PASS（Automated Verified, `53 passed`）；full unit regression PASS (`82 passed`)；T-49 PASS（Real Codex Verified）；T-51 PASS（Real Codex Verified）；T-50、T-59 NOT_RUN
- VALIDATION: `PYTHONPATH=server /tmp/codex-review.lTnq3j/bin/python -m pytest -q server/tests/unit` PASS (`82 passed`)；`REAL_CODEX_EXECUTABLE=/tmp/codex-task-runtime-0.155.1/bin/codex PYTHONPATH=server /tmp/codex-review.lTnq3j/bin/python -m pytest -q server/tests/integration/test_login.py` PASS (`2 passed in 19.41s`)；compile、diff、scope、security and orphan checks PASS
- RUNTIME_EVIDENCE: Official `codex-cli 0.155.1` completed production initialize → device-code start → `account/login/cancel` in isolated empty homes；T-51 returned confirmed cancellation and service published CANCELED；children were shut down/reaped
- SECURITY_EVIDENCE: Runtime login ID、verification URL、user code、raw response、paths、stdout/stderr and credentials were neither printed nor compared literally；non-success responses are generic and preserve prior state
- KNOWN_UNKNOWNS: One earlier standalone T-49 run timed out but did not reproduce in Sol's complete integration rerun；real T-50 and UI T-59 remain NOT_RUN
- NEXT_TASK: TASK-0405 — Minimal Login REST

### TASK-0405 — Minimal Login REST

- STATUS: DONE
- COMPLETED: 2026-09-19
- CHANGED_FILES: `server/app/codex/exceptions.py`, `server/app/codex/protocol.py`, `server/app/codex/adapter.py`, `server/app/services/auth.py`, `server/app/api/login.py`, `server/app/main.py`, `server/tests/unit/test_protocol.py`, `server/tests/unit/test_adapter.py`, `server/tests/unit/test_auth_service.py`, `server/tests/integration/test_login_api.py`
- TESTS: TASK-0405 protocol/adapter/service/REST suite PASS（Automated Verified）；deterministic unit/API/health regression PASS (`101 passed`)；T-49 PASS（Real Codex Verified）；T-51 PASS（Real Codex Verified）；T-50、T-59 NOT_RUN
- VALIDATION: `PYTHONPATH=server /tmp/codex-review.lTnq3j/bin/python -m pytest -q server/tests/unit server/tests/integration/test_health.py server/tests/integration/test_login_api.py` PASS (`101 passed`)；`REAL_CODEX_EXECUTABLE=/tmp/codex-task-runtime-0.155.1/bin/codex ... server/tests/integration/test_login.py` PASS (`2 passed in 24.05s`)；compile、diff、scope、security and orphan checks PASS
- RUNTIME_EVIDENCE: Official `codex-cli 0.155.1` reverified real device-code start/cancel with the dedicated 30-second start timeout；children were shut down/reaped。REST and logout behavior are Automated Verified only；real logout was not run
- SECURITY_EVIDENCE: REST success exposes exactly state、verificationUrl、userCode and omits loginId/protocol DTO；known and unexpected errors use fixed sanitized envelopes；no import-time subprocess、raw payload、auth file、token or credential output
- KNOWN_UNKNOWNS: Real T-50、real logout、T-59 and default app runtime initialization remain NOT_RUN/deferred；server API token protection belongs to TASK-0601
- NEXT_TASK: TASK-0406 — Minimal Login UI

### TASK-0406 — Minimal Login UI

- STATUS: DONE
- COMPLETED: 2026-09-19
- CHANGED_FILES: `web/index.html`, `web/assets/styles.css`, `web/assets/app.mjs`, `server/app/main.py`, `server/tests/integration/test_login_ui.py`, `server/tests/fixtures/login_ui_behavior.mjs`
- TESTS: T-59 PASS（Automated/Mock Verified；served assets plus dependency-free Node DOM behavior）；deterministic unit/API/UI/health regression PASS (`103 passed`)；T-50、T-58、T-60～T-63 NOT_RUN
- VALIDATION: `node server/tests/fixtures/login_ui_behavior.mjs` PASS；`PYTHONPATH=server /tmp/codex-review.lTnq3j/bin/python -m pytest -q server/tests/unit server/tests/integration/test_health.py server/tests/integration/test_login_api.py server/tests/integration/test_login_ui.py` PASS (`103 passed`)；compile、diff、scope and security checks PASS
- RUNTIME_EVIDENCE: NONE；no real browser or human login completion executed
- SECURITY_EVIDENCE: Browser code calls only same-server REST；no loginId/raw protocol/token/localStorage/direct OpenAI/Codex access；user code and messages use textContent；only http/https verification URLs become active hrefs；page contains no fake quota data
- KNOWN_UNKNOWNS: T-59 is not Real Browser Verified；real T-50、real logout and future dashboard/browser tests remain NOT_RUN
- NEXT_TASK: TASK-0501 — RateLimitWindow

### TASK-0501 — RateLimitWindow

- STATUS: DONE
- COMPLETED: 2026-09-19
- CHANGED_FILES: `server/app/models/rate_limit.py`, `server/app/models/__init__.py`, `server/tests/unit/test_rate_limit_window.py`
- TESTS: T-01～T-06、T-16～T-17 PASS（Automated Verified, focused `19 passed`）；deterministic unit/API/UI/health regression PASS (`122 passed`)
- VALIDATION: `PYTHONPATH=server /tmp/codex-review.lTnq3j/bin/python -m pytest -q server/tests/unit server/tests/integration/test_health.py server/tests/integration/test_login_api.py server/tests/integration/test_login_ui.py` PASS (`122 passed`)；compile、diff and changed-file credential keyword checks PASS
- RUNTIME_EVIDENCE: NONE；pure domain validation only，no Codex executable、app-server or account runtime call occurred
- SECURITY_EVIDENCE: Model and tests contain no credential source、auth payload、logging or external dependency；remaining percentage is derived internally and cannot be supplied by callers
- KNOWN_UNKNOWNS: Generic RateLimit、protocol DTO/mapping/service、REST and real `account/rateLimits/read` remain NOT_RUN by task scope
- NEXT_TASK: TASK-0502 — Generic RateLimit

### TASK-0502 — Generic RateLimit

- STATUS: DONE
- COMPLETED: 2026-09-19
- CHANGED_FILES: `server/app/models/rate_limit.py`, `server/app/models/__init__.py`, `server/tests/unit/test_rate_limit.py`
- TESTS: T-07～T-11、T-72～T-74 PASS（Automated Verified at Domain scope；focused RateLimit/RateLimitWindow `30 passed`）；deterministic unit/API/UI/health regression PASS (`133 passed`)
- VALIDATION: `PYTHONPATH=server /tmp/codex-review.lTnq3j/bin/python -m pytest -q server/tests/unit/test_rate_limit.py server/tests/unit/test_rate_limit_window.py` PASS (`30 passed`)；full deterministic suite PASS (`133 passed`)；compile、diff and changed-file credential keyword checks PASS
- RUNTIME_EVIDENCE: NONE；pure domain validation only，no Codex executable、app-server or account runtime call occurred
- SECURITY_EVIDENCE: Compatibility metadata is restricted to JSON-compatible values、defensively rebuilt and recursively read-only；no credential source、raw JSON-RPC parsing、logging or client serialization was added
- KNOWN_UNKNOWNS: T-72/T-73 prove Domain-level unknown metadata safety only；protocol DTO/mapping forward compatibility awaits TASK-0504/TASK-0505，and real `account/rateLimits/read` remains NOT_RUN
- NEXT_TASK: TASK-0503 — ResetCredits

完成 Task 後追加 TASK、STATUS、COMPLETED、CHANGED_FILES、TESTS、VALIDATION、RUNTIME_EVIDENCE、KNOWN_UNKNOWNS、NEXT_TASK。

## Luna Update Rules

Luna 只可更新 current status、relevant task/stage、runtime/security ledger、blockers、human decisions、completed task record。不得在此修改 Requirement、Architecture、Task definition、Test requirement 或 Acceptance Criteria。

## Session Resume Protocol

新 Luna Session 先讀本文件，取得 CURRENT_STAGE/CURRENT_TASK/LAST_COMPLETED_TASK/BLOCKED/HUMAN_REQUIRED，再讀相關 canonical sections/source files。不重做 DONE task、不重規劃 architecture。BLOCKED/HUMAN_REQUIRED 時不得自行前進。

## Current Next Action

```text
STATUS: ACTIVE
READY_TASK: TASK-0503
NEXT_ACTION: Implement and validate TASK-0503 only.
```
