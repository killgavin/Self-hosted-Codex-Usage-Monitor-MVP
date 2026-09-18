# Self-hosted Codex Usage Monitor — SDD Specification

- Version: 0.2
- Status: READY FOR IMPLEMENTATION PLANNING
- Primary Coding Model: GPT-5.6 Luna
- Escalation Model: GPT-5.6 Sol
- Project Type: Open Source / Self-hosted
- Primary Runtime: Server + Web
- Extended Clients: PWA + Android
- Upstream Integration: OpenAI Codex App Server

## 1. Goal

建立 Self-hosted Codex usage quota monitor。使用者透過官方 ChatGPT/Codex 登入，在 Browser 查看 rate limits、remaining percentage、reset time；後續可擴充 PWA 與 Android，而不需要把 OpenAI credentials 交給第三方中央服務。

## 2. Architecture

```text
OpenAI
  ↑
Codex App Server
  ↑ stdio JSON-RPC
Usage Monitor Server
  ├─ REST API
  └─ Web UI
       ↑
     Browser

Later:
Usage Monitor Server
  ├─ PWA
  └─ Android App
       ├─ Widget
       └─ Notification
```

## 3. Non-negotiable Invariants

- INV-001: OpenAI Credential 只存在 Server / Codex App Server；不得出現在 Browser、Android、REST response、log 或 analytics。
- INV-002: Browser / Android 不直接呼叫 OpenAI，只呼叫 Usage Monitor REST API。
- INV-003: 正式整合使用官方 Codex App Server：`account/read`、`account/login/start`、`account/login/cancel`、`account/logout`、`account/rateLimits/read`；Phase 2 才使用 `account/usage/read`。不得以 `/backend-api/wham/*` 作正式依賴。
- INV-004: Codex protocol 必須封裝在 `CodexAppServerAdapter`；business logic 不直接處理 JSON-RPC。
- INV-005: 不假設只有 5H / Weekly；未知 limit 必須安全保留、normalize、expose。
- INV-006: Reset credit 在 MVP 為 read-only。
- INV-007: MVP transport 為 stdio JSON-RPC；WebSocket 不列為必要條件。

## 4. Luna Execution Rules

一次只做一個 bounded task；一般控制 1–3 個主要檔案；不得 speculative refactor；不得猜 upstream API；unknown data 必須安全處理；build 不等於完成；每個 Task 必須包含 Goal、Allowed Files、Required Behavior、Forbidden Changes、Acceptance Criteria、Validation。

Protocol mismatch 時停止並輸出 `STATUS: HUMAN_REQUIRED` 與具體 evidence。

## 5. Scope

### Phase 1 — MVP
Server、Codex App Server integration、ChatGPT authentication、rate-limit retrieval、REST API、Web Dashboard、Docker、安全性、自動測試。

### Phase 2
`account/usage/read`、PWA、cache improvement、usage history、threshold/reset notifications。

### Phase 3
Android App、Widget、persistent notification、background refresh、threshold notification。

## 6. Out of Scope — MVP

ChatGPT conversation management、Codex coding execution、OpenAI API billing dashboard、multi-tenant SaaS、central credential storage、Android root/system status-bar modification、private `/wham` fallback、custom OAuth、reset-credit consumption。

## 7. Server Technology

Python + FastAPI + Pydantic + pytest。Codex App Server 由 subprocess 啟動。

```text
FastAPI → Application Services → CodexAppServerAdapter → codex app-server
```

REST Router 不得直接呼叫 subprocess。

## 8. Domain Model

AccountStatus: authenticated, authMode, planType.

RateLimitWindow: usedPercent, remainingPercent, windowDurationMinutes, resetAt.

`remainingPercent = clamp(100 - usedPercent, 0, 100)`

RateLimit: id, name, primary, secondary, reachedType.

ResetCredits: availableCount, credits.

Domain model 不直接暴露 raw app-server JSON。

## 9. Authentication

使用 `account/read`、`account/login/start`、`account/login/cancel`、`account/logout`。支援 `chatgpt` 與 `chatgptDeviceCode`。Device-code UI 顯示 verification URL、user code、login state。不得自行解析或保存 OpenAI refresh token；lifecycle 交由 Codex App Server。

## 10. Rate Limits

使用 `account/rateLimits/read`。支援 limitId、limitName、primary、secondary、usedPercent、windowDurationMins、resetsAt、planType、rateLimitReachedType；optional field 可缺少。remainingPercent clamp 至 0..100。不得 hard-code primary=5H / secondary=Weekly。300 分鐘可顯示 5 Hours、10080 分鐘可顯示 Weekly；其他優先 name，再 fallback limitId。Server domain 使用 UTC / ISO-8601。

## 11. Reset Credits

支援 availableCount；detail 若存在保留 id/status/grantedAt/expiresAt/title/description。`{availableCount:2, credits:null}` 必須維持 count=2。

## 12. REST API

Base `/api/v1`：
- GET `/api/v1/status`
- GET `/api/v1/account`
- GET `/api/v1/rate-limits`
- Phase 2: GET `/api/v1/usage`

Login HTTP contract 建議最小化為 login/status/cancel/logout。若實作需要改變 canonical API，必須 HUMAN_REQUIRED。

## 13. REST Authentication

External client 使用 `Authorization: Bearer <server-api-token>`，與 OpenAI token 完全分離。

## 14. Web Dashboard

顯示 login status、plan、rate-limit name、used%、remaining%、progress bar、reset time/countdown、reset credit count、last updated。最低 360px，不應需要水平捲動。所有 limits 使用 generic component。

## 15. Cache

MVP 可使用 in-memory TTL cache，預設 60 秒；不得改變 Domain data。

## 16. Error Contract

穩定格式 `{"error":{"code":"...","message":"..."}}`。至少考慮 CODEX_NOT_INSTALLED、CODEX_START_FAILED、CODEX_NOT_AUTHENTICATED、CODEX_LOGIN_PENDING、CODEX_PROTOCOL_ERROR、UPSTREAM_UNAVAILABLE、INVALID_SERVER_TOKEN、INTERNAL_ERROR。不得回傳 credential、raw auth header、stack trace。

## 17. Security

Credential stays server-side。Redact Authorization/Bearer/API token/Cookie/OpenAI credential。Default listen `127.0.0.1`；LAN 才明確使用 `0.0.0.0`。Internet exposure 文件只建議 HTTPS/Tailscale/reverse proxy。Browser 不應把長效 bearer token 放 LocalStorage。

## 18. Docker

MVP 提供 Dockerfile + docker-compose.yml，目標 `docker compose up -d`。Credential/config 必須可持久化。正式實作前需驗證 Codex CLI image 安裝方式、版本策略、credential path、UID/permissions，不得猜測。

## 19. Definition of Done

每個 Stage 都必須具備 Implementation + Tests + Validation + Documentation Update。Build pass 或 UI 看起來正常不足以宣告 DONE。

## 20. Stages

0 Repository Foundation; 1 Codex Process/Transport; 2 Protocol Initialization; 3 Account Read; 4 ChatGPT Login; 5 Rate Limit Mapping; 6 REST API; 7 Web Dashboard; 8 Security Hardening; 9 Docker; 10 Final MVP Validation.

## 21. Product Definition

Self-hosted + Open Source + Official Codex Interface + Credential-Isolated + Web-first + Android-capable.
