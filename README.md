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

## 網路綁定設定（開放區域網路存取）

預設情況下，Compose 僅將連接埠綁定於本機回路（`127.0.0.1:8080`），防止外部未授權存取。若您需要從區網其他裝置或遠端連線，可將主機監聽介面調整為 `0.0.0.0`：

### 推薦方式：透過 `.env` 設定（最佳實踐）
在專案根目錄的 `.env` 檔案中加入 `CODEX_MONITOR_BIND_HOST=0.0.0.0`：

```sh
echo "CODEX_MONITOR_BIND_HOST=0.0.0.0" >> .env
docker compose up -d
```

或在單次啟動時直接帶入環境變數：
```sh
CODEX_MONITOR_BIND_HOST=0.0.0.0 docker compose up -d
```

> [!WARNING]
> 將主機綁定設為 `0.0.0.0` 會使本機所有網路介面（含區網 LAN IP）均可存取該監控服務。請確保該機器處於受保護的受信任內部網路，或已配置主機防火牆限制連線來源；切勿直接暴露於公網（Public Internet）。

## 服務維護與常用指令

### 1. 如何關閉服務
依需求可選擇以下兩種關閉方式：

- **暫停服務（保留容器與網路）**：
  ```sh
  docker compose stop
  ```
  暫時停止容器運作，之後可隨時使用 `docker compose start` 重新喚醒。

- **完全停止並移除容器（推薦，保留登入與配置資料）**：
  ```sh
  docker compose down
  ```
  會停止並移除容器與專屬網路，但**會完整保留**掛載的具名儲存卷 `codex_monitor_home`（包含您的 Codex 登入憑證與設定檔）。下次執行 `docker compose up -d` 即可無縫復原。

> [!CAUTION]
> **切勿隨意執行 `docker compose down -v`**。加上 `-v` 旗標會強制刪除具名儲存卷，導致所有保存的 Codex 登入狀態與組態遺失，必須重新進行裝置授權登入。

### 2. 重啟與更新服務

- **日常重新啟動**：
  ```sh
  docker compose restart
  ```

- **更新專案或 Codex 版本後重新建置**：
  拉取最新程式碼或修改環境變數設定後，執行以下指令重新建置並在背景啟動：
  ```sh
  docker compose up -d --build
  ```

- **檢查運行狀態與日誌**：
  ```sh
  docker compose ps
  docker compose logs -f --tail=100 monitor
  ```

## 核心技術文件 (Canonical documentation)

- [`docs/specification.md`](docs/specification.md) — 需求規格與安全不變量 (Requirements and security invariants)
- [`docs/design.md`](docs/design.md) — 架構與實作設計 (Architecture and implementation design)
- [`docs/test-plan.md`](docs/test-plan.md) — 測試矩陣與驗證準則 (Test matrix and evidence rules)
- [`docs/implementation-plan.md`](docs/implementation-plan.md) — 分階段任務計畫 (Staged task plan)
- [`docs/implementation-status.md`](docs/implementation-status.md) — 當前實作驗證紀錄 (Current implementation evidence)
- [`docs/deployment.md`](docs/deployment.md) — 運維部署指南 (Operational deployment guide)
