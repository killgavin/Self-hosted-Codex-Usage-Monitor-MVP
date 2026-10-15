# Codex Usage Monitor — Validation Execution Record

- Version: 1.4
- Status: GATE A PASS — executed 2026-09-25; GATES B/C NOT RUN
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

**Status:** PASS — completed 2026-09-25

### Environment

```text
Date: 2026-09-25 (Asia/Taipei)
Executor: Codex validation run
Windows version: Windows 10 Pro 25H2, build 26200
Architecture: Windows x64 / AMD64
Codex version: codex-cli 0.157.0
Codex executable: C:\Users\aple0\AppData\Local\Programs\OpenAI\Codex\bin\codex.exe
Runtime boundary: Native Windows executable and native `codex app-server --listen stdio://`; no WSL, Docker, or remote executable was used
```

### Evidence Checklist

| Check | Result | Evidence |
|---|---|---|
| app-server starts | PASS | Native Windows app-server started and completed the current JSON-RPC session. |
| initialize succeeds | PASS | Request `id=1` returned `platformFamily=windows`, `platformOs=windows`; `initialized` notification was sent. |
| account/read succeeds | PASS | Request `id=2` returned a non-null ChatGPT account with `type=chatgpt`, `planType=plus`, and `requiresOpenaiAuth=true`. |
| account/rateLimits/read succeeds | PASS | Request `id=3` returned a JSON-RPC success result. The complete redacted response is retained below. |
| usable rate-limit state returned | PASS | The result contains `rateLimits`, two `rateLimitsByLimitId` entries, usage percentages, reset timestamps, window durations, plan type, and reset-credit state. |
| required product state normalizable | PASS | Limit membership, usage, reset time, window duration, nullable reached state, plan type, reset-credit state, and primary/secondary windows can be represented without inventing absent values. |

### Superseded Validation Attempt

The immediately preceding validation attempt observed `account.type=chatgpt`, `account.planType=plus`, and `requiresOpenaiAuth=true`, then skipped `account/rateLimits/read` by treating that flag as proof that the account was not logged in. That conclusion is **superseded**. `requiresOpenaiAuth=true` indicates an OpenAI authentication requirement; it does not by itself establish whether the current account can read Rate Limits. The current run sent the RPC, and the app-server returned success.

### Protocol Evidence

The tested path was the native Windows process and stdio JSON-RPC/JSONL protocol. Requests were correlated with their matching responses:

```text
codex app-server --listen stdio://
→ {"method":"initialize","id":1,"params":{"clientInfo":{"name":"gate-a-validation","title":"Gate A Validation","version":"0.1.0"}}}
→ {"method":"initialized","params":{}}
→ {"method":"account/read","id":2,"params":{"refreshToken":false}}
→ {"method":"account/rateLimits/read","id":3}
```

Current account read summary:

```text
codex --version: codex-cli 0.157.0
initialize id=1: success; platformFamily=windows; platformOs=windows
account/read id=2: success; account.type=chatgpt; account.planType=plus; requiresOpenaiAuth=true
account/rateLimits/read id=3: success; JSON-RPC error code/message: none (success response)
stderr line count: 0
```

Complete JSON-RPC success result (sensitive account and reset-credit identifiers and reset-credit title/description values are redacted; no credentials were captured):

```json
{
  "id": 3,
  "result": {
    "ordinaryUsageAllowed": true,
    "rateLimits": {
      "limitId": "codex",
      "limitName": null,
      "normalModelSlug": null,
      "primary": {
        "usedPercent": 3,
        "windowDurationMins": 300,
        "resetsAt": 1790362724
      },
      "secondary": {
        "usedPercent": 87,
        "windowDurationMins": 10080,
        "resetsAt": 1790390287
      },
      "credits": {
        "hasCredits": false,
        "unlimited": false,
        "balance": "0"
      },
      "individualLimit": null,
      "spendControlReached": false,
      "planType": "plus",
      "rateLimitReachedType": null
    },
    "rateLimitsByLimitId": {
      "codex": {
        "limitId": "codex",
        "limitName": null,
        "normalModelSlug": null,
        "primary": {
          "usedPercent": 3,
          "windowDurationMins": 300,
          "resetsAt": 1790362724
        },
        "secondary": {
          "usedPercent": 87,
          "windowDurationMins": 10080,
          "resetsAt": 1790390287
        },
        "credits": {
          "hasCredits": false,
          "unlimited": false,
          "balance": "0"
        },
        "individualLimit": null,
        "spendControlReached": false,
        "planType": "plus",
        "rateLimitReachedType": null
      },
      "base_model_inference": {
        "limitId": "base_model_inference",
        "limitName": "gpt-reserve",
        "normalModelSlug": "gpt-5.6-luna",
        "primary": {
          "usedPercent": 53,
          "windowDurationMins": 10080,
          "resetsAt": 1790444376
        },
        "secondary": null,
        "credits": null,
        "individualLimit": null,
        "spendControlReached": null,
        "planType": "plus",
        "rateLimitReachedType": null
      }
    },
    "rateLimitResetCredits": {
      "availableCount": 3,
      "credits": [
        {
          "id": "[REDACTED]",
          "resetType": "codexRateLimits",
          "status": "available",
          "grantedAt": 1788499857,
          "expiresAt": 1791091857,
          "title": "[REDACTED]",
          "description": "[REDACTED]"
        },
        {
          "id": "[REDACTED]",
          "resetType": "codexRateLimits",
          "status": "available",
          "grantedAt": 1788565865,
          "expiresAt": 1791157865,
          "title": "[REDACTED]",
          "description": "[REDACTED]"
        },
        {
          "id": "[REDACTED]",
          "resetType": "codexRateLimits",
          "status": "available",
          "grantedAt": 1790104513,
          "expiresAt": 1792696513,
          "title": "[REDACTED]",
          "description": "[REDACTED]"
        }
      ]
    },
    "accountId": "[REDACTED]",
    "rateLimitUpsell": null
  }
}
```

### Normalization Findings

| Product State field | Actual upstream field(s) | Current mapping |
|---|---|---|
| limit identity / membership | `rateLimitsByLimitId` keys and each `limitId` | Two limits: `codex` and `base_model_inference`; `base_model_inference` has `limitName=gpt-reserve`. |
| used percentage | each limit's `primary.usedPercent` / `secondary.usedPercent` | `codex`: primary 3%, secondary 87%; `base_model_inference`: primary 53%. |
| reset time | each present window's `resetsAt` | `codex` primary `1790362724` (`2026-09-25T18:58:44Z`), secondary `1790390287` (`2026-09-26T02:38:07Z`); `base_model_inference` primary `1790444376` (`2026-09-26T17:39:36Z`). |
| window duration | each present window's `windowDurationMins` | `codex`: 300 and 10080 minutes; `base_model_inference`: primary 10080 minutes. |
| reached state | each limit's `rateLimitReachedType` | Present as `null` for both limits; preserve as unknown/null and do not infer a reached state. |
| plan type | each limit's `planType` | `plus`. |
| reset-credit state | `rateLimitResetCredits.availableCount` and `.credits[]` | `availableCount=3`; all three entries have `status=available` and `resetType=codexRateLimits`. Their identifiers and descriptive text are redacted. |
| primary window | each limit's `primary` | Present for both limits with usage, reset time, and duration above. |
| secondary window | each limit's `secondary` | Present for `codex`; `null` for `base_model_inference`, preserved without inventing a window. |

Additional response fields retained in the full result: `ordinaryUsageAllowed=true`; the separate `rateLimits.credits` object reports `hasCredits=false`, `unlimited=false`, `balance="0"`; `rateLimitUpsell=null`. The distinct `rateLimitResetCredits` collection is preserved separately and is not inferred from `rateLimits.credits`.

The returned state is sufficient to normalize the Formal Specification Product State. Optional `rateLimitReachedType` and secondary-window values remain nullable as returned.

### Result

```text
Gate A: PASS
A-04: PASS
A-05: PASS
A-06: PASS
```

### Issues

- None observed in this Gate A execution.

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
| Gate A — Windows Native Codex | PASS |
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
VALIDATION EXECUTION: GATE A PASS; GATES B/C NOT RUN
FULL IMPLEMENTATION READINESS: NOT YET ESTABLISHED
```
