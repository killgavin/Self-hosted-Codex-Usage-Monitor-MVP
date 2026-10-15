# Codex Usage Monitor — System Architecture

- Version: 0.4-draft
- Status: CURRENT DRAFT / HUMAN REVIEW REQUIRED
- Decision Source: `00-decisions.md`
- Requirement Source: `01-product-requirements.md`
- Purpose: Describe only the current target architecture.

## 1. Current Target Architecture

```text
                           OpenAI
                             ▲
                             │
                     Codex App Server
                             ▲
                             │ stdio JSON-RPC
                             │
┌────────────────────────────┴─────────────────────────────┐
│ Cross-platform Codex Usage Collector                   │
│ Target implementation: Go                             │
│                                                        │
│ Codex Process / JSON-RPC Boundary                     │
│ Rate-limit State                                      │
│ Snapshot Normalizer                                   │
│ Semantic Comparer                                     │
│ 60-second Publish Throttle                            │
│ JSON Serializer                                       │
│ Publisher Abstraction                                 │
└───────────────────────┬──────────────────────┬─────────┘
                        │                      │
                Primary │                      │ Optional
                        │                      │
              Filesystem Publisher       FTP/FTPS/SFTP
                        │                      │
                        ▼                      ▼
              IIS Shared Web Directory   Independent Target
                        │
                   current.json
                        │
                       IIS
                        │ HTTPS
                        ▼
                  Android App
                        │
                   Local Cache
                        │
                      Widget
```

## 2. Current Repository vs Target Architecture

The repository currently contains a completed legacy Web MVP implemented with Python/FastAPI/Docker.

That implementation is **not modified by this documentation pass**.

For future design work:

- legacy Web MVP code and validation remain useful implementation evidence
- legacy Web-first canonical documents are not the source of truth for the new target direction
- migration/retirement of old production code requires a separate future plan

## 3. Collector Architecture

### 3.1 Technology and distribution

Target Collector language:

```text
Go
```

Cross-platform model:

```text
one source tree
→ target-specific native builds
```

Target platform priority:

```text
Windows x64 → Tier 1 (Native Codex validation PASS — Gate A, 2026-09-25)
Linux x64   → Tier 2
```

Gate A establishes Native Windows Codex integration and rate-limit normalization only. It does not establish Gate B, Gate C, Collector implementation readiness, or end-to-end production readiness.

Future optional targets may include Linux ARM64 and macOS.

### 3.2 Core responsibilities

Collector Core owns:

```text
Codex process lifecycle
→ stdio JSON-RPC
→ upstream DTO/state
→ normalization
→ semantic comparison
→ pending latest snapshot
→ publish throttle
→ JSON serialization
→ publisher invocation
```

Collector Core does not require:

- GUI
- database
- public Web server
- cloud database
- IIS application code

### 3.3 Platform boundaries

Platform/environment-specific concerns are kept outside product logic:

- Codex executable path
- Codex arguments
- service hosting
- publish filesystem path
- network-share mounting/credentials
- optional publisher credentials

Windows Service and Linux systemd are hosting concerns, not separate Collector implementations.

## 4. Codex Boundary

Collector starts a configured Codex executable and communicates through stdio JSON-RPC.

Required upstream operations for the current product:

```text
initialize
account/read
account/rateLimits/read
```

Rate-limit notifications/events may update the latest in-memory state when supported.

Formal integration must not depend on:

- private `/backend-api/wham/*`
- direct parsing of `auth.json` as the protocol contract
- Mobile-side Codex authentication

Unknown protocol fields and optional values must fail safely.

## 5. Snapshot Pipeline

```text
Codex response / event
        ↓
Parse protocol DTO
        ↓
Normalize product state
        ↓
Compare against LastPublishedSnapshot
        ↓
Unchanged?
  ├─ Yes → Ignore
  └─ No  → LatestPendingSnapshot
                  ↓
            60-second gate
                  ↓
             Serialize JSON
                  ↓
               Publish
```

### 5.1 Comparison semantics

Semantic comparison includes product-visible state such as:

- limit identity/membership
- used percentage
- reset time
- window duration
- reached state
- plan type
- reset-credit state when exposed

It excludes:

- event arrival timestamp
- JSON property order
- unused upstream metadata

### 5.2 Publish failure

On failure:

- `LastPublishedSnapshot` is not advanced
- existing published file is not intentionally destroyed
- latest pending state remains available for retry
- intermediate states are not replayed

## 6. `current.json` Boundary

`current.json` is the only required Collector-to-Mobile data contract.

Logical shape:

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

Exact wire schema is intentionally not frozen in this architecture document.

When implementation requires a stable wire-level contract, create:

```text
03-current-json-contract.md
```

rather than expanding architecture/history documents.

## 7. Publisher Architecture

### 7.1 Publisher boundary

Collector uses a publisher abstraction conceptually equivalent to:

```text
Publish(snapshot)
```

Core logic must not depend on IIS, FTP, or one operating system.

### 7.2 Primary publisher — filesystem

Primary target is the IIS web directory presented to Collector as a writable filesystem path.

Possible environment presentations:

```text
Windows:
\\IIS-SERVER\<share>\current.json

Linux:
mounted SMB/CIFS share
→ /mnt/<share>/current.json
```

The target path is configuration-driven.

Collector does not require an embedded SMB protocol implementation unless the environment later makes filesystem presentation impossible.

### 7.3 Safe replacement

Expected publication behavior:

```text
serialize latest snapshot
→ write temp file in target directory/filesystem
→ flush/close
→ replace/rename current.json
```

The exact replace/atomicity behavior must be verified on the production IIS share.

### 7.4 Optional publishers

Independent optional publisher implementations may later support:

- SFTP
- FTPS
- FTP

They do not sit between Collector and IIS.

## 8. IIS Architecture

IIS is a static distribution surface only.

Responsibilities:

```text
serve current.json
over HTTPS
```

IIS does not:

- run the Collector
- invoke Codex
- store OpenAI credentials
- expose a new custom Usage API
- forward Mobile requests to Collector

Operational validation must cover:

- external HTTPS reachability
- certificate validity
- JSON MIME type
- Cache-Control
- ETag / Last-Modified where available
- access-control policy

## 9. Android Architecture

### 9.1 Data path

```text
Android App
    ↓ HTTPS GET / conditional GET
IIS current.json
```

The App maintains a local last-valid snapshot.

### 9.2 Cache behavior

Local cache is used for:

- immediate launch rendering
- temporary offline/network failure
- Widget state
- protection against malformed new downloads

Malformed/unparseable new data must not overwrite the last valid snapshot.

### 9.3 Refresh behavior

Required triggers:

- App launch
- App resume
- manual refresh

Periodic foreground refresh is allowed but interval remains undecided.

Conditional HTTP requests should be used when IIS exposes suitable validators.

No per-second network polling is allowed.

## 10. Countdown Architecture

Reset countdown is derived locally:

```text
remaining = resetAt - currentDeviceTime
```

Timer behavior:

- timer updates UI only
- no timer tick performs network I/O
- high-frequency countdown stops when App enters background
- returning to foreground recalculates from absolute reset time, preventing timer drift

Exact UI cadence is presentation policy and does not affect Collector/IIS traffic.

## 11. Widget Architecture

Widget is a summary client, not a Collector.

Preferred data source:

```text
App local cache
```

Widget presents:

- primary percentage
- secondary percentage when present
- absolute reset time
- last updated time
- stale indicator

Widget does not require per-second network or rendering activity.

## 12. Security Boundaries

### Collector host

May contain:

- Codex/OpenAI authentication material managed through Codex runtime
- filesystem/share credentials
- optional FTP-family publisher credentials

### Published `current.json`

Must not contain secrets.

It contains only normalized usage state required by Mobile.

### IIS

Hosts static JSON only.

If anonymous access is enabled, JSON must be treated as potentially public.

### Android / Widget

Read-only consumers.

They never contain credentials capable of modifying the IIS target or authenticating to Codex/OpenAI.

## 13. Failure Behavior

### Codex unavailable

Collector must preserve last known published state and report/log failure locally without inventing quota data.

### Publish target unavailable

Collector retains latest pending state and retries later; previously valid `current.json` remains the client fallback.

### Invalid downloaded JSON

Mobile retains the last valid local cache.

### Mobile offline

Mobile displays last known valid state with stale/age indication.

## 14. Configuration Boundary

Configuration must cover environment-specific values rather than hard-coding OS assumptions.

At minimum:

```text
codex executable
codex arguments
publisher type
publisher target path
minimum publish interval
logging level
optional publisher credentials/reference
```

Secrets must not be committed to the repository.

## 15. Validation Gates

### Gate A — Windows Native Codex

**Status:** PASS  
**Date:** 2026-09-25  
**Evidence:** `04-validation-execution-record.md`, Gate A.  
**Scope:** Native Windows Codex integration, rate-limit state acquisition, and product-state normalization. This does not establish Gate B, Gate C, or full deployment readiness.

Retained validation contract:

```text
Windows x64
→ start codex app-server
→ initialize
→ account/read
→ account/rateLimits/read
→ valid rate-limit snapshot
```

### Gate B — IIS filesystem publish

Required before primary publisher is implementation-ready:

- Collector runtime can write target share
- temp-write + replace works safely
- concurrent IIS reads do not expose partial JSON

### Gate C — IIS HTTPS distribution

Required before Mobile implementation depends on the path:

- external HTTPS GET succeeds
- caching semantics are known
- access-control policy is approved

## 16. Explicitly Not Current Architecture

The following are not part of the current target architecture:

- Mobile → legacy Monitor REST API
- Mobile → Collector directly
- Cloudflare Tunnel
- Firebase / Supabase
- new IIS API
- FTP as IIS relay
- mandatory Debian runtime
- mandatory Docker runtime
- Python/FastAPI as the new Collector technology
