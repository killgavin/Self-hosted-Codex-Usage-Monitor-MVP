# Codex Usage Monitor V1 Collector

Windows x64 Go Collector：Codex App Server → Normalized JSON → AES-128-GCM Binary → Google Drive 固定 File ID → HTTPS 測試 Client。

正式基準為 [V1 Specification 1.0](docs/01-codex-usage-monitor-v1-specification.md)，原檔複製後 SHA256 相同；既有 Python / FastAPI / Docker / Dashboard 未修改。2026-10-15 全部實機 Gate 與 AC-01～AC-30 均 PASS：完整 `drive` scope 人工授權、refresh、本機保存、同一 File ID 連續兩次 PATCH、失敗後舊檔保留、正式匿名 HTTPS／解密／錯誤 Key 拒絕。**V1 尚未 COMPLETE**：本次以外的起始未追蹤資料仍保留，尚不符合「整個工作樹乾淨」的完成條件。詳見 [驗收表](docs/acceptance-checklist.md)。

## Requirements

- Windows x64；本輪已實際 build 並執行 AMD64 PE。
- Go 1.24.0 以上（既有 `golang.org/x/oauth2 v0.31.0` 的最低要求）；本機與 CI 固定使用 Go 1.27.1。
- 官方 Codex CLI / App Server；2026-10-15 續驗實機版本為 `codex-cli 0.162.1`，以各次 evidence 記錄為準。
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
| `CODEX_MONITOR_GOOGLE_SCOPE` | 可選；預設完整 `drive.file` scope URL；僅在實機驗證失敗並獲核准後明確設定完整 `drive` scope URL |
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

預設 scope 為 `https://www.googleapis.com/auth/drive.file`。程式只接受此 URL 或 `https://www.googleapis.com/auth/drive`，不會因為 API 失敗而自動擴大權限。

首次 `go run .` 執行至所有資料處理成功後，才啟動 OAuth：只監聽 `127.0.0.1`，由 OS 指派可用 port，再建立實際 redirect URI。程式顯示授權網址，由使用者在本機系統瀏覽器開啟並授權；等待最多五分鐘。每次 flow 使用新的安全隨機 state、callback 驗證 state，並使用 OAuth 套件提供的 PKCE S256；state 不符、缺少 code 或重複 callback 都被拒絕。新授權指定 `access_type=offline` 與 `prompt=consent`，以便取得可離線使用的 refresh token；既有 token 不重新啟動授權。[Google Desktop OAuth 官方說明](https://developers.google.com/identity/protocols/oauth2/native-app)、[離線授權說明](https://developers.google.com/identity/protocols/oauth2/web-server#offline)。

token 保存於本機。後續 access token 到期時，以 refresh token 換取新 token 並更新本機檔案；token 檔損毀會明確失敗，不會靜默覆蓋。OAuth 與 token endpoint 的原始錯誤 body 不進入 log。

首次授權也可獨立執行，不需要 AES Key 或 Drive File ID。將下載的 Desktop App credentials JSON 與 token 檔案放在 Repository 外，執行以下 opt-in Gate；它不發送 Drive 檔案請求，授權後會讓記憶體中的 token 副本過期，實際驗證 refresh 及保存：

```powershell
$env:CODEX_MONITOR_GOOGLE_LIVE_GATE = "1"
$env:CODEX_MONITOR_GOOGLE_CREDENTIALS_FILE = "<Repository 外的 Desktop App JSON 完整路徑>"
$env:CODEX_MONITOR_GOOGLE_TOKEN_FILE = "<Repository 外的 token JSON 完整路徑>"
$env:CODEX_MONITOR_GOOGLE_LIVE_EVIDENCE = "docs/evidence/local/google-oauth-live.json"
go test -v -count=1 -run '^TestLiveGoogleOAuthGate$' .
```

`CODEX_MONITOR_GOOGLE_CREDENTIALS_FILE` 與 `CODEX_MONITOR_GOOGLE_LIVE_GATE` 僅供測試 Gate 使用；正式 Collector 的 Client ID／Secret 設定仍為上述環境變數。一般 CI 不會啟動此人工 OAuth flow。

`drive.file` 只允許應用程式已獲授權使用的檔案，人工建立與公開分享檔案不等於此 App 已取得更新權限。[Google scope 說明](https://developers.google.com/workspace/drive/api/guides/api-specific-auth)。實機 PATCH 失敗時先保存 HTTP status 與 Google reason，檢查 ownership、檔案／App 授權；不會自動擴大到 `drive` scope。

本次已保留 [HTTP 404／notFound PATCH evidence](docs/evidence/2026-10-15-google-drive-publish.json)。404 本身不足以確定是 scope、ownership 或 ID 問題。依正式規格 §16.2 及使用者明確核准，重新授權時設定：

```powershell
$env:CODEX_MONITOR_GOOGLE_SCOPE = "https://www.googleapis.com/auth/drive"
$env:CODEX_MONITOR_GOOGLE_TOKEN_FILE = "<Repository 外尚不存在的獨立 token JSON 完整路徑>"
```

再執行上述 OAuth Gate，由使用者確認 Google 同意畫面。改 scope 不會讓已存在的 token 自動取得新權限；保留原本 `drive.file` token，使用獨立路徑重新授權，後續 Collector 使用相同 scope 與新 token 路徑。完整 `drive` scope 具有較廣的 Drive 讀寫權限，僅在使用者核准後使用。

本次獨立完整 scope 授權與實際 refresh 已 [PASS](docs/evidence/2026-10-15-google-oauth-drive-live.json)。先前 `drive.file` 的 HTTP 404 原始 evidence 保留；完整 scope 查詢確認目標是人工上傳的 `application/octet-stream`，原始檔案為 0 bytes。

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

真實固定 ID Gate 可設定 `CODEX_MONITOR_DRIVE_LIVE_GATE=1`、`CODEX_MONITOR_GOOGLE_CREDENTIALS_FILE`、token 路徑、scope、AES Key 及明確核准覆寫的 `CODEX_MONITOR_DRIVE_FILE_ID`，執行 `go test -v -count=1 -run '^TestLiveGoogleDrivePublishGate$' .`。此 opt-in 測試會透過正式 pipeline 覆寫兩次；observer 只允許指定 ID 的 media PATCH，驗證加密 Payload 與回傳 ID；Google 錯誤會使測試失敗。可用 `CODEX_MONITOR_DRIVE_LIVE_EVIDENCE` 指定遮罩後 evidence 路徑。一般 CI 不執行真實更新。

失敗保護可使用同一組設定，加上 `CODEX_MONITOR_DRIVE_FAILURE_LIVE_GATE=1`，執行 `go test -v -count=1 -run '^TestLiveGoogleDriveFailureGate$' .`。測試先下載並驗證既有 Binary，再對指定 ID 發送一次將 bearer 改為無效值的 PATCH，body 保持原有有效 Binary；要求實際 HTTP 401，並重新下載比對逐 byte 與 SHA256、驗證 GCM。可用 `CODEX_MONITOR_DRIVE_FAILURE_LIVE_EVIDENCE` 指定 evidence 路徑。此 fault injection 不把測試 credential 寫入 token 檔，不執行 Delete／Create。本次 [兩次更新](docs/evidence/2026-10-15-google-drive-full-scope-publish.json)與[失敗保留](docs/evidence/2026-10-15-google-drive-failure-live.json)均 PASS。

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

一般 CI 不具備使用者登入，Codex、binary 與 Google OAuth 的 opt-in tests 會 SKIP；Windows 本機另有 PASS evidence。

## HTTPS Test Client

Client 只需要 AES Key：

```powershell
go run . --test-url "<正式 HTTPS Binary URL>"
.\scripts\test-client.ps1 -Url "<正式 HTTPS Binary URL>"
# 或
.\dist\codex-usage-monitor.exe --test-url "<正式 HTTPS Binary URL>"
```

依序驗證 HTTPS URL／redirect、HTTP status、Binary minimum length、Magic、Binary version、AES-GCM authentication、UTF-8、JSON、JSON version、所有固定 schema 必要欄位與時間格式。拒絕 HTTP、malformed URL、HTTP downgrade、錯誤 key、竄改資料、unsupported versions、非法 UTF-8／JSON、缺失欄位與未登入 Payload。TLS certificate 驗證正常開啟；下載上限 4 MiB、timeout 30 秒。

Google Drive 檔案必須允許知道連結的任何人檢視，Client 不攜帶 Google token 或登入 cookie。正式下載 URL 採 `files.get` 回傳的 HTTPS `webContentLink`；瀏覽用 `/file/d/.../view` 不是 Binary。私人檔案可能回傳 HTTP 200 的 HTML 登入頁，仍須由 Binary Magic 驗證拒絕，不能因 HTTP 200 宣告 PASS。本次[分享前 evidence](docs/evidence/2026-10-15-google-https-live.json)為 HTML／Magic 拒絕；使用者開啟 anyone／reader 後，[正式匿名 HTTPS evidence](docs/evidence/2026-10-15-google-https-public-live.json)確認最新 Binary 與授權 API 下載雜湊相同，`go run`、PowerShell script、Windows EXE 均 PASS，錯誤 Key 拒絕。

## Failure Semantics / Security Boundary

Codex／account／rate-limit、Normalization、JSON 或 Encrypt 任一步失敗，publisher 不會被呼叫。OAuth 或 refresh 失敗不會送出 PATCH；upload 失敗不會清空、Delete 或另外 Create 遠端檔案。Collector 的 process／scanner／RPC 錯誤均使本輪失敗，成功訊息只在最後 upload 成功後記錄。

AES 使用標準庫 AES-128-GCM：`MDF1 | version=1 | random 12-byte nonce | ciphertext | 16-byte tag`。整份 JSON 一次加密，任何 authentication failure 整份拒絕。安全目標是防止取得分享連結的人直接閱讀 JSON；接受共用 Key 可能被 Client 逆向取得，不導入 Key Server、RSA 或其他 Key Management。

本程式不保留 Codex stderr，也不輸出原始 JSON-RPC error message、OAuth token response body 或 Google 任意錯誤 body，以避免 credentials 進入 log。Drive 錯誤保留 HTTP status 與安全的 machine-readable reason。

## Current Gates

- PASS：format、vet、unit / 本機整合測試、Windows x64 build / exe、Codex live、AES-GCM；兩種 scope OAuth／live refresh／本機保存、完整 scope 固定 File ID 連續兩次更新、實際更新失敗後舊內容保留、正式匿名 HTTPS 最新 Binary／正確 Key／錯誤 Key 拒絕；AC-01～AC-30 均 PASS。
- BLOCKED：原訂「整個 Git 工作樹乾淨」條件。起始已有 `.codex-remote-attachments/`、`docs/formal-spec-v0.5/`、`docs/spec/` 共 9 個未追蹤檔案，保持原樣；沒有刪除、隱藏或擅自納入本次提交。
- PR 保持 Draft；完整 AC-01～AC-30 與 evidence 見 [acceptance checklist](docs/acceptance-checklist.md)。
