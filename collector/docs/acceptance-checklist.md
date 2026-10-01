# V1 Acceptance Checklist

基準：[正式 V1 Specification 1.0](01-codex-usage-monitor-v1-specification.md)，依原始 AC 定義逐項驗收。日期：2026-10-01（Asia/Taipei）。**V1 尚未 COMPLETE**。

## Evidence

- [Windows 最終驗證](evidence/2026-10-01-windows-validation.json)：平台、Go／Codex 版本、format、vet、tests、build、exe SHA256。
- [Codex Live JSON](evidence/2026-10-01-codex-live.json)：實際帳號／rate-limit response 與 Normalization；email、account ID、routing、credit ID 已遮罩，沒有 credentials。
- [Review / 驗證記錄](evidence/2026-10-01-review-and-validation.md)：修正原因、測試名稱、證據邊界與待續 Gate。
- [Collector CI evidence](evidence/2026-10-01-collector-ci.json)：已驗證修正程式 commit bf63c0a 的完整 CI 與 artifact；文件提交後另確認最新 HEAD。
- Google 真實更新與正式公開 HTTPS 尚未執行；本機 transport fixture 的 PASS 不取代這些 Gate。

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
| Codex account/rateLimits/read | PASS | live response；本次 2 個 limits、reset credits summary |
| Codex normalization | PASS | 本次完整 Payload 可 serialize、AES encrypt/decrypt、Client validate |
| AES-GCM | PASS | round-trip / random nonce / tamper / key / format / truncation tests |
| OAuth Desktop live | BLOCKED | Process／User／Machine 均無 Client ID／Secret；需人工 Google 授權 |
| Google fixed File ID live | BLOCKED | OAuth 尚未完成，且沒有正式目標 File ID |
| 正式 HTTPS Test Client | BLOCKED | 需成功發布的 Google Drive Binary 與公開 HTTPS URL |
| GitHub Actions | PASS | [Collector CI 36809477057](https://github.com/killgavin/Self-hosted-Codex-Usage-Monitor-MVP/actions/runs/36809477057)：所有步驟及 artifact upload 成功 |

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
| AC-17 | 目標檔案人工建立 | BLOCKED | 尚無人工建立的 Google Drive 目標檔案證據 |
| AC-18 | Collector 使用固定 File ID | BLOCKED | fixture 同一 ID 連續 PATCH PASS；正式 File ID 未提供，尚不能完成 live 驗收 |
| AC-19 | 成功更新固定 File ID | BLOCKED | 需 Google OAuth 與正式固定 File ID；尚未送出外部 PATCH |
| AC-20 | 不使用 Delete/Create 模擬更新 | PASS | TestTokenRefreshAndFixedFileUpdate：兩次更新及一次失敗只有 PATCH；無其他 method／API |
| AC-21 | HTTPS 可下載最新 Binary | BLOCKED | 需成功發布、分享權限與正式 HTTPS URL；本機 TLS fixture 已 PASS |
| AC-22 | Update 失敗舊檔仍存在 | BLOCKED | fixture 舊內容保留 PASS；尚無 Google 真實舊檔／失敗更新後證據 |
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

## Pending Live Drive Gate

Original File ID：尚未提供。
After Update File ID：BLOCKED。
After Second Update File ID：BLOCKED。

取得 Desktop App credentials 後，先完成當次人工 OAuth，才繼續固定 File ID、連續兩次更新、失敗後檔案保留與正式 HTTPS Client；不會自動擴大 scope，也不會建立或刪除 Drive 檔案。

## Completion / Git Boundary

必須同時滿足所有 AC、真實 OAuth／Drive／HTTPS、Collector CI 與本次變更已提交，才可宣告 COMPLETE。PR #1 保持 Draft。

起始工作樹已有 `.codex-remote-attachments/`、`docs/formal-spec-v0.5/`、`docs/spec/` 三組未追蹤資料；本次保留且不納入 commit。因此即使本次變更全部提交，原工作樹仍不會呈現字面上的 `working tree clean`；不刪除或隱藏這些使用者資料來製造乾淨狀態。
