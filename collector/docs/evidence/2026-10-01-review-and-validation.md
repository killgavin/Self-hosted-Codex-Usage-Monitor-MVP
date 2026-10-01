# Windows V1 Review and Validation Record

Date: 2026-10-01 (Asia/Taipei). Scope: collector/, Collector CI, and V1 documentation. V1 NOT COMPLETE: real Google OAuth, fixed-file publishing, and public HTTPS download remain blocked by missing external setup.

## Specification and scope

The user supplied the formal V1 Specification 1.0 from an existing local attachment. It is preserved without content changes as ../01-codex-usage-monitor-v1-specification.md. SHA256 of both the supplied file and repository copy:

D74023953027C59855692570137425376A2641798A093890795C20F6EE0150F6

The specification explicitly excludes stale thresholds, status.json, heartbeat, mobile clients, Linux acceptance, additional publishers, and key-management expansion. No legacy Python, Docker, or Dashboard files were changed.

SDD classification: S2 for the integrated validation scope. The current user explicitly authorized inspection, bounded fixes, tests, commit, push, and CI verification according to the formal specification. No additional implementation gate was inferred.

## Initial Git state

- main at 7604831; tracked files clean.
- origin: https://github.com/killgavin/Self-hosted-Codex-Usage-Monitor-MVP.git.
- Existing untracked data: .codex-remote-attachments/, docs/formal-spec-v0.5/, docs/spec/.
- Fetched origin and switched to the requested tracking branch feat/codex-usage-monitor-v1 at c356ce5cc2f462fca9ed94f639f9e0bf0eb6ac6a.
- Preserved all pre-existing untracked data. No reset, stash, cleanup, merge, or push to main.

## Review findings and corrections

| Finding | Resulting behavior / regression evidence |
|---|---|
| All original Go sources failed gofmt | Formatted all Collector Go files; retained mandatory CI format check |
| main called missing LoadAESKey | Shared strict 32-hex / 16-byte decoder; config_test.go protects missing, malformed, short, long and valid uppercase hex |
| PowerShell scripts, env example and gitignore contained literal backslash-n | Restored real newlines; scripts check native exit codes and preserve environment; git check-ignore confirms token and exe exclusion |
| go.mod declared 1.23 although existing oauth2 v0.31.0 requires 1.24 | go mod tidy updated minimum Go version and produced go.sum; no new large dependency |
| Windows Git checkout reconverted formatted Go to CRLF | collector/.gitattributes enforces LF. Reproduced failure on a CRLF fixture; git checkout-index with core.autocrlf=true and the new attributes passed gofmt |
| Go map iteration changed output ordering | Output sorted by normalized Limit ID; 50 repeated marshals of the same multiple-limit fixture are byte-identical |
| 100 - float64 produced decimal artifacts | Standard-library math/big exact decimal subtraction; boundary and high-precision tests preserve usedPercent and clamp only remainingPercent |
| requiresOpenaiAuth was treated as logged-out | Account presence and rate RPC determine authenticated state, matching formal §7.2 and the existing Python mapper; true provider flag is accepted with valid account |
| Legacy missing identity became empty string | Nullable identity matches the existing verified domain contract; no guessed ID |
| Malformed source fields silently became null or count=0 | Present malformed windows, timestamps or credit summaries fail the round; optional absent fields remain null |
| JSON-RPC used float64 and unsafe process lifecycle | UseNumber preserves decimal precision; request serialization, ID matching, notification filtering, scanner error reporting, timeout, stop channel, cmd.Wait and idempotent Close |
| Untrusted stderr / RPC errors could enter log | stderr is drained to io.Discard; arbitrary RPC message bodies are not logged; RPC code is retained |
| OAuth used fixed state / fixed port without validation | New crypto-random state each flow, exact callback validation, replay rejection, OS-assigned loopback port, package-supported PKCE S256 |
| OAuth callback could block on duplicate responses or leak server | Buffered nonblocking completion, one callback acceptance, server close on every return, bounded auth context |
| Token errors silently triggered authorization; saves could truncate existing file | Corrupt tokens fail explicitly; write/sync/close a local temp file before replacement; refreshed token and refresh token persist |
| Publisher URL accepted arbitrary ID text | Validate fixed File ID syntax; only one media PATCH with complete authenticated binary; no filename search, create, delete or redirect |
| Client HTTPS check used a string prefix | Standard URL parser, HTTPS host validation, reject HTTP downgrade redirects, normal TLS validation |
| Client only checked a few required fields | Validate fixed schema at root/account/limit/window/reset-credit levels, preserving nullable optionals; reject malformed timestamps and unauthenticated payload |
| Failure semantics had no orchestration coverage | Inject only stage boundaries in tests; every earlier failure stops before publisher; successful pipeline publishes one complete valid binary |

Current live source includes workspaceRouting, ordinaryUsageAllowed, rateLimitUpsell and additional bucket metadata. The redacted response preserves this source topology. The official V1 normalized contract remains unchanged: no raw routing/account identifiers are added to published JSON. ResetCredit.resetType remains source-only, consistent with the existing verified Python mapper.

## Repeatable verification

Run from collector/:

```powershell
gofmt -l .
go vet ./...
go test -v -count=1 ./...
.\scripts\build-win-x64.ps1
```

Local final results: all PASS. Windows OS, architecture, exact Go/Codex versions and executable SHA256 are in 2026-10-01-windows-validation.json. Go was downloaded from the official go.dev release archive and verified against the official SHA256, using a temporary portable toolchain.

Automatic tests use synthetic keys/tokens only. No production AES key, Google client secret, or OAuth token is committed.

### Behavioral tests

- Crypto: TestEncryptDecryptAndIntegrity, TestBinaryValidation, TestTruncatedBinaryAndInvalidKeys.
- Normalize: TestNormalizeVerifiedContract, TestNormalizeRejectsLoggedOut, TestNormalizeOrderingAndOptionalFields, TestPercentageBoundaries, TestResetCreditNullEmptyPopulated, TestNormalizeMalformedSourceFails.
- Client: TestHTTPSURLValidation, TestClientHTTPSAndRejections, TestClientSchemaRejectsMissingAndMalformedFields, TestClientRefusesHTTPRedirectAndOversizedBinary.
- OAuth / publisher: TestOAuthStateAndCallbacks, TestOAuthDesktopRequestContract, TestTokenRefreshAndFixedFileUpdate, TestPublisherRejectsInvalidInputAndCorruptToken, TestTokenRefreshFailureDoesNotUpload.
- JSON-RPC process: TestCodexDispatcherSequenceNumbersAndClose, TestCodexDispatcherFailures, TestCodexCloseWithUnconsumedResponses.
- Pipeline: TestPipelineFailureDoesNotPublish, TestPipelinePublishesOneCompleteAuthenticatedPackage.
- Configuration: TestLoadAESKey, TestLoadConfig.

The local transport test performs two PATCH requests to the same fixed fixture ID, then a failed PATCH and checks prior fixture content. It also verifies one refresh request, persistence and reuse of the refreshed token. This is not a claim of actual Google service authorization or remote content preservation.

TLS HTTPS tests use a local test certificate trusted only by the test client. Production TLS verification remains enabled. CLI/public Google HTTPS acceptance requires the real published binary.

A coverage diagnostic reported 74.4% of statements for ordinary tests; no acceptance threshold is derived from this number. Real OAuth and live Codex tests are explicitly opt-in.

### Windows / Codex live

```powershell
$env:CODEX_MONITOR_LIVE_GATE = "1"
$env:CODEX_MONITOR_LIVE_EVIDENCE = "docs/evidence/local/codex-live.json"
go test -v -count=1 -run '^TestLiveCodexGate$' .
$env:CODEX_MONITOR_BINARY_GATE = "1"
go test -v -count=1 -run '^TestBuiltWindowsBinary$' .
```

PASS:
- Official process startup and initialize response.
- initialized notification sent successfully.
- account/read and account/rateLimits/read returned actual results.
- Authenticated ChatGPT account and source plan normalized.
- Actual keyed limits, nullable windows and reset credits normalized without hardcoded live values.
- Live payload JSON → random-key AES package → decrypt / Client schema validation.
- Actual built executable recognized as AMD64 PE and executed, rejecting HTTP with nonzero exit.

Current requiresOpenaiAuth=true is recorded in 2026-10-01-codex-live.json. Official documentation defines it as provider configuration, not authenticated state; formal §7.2 identifies account=null / rate RPC failure as the logged-out condition. The user-prompt false expectation was not substituted for the higher-priority formal contract.

The restricted tool identity initially reported "Not logged in". The actual Windows user execution reported "Logged in using ChatGPT" and successfully completed live RPCs. This environment difference did not require credential migration or parsing.

Codex changed from 0.159.2 during initial inspection to 0.159.3 during the final checks. The live test now records the executable version and the latest successful response.

## Change-impact review

Documentation: 必須修改. README previously omitted operational constraints and could not represent verified vs blocked gates; the acceptance list lacked actual AC mapping. Both were synchronized to the supplied formal specification and current evidence.

Tests: 必須修改. Reproducible formatting/build defects, numerical precision, account state, malformed-source failures, HTTPS validation, callback state and process lifecycle now have behavioral regression tests.

Concrete remaining verification gaps:
- Actual Desktop OAuth code exchange and Google token refresh.
- drive.file authorization for the manually created target.
- Original / first / second update File ID equality.
- Actual remote old-file content after an upload error.
- Public HTTPS availability of the latest binary, using the same AES key.

Sol consultation: 不需要. Official protocol documentation, existing contract, behavioral fixtures and current live evidence establish the bounded changes without an unresolved technical blocker.

## External gate boundary

Presence-only checks of Process, User and Machine environment settings found no CODEX_MONITOR_GOOGLE_CLIENT_ID, CODEX_MONITOR_GOOGLE_CLIENT_SECRET or CODEX_MONITOR_DRIVE_FILE_ID. No default token / credential file exists in collector/. No external Drive write has been attempted.

Next required user action: prepare the Google OAuth Desktop App credentials locally. The agent should read only the supplied local credential path or retrieve explicitly configured user environment variables without printing secrets. Complete this gate before requesting the next File ID / sharing action.

OAuth credentials, Drive file creation, sharing permissions and the production download URL must not be inferred from the synthetic transport tests.

## Official references

- [Codex App Server contract](https://learn.chatgpt.com/docs/app-server): JSONL handshake and provider auth flag semantics.
- [Google Desktop OAuth](https://developers.google.com/identity/protocols/oauth2/native-app): random available loopback port, state and PKCE.
- [Google files.update](https://developers.google.com/workspace/drive/api/reference/rest/v3/files/update): fixed fileId media PATCH.
- [Google Drive scopes](https://developers.google.com/workspace/drive/api/guides/api-specific-auth): per-file app authorization.

## CI evidence

The initial remote run 36744513188 failed formatting before vet/tests/build. After the first push, run 36809226033 reproduced the Windows CRLF checkout issue and also stopped at formatting. The LF attribute fix was locally validated using a fresh index checkout with core.autocrlf=true and pushed as bf63c0a.

Collector CI run [36809477057](https://github.com/killgavin/Self-hosted-Codex-Usage-Monitor-MVP/actions/runs/36809477057) on commit bf63c0a455086b74c30cd7573d47b6fbdd6cfe96 completed with success. Checkout, setup-go, module download, gofmt, vet, tests, Windows AMD64 build and artifact upload each returned success. The structured evidence is 2026-10-01-collector-ci.json. Documentation is committed after this observation; the final documentation HEAD will also be checked before stopping at the OAuth human gate.
