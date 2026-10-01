package main

import (
	"context"
	"crypto/rand"
	"debug/pe"
	"encoding/json"
	"os"
	"os/exec"
	"path/filepath"
	"testing"
	"time"
)

func redactLive(value any, key string) any {
	switch data := value.(type) {
	case map[string]any:
		result := make(map[string]any, len(data))
		for name, value := range data {
			result[name] = redactLive(value, name)
		}
		return result
	case []any:
		result := make([]any, len(data))
		for i, value := range data {
			result[i] = redactLive(value, key)
		}
		return result
	case string:
		switch key {
		case "type", "authMode", "planType", "limitId", "limitName", "status", "rateLimitReachedType", "reachedType", "generatedAt", "usedPercent", "remainingPercent", "resetAt", "grantedAt", "expiresAt":
			return data
		case "id", "name":
			if data == "codex" || data == "base_model_inference" || data == "gpt-reserve" {
				return data
			}
		}
		return "[REDACTED]"
	default:
		return value
	}
}
func TestLiveCodexGate(t *testing.T) {
	if os.Getenv("CODEX_MONITOR_LIVE_GATE") != "1" {
		t.Skip("opt-in real Windows Codex gate")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 45*time.Second)
	defer cancel()
	account, rates, err := ReadCodexState(ctx, envOr("CODEX_MONITOR_CODEX_PATH", "codex"))
	if err != nil {
		t.Fatal(err)
	}
	p, err := normalize(account, rates, time.Now().UTC())
	if err != nil {
		t.Fatal(err)
	}
	plain, err := json.Marshal(p)
	if err != nil {
		t.Fatal(err)
	}
	key := make([]byte, 16)
	if _, err := rand.Read(key); err != nil {
		t.Fatal(err)
	}
	binary, err := EncryptPackage(plain, key)
	if err != nil {
		t.Fatal(err)
	}
	if _, err := validatePackage(binary, key); err != nil {
		t.Fatal(err)
	}
	var normalized any
	if err := json.Unmarshal(plain, &normalized); err != nil {
		t.Fatal(err)
	}
	report := map[string]any{
		"capturedAt":        time.Now().UTC().Format(time.RFC3339),
		"protocol":          []string{"initialize: PASS", "initialized: PASS (sent; notification has no response)", "account/read: PASS", "account/rateLimits/read: PASS", "normalization: PASS", "AES/client validation: PASS"},
		"accountResponse":   redactLive(account, ""),
		"rateLimitResponse": redactLive(rates, ""),
		"normalizedPayload": redactLive(normalized, ""),
	}
	data, err := json.MarshalIndent(report, "", "  ")
	if err != nil {
		t.Fatal(err)
	}
	if output := os.Getenv("CODEX_MONITOR_LIVE_EVIDENCE"); output != "" {
		if err := os.MkdirAll(filepath.Dir(output), 0755); err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(output, append(data, '\n'), 0600); err != nil {
			t.Fatal(err)
		}
	}
	t.Logf("real account authenticated=%t; requiresOpenaiAuth=%v; limits=%d; resetCreditsPresent=%t", p.Account.Authenticated, account["requiresOpenaiAuth"], len(p.Limits), p.ResetCredits != nil)
}
func TestBuiltWindowsBinary(t *testing.T) {
	if os.Getenv("CODEX_MONITOR_BINARY_GATE") != "1" {
		t.Skip("opt-in built Windows binary gate")
	}
	path := filepath.Join("dist", "codex-usage-monitor.exe")
	file, err := pe.Open(path)
	if err != nil {
		t.Fatal(err)
	}
	defer file.Close()
	if file.Machine != pe.IMAGE_FILE_MACHINE_AMD64 {
		t.Fatal("artifact is not Windows x64")
	}
	command := exec.Command(path, "--test-url", "http://example.invalid/file")
	// Test-only key, never the production key.
	command.Env = append(os.Environ(), "CODEX_MONITOR_AES_KEY=00112233445566778899aabbccddeeff")
	output, err := command.CombinedOutput()
	if err == nil {
		t.Fatal("built Client accepted HTTP")
	}
	t.Logf("PE machine=AMD64; actual executable rejected HTTP (exit nonzero); output bytes=%d", len(output))
}
