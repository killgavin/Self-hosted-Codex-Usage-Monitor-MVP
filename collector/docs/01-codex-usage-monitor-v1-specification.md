# Codex Usage Monitor V1 正式規格文件

## 0. 文件資訊

| 項目 | 內容 |
|---|---|
| 文件名稱 | Codex Usage Monitor V1 正式規格文件 |
| 文件代號 | `01-codex-usage-monitor-v1-specification.md` |
| 文件狀態 | 正式規格 |
| 規格版本 | 1.0 |
| 適用階段 | V1 |
| 主要平台 | Windows x64 |
| Collector 語言 | Go |
| 資料發布目標 | Google Drive 固定 File ID |
| 資料保護方式 | AES-128-GCM |
| Client | V1 僅要求測試 Client / 自動化測試 |
| 手機 App / Widget | 不在 V1 範圍 |

---

# 1. 文件目的

本文件定義 **Codex Usage Monitor V1** 的正式功能規格、資料規格、執行限制、錯誤處理及驗收條件。

本文件為 V1 實作與驗收的主要基準。

實作者不得因推測未來需求，而自行增加本文件未定義的：

- 功能。
- 架構。
- 資料欄位。
- 認證流程。
- 儲存機制。
- 平台支援。
- 安全機制。

若後續需求與本文件衝突，應先修改規格，再進行程式修改。

---

# 2. 系統目標

V1 的目標為：

> 在 Windows x64 環境中，由 Go Collector 透過 `codex app-server` 取得 Codex Usage / Rate Limit 狀態，正規化成固定 JSON Schema，以 AES-128-GCM 加密成 Binary，並透過 Google Drive API 覆寫固定 File ID；最後由測試 Client 透過 HTTPS 下載、驗證、解密並還原 JSON。

V1 重點為建立一條：

```text
可靠
可驗證
低複雜度
可維護
```

的資料發布流程。

---

# 3. 設計原則

V1 採以下優先順序：

```text
正確性
↓
簡單性
↓
可維護性
↓
可驗證性
↓
效能
```

安全性目標限定為：

> 防止直接取得 Google Drive 檔案的人可以一眼閱讀 JSON 內容。

V1 不以以下能力為目標：

- 防專業逆向。
- 防已取得 Client 執行環境的人取得 AES Key。
- 高強度 Key Management。
- 零信任架構。
- 多租戶隔離。
- Internet-facing Backend Security。

---

# 4. 系統範圍

## 4.1 V1 In Scope

V1 必須包含：

1. Codex App Server 啟動或連接。
2. Codex 登入狀態確認。
3. `account/read`。
4. `account/rateLimits/read`。
5. Rate Limit Normalization。
6. 固定 JSON Schema。
7. `version`。
8. `generatedAt`。
9. UTF-8 Serialize。
10. AES-128-GCM Encrypt。
11. Binary Format 封裝。
12. Google Drive OAuth Desktop App 認證。
13. Google Drive 固定 File ID 更新。
14. HTTPS 下載。
15. Binary 格式檢查。
16. AES-GCM Decrypt。
17. JSON Parse。
18. JSON Version 驗證。
19. Windows x64 驗收。
20. 自動化測試或測試 Client。

---

## 4.2 V1 Out of Scope

以下不屬於 V1：

- 正式 Android App。
- Android Widget。
- iOS App。
- Linux 正式驗收。
- Debian Service。
- Docker。
- VM。
- WSL。
- Database。
- Backend REST API。
- WebSocket。
- Google Login for Mobile。
- 多使用者。
- Role / Permission。
- JWT。
- Key Server。
- KMS。
- HSM。
- RSA Key Exchange。
- AES-CBC。
- XOR。
- Base64 作為保護機制。
- 長期歷史資料。
- BI / Reporting。
- FTP。
- FTPS。
- SFTP。
- `status.json`。
- Heartbeat。
- Stale Threshold。
- Widget 即時倒數。
- 多 Publisher 同時支援。
- Linux Gate。

---

# 5. 系統架構

V1 邏輯流程：

```text
Codex CLI / Codex App Server
        ↓
initialize
        ↓
initialized
        ↓
account/read
        ↓
account/rateLimits/read
        ↓
Collector
        ↓
Rate Limit Normalization
        ↓
JSON Serialize
        ↓
UTF-8
        ↓
AES-128-GCM
        ↓
Binary Package
        ↓
Google Drive API
        ↓
固定 File ID
        ↓
HTTPS Download
        ↓
測試 Client
        ↓
Binary Validation
        ↓
AES-GCM Decrypt
        ↓
JSON Parse
        ↓
Schema Validation
```

---

# 6. 執行環境規格

## 6.1 正式支援平台

V1 正式支援：

```text
Windows x64
```

V1 不要求 Linux 實際驗收。

---

## 6.2 Collector 技術

Collector 使用：

```text
Go
```

原始碼應避免無必要使用 Windows-only API。

目的為保留未來跨平台可能性，但：

> 跨平台不得成為 V1 實作阻塞條件。

---

# 7. Codex 前置條件

## 7.1 登入要求

執行 Collector 的 Windows 使用者必須事先完成 Codex 登入。

V1 不自行實作：

- OpenAI Login UI。
- OAuth Authorization Flow。
- Token Refresh。
- Credential Migration。

---

## 7.2 未登入行為

若 `account/read` 顯示：

```text
account = null
requiresOpenaiAuth = true
```

或 `account/rateLimits/read` 因未登入失敗，Collector 必須：

1. 將本次執行判定為失敗。
2. 記錄明確錯誤。
3. 不產生新的有效 Payload。
4. 不覆寫 Google Drive 上上一份有效檔案。
5. 不自行開啟登入流程。

---

# 8. Codex App Server 規格

## 8.1 資料來源

V1 Codex Usage 正式資料來源：

```text
codex app-server
```

傳輸方式：

```text
stdio JSON-RPC
```

---

## 8.2 最低必要流程

Collector 必須支援：

```text
initialize
→ initialized
→ account/read
→ account/rateLimits/read
```

---

## 8.3 禁止替代方式

V1 不得使用以下方式取代正式流程：

- 直接解析 Codex Credential。
- 直接解析不穩定內部 Cache。
- 依賴 private / undocumented backend endpoint。
- 從 UI 畫面擷取 Usage。
- 猜測不存在的欄位。

---

# 9. Rate Limit Normalization 規格

## 9.1 基準

V1 必須沿用目前已經 Gate A 驗證成功的 Rate Limit Normalization Contract。

不得重新設計一套只有：

```json
{
  "usage": 37,
  "resetAt": "..."
}
```

的簡化格式。

---

## 9.2 必須能表達的資料概念

Normalized Schema 至少必須能表達：

- Schema Version。
- Payload Generated Time。
- Account / Plan Type（若來源存在）。
- Limit Identity。
- Primary Window。
- Secondary Window。
- Used Percentage。
- Reset Time。
- Window Duration。
- Reached State。
- Reset Credits（若來源存在）。

---

## 9.3 欄位原則

實際欄位名稱與巢狀結構：

> 必須沿用現有已驗證的 Normalization Contract。

本文件不重新命名現有已驗證欄位。

來源不存在的資料：

```text
不得自行補值
不得自行推測
不得製造預設語意
```

---

# 10. JSON Payload 規格

## 10.1 JSON Encoding

JSON Serialize 完成後必須使用：

```text
UTF-8
```

---

## 10.2 `version`

Payload 必須包含：

```text
version = 1
```

用途：

- 標識 JSON Schema Version。
- 讓 Client 判斷是否支援。

### Version 調整規則

以下情況必須升版：

- 刪除既有欄位。
- 修改欄位資料型別。
- 修改欄位原本語意。
- 改變必要欄位結構。

以下情況原則上可不升版：

- 新增 Optional 欄位。

---

## 10.3 `generatedAt`

Payload 必須包含：

```text
generatedAt
```

格式：

```text
ISO 8601
```

例如：

```text
2026-09-30T22:50:00+08:00
```

`generatedAt` 必須表示：

> Collector 本次成功產生 Payload 的實際時間。

V1 不定義 stale threshold。

---

# 11. AES 加密規格

## 11.1 演算法

固定使用：

```text
AES-128-GCM
```

---

## 11.2 參數

| 項目 | 規格 |
|---|---|
| AES Key | 16 bytes |
| Nonce | 12 bytes |
| Authentication Tag | 16 bytes |
| Plaintext | 完整 UTF-8 JSON |
| 加密粒度 | 整份 JSON 一次加密 |

不得逐欄位加密。

---

# 12. AES Key 規格

## 12.1 Collector Key 來源

AES Key 不得寫死於：

- Go Source。
- Git Repository。
- 編譯常數。

V1 由環境變數取得。

建議變數名稱：

```text
CODEX_MONITOR_AES_KEY
```

---

## 12.2 Key 格式

建議環境變數使用：

```text
32 個 Hex 字元
```

代表：

```text
16 bytes
128 bit
```

Collector 啟動時必須：

1. 檢查環境變數是否存在。
2. 執行 Hex Decode。
3. 確認結果長度正好 16 bytes。
4. Key 錯誤時拒絕啟動。
5. Log 不得輸出 AES Key。

---

## 12.3 安全邊界

未來 Mobile Client 可使用同一組 AES Key。

V1 接受：

> Client 若可自動解密，AES Key 理論上可透過逆向取得。

V1 不為此需求導入：

- Key Server。
- Key Rotation Service。
- Device-specific Key。
- User-specific Key。
- KMS。
- Vault。
- HSM。

---

# 13. Nonce 規格

每次產生新的加密 Payload：

```text
必須產生新的隨機 12-byte Nonce
```

禁止：

- 固定 Nonce。
- 重複 Nonce。
- 單純使用時間戳作為 Nonce。
- 單純使用流水號作為 Nonce。

Nonce：

```text
不需要保密
```

可直接放入 Binary。

---

# 14. Binary File Format

V1 Binary Layout：

```text
Offset   Length      Content
------------------------------------------
0        4 bytes     Magic
4        1 byte      Binary Format Version
5        12 bytes    Nonce
17       N bytes     Ciphertext
最後     16 bytes    GCM Authentication Tag
```

---

## 14.1 Magic

固定：

```text
MDF1
```

ASCII：

```text
4D 44 46 31
```

用途：

- 快速辨識檔案格式。
- 避免誤把 HTML、JSON 或其他內容視為密文。

---

## 14.2 Binary Format Version

固定：

```text
1
```

Binary Format Version：

```text
管理 Binary Layout
```

JSON `version`：

```text
管理 Payload Schema
```

兩者互相獨立。

---

## 14.3 Binary 最小合法長度

Binary 必須至少包含：

```text
4 bytes Magic
+ 1 byte Format Version
+ 12 bytes Nonce
+ 至少 1 byte Ciphertext
+ 16 bytes Tag
```

若長度不足：

```text
直接判定無效
```

---

# 15. Google Drive 目標檔案規格

## 15.1 建立方式

Google Drive 目標檔案：

> 由人工建立一次。

人工設定必須包含：

1. 建立專用目標檔案。
2. 設定分享權限。
3. 取得固定 File ID。
4. 將 File ID 設定給 Collector。

---

## 15.2 Collector 行為

Collector 僅執行：

```text
Update Existing File
```

不得：

- 每次執行建立新檔。
- 以檔名搜尋後自行判定目標。
- Delete 再 Create。
- 自行修復多個同名檔案。

---

## 15.3 固定 File ID 原則

V1 必須維持固定 File ID，以確保：

- Download URL 穩定。
- 分享權限穩定。
- Client 不需更新設定。
- 上傳邏輯簡單。

---

# 16. Google Drive OAuth 規格

## 16.1 認證型態

V1 使用：

```text
OAuth 2.0 Desktop App
```

流程：

```text
首次人工授權
→ Access Token
→ Refresh Token
→ 保存必要 Token
→ 後續自動換取新的 Access Token
```

---

## 16.2 Scope

初始實作優先：

```text
https://www.googleapis.com/auth/drive.file
```

實作驗證時必須確認：

> 此 Scope 是否可成功更新指定固定 File ID。

若無法滿足需求，才允許改用：

```text
https://www.googleapis.com/auth/drive
```

不得在未驗證前直接使用更大權限。

---

## 16.3 Google Drive 禁止儲存內容

Google Drive 上不得保存：

- 明文 JSON。
- AES Key。
- Access Token。
- Refresh Token。
- Client Secret。
- 其他 Credential。

Google Drive 上只發布：

```text
AES-128-GCM Binary
```

---

# 17. Client 驗證規格

V1 不要求正式 Mobile App。

必須提供：

- 測試 Client，或
- 自動化測試

驗證完整讀取流程。

---

## 17.1 Client 處理順序

必須依序：

```text
HTTPS Download
↓
檢查 HTTP 成功
↓
檢查 Binary 最小長度
↓
檢查 Magic
↓
檢查 Binary Format Version
↓
切出 Nonce
↓
切出 Ciphertext
↓
切出 GCM Tag
↓
AES-128-GCM Decrypt
↓
驗證 Authentication Tag
↓
UTF-8 Decode
↓
JSON Parse
↓
檢查 JSON Version
↓
檢查必要欄位
↓
資料可用
```

---

# 18. 錯誤處理規格

## 18.1 任何錯誤不得產生部分有效資料

以下任一情況發生時，整份資料判定無效：

- HTTP Download 失敗。
- HTTP 回傳非預期內容。
- Binary 太短。
- Magic 錯誤。
- Binary Format Version 不支援。
- Binary Layout 不合法。
- Nonce 長度錯誤。
- AES Key 錯誤。
- Ciphertext 被修改。
- GCM Tag 被修改。
- GCM 驗證失敗。
- UTF-8 Decode 失敗。
- JSON Parse 失敗。
- JSON Version 不支援。
- 必要欄位缺失。

---

## 18.2 禁止容錯方式

不得：

- 忽略 Authentication Tag 錯誤。
- 使用部分解密結果。
- 猜測缺失 JSON 欄位。
- 自動修補 Binary。
- 對錯誤密文進行模糊解析。

---

# 19. 發布失敗規格

若以下任一步驟失敗：

```text
Codex Usage 取得
Normalization
JSON Serialize
UTF-8 Encode
AES Encryption
Google OAuth
Google Drive Upload
```

Collector 必須：

1. 將本輪執行標示為失敗。
2. 記錄錯誤。
3. 不發布錯誤 Binary。
4. 不覆寫上一份有效檔案。
5. 不刪除 Google Drive 現有檔案。

---

# 20. Logging 規格

V1 至少需記錄：

- Collector 啟動。
- Codex App Server 初始化結果。
- Account 狀態。
- Rate Limit 取得成功 / 失敗。
- Normalization 成功 / 失敗。
- Encryption 成功 / 失敗。
- Google Drive Upload 成功 / 失敗。
- File ID 更新結果。
- 本輪執行最終狀態。

Log 不得包含：

- AES Key。
- OAuth Access Token。
- Refresh Token。
- Client Secret。
- 其他 Credential 明文。

---

# 21. 非功能需求

## 21.1 效能

資料量屬小型 JSON。

V1 不需進行複雜效能最佳化。

AES-128-GCM、JSON Serialize、Binary 組裝均應使用標準函式庫或成熟套件。

不得因微小效能差異自行實作低階加密演算法。

---

## 21.2 可維護性

程式碼應將以下責任分離：

```text
Codex Client
Normalization
JSON Serialization
Encryption
Binary Format
Google Drive Publisher
Configuration
Logging
```

避免所有流程集中於單一函式。

---

## 21.3 測試性

加密、Binary Parse、Normalization、Publisher 應盡可能可獨立測試。

Google Drive 實際 API 驗證可視為 Integration Test。

---

# 22. 驗收條件

## 22.1 Codex Gate

| 編號 | 驗收項目 | 結果 |
|---|---|---|
| AC-01 | Windows x64 可執行 Collector | 必須 PASS |
| AC-02 | `codex app-server` 可初始化 | 必須 PASS |
| AC-03 | `account/read` 成功 | 必須 PASS |
| AC-04 | `account/rateLimits/read` 成功 | 必須 PASS |
| AC-05 | 已登入帳號可取得有效 Rate Limit State | 必須 PASS |
| AC-06 | 未登入時不發布錯誤資料 | 必須 PASS |

---

## 22.2 JSON Gate

| 編號 | 驗收項目 | 結果 |
|---|---|---|
| AC-07 | 使用既有已驗證 Normalized Schema | 必須 PASS |
| AC-08 | `version = 1` | 必須 PASS |
| AC-09 | `generatedAt` 為合法 ISO 8601 | 必須 PASS |
| AC-10 | 不直接發布未正規化來源資料 | 必須 PASS |

---

## 22.3 Encryption Gate

| 編號 | 驗收項目 | 結果 |
|---|---|---|
| AC-11 | AES-128-GCM 正常加密 | 必須 PASS |
| AC-12 | Key 正好 16 bytes | 必須 PASS |
| AC-13 | 每次加密使用新的 12-byte Nonce | 必須 PASS |
| AC-14 | Tag 為 16 bytes | 必須 PASS |
| AC-15 | Magic = `MDF1` | 必須 PASS |
| AC-16 | Binary Format Version = `1` | 必須 PASS |

---

## 22.4 Google Drive Gate

| 編號 | 驗收項目 | 結果 |
|---|---|---|
| AC-17 | 目標檔案由人工建立 | 必須 PASS |
| AC-18 | Collector 使用固定 File ID | 必須 PASS |
| AC-19 | 可成功更新固定 File ID | 必須 PASS |
| AC-20 | 不使用 Delete/Create 模擬更新 | 必須 PASS |
| AC-21 | HTTPS 可下載最新 Binary | 必須 PASS |
| AC-22 | Update 失敗時舊檔仍存在 | 必須 PASS |

---

## 22.5 Integrity / Decryption Gate

| 編號 | 驗收項目 | 結果 |
|---|---|---|
| AC-23 | 正確 Key 可還原 JSON | 必須 PASS |
| AC-24 | 修改 Ciphertext 任一 Byte 後驗證失敗 | 必須 PASS |
| AC-25 | 修改 Tag 後驗證失敗 | 必須 PASS |
| AC-26 | 錯誤 Key 解密失敗 | 必須 PASS |
| AC-27 | 錯誤 Magic 被拒絕 | 必須 PASS |
| AC-28 | 不支援 Binary Version 被拒絕 | 必須 PASS |
| AC-29 | 不支援 JSON Version 被拒絕 | 必須 PASS |
| AC-30 | 必要欄位缺失被拒絕 | 必須 PASS |

---

# 23. V1 完成定義

所有 `AC-01` ～ `AC-30` 均為：

```text
PASS
```

才可宣告：

```text
V1 COMPLETE
```

若任一必須項目未通過：

```text
V1 NOT COMPLETE
```

不得以：

- 後續再補。
- 不影響主要流程。
- 測試環境限制。
- 理論上可行。

等理由直接視為完成。

若確有外部環境阻塞，應標記：

```text
BLOCKED
```

並記錄明確 Blocking Reason。

---

# 24. V1 完成後才允許評估的功能

V1 COMPLETE 後，才可另外規劃：

- Android Mobile App。
- Widget。
- Linux 驗證。
- Semantic Dedup。
- Retry Policy 強化。
- Stale Handling。
- Heartbeat。
- 其他 Publisher。
- Key Obfuscation。
- 更完整 Deployment Automation。

以上不得提前併入 V1。

---

# 25. 規格變更原則

若後續需要變更本文件，必須先判斷屬於：

```text
Requirement Change
Design Change
Implementation Detail
```

若變更會影響：

- JSON Schema。
- Binary Layout。
- AES 規格。
- Google Drive File ID 行為。
- 認證方式。
- 支援平台。
- V1 驗收條件。

則必須先更新本規格文件，再開始修改程式。

---

# 26. 最終 V1 邊界

V1 最終邊界固定為：

```text
Codex Usage
    ↓
Normalized JSON
    ↓
AES-128-GCM Binary
    ↓
Google Drive 固定 File ID
    ↓
HTTPS Download
    ↓
正確解密與驗證
```

只要此資料流可靠完成並通過所有驗收條件，即為 V1 成功。

其餘 UI、Widget、歷史資料、更多平台、更多發布方式，均屬後續階段。
