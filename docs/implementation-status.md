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
CURRENT_STAGE: Stage 8 — Security Hardening
CURRENT_TASK: TASK-0802 — Sanitization Revalidation
LAST_COMPLETED_TASK: TASK-0801 — Logging Redaction
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
| Stage 5 Rate Limit Domain | DONE |
| Stage 6 REST API | DONE |
| Stage 7 Web Dashboard | DONE（T-63 deferred Final Gate） |
| Stage 8 Security Hardening | IN_PROGRESS |
| Stage 9 Docker Deployment | NOT_STARTED |
| Stage 10 Final MVP Validation | NOT_STARTED |

## Task Ledger

TASK-0001～TASK-0003、TASK-0101～TASK-0106、TASK-0201～TASK-0203、TASK-0301～TASK-0304、TASK-0401～TASK-0406、TASK-0501～TASK-0507、TASK-0601～TASK-0606、TASK-0701～TASK-0705、TASK-0801 DONE。TASK-0802 READY。TASK-0803～TASK-1007 依 implementation-plan.md 為 NOT_STARTED。T-63 real-browser validation remains BLOCKED/DEFERRED and is a mandatory Stage 10 gate，not a PASS.

## Real Runtime Validation Ledger

Codex executable：PASS（Real Codex Verified, latest rerun `codex-cli 0.155.1`）。app-server startup：PASS（Real Codex Verified）。app-server stop/no orphan：PASS（Real Codex Verified）。protocol initialize：PASS（Real Codex Verified）。account/read：PASS（Real Codex Verified；authenticated current environment and unauthenticated isolated clean environment）。device-code login start：PASS（Real Codex Verified in isolated clean environment）。login cancel：PASS（Real Codex Verified）。rateLimits/read：PASS（Real Codex Verified；T-52 and T-53 passed against the current authenticated account，including multiple keyed buckets）。login completion、Docker startup、credential persistence：NOT_RUN。

## Security Validation Ledger

Server API token authentication：PASS（Automated Verified；T-25～T-28）。Logging redaction：PASS（Automated/Synthetic Verified；T-29～T-32，including final Formatter output and exception text）。Account API isolation：PASS（Automated Verified；T-33/T-55）。Rate Limit API isolation and successful-response raw protocol isolation：PASS（Automated Verified；T-34/T-56/T-57/T-75/T-76）。Error sanitization：PASS（Automated Verified；T-35）。

## Known Blockers

No current implementation task is blocked. Deferred Final Gate blocker: T-63 lacks a runnable browser layout engine in the current ChatGPT Work workspace. The Work runtime provides the Playwright package, but `chromium.executablePath()` resolves to `/root/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome`, and that executable is absent. Fresh PATH/common-directory/recursive executable checks also found no Chrome/Chromium/Firefox. Two default 30-second official CDN attempts timed out；a 120-second attempt returned a zero-byte/non-ZIP artifact and failed extraction, so the workspace could not acquire Chromium through the available download path. On 2026-09-20，a fresh retry served the repository `web/` directory through a temporary local HTTP server and attempted the Cloud Browser navigation to `http://127.0.0.1:8765/`; the browser returned `net::ERR_BLOCKED_BY_CLIENT` and changed the tab to `chrome-error://chromewebdata/`. A follow-up DOM inspection was rejected by the browser security policy，which explicitly forbids workarounds. CSS/static tests and the full deterministic suite pass，but they cannot replace the required 360px layout measurement. Human approved deferring this real-browser execution to Stage10；T-63 remains BLOCKED/NOT_RUN and prevents Final `OVERALL: PASS` until real evidence exists.

## Human Decisions

Human completed the official Codex device-auth flow to restore the current CLI session. No further decision is required for TASK-0507. This action is not counted as production AuthService/app-server login completion T-50.

On 2026-09-20，the human directed Sol to handle planning、review gates、blockers and work that Luna could not complete，while simple bounded implementation tasks should still be delegated to Luna when practical. This execution-role decision does not waive T-63，change the canonical SDD，or authorize TASK-0705 to start while TASK-0704 is blocked.

On 2026-09-20，the human explicitly approved deferring real-browser T-63 to Stage10 and continuing with TASK-0705. This is a sequencing change only：T-63 remains mandatory，is not PASS，and must block Final `OVERALL: PASS` until real evidence exists.

The user does not need to provide a local executable path. The current ChatGPT Work workspace cannot supply or acquire the required browser under the recorded constraints. A browser-capable workspace/session or complete sanitized real-browser T-63 PASS evidence will still be required at Stage10.

## Known Limitations

Stages 0–3、5、6 and 7 are complete. Stage 4 implementation tasks are complete but the stage remains IN_PROGRESS because production AuthService/app-server login completion T-50 is NOT_RUN. T-58/T-59 are Automated/Mock Verified only；real browser、real logout and default app runtime initialization remain NOT_RUN/deferred. Stage 5 T-52/T-53 are Real Codex Verified；actual account identity、quota values and raw protocol payloads were deliberately not recorded. Stage 6 REST/auth/schema/error/cache tests are Automated Verified with injected services and are not end-to-end Real Codex REST evidence. Stage 7 T-60～T-62 are Automated Verified；TASK-0705 focused UI validation PASS (`13 passed`) and deterministic regression PASS (`212 passed`)，while T-63 remains BLOCKED/DEFERRED because the workspace has neither a runnable local browser executable nor Cloud Browser access to repository localhost. Logging redaction T-29～T-32 is Automated/Synthetic Verified；TASK-0802 security revalidation remains NOT_RUN；Codex degraded/exit/upstream behavior T-69～T-71 remains NOT_RUN until TASK-0804.

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

### TASK-0503 — ResetCredits

- STATUS: DONE
- COMPLETED: 2026-09-19
- CHANGED_FILES: `server/app/models/rate_limit.py`, `server/app/models/__init__.py`, `server/tests/unit/test_reset_credits.py`
- TESTS: T-12～T-15 PASS（Automated Verified at Domain scope；focused Stage 5 domain suite `40 passed`）；deterministic unit/API/UI/health regression PASS (`143 passed`)
- VALIDATION: `PYTHONPATH=server /tmp/codex-review.lTnq3j/bin/python -m pytest -q server/tests/unit/test_reset_credits.py server/tests/unit/test_rate_limit.py server/tests/unit/test_rate_limit_window.py` PASS (`40 passed`)；full deterministic suite PASS (`143 passed`)；compile、diff and changed-file security keyword checks PASS
- RUNTIME_EVIDENCE: NONE；pure domain validation only，no Codex executable、app-server or account runtime call occurred
- SECURITY_EVIDENCE: Models are immutable and read-only；no protocol payload、reset-credit mutation/redeem path、credential source or logging was added
- KNOWN_UNKNOWNS: T-12 proves only the Domain representation of an absent summary as `None`；raw null/detail mapping awaits TASK-0504/TASK-0505，and real reset-credit behavior remains NOT_RUN
- NEXT_TASK: TASK-0504 — Rate Limit Protocol DTO

### TASK-0504 — Rate Limit Protocol DTO

- STATUS: DONE
- COMPLETED: 2026-09-19
- CHANGED_FILES: `server/app/codex/protocol.py`, `server/tests/unit/test_protocol.py`
- TESTS: Protocol-scope T-10～T-15 and T-72～T-74 PASS（Automated Verified with synthetic payloads；protocol suite `16 passed`）；deterministic unit/API/UI/health regression PASS (`146 passed`)
- VALIDATION: `PYTHONPATH=server /tmp/codex-review.lTnq3j/bin/python -m pytest -q server/tests/unit/test_protocol.py` PASS (`16 passed`)；full deterministic suite PASS (`146 passed`)；compile、diff、scope and security/private-endpoint keyword checks PASS
- RUNTIME_EVIDENCE: NONE；DTOs were validated with synthetic payloads only，and `account/rateLimits/read` was not called
- SECURITY_EVIDENCE: Unknown fields remain confined to the protocol DTO boundary；no REST serialization、raw payload logging、credential handling、private endpoint or usage-read method was added
- KNOWN_UNKNOWNS: Domain mapping、adapter method、service and real current-account response remain NOT_RUN；upstream enum/field compatibility is synthetic-only until TASK-0507
- NEXT_TASK: TASK-0505 — Rate Limit Mapping

### TASK-0505 — Rate Limit Mapping

- STATUS: DONE
- COMPLETED: 2026-09-19
- CHANGED_FILES: `server/app/codex/rate_limit_mapper.py`, `server/tests/unit/test_rate_limit_mapping.py`
- TESTS: T-01～T-17 and T-72～T-74 PASS at mapping scope（Automated Verified with synthetic DTOs）；multiple-limit ordering/fallback/no-duplication PASS（Automated Verified）；focused mapping/domain suite `54 passed`；deterministic regression `160 passed`
- VALIDATION: `PYTHONPATH=server /tmp/codex-review.lTnq3j/bin/python -m pytest -q server/tests/unit/test_rate_limit_mapping.py server/tests/unit/test_rate_limit_window.py server/tests/unit/test_rate_limit.py server/tests/unit/test_reset_credits.py` PASS (`54 passed`)；full deterministic suite PASS (`160 passed`)；compile、diff、scope and security/private-endpoint checks PASS
- RUNTIME_EVIDENCE: NONE；mapping used synthetic DTOs only，and T-53 is not Real Codex Verified
- SECURITY_EVIDENCE: Mapper copies only per-rate unknown metadata into an immutable compatibility bag、ignores unknown top-level fields、omits protocol-only resetType and does not serialize/log raw responses
- KNOWN_UNKNOWNS: Adapter/service orchestration and real current-account response remain NOT_RUN；actual multiple-limit availability remains unknown until TASK-0507
- NEXT_TASK: TASK-0506 — RateLimitService

### TASK-0506 — RateLimitService

- STATUS: DONE
- COMPLETED: 2026-09-19
- CHANGED_FILES: `server/app/codex/adapter.py`, `server/app/services/rate_limits.py`, `server/app/services/__init__.py`, `server/tests/unit/test_rate_limit_service.py`
- TESTS: Adapter/service orchestration PASS（Automated/Mock Verified）；focused adapter/service/mapping suite `52 passed`；deterministic regression `168 passed`；T-52/T-53 Real Codex NOT_RUN
- VALIDATION: `PYTHONPATH=server /tmp/codex-review.lTnq3j/bin/python -m pytest -q server/tests/unit/test_rate_limit_service.py server/tests/unit/test_adapter.py server/tests/unit/test_rate_limit_mapping.py` PASS (`52 passed`)；full deterministic suite PASS (`168 passed`)；compile、diff、scope and security/private-endpoint checks PASS
- RUNTIME_EVIDENCE: NONE；the adapter used fake transports only，so `account/rateLimits/read` is not Real Codex Verified
- SECURITY_EVIDENCE: Adapter validation errors use a fixed sanitized message and never include response data；service adds no logging、cache、retry、credential handling or raw protocol exposure
- KNOWN_UNKNOWNS: T-52/T-53 and actual current-account rate-limit/reset-credit shapes remain NOT_RUN until TASK-0507
- NEXT_TASK: TASK-0507 — Real Rate Limit Validation

### TASK-0507 — Real Rate Limit Validation

- STATUS: DONE
- COMPLETED: 2026-09-19
- EXECUTION_AGENT: Sol fallback；GPT-5.6 Luna was assigned the bounded contract but did not return evidence and had no running validation process，so Sol executed the identical bounded scope
- CHANGED_FILES: `server/tests/integration/test_rate_limits.py`, `docs/implementation-status.md`
- TESTS: T-52 PASS（Real Codex Verified）；T-53 PASS（Real Codex Verified with multiple keyed buckets actually available and preserved）；deterministic regression PASS (`168 passed`)
- VALIDATION: `REAL_CODEX_EXECUTABLE=/tmp/codex-login-runtime-0.155.1.zVVzlb/bin/codex PYTHONPATH=server /tmp/task0507-venv.9dQyC0/bin/python -m pytest -q server/tests/integration/test_rate_limits.py` PASS (`2 passed`)；deterministic unit/API/UI/health regression PASS (`168 passed`)；compile、`git diff --check`、post-test no-orphan and changed-file credential-pattern checks PASS
- RUNTIME_EVIDENCE: Official `codex-cli 0.155.1` started and initialized production app-server twice；production `RateLimitService` completed real `account/rateLimits/read`；the current account exposed multiple keyed rate-limit buckets and the mapped count/order matched；both child processes shut down and were reaped
- SECURITY_EVIDENCE: Tests asserted only normalized types、safe ranges and bucket preservation；no account identity、quota value、raw JSON-RPC/auth payload or credential was printed or committed；changed-file credential-pattern scan PASS
- KNOWN_UNKNOWNS: Production AuthService/app-server login completion T-50 remains NOT_RUN；Docker startup and credential persistence remain NOT_RUN for their planned stages
- NEXT_TASK: TASK-0601 — Server API Token

### TASK-0601 — Server API Token

- STATUS: DONE
- COMPLETED: 2026-09-19
- EXECUTION_AGENT: Sol fallback；a fresh GPT-5.6 Luna agent was assigned the bounded contract but did not start a command or file change and returned no blocker，so Sol executed the identical bounded scope
- CHANGED_FILES: `server/app/config.py`, `server/app/security/__init__.py`, `server/app/security/server_token.py`, `server/tests/integration/test_server_token.py`, `docs/implementation-status.md`
- TESTS: T-25 PASS；T-26 PASS；T-27 PASS；T-28 PASS（Automated Verified through a protected ASGI route）；configuration source isolation PASS；deterministic regression PASS (`175 passed`)
- VALIDATION: `PYTHONPATH=server /tmp/task0507-venv.9dQyC0/bin/python -m pytest -q server/tests/integration/test_server_token.py` PASS (`7 passed`)；deterministic unit/login API/login UI/health/server-token regression PASS (`175 passed`)；compile、`git diff --check`、scope、forbidden-integration and live-credential pattern checks PASS
- RUNTIME_EVIDENCE: Local ASGI requests proved valid monitor Bearer access and fixed HTTP 401 rejection for missing、invalid and OpenAI-style non-monitor credentials；no Codex/OpenAI runtime call occurred
- SECURITY_EVIDENCE: `CODEX_MONITOR_API_TOKEN` is the only accepted configuration source and is excluded from `Settings` repr；comparison is timing-safe and exact；errors contain only the fixed `INVALID_SERVER_TOKEN` envelope and never echo authorization input；T-29～T-32 remain NOT_RUN
- KNOWN_UNKNOWNS: The reusable dependency is not globally applied to existing Stage 4 login/UI routes；planned Stage 6 data routes will attach it beginning in TASK-0602. Redaction logging and account/rate-limit endpoint isolation remain future bounded tasks
- NEXT_TASK: TASK-0602 — Status Endpoint

### TASK-0602 — Status Endpoint

- STATUS: DONE
- COMPLETED: 2026-09-19
- EXECUTION_AGENT: Sol fallback under the same bounded-task contract after two independent GPT-5.6 Luna agents failed to start any repository action
- CHANGED_FILES: `server/app/api/status.py`, `server/app/main.py`, `server/tests/integration/test_status_api.py`, `docs/implementation-status.md`
- TESTS: T-54 PASS（Automated Verified through authenticated ASGI requests）；server-token rejection on the concrete route PASS；deterministic regression PASS (`177 passed`)
- VALIDATION: `PYTHONPATH=server /tmp/task0507-venv.9dQyC0/bin/python -m pytest -q server/tests/integration/test_status_api.py` PASS (`2 passed`)；deterministic unit/login API/login UI/health/server-token/status regression PASS (`177 passed`)；compile、`git diff --check`、scope and live-credential pattern checks PASS
- RUNTIME_EVIDENCE: Local ASGI request with the configured monitor Bearer token returned HTTP 200 and exact JSON `{"status":"ok"}`；missing token returned fixed HTTP 401；no Codex/OpenAI runtime call occurred
- SECURITY_EVIDENCE: The concrete status route attaches `ServerTokenAuth` and the application installs only the fixed invalid-token handler；the response contains no credential、account、protocol or process detail
- KNOWN_UNKNOWNS: T-69～T-71 degraded/process-exit/upstream behavior remains NOT_RUN until TASK-0804；status currently reports HTTP process availability only and deliberately does not start or probe Codex
- NEXT_TASK: TASK-0603 — Account Endpoint

### TASK-0603 — Account Endpoint

- STATUS: DONE
- COMPLETED: 2026-09-19
- EXECUTION_AGENT: Sol fallback under the same bounded-task contract after the GPT-5.6 Luna execution environment failed to start repository actions
- CHANGED_FILES: `server/app/api/account.py`, `server/app/main.py`, `server/tests/integration/test_account_api.py`, `docs/implementation-status.md`
- TESTS: T-33 PASS；T-55 PASS（Automated Verified through authenticated ASGI requests with injected AccountService boundary）；server-token short-circuit PASS；deterministic regression PASS (`180 passed`)
- VALIDATION: `PYTHONPATH=server /tmp/task0507-venv.9dQyC0/bin/python -m pytest -q server/tests/integration/test_account_api.py` PASS (`3 passed`)；deterministic unit/login API/UI/health/server-token/status/account regression PASS (`180 passed`)；compile、`git diff --check`、scope and live-credential pattern checks PASS
- RUNTIME_EVIDENCE: Local ASGI requests returned the exact authenticated and unauthenticated account schemas；this task used an injected fake AccountService and made no Codex/OpenAI runtime call
- SECURITY_EVIDENCE: Response keys are restricted to `authenticated`、`authMode` and `planType`；no email、credential、authorization、cookie、token or raw protocol field is serialized；missing server token prevents the service call
- KNOWN_UNKNOWNS: General account-route exception mapping/sanitization remains TASK-0605/TASK-0802；default application Codex lifecycle initialization remains NOT_RUN/deferred
- NEXT_TASK: TASK-0604 — Rate Limits Endpoint

### TASK-0604 — Rate Limits Endpoint

- STATUS: DONE
- COMPLETED: 2026-09-19
- EXECUTION_AGENT: Sol fallback under the same bounded-task contract after the GPT-5.6 Luna execution environment failed to start repository actions
- CHANGED_FILES: `server/app/api/rate_limits.py`, `server/app/main.py`, `server/tests/integration/test_rate_limits_api.py`, `docs/implementation-status.md`
- TESTS: T-34 PASS；T-56 PASS；T-57 PASS；T-75 PASS；T-76 PASS at successful-response serialization boundary（Automated Verified with injected RateLimitService）；server-token short-circuit PASS；deterministic regression PASS (`184 passed`)
- VALIDATION: `PYTHONPATH=server /tmp/task0507-venv.9dQyC0/bin/python -m pytest -q server/tests/integration/test_rate_limits_api.py` PASS (`4 passed`)；deterministic unit/login API/UI/health/server-token/status/account/rate-limit regression PASS (`184 passed`)；compile、`git diff --check`、scope and live-credential pattern checks PASS
- RUNTIME_EVIDENCE: Local ASGI requests returned the stable rate-limit/reset-credit schema with exact decimal strings、UTC timestamps、unknown IDs/types and null optionals preserved；this task used an injected fake RateLimitService and made no Codex/OpenAI runtime call
- SECURITY_EVIDENCE: Response excludes `raw_metadata` and protocol-only fields；a private synthetic raw marker did not cross the REST boundary；no authorization、cookie、access-token or refresh-token material appeared；missing server token prevents the service call
- KNOWN_UNKNOWNS: General exception mapping and failure-response sanitization remain TASK-0605/TASK-0802；cache behavior remains TASK-0606
- NEXT_TASK: TASK-0605 — REST Error Mapping

### TASK-0605 — REST Error Mapping

- STATUS: DONE
- COMPLETED: 2026-09-19
- EXECUTION_AGENT: Sol fallback under the same bounded-task contract after the GPT-5.6 Luna execution environment failed to start repository actions
- CHANGED_FILES: `server/app/api/errors.py`, `server/app/api/login.py`, `server/app/api/account.py`, `server/app/api/rate_limits.py`, `server/tests/integration/test_rest_errors.py`, `docs/implementation-status.md`
- TESTS: T-35 PASS（Automated Verified across account and rate-limit service failures；existing login error integration regression PASS）；focused REST route/error suite PASS (`22 passed`)；deterministic regression PASS (`191 passed`)
- VALIDATION: Initial focused run exposed FastAPI response-model collection errors after adding mixed success/error return types；routes were corrected with explicit manual response schemas，then the same focused command PASS (`22 passed`) and full deterministic suite PASS (`191 passed`)；compile、`git diff --check`、scope and live-credential pattern checks PASS
- RUNTIME_EVIDENCE: Local ASGI requests mapped executable missing、start failure、adapter unavailable、communication/stop failure and unexpected exceptions to fixed HTTP/error envelopes；no Codex/OpenAI runtime call occurred
- SECURITY_EVIDENCE: Error mapping never uses exception text；synthetic private auth/trace markers and configured server token did not appear in responses；no traceback、authorization、cookie、access-token or refresh-token field leaked
- KNOWN_UNKNOWNS: Logging redaction T-29～T-32 remains NOT_RUN until TASK-0801；T-33～T-35/T-76 security revalidation remains TASK-0802；degraded/runtime-exit handling remains TASK-0804
- NEXT_TASK: TASK-0606 — TTL Cache

### TASK-0606 — TTL Cache

- STATUS: DONE
- COMPLETED: 2026-09-19
- EXECUTION_AGENT: Sol fallback under the same bounded-task contract after the GPT-5.6 Luna execution environment failed to start repository actions
- CHANGED_FILES: `server/app/config.py`, `server/app/services/rate_limits.py`, `server/app/main.py`, `server/tests/unit/test_rate_limit_cache.py`, `docs/implementation-status.md`
- TESTS: T-21 PASS；T-22 PASS；T-23 PASS；T-24 PASS（Automated Verified with deterministic fake clock and reader）；focused cache/service/config suite PASS (`23 passed`)；deterministic regression PASS (`201 passed`)
- VALIDATION: `PYTHONPATH=server /tmp/task0507-venv.9dQyC0/bin/python -m pytest -q server/tests/unit/test_rate_limit_cache.py server/tests/unit/test_rate_limit_service.py server/tests/unit/test_config.py` PASS (`23 passed`)；full deterministic unit/noninteractive REST/UI regression PASS (`201 passed`)；compile、`git diff --check`、scope and live-credential pattern checks PASS
- RUNTIME_EVIDENCE: NONE；cache behavior used an injected reader and deterministic clock，with no Codex/OpenAI runtime call
- SECURITY_EVIDENCE: Cache is process-local and stores only immutable mapped domain tuples；no credential、raw protocol payload、disk persistence、DB or external cache was added
- KNOWN_UNKNOWNS: Concurrent first-miss coalescing and Phase 2 cache enhancements are out of MVP scope；end-to-end cache behavior with real Codex remains NOT_RUN/not required by T-21～T-24
- NEXT_TASK: TASK-0701 — Web Shell

### TASK-0701 — Web Shell

- STATUS: DONE
- COMPLETED: 2026-09-19
- EXECUTION_AGENT: Sol fallback under the same bounded-task contract after the GPT-5.6 Luna execution environment failed to start repository actions
- CHANGED_FILES: `web/index.html`, `web/assets/styles.css`, `server/tests/integration/test_login_ui.py`, `docs/implementation-status.md`
- TESTS: Dashboard shell structural validation PASS；existing login UI behavior regression PASS (`2 passed`)；deterministic regression PASS (`201 passed`)；T-58～T-63 NOT_RUN for this bounded task
- VALIDATION: `PYTHONPATH=server /tmp/task0507-venv.9dQyC0/bin/python -m pytest -q server/tests/integration/test_login_ui.py` PASS (`2 passed`)；full deterministic unit/noninteractive REST/UI regression PASS (`201 passed`)；compile、`git diff --check`、web token-storage and fake-quota scans PASS
- RUNTIME_EVIDENCE: Local ASGI served the dashboard HTML and JS asset；dependency-free Node fixture revalidated existing login behavior. No real browser、Codex or account request occurred
- SECURITY_EVIDENCE: Server API token control is a password input with no embedded value；HTML/CSS/JS contain no LocalStorage、SessionStorage or cookie persistence；shell contains no fake quota values
- KNOWN_UNKNOWNS: Connect/data-fetch behavior、generic cards、unknown fallback、browser-local time、360px layout and full E2E remain TASK-0702～TASK-0705；T-58～T-63 remain NOT_RUN
- NEXT_TASK: TASK-0702 — Generic RateLimitCard

### TASK-0702 — Generic RateLimitCard

- STATUS: DONE
- COMPLETED: 2026-09-19
- EXECUTION_AGENT: Sol fallback under the same bounded-task contract after the GPT-5.6 Luna execution environment failed to start repository actions
- CHANGED_FILES: `web/assets/app.mjs`, `web/assets/styles.css`, `server/tests/fixtures/rate_limit_card_behavior.mjs`, `server/tests/integration/test_rate_limit_card_ui.py`, `docs/implementation-status.md`
- TESTS: T-60 PASS；T-61 PASS（Automated Verified with dependency-free Node DOM fixture）；focused card/login UI regression PASS (`4 passed`)；deterministic regression PASS (`203 passed`)
- VALIDATION: `PYTHONPATH=server /tmp/task0507-venv.9dQyC0/bin/python -m pytest -q server/tests/integration/test_rate_limit_card_ui.py server/tests/integration/test_login_ui.py` PASS (`4 passed`)；full deterministic unit/noninteractive REST/UI regression PASS (`203 passed`)；compile、`git diff --check`、DOM injection/storage and hard-coded limit ID scans PASS
- RUNTIME_EVIDENCE: Dependency-free Node execution created one generic card per supplied limit，validated known duration labels、unknown ID/title fallback、nullable windows、progress and empty state. No real browser、Codex or account request occurred
- SECURITY_EVIDENCE: Renderer uses `createElement`/`textContent` only，does not use HTML injection APIs，does not interpret unknown/raw fields and does not persist credentials
- KNOWN_UNKNOWNS: Reset time/browser-local formatting T-62、360px T-63 and full dashboard data-fetch/E2E T-58 remain NOT_RUN until TASK-0703～TASK-0705
- NEXT_TASK: TASK-0703 — Browser-Local Time

### TASK-0703 — Browser-Local Time

- STATUS: DONE
- COMPLETED: 2026-09-19
- EXECUTION_AGENT: Sol fallback under the same bounded-task contract after the GPT-5.6 Luna execution environment failed to start repository actions
- CHANGED_FILES: `web/assets/app.mjs`, `web/assets/styles.css`, `server/tests/fixtures/local_time_behavior.mjs`, `server/tests/fixtures/rate_limit_card_behavior.mjs`, `server/tests/integration/test_local_time_ui.py`, `docs/implementation-status.md`
- TESTS: T-62 PASS（Automated Verified by executing the same UTC timestamp under Node `TZ=UTC` and `TZ=Asia/Taipei` plus RateLimitCard integration）；focused local-time/card suite PASS (`4 passed`)；deterministic regression PASS (`205 passed`)
- VALIDATION: `PYTHONPATH=server /tmp/task0507-venv.9dQyC0/bin/python -m pytest -q server/tests/integration/test_local_time_ui.py server/tests/integration/test_rate_limit_card_ui.py` PASS (`4 passed`)；full deterministic unit/noninteractive REST/UI regression PASS (`205 passed`)；compile、`git diff --check`、fixed-timezone and web-safety scans PASS
- RUNTIME_EVIDENCE: Dependency-free Node runs produced different local display strings for one canonical UTC ISO timestamp under UTC and Asia/Taipei；the card preserved the original ISO value in its `datetime` attribute. No real browser、Codex or account request occurred
- SECURITY_EVIDENCE: Formatter uses browser-local `Intl.DateTimeFormat` without a fixed timezone；invalid input returns a fixed fallback and no HTML/storage API was introduced
- KNOWN_UNKNOWNS: Real-browser locale rendering、360px T-63 and full dashboard data-fetch/E2E T-58 remain NOT_RUN until TASK-0704/TASK-0705
- NEXT_TASK: TASK-0704 — 360px Layout

### TASK-0704 — 360px Layout Implementation

- STATUS: DONE（implementation/static validation；real-browser T-63 explicitly deferred to Stage10 by Human decision）
- COMPLETED: 2026-09-20
- EXECUTION_AGENT: Sol direct execution and reconciliation
- CHANGED_FILES: `web/assets/styles.css`, `server/tests/integration/test_mobile_layout.py`, `server/tests/fixtures/mobile_layout_browser.mjs`, `docs/test-plan.md`, `docs/implementation-plan.md`, `docs/implementation-status.md`
- TESTS: TASK-0704 static prerequisites PASS (`3 passed`)；deterministic unit/non-real integration regression PASS (`208 passed`)；T-63 BLOCKED/DEFERRED，not PASS
- VALIDATION: `PYTHONPATH=server /tmp/task0704-venv.ouzhoG/bin/python -m pytest -q server/tests/integration/test_mobile_layout.py` PASS (`3 passed`)；deterministic suite with six real-runtime integration modules explicitly excluded PASS (`208 passed`)；`git diff --check` PASS
- RUNTIME_EVIDENCE: Cloud Browser navigation to the temporary repository server at `http://127.0.0.1:8765/` failed with `net::ERR_BLOCKED_BY_CLIENT`；local Playwright Chromium executable is absent；T-63 remains BLOCKED/NOT_RUN
- SECURITY_EVIDENCE: No credential source、request、response or log was used；temporary static server was stopped after the browser reachability check
- KNOWN_UNKNOWNS: Actual 360px rendered overflow behavior remains unverified until mandatory Stage10 T-63；this prevents Final `OVERALL: PASS` but no longer blocks implementation sequencing
- NEXT_TASK: TASK-0705 — Web Dashboard E2E

### TASK-0705 — Web Dashboard E2E

- STATUS: DONE
- COMPLETED: 2026-09-20
- EXECUTION_AGENT: GPT-5.6 Luna bounded implementation；Sol Review Gate PASS after two evidence fixes
- CHANGED_FILES: `web/assets/app.mjs`, `server/tests/fixtures/dashboard_e2e_behavior.mjs`, `server/tests/integration/test_dashboard_e2e.py`, `docs/implementation-status.md`
- TESTS: T-58 PASS（Automated/Mock Verified only）；T-59 PASS；T-60 PASS；T-61 PASS；T-62 PASS；T-63 BLOCKED/DEFERRED，NOT_RUN
- VALIDATION: `node server/tests/fixtures/dashboard_e2e_behavior.mjs` PASS；focused dashboard/login/card/local-time/mobile-static UI suite PASS (`13 passed`)；deterministic unit/non-real integration suite PASS (`212 passed`)；Python compile、`git diff --check`、allowed-scope and credential/direct-call scans PASS
- RUNTIME_EVIDENCE: Node/mock only — actual fixture execution exercised three same-origin authenticated GETs、success and non-OK failure states、whitespace-token rejection、safe account/reset/rate rendering、generic cards、browser-local last-updated formatting、accessibility heading IDs and token clearing. No real-browser evidence.
- SECURITY_EVIDENCE: Token is read at Connect action time，sent only as same-origin Bearer headers，then cleared；no storage APIs、cookies、URL token、raw payload rendering、direct OpenAI/Codex calls or token logging. Rendered element trees were inspected for private/raw markers.
- KNOWN_UNKNOWNS: T-63 real-browser mobile validation remains BLOCKED/DEFERRED until mandatory Stage10 evidence.
- NEXT_TASK: TASK-0801 — Logging Redaction

### TASK-0801 — Logging Redaction

- STATUS: DONE
- COMPLETED: 2026-09-20
- EXECUTION_AGENT: GPT-5.6 Luna bounded implementation；Sol Review Gate PASS after quoted-key、exception-text and preformatted-Authorization fixes
- CHANGED_FILES: `server/app/security/redaction.py`, `server/app/security/__init__.py`, `server/tests/unit/test_redaction.py`, `docs/implementation-status.md`
- TESTS: T-29 PASS；T-30 PASS；T-31 PASS；T-32 PASS（Automated/Synthetic Verified）
- VALIDATION: `PYTHONPATH=server /tmp/task0704-venv.ouzhoG/bin/python -m pytest -q server/tests/unit/test_redaction.py` PASS (`9 passed`)；deterministic unit/non-real integration suite PASS (`221 passed`)；Python compile、direct preformatted sample execution、`git diff --check`、allowed-scope and credential/environment-access scans PASS
- RUNTIME_EVIDENCE: Standard-library logging records、handler/filter and final Formatter output were executed with synthetic markers only；Authorization/Bearer、access token、refresh token、API/server-monitor token、Cookie、nested structured args and exception text were redacted. No real credential was accessed.
- SECURITY_EVIDENCE: Synthetic secret markers were absent from final formatted output；caller-owned nested inputs and original exception objects were not used as credential sources or mutated for redaction.
- KNOWN_UNKNOWNS: The filter is a reusable logging boundary；the current application has no credential-bearing application log sites. Any future handler/logger that may emit sensitive data must attach the filter and be revalidated.
- NEXT_TASK: TASK-0802 — Sanitization Revalidation

完成 Task 後追加 TASK、STATUS、COMPLETED、CHANGED_FILES、TESTS、VALIDATION、RUNTIME_EVIDENCE、KNOWN_UNKNOWNS、NEXT_TASK。

## Luna Update Rules

Luna 只可更新 current status、relevant task/stage、runtime/security ledger、blockers、human decisions、completed task record。不得在此修改 Requirement、Architecture、Task definition、Test requirement 或 Acceptance Criteria。

## Session Resume Protocol

新 Luna Session 先讀本文件，取得 CURRENT_STAGE/CURRENT_TASK/LAST_COMPLETED_TASK/BLOCKED/HUMAN_REQUIRED，再讀相關 canonical sections/source files。不重做 DONE task、不重規劃 architecture。BLOCKED/HUMAN_REQUIRED 時不得自行前進。

## Current Next Action

```text
STATUS: CONTINUE
DEFERRED_GATE: T-63 — BLOCKED/NOT_RUN until Stage10 real-browser evidence
NEXT_ACTION: TASK-0802 — Sanitization Revalidation
```
