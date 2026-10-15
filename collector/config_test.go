package main

import (
	"bytes"
	"testing"
)

func TestLoadAESKey(t *testing.T) {
	for _, value := range []string{"", "not-hex", "00", "00112233445566778899aabbccddeeff00"} {
		t.Run(value, func(t *testing.T) {
			t.Setenv("CODEX_MONITOR_AES_KEY", value)
			if _, err := LoadAESKey(); err == nil {
				t.Fatal("invalid key accepted")
			}
		})
	}
	t.Setenv("CODEX_MONITOR_AES_KEY", "00112233445566778899AABBCCDDEEFF")
	key, err := LoadAESKey()
	if err != nil || !bytes.Equal(key, []byte{0, 17, 34, 51, 68, 85, 102, 119, 136, 153, 170, 187, 204, 221, 238, 255}) {
		t.Fatalf("hex decode: %v", err)
	}
}

func TestLoadConfig(t *testing.T) {
	t.Setenv("CODEX_MONITOR_AES_KEY", "00112233445566778899aabbccddeeff")
	for _, name := range []string{"CODEX_MONITOR_DRIVE_FILE_ID", "CODEX_MONITOR_GOOGLE_CLIENT_ID", "CODEX_MONITOR_GOOGLE_CLIENT_SECRET"} {
		t.Setenv(name, "")
	}
	if _, err := LoadConfig(); err == nil {
		t.Fatal("missing Google config accepted")
	}
	t.Setenv("CODEX_MONITOR_DRIVE_FILE_ID", "test-file")
	t.Setenv("CODEX_MONITOR_GOOGLE_CLIENT_ID", "test-client")
	t.Setenv("CODEX_MONITOR_GOOGLE_CLIENT_SECRET", "test-only")
	t.Setenv("CODEX_MONITOR_GOOGLE_TOKEN_FILE", "")
	t.Setenv("CODEX_MONITOR_CODEX_PATH", "")
	t.Setenv("CODEX_MONITOR_GOOGLE_SCOPE", "")
	cfg, err := LoadConfig()
	if err != nil || cfg.TokenFile != "google-token.json" || cfg.CodexExecutable != "codex" || cfg.GoogleScope != driveFileScope {
		t.Fatalf("defaults: %+v %v", cfg, err)
	}
	t.Setenv("CODEX_MONITOR_GOOGLE_SCOPE", driveScope)
	cfg, err = LoadConfig()
	if err != nil || cfg.GoogleScope != driveScope {
		t.Fatal("explicit full Drive scope rejected")
	}
	t.Setenv("CODEX_MONITOR_GOOGLE_SCOPE", "drive")
	if _, err := LoadConfig(); err == nil {
		t.Fatal("invalid scope accepted")
	}
}

func TestLoadGoogleScope(t *testing.T) {
	for _, value := range []string{"", driveFileScope, driveScope} {
		t.Setenv("CODEX_MONITOR_GOOGLE_SCOPE", value)
		want := value
		if want == "" {
			want = driveFileScope
		}
		if got, err := LoadGoogleScope(); err != nil || got != want {
			t.Fatalf("scope %q: got %q, %v", value, got, err)
		}
	}
	for _, value := range []string{"drive", "drive.file", driveScope + ".readonly", " " + driveScope, driveFileScope + " " + driveScope, "https://example.invalid/scope"} {
		t.Setenv("CODEX_MONITOR_GOOGLE_SCOPE", value)
		if _, err := LoadGoogleScope(); err == nil {
			t.Fatalf("invalid scope %q accepted", value)
		}
	}
}
