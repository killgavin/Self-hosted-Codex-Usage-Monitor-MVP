# Codex Usage Monitor V1 Collector

本目錄實作 V1 正式規格的 Windows x64 Go Collector。既有 Python/Docker MVP 保留，但不是 V1 runtime dependency。

## 環境變數

- `CODEX_MONITOR_AES_KEY`：32 個 Hex 字元，解碼後必須為 16 bytes。
- `CODEX_MONITOR_DRIVE_FILE_ID`：人工建立之 Google Drive 固定 File ID。
- `CODEX_MONITOR_GOOGLE_CLIENT_ID`：OAuth 2.0 Desktop App Client ID。
- `CODEX_MONITOR_GOOGLE_CLIENT_SECRET`：OAuth 2.0 Desktop App Client Secret。
- `CODEX_MONITOR_GOOGLE_TOKEN_FILE`：可選，預設 `google-token.json`。
- `CODEX_MONITOR_CODEX_PATH`：可選，預設 `codex`。

## 執行

先完成 Codex 登入，並在 Google Cloud 建立 OAuth Desktop App。人工建立 Drive 目標檔案、設定分享權限、取得固定 File ID，再設定上述環境變數。

```powershell
go mod tidy
go test ./...
go run .
```

首次執行會進行 Google Desktop OAuth 人工授權；後續使用 refresh token。Drive scope 固定先使用 `drive.file`。若 Integration Gate 證明此 scope 無法更新指定固定 File ID，才依正式規格評估 `drive` scope。

## 驗收邊界

單元測試涵蓋 AES-GCM round-trip、隨機 nonce、ciphertext/tag tamper、錯誤 key、Magic、Binary Version、Normalization 與未登入拒絕。

Google Drive 真實更新、HTTPS 公開下載、Windows x64 Codex live flow 必須在具備真實帳號與 Drive 設定的 Windows 環境執行後才可標記 PASS；未執行不得宣告 V1 COMPLETE。
