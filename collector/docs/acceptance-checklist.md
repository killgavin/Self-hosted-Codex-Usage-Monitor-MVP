# V1 Acceptance Checklist

此文件只記錄驗證狀態，不以「程式已存在」取代實際 Gate。

## 可自動驗證

| Gate | 驗證方式 | 狀態 |
|---|---|---|
| Go format | `gofmt -l .` | CI 執行 |
| Static analysis | `go vet ./...` | CI 執行 |
| Unit tests | `go test -v ./...` | CI 執行 |
| Windows x64 build | `GOOS=windows GOARCH=amd64 go build` | CI 執行 |
| AES-GCM round-trip | `crypto_test.go` | CI 執行 |
| Nonce uniqueness | `crypto_test.go` | CI 執行 |
| Tamper / wrong key / format rejection | `crypto_test.go` | CI 執行 |
| Normalization / logged-out rejection | `normalize_test.go` | CI 執行 |

## 必須在真實 Windows / Google Drive 環境驗證

以下項目在沒有真實帳號、OAuth Desktop App、固定 Drive File ID 與公開 HTTPS URL 時不得標記 PASS：

1. Windows x64 執行 `codex app-server --listen stdio://`。
2. `initialize → initialized → account/read → account/rateLimits/read` live response。
3. 已登入狀態成功產生 V1 Payload。
4. 未登入或 Codex 失敗時不覆寫上一份有效 Drive 檔案。
5. Google Desktop OAuth loopback 首次授權。
6. refresh token 後續自動換取 access token。
7. `drive.file` 對既有固定 File ID 的 PATCH 更新能力。
8. Drive File ID 更新前後保持不變。
9. 公開分享 URL 可透過 HTTPS 下載 Binary。
10. `--test-url` 完整執行 Download → Binary → GCM → UTF-8 → JSON → Version/Required Fields。
11. 依正式規格逐項確認 AC-01～AC-30。

## 完成條件

只有正式規格要求的 Acceptance Criteria 全部實際 PASS 後，才可將 Draft PR 改為 Ready 並宣告 V1 COMPLETE。
