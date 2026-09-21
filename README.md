# 自託管 Codex 用量監控儀表板 (Self-hosted Codex Usage Monitor)

本儲存庫包含自託管 MVP 伺服器與 Web 儀表板，透過官方 Codex app-server 介面讀取 Codex 帳號狀態與速率限制（Rate Limits）。本監控系統設計於您自行控制的機器上執行；OpenAI 憑證會保留在該伺服器上，絕不會傳送至瀏覽器或透過監控 API 對外洩漏。

## 架構與安全邊界 (Architecture and security boundary)

FastAPI 監控服務會在本地啟動官方 Codex app-server 作為子程序，並提供同源（same-origin）REST API 與儀表板前端。瀏覽器僅與此監控服務通訊。監控服務透過獨立的 `CODEX_MONITOR_API_TOKEN` 保護資料端點（此非 OpenAI 憑證）。Compose 設定預設僅綁定至本機 Loopback (127.0.0.1)、卸除不必要的 Linux Capabilities，並以專用執行階段使用者身份運行容器映像檔。若需遠端存取，應使用 HTTPS 反向代理、Tailscale 或其他同等保護措施，請勿直接暴露於公網。

## 快速開始 (Quick start)

本專案需要具備 Compose v2 的 Docker Engine。完整且可直接複製的設定、環境變數配置、登入、資料持久化與疑難排解說明請參閱 [`docs/deployment.md`](docs/deployment.md)。簡易啟動步驟如下：

```sh
umask 077
printf 'CODEX_MONITOR_API_TOKEN=%s\n' "$(openssl rand -hex 32)" > .env
chmod 600 .env
docker compose up -d --build
```

受保護的資料端點要求監控 Token 不得為空；在啟動 Compose 前，請遵循[Token 設定說明](docs/deployment.md#configure-the-monitor-token)。

啟動後，請於瀏覽器開啟 `http://127.0.0.1:8080/`，並使用儀表板提供的官方 Codex/ChatGPT 裝置代碼（Device-code）流程進行登入。

本儲存庫針對所有記載合約皆具備靜態檢查、自動化測試以及真實執行環境驗證紀錄。T-64 至 T-68 已於 Stage 10 在 Debian 13 Docker 環境中完成驗證，涵蓋映像檔建置、Compose 正常啟動、全新儲存卷之未登入行為、容器重啟持久性，以及重建/重新建立容器之資料持久性。真實 Chrome 360px 響應式驗證 T-63 亦為 PASS，已通過 Final MVP Gate。
整體狀態：`OVERALL: PASS` — `MVP COMPLETE`。

## 核心技術文件 (Canonical documentation)

- [`docs/specification.md`](docs/specification.md) — 需求規格與安全不變量 (Requirements and security invariants)
- [`docs/design.md`](docs/design.md) — 架構與實作設計 (Architecture and implementation design)
- [`docs/test-plan.md`](docs/test-plan.md) — 測試矩陣與驗證準則 (Test matrix and evidence rules)
- [`docs/implementation-plan.md`](docs/implementation-plan.md) — 分階段任務計畫 (Staged task plan)
- [`docs/implementation-status.md`](docs/implementation-status.md) — 當前實作驗證紀錄 (Current implementation evidence)
- [`docs/deployment.md`](docs/deployment.md) — 運維部署指南 (Operational deployment guide)
