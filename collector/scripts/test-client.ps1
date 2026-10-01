param(
    [Parameter(Mandatory = $true)]
    [string]$Url
)

$ErrorActionPreference = "Stop"

# 目的：執行正式規格定義的 HTTPS 測試 Client。
# 前提：CODEX_MONITOR_AES_KEY 已設定；URL 必須是 HTTPS。
Push-Location (Split-Path $PSScriptRoot -Parent)
try {
    go run . --test-url $Url
    if ($LASTEXITCODE -ne 0) { throw "HTTPS test client failed" }
}
finally {
    Pop-Location
}
