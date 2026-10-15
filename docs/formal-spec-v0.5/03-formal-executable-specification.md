# Codex Usage Monitor — Formal Executable Specification

- Version: 0.5
- Status: FORMAL / EXECUTABLE WITH EXPLICIT GATES
- Authority: Derived only from the Current Canonical Context:
  1. `00-decisions.md`
  2. `01-product-requirements.md`
  3. `02-system-architecture.md`
- Precedence: `00-decisions.md` > `01-product-requirements.md` > `02-system-architecture.md` > this document.
- Purpose: Convert the accepted product direction into unambiguous, testable, execution-ready requirements without defining an Implementation Plan.
- Important: A Validation Gate that has not passed remains unresolved. No executor may silently assume it has passed.

## 1. How an Executor Must Use This Document

An engineer or coding agent executing future work MUST:

1. read the three canonical documents before this specification;
2. obey Accepted Decisions;
3. treat Proposed Decisions as conditional;
4. ignore Superseded Decisions as implementation direction;
5. stop at any dependency whose required Validation Gate has not passed;
6. record validation evidence before treating a gated assumption as true;
7. implement only behavior explicitly required by the canonical context or this specification;
8. not reintroduce the legacy Web-first/Python/FastAPI/Debian architecture unless a future Decision explicitly does so.

This document is executable as a **requirements and validation contract**. It is not a task sequence, sprint plan, file-by-file coding plan, or repository migration plan.

## 2. Normative Terms

- **MUST / MUST NOT** — mandatory.
- **SHOULD / SHOULD NOT** — expected unless a documented reason justifies deviation.
- **MAY** — optional.
- **OPEN** — unresolved Human Gate; no implementation assumption may be made.
- **GATED** — dependent behavior may be designed abstractly, but production/platform claims require gate evidence.
- **PASS** — all stated pass criteria are satisfied with evidence.
- **FAIL** — at least one pass criterion is not satisfied.
- **BLOCKED** — validation cannot be completed because a prerequisite/environment is unavailable.

## 3. Required System Outcome

The target product MUST provide this logical flow:

```text
Codex App Server
    ↓ stdio JSON-RPC
Collector
    ↓ normalize
Semantic comparison
    ↓ latest changed state
60-second publication throttle
    ↓
Versioned current.json
    ↓ filesystem publication
IIS static web directory
    ↓ HTTPS
Android App
    ↓ last-valid local cache
Home Screen Widget
```

The primary product MUST NOT require a publicly reachable Collector endpoint.

## 4. Component Contracts

### FS-CODEX-001 — Upstream protocol

Collector MUST use official `codex app-server` through stdio JSON-RPC.

Required operations:

```text
initialize
account/read
account/rateLimits/read
```

Collector MUST NOT use private `/backend-api/wham/*` endpoints or direct credential-file parsing as the formal integration contract.

**Acceptance:** Gate A demonstrates the required sequence and obtains rate-limit data that can be normalized.

### FS-COL-001 — Collector responsibilities

Collector MUST own:

- Codex process lifecycle;
- JSON-RPC communication;
- upstream state parsing;
- product-state normalization;
- semantic comparison;
- latest pending snapshot;
- publication throttling;
- JSON serialization;
- publisher invocation;
- local operational logging.

Collector MUST NOT require:

- GUI;
- database;
- public Web server;
- cloud database;
- IIS application code.

### FS-COL-002 — Cross-platform source model

Collector MUST use one shared source base and target-specific native builds.

Accepted targets:

```text
Windows x64 — Tier 1; Gate A validated for Native Codex integration (2026-09-25)
Linux x64   — Tier 2 target; not validated by Gate A
```

Gate A establishes the Native Windows Codex integration only. It does not establish Gate B, Gate C, Collector implementation readiness, or end-to-end production readiness.

### FS-DATA-001 — Generic limit model

The normalized model MUST NOT hard-code only “5-hour” and “Weekly” limits.

For each limit, the model MUST be capable of representing:

- stable identity;
- optional display name;
- optional primary window;
- optional secondary window;
- used percentage;
- reset time;
- window duration;
- reached state when available;
- reset-credit state when available.

Unknown optional upstream fields MUST NOT crash Collector or Mobile solely because they are unknown.

### FS-DATA-002 — Logical published snapshot

`current.json` MUST represent this logical model:

```text
PublishedUsageSnapshot
├─ schemaVersion
├─ snapshotUpdatedAt
├─ account
│  └─ planType?
├─ limits[]
│  ├─ id
│  ├─ name?
│  ├─ primary?
│  │  ├─ usedPercent
│  │  ├─ resetAt
│  │  └─ windowDurationMinutes
│  ├─ secondary?
│  │  ├─ usedPercent
│  │  ├─ resetAt
│  │  └─ windowDurationMinutes
│  └─ reachedType?
└─ resetCredits?
```

The exact wire schema is **not yet frozen by the Current Canonical Context**. An executor MUST NOT invent a permanent wire contract and call it canonical.

Before Collector↔Mobile integration is declared contract-complete, the exact schema MUST be promoted through a future explicit specification/Decision review.

### FS-DATA-003 — Sensitive-data exclusion

Published data MUST NOT contain:

- OpenAI/Codex credentials;
- tokens;
- publisher credentials;
- passwords;
- unnecessary sensitive account identifiers;
- unnecessary internal host/network details.

The published snapshot MUST be safe under the assumption that an anonymously readable IIS resource can become publicly observable.

## 5. Normalization and Comparison

### FS-NORM-001 — Semantic normalization

Normalization MUST preserve product-visible values and MUST remove representation-only differences.

Semantic values include, when present:

- limit identity/membership;
- used percentage;
- reset time;
- window duration;
- reached state;
- plan type;
- reset-credit state.

The following MUST NOT independently create a semantic change:

- event arrival timestamp;
- JSON property ordering;
- unused upstream metadata.

### FS-NORM-002 — Comparison baseline

Collector MUST compare the latest normalized state against the **last successfully published normalized state**.

If there is no semantic difference, Collector MUST NOT publish.

If there is a semantic difference, the newest normalized state MUST become the latest pending state.

A failed publication MUST NOT advance the comparison baseline.

## 6. Publication Throttle

### FS-PUB-001 — Maximum successful publication frequency

Collector MUST allow at most one successful snapshot publication in any 60-second minimum interval.

The minimum interval MUST be externally configurable, with **60 seconds as the current required product value**.

### FS-PUB-002 — Coalescing

If multiple semantic changes occur while publication is not permitted:

```text
older pending state → replace
newest pending state → retain
```

Only the newest pending state is required for the next publication attempt.

Intermediate states MUST NOT be replayed as history.

### FS-PUB-003 — Failure retention

If publication fails:

- `LastPublishedSnapshot` MUST remain unchanged;
- the newest pending state MUST remain retryable;
- the previous valid published file MUST remain the intended client fallback;
- failure MUST be logged locally without secrets.

## 7. Filesystem Publisher

### FS-FILE-001 — Primary target

The primary publisher MUST write to the IIS web directory presented as a filesystem path.

Environment presentation MAY be:

```text
Windows UNC/shared path
Linux mounted SMB/CIFS path
```

Network-share setup and credentials are environment concerns, not Collector business logic.

### FS-FILE-002 — Safe replacement

Required logical sequence:

```text
serialize complete snapshot
→ create/write temporary file in target directory/filesystem
→ flush/close
→ replace/rename published current.json
```

A write MUST be considered successful only after the final published representation is established.

Exact production safety on the real share is **GATED by Gate B**.

## 8. IIS Distribution

### FS-IIS-001 — Static-only responsibility

IIS MUST:

- statically serve `current.json`;
- serve it through HTTPS.

IIS MUST NOT be required to:

- run Collector;
- invoke Codex;
- store OpenAI/Codex credentials;
- expose a custom Usage API;
- proxy Mobile requests to Collector.

### FS-IIS-002 — HTTP behavior

Production use is **GATED by Gate C**.

Gate C MUST establish:

- external HTTPS retrieval;
- acceptable certificate behavior;
- correct JSON MIME behavior;
- caching behavior that does not prevent freshness;
- known `ETag` and/or `Last-Modified` behavior when available;
- approved access-control policy.

## 9. Android App Contract

### FS-APP-001 — Read-only client

The App MUST retrieve `current.json` through HTTPS.

It MUST NOT:

- call Codex/OpenAI directly;
- require Collector-host access;
- contain Collector publishing credentials;
- require FTP for the primary path.

### FS-APP-002 — Last-valid cache

The App MUST retain the last valid supported snapshot locally.

A new download MUST replace that cache only after validation succeeds.

Malformed/unparseable/unsupported data MUST NOT overwrite the last-valid cache.

### FS-APP-003 — Refresh triggers

The App MUST attempt refresh on:

- launch;
- resume;
- manual refresh.

Per-second network polling MUST NOT occur.

Foreground periodic refresh MAY be implemented only after its interval is explicitly resolved.

### FS-APP-004 — Stale state

If retrieval fails and a valid cache exists, the App MUST remain capable of displaying cached state and MUST support a stale/age indication.

The exact stale threshold remains OPEN.

### FS-APP-005 — Countdown

Countdown MUST be derived from:

```text
remaining = resetAt - currentDeviceTime
```

Countdown ticks MUST NOT perform network I/O.

High-frequency countdown UI MUST run only in foreground.

On foreground return, countdown MUST be recalculated from absolute reset time.

## 10. Widget Contract

### FS-WGT-001 — Summary content

When delivered, the Widget MUST support concise display of:

- primary percentage;
- secondary percentage when present;
- absolute reset time;
- last snapshot update time;
- stale indication when applicable.

### FS-WGT-002 — Resource behavior

Widget MUST NOT perform per-second network polling or require continuous second-level background execution.

Widget SHOULD use the App's local valid cache whenever practical.

The exact delivery phase remains OPEN.

## 11. Security Invariants

| ID | Mandatory invariant |
|---|---|
| SEC-001 | OpenAI/Codex authentication material remains on Collector host. |
| SEC-002 | Publisher write credentials remain Collector-side. |
| SEC-003 | Mobile/Widget do not possess Codex/OpenAI or publisher-write credentials. |
| SEC-004 | Secrets/tokens/passwords are not written to normal logs. |
| SEC-005 | `current.json` contains only data approved for static distribution. |
| SEC-006 | Secrets are not committed to the repository. |

Any violation of these invariants is a conformance failure.

## 12. Failure Semantics

| Condition | Required result |
|---|---|
| Codex unavailable | Do not invent quota data; preserve last published state. |
| Optional/unknown upstream field | Do not fail solely because the field is optional/unknown. |
| Publish target unavailable | Preserve previous published state; retain newest pending state. |
| Temp/final write fails | Do not advance `LastPublishedSnapshot`. |
| HTTPS retrieval fails | Use last-valid Mobile cache when available. |
| New JSON malformed | Do not overwrite last-valid cache. |
| Mobile offline | Cached state may display with stale/age indication. |
| UI timer delayed/suspended | Recalculate from absolute reset time. |

## 13. Configuration Contract

Environment-specific configuration MUST support at least:

```text
codex executable
codex arguments
publisher type
publisher target path
minimum publish interval
logging level
optional publisher credential/reference
```

Hard-coded production credentials are prohibited.

## 14. Validation Gates

### Gate A — Windows Native Codex

**Purpose:** validate Native Windows Codex integration as the Gate A criterion for the Windows x64 Tier 1 target.

**Status:** PASS — 2026-09-25  
**Evidence:** `04-validation-execution-record.md`, Gate A.  
**Scope:** Windows Native Codex integration, rate-limit state acquisition, and product-state normalization only. Gate B and Gate C remain separate.

**Precondition:** Windows x64 environment with configured Codex runtime.

**Execution:**

```text
1. Start configured codex app-server.
2. Complete initialize.
3. Execute account/read.
4. Execute account/rateLimits/read.
5. Capture returned rate-limit state.
6. Demonstrate that required product fields can be normalized.
```

**PASS only if:**

- app-server starts;
- initialize succeeds;
- account/read succeeds;
- account/rateLimits/read succeeds;
- usable rate-limit state is returned;
- required product state can be normalized.

Otherwise status is FAIL or BLOCKED.

### Gate B — IIS Filesystem Publication

**Purpose:** validate the real primary publication path.

**Precondition:** intended Collector runtime can access the actual IIS shared directory.

**Execution:**

```text
1. Write a complete temporary JSON file in the target directory.
2. Flush/close it.
3. Replace/rename it to the production-style current.json path.
4. Repeat publication while IIS/static readers retrieve current.json.
5. Verify readers never intentionally receive a partially written JSON document.
6. Verify permissions and credential handling are operationally acceptable.
```

**PASS only if:**

- write access succeeds;
- replacement succeeds;
- repeated read/write testing does not expose partial JSON;
- the credential/permission model is acceptable.

### Gate C — IIS HTTPS Distribution

**Purpose:** validate the actual Mobile distribution path.

**Precondition:** production-style IIS static path is externally reachable for testing.

**Execution:**

```text
1. Retrieve current.json through external HTTPS.
2. Verify certificate behavior.
3. Verify JSON content type/MIME behavior.
4. Inspect cache headers.
5. Inspect ETag and/or Last-Modified when available.
6. Replace current.json and verify clients can observe the new representation.
7. Confirm and record access-control policy.
```

**PASS only if:**

- external HTTPS GET succeeds;
- certificate behavior is acceptable;
- JSON is served correctly;
- cache behavior does not prevent required freshness;
- validator behavior is known;
- access-control policy is explicitly approved.

## 15. Gate Dependency Matrix

Gate results recorded on 2026-09-25: Gate A PASS; Gate B NOT RUN; Gate C NOT RUN.

| Capability | Evidence status | Current conclusion |
|---|---|---|
| Abstract Collector core behavior | Specification only | Specified; no implementation claim. |
| Windows x64 Tier 1 Native Codex integration | Gate A PASS — 2026-09-25 | Established for Native Codex integration and product-state normalization. |
| Real IIS filesystem publisher | Gate B NOT RUN | Not established; production-safe claim is not supported. |
| Real Mobile HTTPS distribution | Gate C NOT RUN | Not established; production-ready claim is not supported. |
| End-to-end Windows→IIS→Android production readiness | Gate A PASS; Gate B/C NOT RUN | Not established; not production-ready. |
| Linux x64 design target | Not validated by Gate A | Tier 2 target; Linux runtime is not validated by these gates. |

A coding agent MUST NOT claim an unvalidated capability is established without its required evidence.

## 16. Open Human Gates

These are deliberately unresolved:

| ID | Item | Executor rule |
|---|---|---|
| HG-001 | Android technology (`.NET MAUI` vs `Kotlin`) | Do not choose silently. |
| HG-002 | Widget delivery phase | Do not assume MVP inclusion timing. |
| HG-003 | Foreground periodic refresh interval | Do not invent an interval. |
| HG-004 | Stale threshold | Do not invent a threshold. |
| HG-005 | Separate heartbeat/status resource | Do not add one without decision. |
| HG-006 | Optional FTP/FTPS/SFTP publisher need/protocol | Do not make it mandatory. |
| HG-007 | Exact `current.json` wire schema | Do not declare a permanent schema canonical without explicit review. |

These Human Gates do not prevent validation of unrelated components.

## 17. Explicit Non-requirements

The current target MUST NOT be expanded to require:

- public Collector Web server;
- Mobile→Collector direct connection;
- Mobile→Codex direct connection;
- Cloudflare Tunnel;
- Firebase/Supabase;
- new IIS API;
- FTP as IIS relay;
- Debian-only runtime;
- Docker as mandatory runtime;
- Python/FastAPI as the new Collector;
- usage-history database;
- multi-user SaaS;
- remote Codex command execution;
- iOS support;
- push infrastructure.

## 18. Requirement Traceability

| Formal ID group | Canonical source |
|---|---|
| FS-CODEX | DEC-002, PR-002, Architecture §4 |
| FS-COL | DEC-013/014/015/016, PR-001/002, Architecture §3 |
| FS-DATA | DEC-003/012, PR-003/004, Architecture §6 |
| FS-NORM | DEC-008, PR-005, Architecture §5 |
| FS-PUB | DEC-009, PR-006/021, Architecture §5 |
| FS-FILE | DEC-006/007, PR-007/008/009, Architecture §7 |
| FS-IIS | DEC-004/005, PR-010/011, Architecture §8 |
| FS-APP | DEC-001/010/011, PR-012–015/018–022, Architecture §9–10 |
| FS-WGT | DEC-001/010, PR-016/017, Architecture §11 |
| Security | DEC-011, PR-018–020, Architecture §12 |
| Gates | DEC-002/004/007/016, PR §10, Architecture §15 |

## 19. Definition of Specification Conformance

A future implementation is conformant only when:

1. every applicable MUST/MUST NOT requirement is satisfied;
2. no Accepted Decision is violated;
3. no Superseded Decision is reintroduced as current direction;
4. all production claims dependent on a Validation Gate have PASS evidence;
5. unresolved Human Gates are not silently decided by the implementer;
6. failure and security invariants are verified;
7. the final Collector↔Mobile wire contract is explicitly frozen before cross-component integration is declared complete.

## 20. Current Execution Boundary

As of this specification version:

```text
Allowed now:
- execute Gate B validation when target environment is available
- execute Gate C validation when target IIS path is available
- perform requirements-based design that does not assume unresolved Human Gates

Not established by current validation evidence:
- declare IIS publication production-safe
- declare IIS HTTPS distribution production-ready
- declare the full Windows→IIS→Android path production-ready

Not authorized by this document alone:
- freeze the final current.json wire schema
- silently select Android technology
- begin a repository-wide implementation/migration plan
```

This boundary is intentional. “Executable” means every known prerequisite, pass condition, stop condition, and acceptance rule is explicit; it does not mean unresolved decisions are fabricated.
