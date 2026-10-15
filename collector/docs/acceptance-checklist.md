# V1 Acceptance Checklist

基準：[正式 V1 Specification 1.0](01-codex-usage-monitor-v1-specification.md)，依原始 AC 定義逐項驗收。更新日期：2026-10-15（Asia/Taipei）。全部實機 Gate 與 AC-01～AC-30 均 PASS。**V1 尚未 COMPLETE**：原訂「整個 Git 工作樹乾淨」條件仍受起始未追蹤資料阻擋。

## Evidence

- [Windows 最終驗證](evidence/2026-10-01-windows-validation.json)：平台、Go／Codex 版本、format、vet、tests、build、exe SHA256。
- [Codex Live JSON](evidence/2026-10-01-codex-live.json)：實際帳號／rate-limit response 與 Normalization；email、account ID、routing、credit ID 已遮罩，沒有 credentials。
- [Review / 驗證記錄](evidence/2026-10-01-review-and-validation.md)：修正原因、測試名稱、證據邊界與待續 Gate。
- [Collector CI evidence](evidence/2026-10-01-collector-ci.json)：已驗證修正程式 commit bf63c0a 的完整 CI 與 artifact；文件提交後另確認最新 HEAD。
- [Google OAuth Live evidence](evidence/2026-10-15-google-oauth-live.json)：Desktop App 首次授權、實際 token refresh 與本機保存均 PASS；Drive 檔案請求數為 0。
- [2026-10-15 Windows 續驗](evidence/2026-10-15-windows-validation.json)與 [Codex Live](evidence/2026-10-15-codex-live.json)：format、vet、全部一般測試、Windows x64 build／exe 與目前 Codex RPC 均 PASS。
- [2026-10-15 Collector CI](evidence/2026-10-15-collector-ci.json)：scope 修正 commit `4e4a37f` 的 checkout 至 Windows artifact upload 全部 PASS；人工 OAuth／Drive 不由 CI 代驗。
- [指定目標的 metadata 查詢](evidence/2026-10-15-google-drive-metadata.json)：以 `drive.file` 對使用者提供之 ID 只讀查詢，HTTP 404／notFound；沒有發送 PATCH，無法據此確認 MIME type 或斷定權限失敗原因。
- [人工上傳 Binary 的 metadata 查詢](evidence/2026-10-15-google-drive-blob-metadata.json)及[實際 PATCH](evidence/2026-10-15-google-drive-publish.json)：`drive.file` 均回傳 HTTP 404／notFound；PATCH 測試 FAIL，完成更新 0 次，無 Delete／Create。404 不足以唯一判定 scope、ownership 或 App 授權問題。
- 本機 transport fixture 的 PASS 不取代 Google Gate；以下另有實際 OAuth、Drive 與匿名 HTTPS evidence。
- [完整 scope OAuth](evidence/2026-10-15-google-oauth-drive-live.json)、[目標 metadata](evidence/2026-10-15-google-drive-full-scope-metadata.json)、[兩次實際 PATCH](evidence/2026-10-15-google-drive-full-scope-publish.json)：新授權／refresh PASS，目標為人工上傳的普通 Binary，兩次 HTTP 200 且回傳相同 ID。
- [實際 Google 更新失敗](evidence/2026-10-15-google-drive-failure-live.json)：故意將一次 PATCH 的 bearer 改成無效值，HTTP 401；前後實際下載的完整 Binary 逐 byte 及 SHA256 相同，GCM／schema 驗證成功。
- [分享前匿名 HTTPS](evidence/2026-10-15-google-https-live.json)：採 Google 回傳的 webContentLink，無 Authorization／登入 cookie；當時 HTTP 200 但 Content-Type=text/html，Windows Client 正確拒絕 Magic，metadata 只有 owner 權限。
- [分享後正式匿名 HTTPS](evidence/2026-10-15-google-https-public-live.json)：使用者開啟 anyone／reader 後，由 Windows EXE 再發布最新資料；匿名 HTTP 200 Binary 與授權 API 下載 SHA256 相同，generatedAt 屬於此次發布，Go／PowerShell／EXE Client 均 PASS，錯誤 Key 被拒絕。先前分享前失敗 evidence 保留。
- [Drive Gate 測試版 CI](evidence/2026-10-15-drive-gates-ci.json)：commit `517e424` 的 checkout 至 Windows artifact upload 全部 PASS。

## Gates

| Gate | 狀態 | Evidence |
|---|---|---|
| gofmt | PASS | 最終 `gofmt -l .` 無輸出 |
| go vet | PASS | `go vet ./...` exit 0 |
| go test | PASS | `go test -v -count=1 ./...`；所有一般測試 PASS |
| 本機 Integration | PASS | TLS、Google transport fixture、JSON-RPC child process、failure semantics |
| Windows x64 build | PASS | `scripts/build-win-x64.ps1`；PE Machine=AMD64，exe 實際執行 |
| Codex initialize | PASS | live initialize response 成功 |
| Codex initialized | PASS | live notification 已送出；此 method 不回傳 response |
| Codex account/read | PASS | account 非 null，type=chatgpt，planType=plus |
| Codex account/rateLimits/read | PASS | 2026-10-15 live response 有 1 個 limit 與 reset credits summary；沒有硬編碼歷史 2-limit 狀態 |
| Codex normalization | PASS | 本次完整 Payload 可 serialize、AES encrypt/decrypt、Client validate |
| AES-GCM | PASS | round-trip / random nonce / tamper / key / format / truncation tests |
| OAuth Desktop live | PASS | 2026-10-15 TestLiveGoogleOAuthGate：取得 access／refresh token，實際 refresh，重新讀取本機 token 比對成功 |
| 完整 drive scope 重新授權 | PASS | 使用者核准並完成人工同意；獨立 token 的取得、實際 refresh、保存均 PASS |
| Google fixed File ID live | PASS | 同一人工上傳 Binary 連續兩次 PATCH HTTP 200／ID 相同；實際 HTTP 401 失敗後內容逐 byte 保留 |
| 正式 HTTPS Test Client | PASS | 使用者開啟分享後，正式 webContentLink 匿名下載最新 Binary；SHA256 與 API 相同，Go／PowerShell／EXE 驗證及錯誤 Key 拒絕成功 |
| GitHub Actions | PASS | [Collector CI 38691608081](https://github.com/killgavin/Self-hosted-Codex-Usage-Monitor-MVP/actions/runs/38691608081)：commit 517e424 所有步驟及 artifact upload 成功；最終文件提交後再確認 HEAD |

本次 `requiresOpenaiAuth=true`，且 account 與 rate-limit RPC 均成功。依正式規格 §7.2（account=null 或 rate RPC 未登入失敗）與既有 contract，此 provider 旗標不是未登入判斷；沒有修改正式需求或硬編碼帳號／Limit ID。

## AC-01 ～ AC-30

| AC | 正式驗收項目 | 狀態 | Evidence / Blocking Reason |
|---|---|---|---|
| AC-01 | Windows x64 可執行 Collector | PASS | build + TestBuiltWindowsBinary，PE AMD64；實際 exe 的 Client 拒絕 HTTP |
| AC-02 | codex app-server 可初始化 | PASS | live initialize → initialized |
| AC-03 | account/read 成功 | PASS | live account response |
| AC-04 | account/rateLimits/read 成功 | PASS | live rate response |
| AC-05 | 已登入帳號取得有效 Rate Limit State | PASS | TestLiveCodexGate：normalize → JSON → AES → Client |
| AC-06 | 未登入不發布錯誤資料 | PASS | TestNormalizeRejectsLoggedOut、TestPipelineFailureDoesNotPublish/logged-out；publisher call count=0 |
| AC-07 | 使用既有已驗證 Normalized Schema | PASS | 既有 Python mapper／models 對照、Normalization tests + live evidence |
| AC-08 | version=1 | PASS | live JSON + TestNormalizeVerifiedContract |
| AC-09 | generatedAt 合法 ISO 8601 | PASS | live UTC RFC3339 + missing／invalid／null Client tests |
| AC-10 | 不直接發布來源資料 | PASS | TestPipelinePublishesOneCompleteAuthenticatedPackage；發布 body 完整 GCM Binary，解密為固定 schema |
| AC-11 | AES-128-GCM 正常加密 | PASS | TestEncryptDecryptAndIntegrity + live round-trip |
| AC-12 | Key 正好 16 bytes | PASS | TestLoadAESKey、TestTruncatedBinaryAndInvalidKeys |
| AC-13 | 新的隨機 12-byte Nonce | PASS | 兩次相同 plaintext / key，nonce 與 ciphertext 不同；crypto/rand |
| AC-14 | Tag 為 16 bytes | PASS | Binary 長度等於 4+1+12+plaintext+16，tag tamper 拒絕 |
| AC-15 | Magic=MDF1 | PASS | TestBinaryValidation |
| AC-16 | Binary Format Version=1 | PASS | TestBinaryValidation |
| AC-17 | 目標檔案人工建立 | PASS | 使用者人工上傳 placeholder 後提供固定 ID；完整 scope GET HTTP 200，application/octet-stream、初始 0 bytes |
| AC-18 | Collector 使用固定 File ID | PASS | 實際 PATCH observer 僅允許使用者提供的固定 ID，未搜尋／替換 ID；連續兩次回傳相同 ID |
| AC-19 | 成功更新固定 File ID | PASS | 完整 scope 正式 pipeline 連續兩次 PATCH HTTP 200，回傳 ID 都等於原始 ID |
| AC-20 | 不使用 Delete/Create 模擬更新 | PASS | TestTokenRefreshAndFixedFileUpdate：兩次更新及一次失敗只有 PATCH；無其他 method／API |
| AC-21 | HTTPS 可下載最新 Binary | PASS | Windows EXE 發布新資料後，正式 webContentLink 匿名 HTTP 200 Binary；與 API SHA256 相同、generatedAt 對應本輪，三種 Client 均成功 |
| AC-22 | Update 失敗舊檔仍存在 | PASS | 實際無效 bearer PATCH HTTP 401；同 ID 前後下載成功、逐 byte／SHA256 相同，兩份都通過 GCM／schema |
| AC-23 | 正確 Key 還原 JSON | PASS | crypto round-trip、HTTPS TLS fixture + live Payload round-trip |
| AC-24 | 修改任一 ciphertext byte 失敗 | PASS | TestTruncatedBinaryAndInvalidKeys 遍歷 ciphertext bytes + Client tamper |
| AC-25 | 修改 Tag 失敗 | PASS | TestEncryptDecryptAndIntegrity + Client tag tamper |
| AC-26 | 錯誤 Key 解密失敗 | PASS | crypto wrong key + HTTPS Client wrong key |
| AC-27 | 錯誤 Magic 拒絕 | PASS | crypto 與 Client Magic tests |
| AC-28 | 不支援 Binary Version 拒絕 | PASS | crypto 與 Client Binary version tests |
| AC-29 | 不支援 JSON Version 拒絕 | PASS | TestClientSchemaRejectsMissingAndMalformedFields/version |
| AC-30 | 必要欄位缺失拒絕 | PASS | root／account／limit／window／credits 缺失與 null tests |

## AES-GCM Detailed Gate

| 測試 | 結果 |
|---|---|
| Encrypt → Decrypt round-trip | PASS |
| 同 plaintext / key 兩次 nonce 不同 | PASS |
| ciphertext 不同 | PASS |
| 修改 ciphertext | PASS（拒絕） |
| 修改 tag | PASS（拒絕） |
| wrong key | PASS（拒絕） |
| wrong Magic | PASS（拒絕） |
| unsupported Binary Version | PASS（拒絕） |
| 所有截短長度 | PASS（拒絕） |
| invalid key length：0／15／17／24／32 bytes | PASS（拒絕） |
| 空 plaintext | PASS（拒絕；符合 Binary 最小長度） |

## Live Drive 與 HTTPS Gate

Original File ID：已提供人工上傳之專用 Binary 目標（遮罩 `1_Gy…OHep`）；原先 Google 文件目標不再使用。
After Update File ID：`1_Gy…OHep`，Google 回傳與原始 ID 相同（PASS）。
After Second Update File ID：`1_Gy…OHep`，Google 回傳與原始 ID 相同（PASS）。

2026-10-15 已完成 `drive.file` 人工 OAuth、實際 refresh 與本機 token 保存。使用者依提示上傳一般 Binary 並提供固定 ID；其 metadata GET 及正式 pipeline media PATCH 均回傳 HTTP 404／notFound。此次 PATCH 前 Codex RPC、Normalize、JSON、Encrypt 與完整 Payload 驗證成功；完成更新 0 次，沒有清空、Delete 或 Create。

依正式規格 §16.2，已向使用者說明 404 與較廣權限；使用者明確選擇「B：允許完整 drive scope，重新授權」，並回覆「完成」。本輪維持 S2 整合工作的既有規格及實作授權，限定 production 變更為 `CODEX_MONITOR_GOOGLE_SCOPE` 明確選擇兩種 scope URL（預設仍為 drive.file），以及新離線授權的 `prompt=consent`。不修改 JSON、Binary、固定 ID PATCH contract 或舊 MVP；不新增 dependency。測試涵蓋預設／完整／無效 scope、state／PKCE／offline／consent request、原有 refresh 與 PATCH；獨立 token 的重新授權及 refresh 均已 PASS，保留原 narrow token。回復時移除 scope 設定並使用原 token 檔即可，程式不撤銷遠端授權。

完整 scope 下已確認人工建立的普通 Binary，完成兩次正式更新，以及一次刻意無效 bearer 的實際失敗更新與舊檔比對。此故障注入的 body 為原有有效 Binary，不把無效 credential 寫入 token 檔，不送清空、Delete 或 Create。之後使用者將該檔案設為「知道連結的任何人／檢視者」並回覆完成；Windows EXE 再成功發布一次，匿名 HTTPS 與已授權 API 回讀 Binary 雜湊相同。Go／PowerShell／EXE Client 均驗證成功，錯誤 Key 被拒絕。AC-21 使用真正匿名下載證據，未以已授權 API 下載代驗。

## Completion / Git Boundary

必須同時滿足所有 AC、真實 OAuth／Drive／HTTPS、Collector CI 與本次變更已提交，才可宣告 COMPLETE。PR #1 保持 Draft。

起始工作樹已有 `.codex-remote-attachments/`、`docs/formal-spec-v0.5/`、`docs/spec/` 三組未追蹤資料；本次保留且不納入 commit。因此即使本次變更全部提交，原工作樹仍不會呈現字面上的 `working tree clean`；不刪除或隱藏這些使用者資料來製造乾淨狀態。

2026-10-15 只讀盤點：`.codex-remote-attachments/` 2 files／47,042 bytes、`docs/formal-spec-v0.5/` 6 files／70,321 bytes、`docs/spec/` 1 file／7,342 bytes。共 9 files／124,705 bytes。本次尚未取得將這些既有資料納入版本控制、搬移、刪除或排除的核准；也未取得調整「整個工作樹乾淨」驗收範圍的核准。此項為唯一剩餘完成條件，功能與實機 AC 均已 PASS。
