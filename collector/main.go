package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"time"
)

func run(ctx context.Context) error {
	log.Print("Collector 啟動")
	cfg, err := LoadConfig()
	if err != nil {
		return err
	}
	return collectAndPublish(ctx, cfg, defaultPipeline())
}

type pipeline struct {
	read      func(context.Context, string) (map[string]any, map[string]any, error)
	normalize func(map[string]any, map[string]any, time.Time) (Payload, error)
	marshal   func(Payload) ([]byte, error)
	encrypt   func([]byte, []byte) ([]byte, error)
	publish   func(context.Context, Config, []byte) error
}

func defaultPipeline() pipeline {
	return pipeline{ReadCodexState, normalize, func(p Payload) ([]byte, error) { return json.Marshal(p) }, EncryptPackage, UpdateDriveFile}
}
func collectAndPublish(ctx context.Context, cfg Config, steps pipeline) error {
	account, rates, err := steps.read(ctx, cfg.CodexExecutable)
	if err != nil {
		return err
	}
	log.Print("Codex App Server / Account / Rate Limit 取得成功")
	payload, err := steps.normalize(account, rates, time.Now().UTC())
	if err != nil {
		return fmt.Errorf("Normalization: %w", err)
	}
	log.Print("Normalization 成功")
	plain, err := steps.marshal(payload)
	if err != nil {
		return fmt.Errorf("JSON Serialize: %w", err)
	}
	binary, err := steps.encrypt(plain, cfg.AESKey)
	if err != nil {
		return fmt.Errorf("Encryption: %w", err)
	}
	log.Print("Encryption 成功")
	if err = steps.publish(ctx, cfg, binary); err != nil {
		return err
	}
	log.Printf("Google Drive Upload 成功；固定 File ID 已更新: %s", cfg.DriveFileID)
	return nil
}
func main() {
	if len(os.Args) == 3 && os.Args[1] == "--test-url" {
		key, err := LoadAESKey()
		if err != nil {
			log.Printf("測試 Client 設定失敗: %v", err)
			os.Exit(1)
		}
		p, e := DownloadAndValidate(context.Background(), os.Args[2], key)
		if e != nil {
			log.Printf("測試 Client 驗證失敗: %v", e)
			os.Exit(1)
		}
		log.Printf("測試 Client 驗證成功：version=%d generatedAt=%s limits=%d", p.Version, p.GeneratedAt, len(p.Limits))
		return
	}
	if err := run(context.Background()); err != nil {
		log.Printf("本輪執行失敗: %v", err)
		os.Exit(1)
	}
	log.Print("本輪執行成功")
}
