# Codex Usage Monitor V1 Collector

Windows x64 Go Collector：Codex App Server → Normalized JSON → AES-128-GCM Binary → Google Drive 固定 File ID → HTTPS 測試 Client。

正式基準為 [V1 Specification 1.0](docs/01-codex-usage-monitor-v1-specification.md)，原檔複製後 SHA256 相同；既有 Python / FastAPI / Docker / Dashboard 未修改。**V1 尚未 COMPLETE**，目前等待 Google OAuth credentials，後續仍需真實固定 File ID 與公開 HTTPS 驗證。詳見 [驗收表](docs/acceptance-checklist.md)。

## Requirements

- Windows x64；本輪已實際 build 並執行 AMD64 PE。
- Go 1.24.0 以上（既有 `golang.org/x/oauth2 v0.31.0` 的最低要求）；本機與 CI 固定使用 Go 1.27.1。
- 官方 Codex CLI / App Server；本輪最終實機版本為 `codex-cli 0.159.3`（初次檢查為 0.159.2），以 evidence 記錄為準。
- 執行 Collector 的 Windows 使用者須事先透過官方 Codex 完成登入。Collector 不啟動 OpenAI 登入、不解析 credentials、不使用私有 backend endpoint。
- Google Cloud 已啟用 Drive API，OAuth Client 類型為 **Desktop app**。
- 人工建立的專用 Drive Binary 目標檔案、固定 File ID、可下載 Binary 的 HTTPS URL。

以下命令在 `collector/` 執行；環境變數須設定於同一個 PowerShell session。程式**不會自動載入 .env**。

## Environment Variables

| 變數 | 用途 |
|---|---|
| `CODEX_MONITOR_AES_KEY` | 必要；32 個 Hex 字元，解碼後正好 16 bytes |
| `CODEX_MONITOR_DRIVE_FILE_ID` | 必要；人工建立目標檔案的固定 ID |
| `CODEX_MONITOR_GOOGLE_CLIENT_ID` | 必要；Google OAuth Desktop App Client ID |
| `CODEX_MONITOR_GOOGLE_CLIENT_SECRET` | 必要；對應的 Client Secret |
| `CODEX_MONITOR_GOOGLE_TOKEN_FILE` | 可選；預設 `google-token.json` |
| `CODEX_MONITOR_CODEX_PATH` | 可選；預設 `codex`，可指定官方 exe 完整路徑 |

AES Key 可在本機產生，以下命令只設定環境變數，不列印 Key：

```powershell
$keyBytes = [byte[]]::new(16)
[Security.Cryptography.RandomNumberGenerator]::Fill($keyBytes)
$env:CODEX_MONITOR_AES_KEY = [Convert]::ToHexString($keyBytes)
```

同一份 Binary 的 Collector 與 Client 必須使用同一組 Key；既有發布流程應保留原 Key。不要把真實 Key、Client Secret 或 token 貼到命令輸出、文件或 Git。

環境變數範本為 [.env.example](.env.example)。預設 token、暫存 token、`.env` 與 build outputs 已排除。自訂 token 路徑應放在 Repository 外的本機使用者目錄；若放在 Repository 內，必須先自行加入 ignore 規則並確認 `git check-ignore`。Windows token 檔案繼承所在目錄的 ACL，應由使用者限制存取權限；Go 的 Unix permission mode 不等於 Windows ACL。

## Google OAuth Desktop App / First OAuth Flow

預設且目前唯一使用的 scope 為 `https://www.googleapis.com/auth/drive.file`。

首次 `go run .` 執行至所有資料處理成功後，才啟動 OAuth：只監聽 `127.0.0.1`，由 OS 指派可用 port，再建立實際 redirect URI。程式顯示授權網址，由使用者在本機系統瀏覽器開啟並授權；等待最多五分鐘。每次 flow 使用新的安全隨機 state、callback 驗證 state，並使用 OAuth 套件提供的 PKCE S256；state 不符、缺少 code 或重複 callback 都被拒絕。[Google Desktop OAuth 官方說明](https://developers.google.com/identity/protocols/oauth2/native-app)。

token 保存於本機。後續 access token 到期時，以 refresh token 換取新 token 並更新本機檔案；token 檔損毀會明確失敗，不會靜默覆蓋。OAuth 與 token endpoint 的原始錯誤 body 不進入 log。

`drive.file` 只允許應用程式已獲授權使用的檔案，人工建立與公開分享檔案不等於此 App 已取得更新權限。[Google scope 說明](https://developers.google.com/workspace/drive/api/guides/api-specific-auth)。實機 PATCH 失敗時先保存 HTTP status 與 Google reason，檢查 ownership、檔案／App 授權；不會自動擴大到 `drive` scope。

## Run Collector

先確認同一 Windows 使用者已登入：

```powershell
codex --version
codex login status
go run .
# 或
.\dist\codex-usage-monitor.exe
```

執行順序固定為 `initialize → initialized → account/read → account/rateLimits/read`。每輪新資料完成 Normalize → JSON → Encrypt 後，以完整 Binary 執行一次：

```text
PATCH https://www.googleapis.com/upload/drive/v3/files/{FILE_ID}?uploadType=media
```

不搜尋檔名、不 Create、不 Delete，也不先清空檔案。[Google files.update](https://developers.google.com/workspace/drive/api/reference/rest/v3/files/update)。

`requiresOpenaiAuth` 反映 active provider，不能單獨作為未登入判斷。本次 live 值為 `true`，同時 `account.type=chatgpt`、`planType=plus` 與 rate-limit RPC 均成功。[官方 Codex contract](https://learn.chatgpt.com/docs/app-server)。

## Normalized Contract

Payload 固定包含 `version=1`、`generatedAt`、`account`、`limits`、`resetCredits`。

- 沿用既有 contract 的 decimal **字串**百分比，不改成 JSON float。保留來源 usedPercent，只將 remainingPercent clamp 至 0～100，採標準庫精確十進位計算。
- 依 Limit ID 穩定排序；未知 Limit ID 仍保留，legacy source 沒有 identity 時輸出 null。
- optional name、primary / secondary、authMode、planType、reachedType、reset time 等缺失時保持 null。
- reset-credit summary 缺失為 null；details 的 null / [] / populated 保持不同；present summary 缺少 availableCount 為錯誤，不猜成 0。
- generatedAt 為此次成功建立 Payload 的實際 UTC RFC3339 時間；reset timestamps 轉為 UTC。
- 正式 V1 明確不定義 stale threshold，也不因資料較舊而自行拒絕。
- 新 live source 欄位保存在遮罩 evidence；只將既有正式 contract 定義的欄位映射到發布 JSON，不新增 workspace routing 或帳號識別資料。

## Build / Tests

```powershell
gofmt -l .
go mod tidy
go vet ./...
go test -v ./...
.\scripts\build-win-x64.ps1
```

輸出：`collector/dist/codex-usage-monitor.exe`，`GOOS=windows`、`GOARCH=amd64`、`CGO_ENABLED=0`。腳本檢查各 Go 命令 exit code，並還原原有環境設定。Build 不代表所有外部 Gate 完成。

本機整合測試包含 TLS HTTPS、模擬 Google token／PATCH transport、JSON-RPC 真實子程序 fixture、完整 failure semantics。這些不取代 Google 實機 Gate。

可重跑實機 Gate：

```powershell
$env:CODEX_MONITOR_LIVE_GATE = "1"
$env:CODEX_MONITOR_BINARY_GATE = "1"
$env:CODEX_MONITOR_LIVE_EVIDENCE = "docs/evidence/local/codex-live.json"
go test -v -count=1 -run 'TestLiveCodexGate|TestBuiltWindowsBinary' .
Remove-Item Env:CODEX_MONITOR_LIVE_GATE, Env:CODEX_MONITOR_BINARY_GATE
```

一般 CI 不具備使用者登入，這兩個 opt-in tests 會 SKIP；Windows 本機另有 PASS evidence。

## HTTPS Test Client

Client 只需要 AES Key：

```powershell
go run . --test-url "<正式 HTTPS Binary URL>"
.\scripts\test-client.ps1 -Url "<正式 HTTPS Binary URL>"
# 或
.\dist\codex-usage-monitor.exe --test-url "<正式 HTTPS Binary URL>"
```

依序驗證 HTTPS URL／redirect、HTTP status、Binary minimum length、Magic、Binary version、AES-GCM authentication、UTF-8、JSON、JSON version、所有固定 schema 必要欄位與時間格式。拒絕 HTTP、malformed URL、HTTP downgrade、錯誤 key、竄改資料、unsupported versions、非法 UTF-8／JSON、缺失欄位與未登入 Payload。TLS certificate 驗證正常開啟；下載上限 4 MiB、timeout 30 秒。

## Failure Semantics / Security Boundary

Codex／account／rate-limit、Normalization、JSON 或 Encrypt 任一步失敗，publisher 不會被呼叫。OAuth 或 refresh 失敗不會送出 PATCH；upload 失敗不會清空、Delete 或另外 Create 遠端檔案。Collector 的 process／scanner／RPC 錯誤均使本輪失敗，成功訊息只在最後 upload 成功後記錄。

AES 使用標準庫 AES-128-GCM：`MDF1 | version=1 | random 12-byte nonce | ciphertext | 16-byte tag`。整份 JSON 一次加密，任何 authentication failure 整份拒絕。安全目標是防止取得分享連結的人直接閱讀 JSON；接受共用 Key 可能被 Client 逆向取得，不導入 Key Server、RSA 或其他 Key Management。

本程式不保留 Codex stderr，也不輸出原始 JSON-RPC error message、OAuth token response body 或 Google 任意錯誤 body，以避免 credentials 進入 log。Drive 錯誤保留 HTTP status 與安全的 machine-readable reason。

## Current Gates

- PASS：format、vet、unit / 本機整合測試、Windows x64 build / exe、Codex live、AES-GCM。
- BLOCKED：Google Desktop OAuth 首次授權／live refresh、固定 File ID 實際更新兩次／舊檔保留、正式公開 HTTPS 最新 Binary 下載。
- PR 保持 Draft；完整 AC-01～AC-30 與 evidence 見 [acceptance checklist](docs/acceptance-checklist.md)。
