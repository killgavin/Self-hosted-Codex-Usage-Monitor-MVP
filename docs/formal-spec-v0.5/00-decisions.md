# Codex Usage Monitor — Decisions

- Version: 0.4-draft
- Status: CURRENT DRAFT / HUMAN REVIEW REQUIRED
- Purpose: Single decision record for the current product direction.
- Current canonical set:
  1. `00-decisions.md`
  2. `01-product-requirements.md`
  3. `02-system-architecture.md`

## Status Definitions

- `Accepted`: Current design decision. Future work should follow it unless explicitly superseded.
- `Proposed`: Intended direction, but a required validation gate or Human decision is still open.
- `Superseded`: Historical direction retained only to prevent old context from being treated as current.

---

## DEC-001 — Mobile-first Client

**Status:** Accepted

**Decision:**  
Android App becomes the primary user interface. A Home Screen Widget is part of the product direction. Browser/Web Dashboard is no longer the primary product interface.

**Reason:**  
The primary usage need is to check Codex usage quickly from a phone, ideally without opening a browser.

**Alternatives:**
- Existing Web Dashboard
- PWA
- Browser-only remote access

**Consequences:**
- Mobile becomes the primary client.
- Existing Web UI may remain as legacy/local tooling, but is not the target UX.
- Mobile-specific efficiency and Widget constraints become first-class requirements.

**Revisit If:**  
A future requirement makes browser-only access the primary use case again.

---

## DEC-002 — Official Codex App Server Remains the Upstream Boundary

**Status:** Accepted

**Decision:**  
Collector obtains account/rate-limit data through official `codex app-server` using stdio JSON-RPC.

**Reason:**  
The existing project has already implemented and validated this boundary, and it provides the required Codex account/rate-limit data without depending on private ChatGPT endpoints.

**Alternatives:**
- Private `/backend-api/wham/*`
- Mobile directly calling OpenAI
- OpenAI Organization Usage API
- Parsing local credential/state files directly

**Consequences:**
- Collector requires an available Codex runtime.
- Codex protocol compatibility remains isolated behind the Collector's Codex boundary.
- The platform support of the final Collector is constrained by actual `codex app-server` support on that platform.

**Validation Gate:**  
Windows Native PoC must validate `initialize → account/read → account/rateLimits/read` before Windows is declared Tier 1.

**Validation Evidence:**  
Gate A: PASS — 2026-09-25. Native Windows successfully completed `codex app-server → initialize → account/read → account/rateLimits/read`, returned usable rate-limit state, and supported product-state normalization.  
Evidence: `04-validation-execution-record.md`, Gate A.

**Revisit If:**  
OpenAI introduces a stable public API that directly exposes the same ChatGPT/Codex rate-limit information needed by this product.

---

## DEC-003 — `current.json` Is the Client Contract

**Status:** Accepted

**Decision:**  
Collector publishes a normalized, versioned `current.json`; Mobile App/Widget consume that contract instead of consuming Codex protocol or the previous Monitor REST API.

**Reason:**  
The product only needs the latest usage snapshot. A small static JSON contract removes the need for a public Collector Web server or cloud database.

**Alternatives:**
- FastAPI REST API
- ASP.NET Core API on IIS
- Firebase / Supabase
- Direct Codex JSON-RPC from Mobile

**Consequences:**
- JSON schema must be versioned and forward-compatible.
- `current.json` contains current state, not full usage history.
- Exact schema can later be promoted to a separate formal contract document.

**Revisit If:**  
The product requires server-side commands, multi-user queries, history search, or bidirectional control that static JSON cannot support cleanly.

---

## DEC-004 — Existing Company IIS Is the Primary Mobile Distribution Point

**Status:** Accepted

**Decision:**  
Primary Mobile data path is `IIS static current.json → HTTPS → Android App/Widget`. IIS serves a static file only; it does not run the Collector or a new Usage API.

**Reason:**  
The company already operates an externally reachable IIS site. Reusing it avoids exposing the Collector and avoids an additional cloud service.

**Alternatives:**
- Cloudflare Tunnel to Collector
- Firebase / Firestore
- Supabase
- New IIS API
- Direct Mobile-to-Collector access

**Consequences:**
- IIS static-file MIME/cache/access behavior must be validated.
- Collector does not need a public inbound listener.
- Mobile only requires standard HTTPS retrieval.

**Validation Gate:**  
Verify external HTTPS access, JSON MIME handling, caching behavior, and access-control policy for the actual IIS path.

---

## DEC-005 — No Cloudflare Tunnel or Cloud Database in the Primary Path

**Status:** Accepted

**Decision:**  
Cloudflare Tunnel, Firebase, and Supabase are not part of the primary architecture.

**Reason:**  
The mobile requirement can be satisfied using the existing company IIS static hosting path with less operational complexity and no additional cloud dependency.

**Alternatives:**
- Cloudflare Tunnel
- Firebase / Firestore
- Supabase

**Consequences:**
- No cloud realtime database is required.
- Mobile freshness uses HTTPS retrieval rather than cloud realtime listeners.
- Push notification infrastructure is deferred.

**Revisit If:**  
IIS cannot safely expose the required JSON, or future realtime/push requirements justify introducing a managed backend.

---

## DEC-006 — IIS and FTP Are Independent Publish Targets

**Status:** Accepted

**Decision:**  
IIS Server and FTP Server are separate systems. The primary target is the IIS shared web directory. FTP / FTPS / SFTP may be independent optional publish targets; they are not an intermediate hop to IIS.

**Reason:**  
Current infrastructure confirms IIS and FTP are different computers/services, while the IIS web directory can be accessed through Windows file sharing.

**Alternatives:**
- Collector → FTP → sync/copy → IIS
- Mobile directly using FTP as the primary data source

**Consequences:**
- Primary mobile route stays short: Collector → IIS → HTTPS → Mobile.
- Optional FTP-family publishers can be added without changing the JSON contract.
- Mobile MVP does not require an FTP client.

**Revisit If:**  
Infrastructure policy later prevents direct publish to the IIS shared directory.

---

## DEC-007 — Filesystem Publisher Is the Primary Publisher Abstraction

**Status:** Accepted

**Decision:**  
Primary publisher writes through a filesystem-style target to the IIS shared directory. OS-specific network-share setup stays outside Collector business logic.

**Reason:**  
Windows can use a UNC/shared path; Linux can mount the same SMB/CIFS share and expose it as a normal filesystem path. This avoids hard-wiring SMB protocol logic into Collector Core.

**Alternatives:**
- Go SMB protocol client embedded in Collector
- SFTP/FTPS as mandatory primary transport
- New HTTP upload API

**Consequences:**
- Publish path is configuration-driven.
- Windows and Linux can share the same publish logic.
- Exact UNC/mount/credential setup remains environment-specific.

**Validation Gate:**  
Validate safe write/replace behavior on the actual IIS share from the intended runtime platform.

**Revisit If:**  
The target environment cannot present the IIS destination as a reliable writable filesystem path.

---

## DEC-008 — Semantic Deduplication Before Publish

**Status:** Accepted

**Decision:**  
Collector compares normalized product-relevant snapshot values against the last successfully published snapshot. Unchanged state is not published.

**Reason:**  
Codex may emit frequent events even when externally visible usage values do not change.

**Alternatives:**
- Publish every Codex event
- Publish every minute unconditionally

**Consequences:**
- Event frequency does not directly become file-write frequency.
- Comparison must ignore non-product metadata and event-arrival timestamps.
- Relevant fields include rate-limit values, reset times, plan/reached state, limit membership, and reset-credit state when present.

---

## DEC-009 — Publish Frequency Is Capped at Once per 60 Seconds

**Status:** Accepted

**Decision:**  
Even when semantic state changes repeatedly, Collector publishes at most one successful usage snapshot per 60 seconds and publishes the latest pending state.

**Reason:**  
Continuous Codex use could generate rapid changes. The phone does not need every intermediate state.

**Alternatives:**
- Publish every change immediately
- Fixed polling/upload every minute regardless of change

**Consequences:**
- Rapid changes are coalesced.
- Failed publish does not advance `LastPublishedSnapshot`.
- Retry only needs the latest pending snapshot; intermediate history is not replayed.

**Revisit If:**  
Future product requirements require sub-minute historical fidelity.

---

## DEC-010 — App Countdown Is Local; Widget Is Not a Per-second Surface

**Status:** Accepted

**Decision:**  
App countdown is calculated locally from `resetAt - deviceNow`. Per-second countdown updates, when shown, are foreground UI work only. Widget does not perform per-second refresh or network polling.

**Reason:**  
Countdown does not require new server data every second, and mobile background/widget execution is constrained and should remain low-cost.

**Alternatives:**
- Per-second network refresh
- Per-second Widget re-render
- Background second-level timer

**Consequences:**
- Network usage is independent of countdown display cadence.
- App stops high-frequency UI timers in background.
- Widget favors percentage, absolute reset time, last update, and stale state.

---

## DEC-011 — OpenAI/Codex Credentials Never Leave the Collector Host

**Status:** Accepted

**Decision:**  
OpenAI/Codex authentication material remains on the Collector host. `current.json`, IIS, Mobile App, Widget, and optional publish targets never receive these credentials.

**Reason:**  
The client only needs normalized usage state; distributing upstream credentials is unnecessary and increases risk.

**Alternatives:**
- Mobile authenticates directly to Codex/OpenAI
- Cloud/IIS stores upstream credentials

**Consequences:**
- Published JSON must be low-sensitivity and credential-free.
- Publisher credentials also remain Collector-side and are never embedded in Mobile.
- If JSON is anonymously readable, its content must be treated as potentially public.

---

## DEC-012 — Rate Limits Remain Generic and Forward-compatible

**Status:** Accepted

**Decision:**  
System must not hard-code only 5-hour and Weekly windows. Unknown/new limits must remain representable and must not crash Collector or Mobile.

**Reason:**  
Codex rate-limit shape can evolve, and the existing project already adopted a generic limit model.

**Alternatives:**
- Fixed two-card schema for 5H + Weekly only

**Consequences:**
- Snapshot uses a generic limits collection.
- Friendly labels may be presentation logic, not schema identity.
- Missing/unknown optional data must fail safely.

---

## DEC-013 — Collector Becomes Cross-platform

**Status:** Accepted

**Decision:**  
`Debian Collector` is replaced by a cross-platform Collector with one source code base and target-specific builds.

**Reason:**  
Debian should not be an architectural requirement. Future maintainers are more Windows-oriented, while Linux should remain supported.

**Alternatives:**
- Debian-only Collector
- Separate Windows and Linux implementations

**Consequences:**
- OS-specific behavior must be isolated.
- Executable path, service hosting, filesystem path, and credentials are configuration/environment concerns.
- Linux becomes one deployment platform rather than the architecture itself.

---

## DEC-014 — Collector Language Is Go

**Status:** Accepted

**Decision:**  
The new Collector is implemented in Go.

**Reason:**  
Collector is a small long-running I/O-oriented program requiring process control, stdio, JSON/JSON-RPC, timers, file/network I/O, concurrency, and simple native deployment. Go fits this profile and produces native target binaries without a separately managed runtime.

**Alternatives:**
- Python
- C#/.NET
- Rust
- Java
- Node.js

**Consequences:**
- Existing Python implementation is a reference for behavior/protocol mapping, not the target Collector runtime.
- Collector and Mobile may use different languages because `current.json` is their boundary.
- Go becomes a new maintenance skill for the project.

**Revisit If:**  
The Windows Codex integration or required publisher/runtime libraries prove materially less reliable than the alternatives.

---

## DEC-015 — Native Build per Target Platform

**Status:** Accepted

**Decision:**  
Distribution uses one source tree with separate native builds per target OS/architecture; one universal executable is not required.

**Reason:**  
This is the normal cross-platform model for Go and keeps deployment simple.

**Alternatives:**
- Shared runtime installation
- One OS-specific Collector only

**Consequences:**
- Release artifacts are platform-specific.
- Build/release validation must cover each supported target.

---

## DEC-016 — Windows x64 First, Linux x64 Second

**Status:** Accepted

**Decision:**  
Platform tiers:
- Windows x64: Tier 1; Native Codex integration validated by Gate A.
- Linux x64: Tier 2 target.

**Reason:**  
Primary maintainers are more familiar with Windows, while Linux remains valuable and technically feasible for the Collector.

**Alternatives:**
- Linux-first
- Equal support from day one
- Windows-only

**Consequences:**
- Initial runtime validation focuses on Native Windows.
- Linux support remains a design constraint, not an afterthought.

**Validation Gate:**  
Native Windows must successfully run:
`codex app-server → initialize → account/read → account/rateLimits/read`.

**Validation Evidence:**  
Gate A: PASS — 2026-09-25. Native Windows successfully completed the validation sequence, obtained usable rate-limit state, and supported product-state normalization.  
Evidence: `04-validation-execution-record.md`, Gate A.

**Revisit If:**  
Native Windows Codex App Server cannot be used reliably. WSL may be considered only as fallback, not the initial architecture.

---

## DEC-017 — Current Canonical Context Is Reduced to Three Core Documents

**Status:** Accepted

**Decision:**  
For the new product direction, the current canonical context is limited to:
`00-decisions.md`, `01-product-requirements.md`, and `02-system-architecture.md`.

**Reason:**  
The repository's previous Web MVP documents contain valid implementation history but now conflict with the Mobile-first / static-JSON / cross-platform direction. Keeping all of them canonical would pollute future Agent context.

**Alternatives:**
- Keep old specification/design/test/deployment documents canonical
- Create separate branch/mainline history files

**Consequences:**
- Decision history is compressed into this file.
- Current requirements and architecture contain no chat-history narrative.
- Formal `current.json` contract and new Implementation Plan are created only when needed.
- Previous Web MVP test/deployment/status documents remain legacy evidence until an explicit archive/retirement action is approved.

---

# Superseded Decisions

## DEC-901 — Web-first Server + Browser Is the Primary Product

**Status:** Superseded  
**Superseded By:** DEC-001, DEC-003, DEC-004

The existing Web MVP remains historical implementation/evidence, but it is not the current target product architecture.

## DEC-902 — Debian/Python/FastAPI Is the Required Collector Runtime

**Status:** Superseded  
**Superseded By:** DEC-013, DEC-014, DEC-016

Debian/Linux is no longer mandatory; Python/FastAPI is not the target Collector implementation.

## DEC-903 — Cloudflare Tunnel Is the Main Remote-Mobile Access Mechanism

**Status:** Superseded  
**Superseded By:** DEC-004, DEC-005

The current primary path uses static JSON on existing IIS.

## DEC-904 — Firebase/Supabase Is the Mobile Data Layer

**Status:** Superseded  
**Superseded By:** DEC-003, DEC-004, DEC-005

No cloud database is required for the current MVP direction.

## DEC-905 — FTP/SFTP/FTPS Is an Intermediate Path into IIS

**Status:** Superseded  
**Superseded By:** DEC-006, DEC-007

FTP-family services are independent optional targets, not the IIS relay.

## DEC-906 — Android Consumes the Monitor REST API

**Status:** Superseded  
**Superseded By:** DEC-003, DEC-004

Android consumes versioned static JSON over HTTPS.

## DEC-907 — Docker/Debian Deployment Is a Mandatory Product Requirement

**Status:** Superseded  
**Superseded By:** DEC-013, DEC-015, DEC-016

The target Collector is a native cross-platform executable. OS service hosting is platform-specific.
