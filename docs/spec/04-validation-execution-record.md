# Codex Usage Monitor — Validation Execution Record

- Version: 0.6
- Status: GATE A EXECUTED — BLOCKED; GATES B/C NOT RUN
- Source: `03-formal-executable-specification.md`
- Purpose: Standard evidence record for Validation Gates. This is not an Implementation Plan.

## Rules

1. Do not mark PASS without evidence.
2. Do not infer missing evidence.
3. Record FAIL when a criterion is demonstrably not satisfied.
4. Record BLOCKED when the environment/prerequisite prevents execution.
5. Redact credentials, tokens, passwords, and sensitive identifiers.
6. A rerun supersedes an earlier result only when the new evidence is retained.

---

## Gate A — Windows Native Codex

**Status:** BLOCKED — executed 2026-09-25

### Environment

```text
Date: 2026-09-25 (Asia/Taipei; current rerun)
Executor: Codex validation run
Windows version: Registry evidence = Windows 10 Pro, version 10.0.26200.0, display version 25H2, build 26200
Architecture: Windows x64 (RuntimeInformation.OSArchitecture = X64; PROCESSOR_ARCHITECTURE = AMD64)
Codex version: codex-cli 0.156.1
Codex executable: C:\Users\aple0\AppData\Local\Programs\OpenAI\Codex\bin\codex.exe
Runtime boundary: native Windows executable and native `codex app-server --listen stdio://`; no WSL, Debian, Docker, or remote executable was used
Authentication status: `codex login status` = Not logged in
```

### Evidence Checklist

| Check | Result | Evidence |
|---|---|---|
| app-server starts | PASS | Native Windows `codex.exe app-server --listen stdio://` process started, completed the exchange, exited with code 0, and emitted 0 non-empty stderr lines. |
| initialize succeeds | PASS | Request id 1 returned a result with `platformFamily=windows`, `platformOs=windows`; result keys were `userAgent`, `codexHome`, `platformFamily`, `platformOs`. The required `initialized` notification was then sent. |
| account/read succeeds | PASS | Request id 2 returned a JSON-RPC result with `account=null` and `requiresOpenaiAuth=true`; result keys were `account`, `requiresOpenaiAuth`, `workspaceRouting`. No account value was retained. |
| account/rateLimits/read succeeds | BLOCKED | Not sent after `account/read` established that authentication is required. Per Gate A authentication rule, execution stopped before this step; this is not classified as FAIL. |
| usable rate-limit state returned | BLOCKED | No rate-limit response was obtained because authentication is required. |
| required product state normalizable | BLOCKED | No live `account/rateLimits/read` response was available for normalization; no rate-limit fields were invented. |

### Protocol Evidence

The tested path was the native Windows process and stdio JSON-RPC/JSONL protocol. Each request was sent after the previous request's matching response was received:

```text
codex app-server --listen stdio://
→ {"method":"initialize","id":1,"params":{"clientInfo":{"name":"gate-a-validation","title":"Gate A Validation","version":"0.1.0"}}}
→ {"method":"initialized","params":{}}
→ {"method":"account/read","id":2,"params":{"refreshToken":false}}
```

Secret-free runtime summary:

```text
codex --version: codex-cli 0.156.1
codex login status: Not logged in
id=1: result; platformFamily=windows; platformOs=windows; result keys=userAgent,codexHome,platformFamily,platformOs
id=2: result; account=null; requiresOpenaiAuth=true; result keys=account,requiresOpenaiAuth,workspaceRouting
additional notification observed: remoteControl/status/changed (not used for the gate decision)
process exit code=0; stderr line count=0
```

The request sequence and method names are consistent with the official Codex App Server protocol documentation: https://developers.openai.com/codex/app-server

No credential, token, cookie, password, account identifier value, email, or API key was retained in evidence. The exchange used only the native stdio app-server boundary; no private endpoint or credential-file parsing was used. Because the live account result required authentication, no login attempt was made.

### Normalization Findings

No Formal Product State rate-limit fields can be confirmed in this rerun. The only live account-level fact relevant to the gate is `requiresOpenaiAuth=true`; `account` and `planType` were absent. Limit identity/membership, used percentage, reset time, window duration, reached state, plan type from rate-limit data, reset-credit state, primary window, and secondary window remain unassessed pending authentication.

### Result

```text
Gate A: BLOCKED
Reason: Authentication required
```

### Issues

- `codex login status` reported `Not logged in`; `account/read` returned `account=null` and `requiresOpenaiAuth=true`, so the rate-limit request was not attempted.
- `00-decisions.md`, `01-product-requirements.md`, `02-system-architecture.md`, and `03-formal-executable-specification.md` were not found anywhere in the current checkout; only this validation record was present under `docs/spec/`.
- The initial `Get-CimInstance Win32_OperatingSystem` query was denied by the execution environment; Windows version/build evidence was obtained read-only from the Windows registry instead.

---

## Gate B — IIS Filesystem Publication

**Status:** NOT RUN

### Environment

```text
Date:
Executor:
Collector OS/runtime platform:
Target filesystem/share type:
Target directory (redact if required):
IIS relationship to target:
Credential mechanism (type only; never secret):
```

### Evidence Checklist

| Check | Result | Evidence reference / note |
|---|---|---|
| target directory writable | NOT RUN | |
| temp file can be created in target directory | NOT RUN | |
| temp file flush/close succeeds | NOT RUN | |
| final replace/rename succeeds | NOT RUN | |
| repeated publication succeeds | NOT RUN | |
| concurrent static reads never intentionally expose partial JSON | NOT RUN | |
| permission/credential model acceptable | NOT RUN | |

### Result

```text
Gate B: NOT RUN
```

**PASS rule:** every checklist item is PASS.

---

## Gate C — IIS HTTPS Distribution

**Status:** NOT RUN

### Environment

```text
Date:
Executor:
Public test endpoint: [REDACT IF REQUIRED]
IIS version:
Client/network used for external test:
```

### Evidence Checklist

| Check | Result | Evidence reference / note |
|---|---|---|
| external HTTPS GET succeeds | NOT RUN | |
| certificate behavior acceptable | NOT RUN | |
| JSON MIME/content type correct | NOT RUN | |
| Cache-Control behavior known | NOT RUN | |
| ETag and/or Last-Modified behavior known | NOT RUN | |
| replaced snapshot becomes observable | NOT RUN | |
| access-control policy explicitly approved | NOT RUN | |

### Result

```text
Gate C: NOT RUN
```

**PASS rule:** every checklist item is PASS.

---

## Overall Readiness

| Dependency | Status |
|---|---|
| Gate A — Windows Native Codex | BLOCKED |
| Gate B — IIS Filesystem Publication | NOT RUN |
| Gate C — IIS HTTPS Distribution | NOT RUN |
| Exact current.json wire contract | OPEN |
| Android technology | OPEN |
| Widget delivery phase | OPEN |
| Foreground refresh interval | OPEN |
| Stale threshold | OPEN |
| Heartbeat/status resource | OPEN |
| Optional FTP-family publisher | OPEN |

### Overall Result

```text
FORMAL SPECIFICATION: READY
VALIDATION EXECUTION: INCOMPLETE — GATES B/C NOT RUN
FULL IMPLEMENTATION READINESS: NOT YET ESTABLISHED
```
