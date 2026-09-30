package main

import (
 "encoding/hex"
 "errors"
 "fmt"
 "os"
)

type Config struct {
 AESKey []byte
 DriveFileID string
 GoogleClientID string
 GoogleSecret string
 TokenFile string
 CodexExecutable string
}

func LoadConfig() (Config,error) {
 key,err:=hex.DecodeString(os.Getenv("CODEX_MONITOR_AES_KEY"))
 if err!=nil || len(key)!=16 { return Config{},errors.New("CODEX_MONITOR_AES_KEY 必須是 32 個 Hex 字元（16 bytes）") }
 cfg:=Config{AESKey:key,DriveFileID:os.Getenv("CODEX_MONITOR_DRIVE_FILE_ID"),GoogleClientID:os.Getenv("CODEX_MONITOR_GOOGLE_CLIENT_ID"),GoogleSecret:os.Getenv("CODEX_MONITOR_GOOGLE_CLIENT_SECRET"),TokenFile:envOr("CODEX_MONITOR_GOOGLE_TOKEN_FILE","google-token.json"),CodexExecutable:envOr("CODEX_MONITOR_CODEX_PATH","codex")}
 if cfg.DriveFileID==""||cfg.GoogleClientID==""||cfg.GoogleSecret=="" { return Config{},fmt.Errorf("缺少 Google Drive 設定環境變數") }
 return cfg,nil
}
func envOr(name,fallback string)string{if v:=os.Getenv(name);v!=""{return v};return fallback}
