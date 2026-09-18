# Self-hosted Codex Usage Monitor — Design

- Version: 0.1
- Status: READY
- Source of Truth: `specification.md`

## Purpose and Boundaries

定義技術邊界與責任分工。功能需求以 specification.md 為最高來源。

Dependency direction: Protocol → Domain → Application → API → Client。Domain 不依賴 FastAPI、subprocess、JSON-RPC、Codex、Web 或 Android。

## Technology

Python 3.12+、FastAPI、Pydantic、pytest、asyncio、uvicorn；`codex app-server` subprocess；stdin/stdout JSON Lines JSON-RPC。

## Project Structure

```text
server/app/
├─ main.py
├─ config.py
├─ api/
├─ codex/
│  ├─ adapter.py
│  ├─ process.py
│  ├─ transport.py
│  ├─ protocol.py
│  └─ exceptions.py
├─ models/
├─ services/
└─ security/

server/tests/
├─ unit/
├─ integration/
└─ fixtures/
```

## Codex Process

process.py 只負責 start/stop/stdin/stdout/process state/cleanup。Failure 至少區分 ExecutableNotFound、ProcessStartFailed、ProcessExited、ProcessCommunicationFailed。

## JSON-RPC Transport

transport.py 負責 serialization、parsing、request id、pending correlation、stdout loop、notification dispatch、timeout。必須支援 concurrent requests；notification 可穿插 response。

## Protocol

protocol.py 定義 Codex boundary DTO；不得直接回 REST。Forward-compatible：known parse、unknown ignore/preserve、missing optional→None、unknown enum 儘量保留 raw。

## CodexAppServerAdapter

唯一允許直接使用 Codex method name 的模組。介面：initialize/read_account/start_login/cancel_login/logout/read_rate_limits；Phase 2 才 read_usage。State: STOPPED/STARTING/INITIALIZING/READY/FAILED。

## Domain

AccountStatus(authenticated, auth_mode, plan_type)。
RateLimitWindow(used_percent, remaining_percent, window_duration_minutes, reset_at)。
RateLimit(id, name, primary, secondary, reached_type, raw_metadata?)。
ResetCredits(available_count, credits)。

Domain 不含 credential/JSON-RPC detail。

## Services

AccountService、AuthService、RateLimitService。Service 不知道 subprocess、JSON-RPC、FastAPI Request 或 HTML。

## Mapping

```text
Codex DTO → Mapper → Domain → Application Service → REST Schema
```

Friendly labels 屬 Presentation：300→5 Hours、10080→Weekly，否則 upstream name，再 fallback limitId。

## Cache

MVP in-memory TTL 60 秒；不得引入 Redis/DB。

## REST

Route 只做 HTTP parsing、server API token authentication、service call、serialization、error mapping。不得直接使用 Transport。Client token 由 CODEX_MONITOR_API_TOKEN 提供。

## Errors / Logging

Internal exception 映射為穩定 API error。不得回 client traceback、credential path、raw auth payload。Log redaction 至少處理 Authorization、Bearer、access_token、refresh_token、api_token、cookie。

## Web

Server-hosted UI，只呼叫 REST。MVP 優先簡單 HTML/CSS/JS。Dashboard 使用 ConnectionStatus、AccountSummary、RateLimitList、Generic RateLimitCard、ResetCreditSummary、LastUpdated。Server UTC，Browser local time。

## Login UI

未登入顯示 login action；device code 顯示 verification URL、user code、state、cancel；完成後重新載入 account/rates。

## Docker

Container 必須能執行 Usage Monitor 與 Codex App Server。Credential/config persistent。實際 credential path、Codex CLI installation/version、UID permissions 必須 runtime verify。

## Configuration

CODEX_MONITOR_HOST、CODEX_MONITOR_PORT、CODEX_MONITOR_API_TOKEN、CODEX_EXECUTABLE、CACHE_TTL_SECONDS、LOG_LEVEL。預設 127.0.0.1、8080、60、INFO；Docker/LAN 才明確 0.0.0.0。

## Health / Degraded

Codex 缺失時 HTTP Server 優先保持 available 並進入 DEGRADED。

## Android Boundary

Phase 3 only；Android 只呼叫 Usage Monitor REST API，不持有 OpenAI credential、不啟動 Codex、不實作 OpenAI OAuth。

## Testing

Unit: Domain/mapping/redaction/cache。
Integration: process/transport/initialize/adapter/REST auth。
E2E: Docker/Web/Login/Rate-limit/Persistence；real-account manual/opt-in。

## Compatibility

Upstream compatibility 集中 codex/。Protocol 變動正常只影響 DTO/Adapter/Mapper/tests。

## Invariants

Codex protocol only in codex/；Domain unaware of JSON-RPC；REST Route no direct Transport；Web/Android no Codex/OpenAI；credential stays server；unknown quota safe；generic limits model；core mapping unit-testable；MVP no experimental WebSocket.

## Escalation

Protocol mismatch、核心 Domain、安全 boundary、服務拆分、DB/central service、REST version contract 或重大 security trade-off → HUMAN_REQUIRED / Sol。
