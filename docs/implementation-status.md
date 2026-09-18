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
CURRENT_STAGE: Stage 2 — Protocol Initialization
CURRENT_TASK: TASK-0201 — Initialization DTO
LAST_COMPLETED_TASK: TASK-0106 — Malformed JSON and Timeout Handling
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
| Stage 2 Protocol Initialization | READY |
| Stage 3 Account Read | NOT_STARTED |
| Stage 4 ChatGPT Login | NOT_STARTED |
| Stage 5 Rate Limit Domain | NOT_STARTED |
| Stage 6 REST API | NOT_STARTED |
| Stage 7 Web Dashboard | NOT_STARTED |
| Stage 8 Security Hardening | NOT_STARTED |
| Stage 9 Docker Deployment | NOT_STARTED |
| Stage 10 Final MVP Validation | NOT_STARTED |

## Task Ledger

TASK-0001～TASK-0003、TASK-0101～TASK-0106 DONE。TASK-0201 READY。TASK-0202～TASK-1007 依 implementation-plan.md 為 NOT_STARTED。

## Real Runtime Validation Ledger

Codex executable：PASS（Real Codex Verified, `codex-cli 0.155.0`）。app-server startup：PASS（Real Codex Verified）。app-server stop/no orphan：PASS（Real Codex Verified）。protocol initialize、account/read、device-code login、login completion、rateLimits/read、Docker startup、credential persistence：NOT_RUN。

## Security Validation Ledger

Authorization redaction、Access Token、Refresh Token、Cookie、Account API isolation、Rate Limit API isolation、Error sanitization、Raw protocol isolation：全部 NOT_RUN。

## Known Blockers

NONE.

## Human Decisions

NONE.

## Known Limitations

Stages 0–1 are complete. Real Codex process lifecycle is verified; transport T-40–T-44 are automated verified. Real protocol initialization and account/login/rate-limit behavior remain NOT_RUN.

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

完成 Task 後追加 TASK、STATUS、COMPLETED、CHANGED_FILES、TESTS、VALIDATION、RUNTIME_EVIDENCE、KNOWN_UNKNOWNS、NEXT_TASK。

## Luna Update Rules

Luna 只可更新 current status、relevant task/stage、runtime/security ledger、blockers、human decisions、completed task record。不得在此修改 Requirement、Architecture、Task definition、Test requirement 或 Acceptance Criteria。

## Session Resume Protocol

新 Luna Session 先讀本文件，取得 CURRENT_STAGE/CURRENT_TASK/LAST_COMPLETED_TASK/BLOCKED/HUMAN_REQUIRED，再讀相關 canonical sections/source files。不重做 DONE task、不重規劃 architecture。BLOCKED/HUMAN_REQUIRED 時不得自行前進。

## Current Next Action

```text
STATUS: ACTIVE
READY_TASK: TASK-0201
NEXT_ACTION: Implement TASK-0201 only.
```
