# Codex Usage Monitor — Product Requirements

- Version: 0.4-draft
- Status: CURRENT DRAFT / HUMAN REVIEW REQUIRED
- Source of Decisions: `00-decisions.md`
- Purpose: Describe only what the current system must do.

## 1. Product Goal

Provide a Mobile-first Codex usage monitor that lets the user quickly inspect current Codex rate-limit state from Android without exposing the Collector to the public Internet and without placing OpenAI/Codex credentials on the phone.

Primary user surfaces:

- Android App
- Android Home Screen Widget

The system publishes only the latest normalized usage snapshot needed by those clients.

## 2. Current End-to-end Requirement

```text
Codex App Server
    ↓
Collector
    ↓
Normalize / Semantic Deduplication / Publish Throttle
    ↓
current.json
    ↓
Company IIS static web directory
    ↓
HTTPS
    ↓
Android App / Widget
```

FTP / FTPS / SFTP may exist as independent optional publish destinations, but are not required for the primary Mobile path.

## 3. Collector Requirements

### PR-001 — Platform portability

Collector must use one shared source code base and support target-specific native builds.

Target priority:

- Windows x64: validated Tier 1 primary runtime for Native Codex integration (Gate A PASS — 2026-09-25)
- Linux x64: Tier 2 target and supported secondary runtime
- Linux ARM64 / macOS: future optional targets

### PR-002 — Codex integration

Collector must:

- start/manage configured `codex app-server`
- communicate through stdio JSON-RPC
- initialize the protocol
- read account state required by the product
- read rate-limit state
- safely handle rate-limit update events/notifications when available

Collector must not depend on private `/backend-api/wham/*` endpoints or direct parsing of Codex credential files as the formal integration contract.

### PR-003 — Generic rate-limit model

System must not assume only 5-hour and Weekly limits.

It must safely preserve and expose:

- limit identity/name when available
- primary window when available
- secondary window when available
- used percentage
- reset time
- window duration
- reached state
- reset-credit state when available

Unknown/new optional fields or limits must not crash Collector or Mobile.

### PR-004 — Normalized current snapshot

Collector must produce a versioned `current.json` containing only Mobile-relevant normalized state.

Minimum logical content:

```text
schemaVersion
snapshotUpdatedAt
account.planType

limits[]
  id
  name
  primary?
    usedPercent
    resetAt
    windowDurationMinutes
  secondary?
    usedPercent
    resetAt
    windowDurationMinutes
  reachedType?

resetCredits? 
```

Exact schema becomes a separate formal contract only when implementation planning requires it.

### PR-005 — Semantic deduplication

Collector must compare normalized product-relevant values against the last successfully published snapshot.

If no relevant state changed:

```text
Do Not Publish
```

Event arrival time, JSON property order, or unused upstream metadata must not alone trigger a publish.

### PR-006 — Publish throttling

Successful snapshot publication must be capped at:

```text
Maximum 1 publish / 60 seconds
```

If multiple relevant changes occur within the interval:

- retain only the latest pending state
- publish the latest state when permitted
- do not replay intermediate states

A failed publish must not be treated as successful.

### PR-007 — Safe file replacement

Publishing must not expose a partially written `current.json`.

Required behavior:

```text
write temporary file
→ flush/close
→ replace/rename to current.json
```

Exact safe-replace semantics must be validated on the real target share/filesystem.

### PR-008 — Primary publish destination

Primary destination is the IIS web directory accessible to the Collector as a filesystem-style path.

Examples of environment presentation may include:

- Windows UNC/shared path
- Linux-mounted SMB/CIFS path

The application contract must not require IIS to run a new API.

### PR-009 — Optional independent publishers

FTP / FTPS / SFTP may be supported as independent optional publish destinations.

They are not required for the primary Android/IIS path.

## 4. IIS / Distribution Requirements

### PR-010 — Static hosting only

IIS must serve `current.json` over HTTPS.

IIS does not need to:

- run the Collector
- query Codex
- hold OpenAI credentials
- run a new Usage API
- relay requests to the Collector

### PR-011 — HTTP behavior

The IIS path must be validated for:

- external HTTPS reachability
- valid certificate
- `.json` MIME handling
- suitable `Cache-Control`
- `ETag` and/or `Last-Modified` behavior where available
- access-control policy

Long-lived caching must not prevent clients from seeing updated snapshots.

## 5. Android App Requirements

### PR-012 — HTTPS snapshot retrieval

App must read `current.json` through HTTPS.

App must not:

- call Codex/OpenAI directly
- require access to Collector host
- contain Collector publish credentials
- require FTP access for the MVP

### PR-013 — Local cache

App must retain the last valid snapshot locally.

Uses:

- immediate display on launch
- offline/temporary network-failure display
- Widget data source
- fallback when a newly downloaded JSON is invalid

Invalid JSON must not overwrite the last valid cached snapshot.

### PR-014 — Refresh behavior

App must refresh on launch/resume and support manual refresh.

Periodic foreground refresh may be added, but the exact interval remains a Human Gate.

The App must not perform per-second network polling.

### PR-015 — Local reset countdown

Reset countdown is calculated locally:

```text
remaining = resetAt - currentDeviceTime
```

No countdown tick may require network I/O.

When high-frequency countdown UI is shown, it runs only while the App is foreground.

## 6. Widget Requirements

### PR-016 — Summary surface

Widget must provide a concise view of:

- primary usage/remaining percentage
- secondary usage/remaining percentage when available
- reset absolute time
- last snapshot update time
- stale indication when applicable

### PR-017 — No per-second Widget polling

Widget must not perform per-second network requests or require continuous second-level background execution.

Widget should consume the App's local cached snapshot whenever practical.

The exact MVP phase for Widget delivery remains a Human Gate.

## 7. Security Requirements

### PR-018 — Credential isolation

OpenAI/Codex credentials must remain on the Collector host.

They must not appear in:

- `current.json`
- IIS static content
- Android App
- Widget
- logs
- analytics
- optional publish destinations

### PR-019 — Publish credential isolation

Credentials used to write to IIS share or optional FTP-family targets remain Collector-side.

Mobile is read-only with respect to published usage state.

### PR-020 — Public JSON assumption

If `current.json` can be read anonymously, its contents must be treated as potentially public.

It must not include:

- OpenAI/Codex credentials
- publish credentials
- API/session tokens
- internal passwords
- sensitive account identifiers
- unnecessary internal host/network details

If anonymous read is unacceptable, existing IIS access control must be used or the distribution design must be revisited.

## 8. Reliability Requirements

### PR-021 — Failure preservation

If publish fails:

- existing valid `current.json` remains usable
- latest pending state is retained for retry
- failed state is not recorded as successfully published

### PR-022 — Stale data handling

Mobile must be able to show that displayed data is the last known snapshot and may be stale.

The exact stale threshold and whether a separate `status.json`/heartbeat is required remain Human Gates.

## 9. Out of Scope for the Current MVP Direction

- Public Collector Web server for Mobile access
- Cloudflare Tunnel as the primary access path
- Firebase / Supabase
- New IIS Usage API
- Direct Mobile-to-Codex integration
- Direct Mobile-to-Collector integration
- Mandatory Mobile FTP client
- Multi-user SaaS
- Usage-history database
- Remote Codex command execution
- iOS implementation
- Push notification infrastructure
- Formal new Implementation Plan in this documentation pass

## 10. Validation Status and Current Human Gates

**Completed validation:** Gate A PASS — 2026-09-25. Windows x64 Native Codex integration, rate-limit state acquisition, and product-state normalization were validated. Windows x64 is the Tier 1 target; Linux x64 remains the Tier 2 target. Evidence: `04-validation-execution-record.md`, Gate A. This result does not establish Gate B, Gate C, or full product production readiness.

**Open Human Gates:**

1. **IIS filesystem target**
   - Confirm actual shared path, permissions, credential model, and safe replace behavior.

2. **IIS HTTPS/static-file behavior**
   - Confirm external URL, MIME type, caching/validation headers, and access-control policy.

3. **Android technology**
   - `.NET MAUI` vs `Kotlin` is not yet decided.

4. **Widget phase**
   - Product direction includes Widget; whether it ships in the first implementation phase remains undecided.

5. **Mobile freshness policy**
   - Foreground auto-refresh interval and stale threshold remain undecided.

6. **Collector liveness**
   - Whether `current.json` alone is sufficient or a separate `status.json`/heartbeat is needed remains undecided.

7. **Optional FTP-family publisher**
   - Need and supported protocol(s) remain undecided.
