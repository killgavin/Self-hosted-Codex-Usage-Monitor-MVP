$ErrorActionPreference = "Stop"
$oldGOOS = $env:GOOS
$oldGOARCH = $env:GOARCH
$oldCGO = $env:CGO_ENABLED

# 目的：建立 Windows x64 Collector 發布檔。
# 注意：此腳本只做可重現 Build，不執行需要真實 OAuth/Codex 登入的 Integration Gate。
Push-Location (Split-Path $PSScriptRoot -Parent)
try {
    go mod download
    if ($LASTEXITCODE -ne 0) { throw "go mod download failed" }
    go test ./...
    if ($LASTEXITCODE -ne 0) { throw "go test failed" }

    $env:GOOS = "windows"
    $env:GOARCH = "amd64"
    $env:CGO_ENABLED = "0"
    New-Item -ItemType Directory -Force -Path "dist" | Out-Null
    go build -trimpath -o "dist/codex-usage-monitor.exe" .
    if ($LASTEXITCODE -ne 0) { throw "Windows x64 build failed" }
    Write-Host "Build completed: collector/dist/codex-usage-monitor.exe"
}
finally {
    $env:GOOS = $oldGOOS
    $env:GOARCH = $oldGOARCH
    $env:CGO_ENABLED = $oldCGO
    Pop-Location
}
