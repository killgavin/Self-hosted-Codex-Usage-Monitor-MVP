package main

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

// This test-only loader reads a downloaded Desktop App credentials file.
// Production configuration continues to come from its existing environment variables.
func googleDesktopConfig(path, tokenFile string) (Config, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return Config{}, errors.New("cannot read Desktop OAuth credentials file")
	}
	var document struct {
		Installed *struct {
			ClientID     string `json:"client_id"`
			ClientSecret string `json:"client_secret"`
			AuthURI      string `json:"auth_uri"`
			TokenURI     string `json:"token_uri"`
		} `json:"installed"`
	}
	if err := json.Unmarshal(data, &document); err != nil {
		return Config{}, errors.New("invalid Desktop OAuth credentials JSON")
	}
	installed := document.Installed
	if installed == nil || installed.ClientID == "" || installed.ClientSecret == "" {
		return Config{}, errors.New("Desktop OAuth installed client credentials are required")
	}
	if installed.TokenURI != "https://oauth2.googleapis.com/token" ||
		(installed.AuthURI != "https://accounts.google.com/o/oauth2/auth" && installed.AuthURI != "https://accounts.google.com/o/oauth2/v2/auth") {
		return Config{}, errors.New("unexpected Google OAuth endpoints")
	}
	if tokenFile == "" {
		return Config{}, errors.New("explicit local token file is required")
	}
	scope, err := LoadGoogleScope()
	if err != nil {
		return Config{}, err
	}
	return Config{GoogleClientID: installed.ClientID, GoogleSecret: installed.ClientSecret, GoogleScope: scope, TokenFile: tokenFile}, nil
}

func TestGoogleDesktopConfig(t *testing.T) {
	path := filepath.Join(t.TempDir(), "credentials.json")
	for _, source := range []string{
		`{`, `{"web":{"client_id":"test","client_secret":"test"}}`,
		`{"installed":{"client_id":"test"}}`,
		`{"installed":{"client_id":"test","client_secret":"test","auth_uri":"https://example.invalid/auth","token_uri":"https://example.invalid/token"}}`,
	} {
		if err := os.WriteFile(path, []byte(source), 0600); err != nil {
			t.Fatal(err)
		}
		if _, err := googleDesktopConfig(path, "token.json"); err == nil {
			t.Fatal("invalid credentials accepted")
		}
	}
	source := `{"installed":{"client_id":"synthetic-client","client_secret":"synthetic-secret","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token"}}`
	if err := os.WriteFile(path, []byte(source), 0600); err != nil {
		t.Fatal(err)
	}
	config, err := googleDesktopConfig(path, "token.json")
	if err != nil || config.GoogleClientID != "synthetic-client" || config.GoogleSecret != "synthetic-secret" || config.TokenFile != "token.json" {
		t.Fatal("valid Desktop credentials rejected")
	}
	if _, err := googleDesktopConfig(path, ""); err == nil {
		t.Fatal("implicit token path accepted")
	}
}

func TestLiveGoogleOAuthGate(t *testing.T) {
	if os.Getenv("CODEX_MONITOR_GOOGLE_LIVE_GATE") != "1" {
		t.Skip("opt-in real Google Desktop OAuth gate; no Drive writes")
	}
	config, err := googleDesktopConfig(os.Getenv("CODEX_MONITOR_GOOGLE_CREDENTIALS_FILE"), os.Getenv("CODEX_MONITOR_GOOGLE_TOKEN_FILE"))
	if err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithTimeout(context.Background(), 6*time.Minute)
	defer cancel()
	token, err := EnsureToken(ctx, config)
	if err != nil {
		t.Fatal(err)
	}
	if token.AccessToken == "" || token.RefreshToken == "" {
		t.Fatal("OAuth access and refresh tokens are both required")
	}
	// Expire only the in-memory copy to exercise the production refresh path.
	expired := *token
	expired.Expiry = time.Now().Add(-time.Hour)
	fresh, err := refreshedToken(ctx, config, &expired)
	if err != nil {
		t.Fatal(err)
	}
	if !fresh.Valid() || fresh.RefreshToken == "" {
		t.Fatal("refreshed OAuth token is invalid")
	}
	saved, err := loadToken(config.TokenFile)
	if err != nil || saved.AccessToken != fresh.AccessToken || saved.RefreshToken != fresh.RefreshToken {
		t.Fatal("refreshed token was not persisted")
	}
	if evidence := os.Getenv("CODEX_MONITOR_GOOGLE_LIVE_EVIDENCE"); evidence != "" {
		report := map[string]any{"capturedAt": time.Now().UTC().Format(time.RFC3339), "desktopCredentials": "PASS", "tokenAcquisition": "PASS", "refreshToken": "PASS", "tokenPersistence": "PASS", "scope": config.GoogleScope, "driveRequestsSent": 0}
		data, err := json.MarshalIndent(report, "", "  ")
		if err != nil {
			t.Fatal(err)
		}
		if err := os.MkdirAll(filepath.Dir(evidence), 0755); err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(evidence, append(data, '\n'), 0600); err != nil {
			t.Fatal(err)
		}
	}
	t.Log("Google Desktop OAuth token acquisition, refresh and local persistence: PASS; no Drive writes")
}

// Opt-in only: publish two current Codex snapshots through the production pipeline.
// The observer permits media PATCH to the one explicitly supplied ID and preserves
// redacted Google response bodies, including failures, without changing the publisher.
func TestLiveGoogleDrivePublishGate(t *testing.T) {
	if os.Getenv("CODEX_MONITOR_DRIVE_LIVE_GATE") != "1" {
		t.Skip("opt-in real fixed-file Drive publication gate")
	}
	config, err := googleDesktopConfig(os.Getenv("CODEX_MONITOR_GOOGLE_CREDENTIALS_FILE"), os.Getenv("CODEX_MONITOR_GOOGLE_TOKEN_FILE"))
	if err != nil {
		t.Fatal(err)
	}
	config.DriveFileID = os.Getenv("CODEX_MONITOR_DRIVE_FILE_ID")
	config.CodexExecutable = envOr("CODEX_MONITOR_CODEX_PATH", "codex")
	config.AESKey, err = LoadAESKey()
	if err != nil || !fileIDPattern.MatchString(config.DriveFileID) {
		t.Fatal("a valid AES key and explicit Drive File ID are required")
	}
	original := http.DefaultTransport
	var attempts []map[string]any
	http.DefaultTransport = roundTripFunc(func(request *http.Request) (*http.Response, error) {
		if request.URL.Scheme == "https" && request.URL.Host == "oauth2.googleapis.com" {
			return original.RoundTrip(request) // Never record token endpoint bodies.
		}
		if request.Method != http.MethodPatch || request.URL.Scheme != "https" || request.URL.Host != "www.googleapis.com" || request.URL.Path != "/upload/drive/v3/files/"+config.DriveFileID || request.URL.Query().Get("uploadType") != "media" {
			return nil, errors.New("live gate refused an unexpected Drive request")
		}
		data, err := io.ReadAll(request.Body)
		_ = request.Body.Close()
		if err != nil {
			return nil, err
		}
		request.Body = io.NopCloser(bytes.NewReader(data))
		if _, err := validatePackage(data, config.AESKey); err != nil {
			return nil, errors.New("live gate refused an invalid encrypted Payload")
		}
		attempt := map[string]any{"method": "PATCH", "fileID": "[REDACTED]", "binarySchemaValidated": true, "binaryBytes": len(data)}
		attempts = append(attempts, attempt)
		response, err := original.RoundTrip(request)
		if err != nil {
			attempt["transportFailure"] = true
			return nil, err
		}
		body, err := io.ReadAll(response.Body)
		_ = response.Body.Close()
		if err != nil {
			return nil, err
		}
		response.Body = io.NopCloser(bytes.NewReader(body))
		attempt["httpStatus"] = response.StatusCode
		masked := strings.ReplaceAll(string(body), config.DriveFileID, "[REDACTED FILE ID]")
		if json.Valid([]byte(masked)) {
			attempt["response"] = json.RawMessage(masked)
		} else {
			attempt["response"] = masked
		}
		if response.StatusCode >= 200 && response.StatusCode < 300 {
			var file struct {
				ID string `json:"id"`
			}
			if err := json.Unmarshal(body, &file); err != nil || file.ID != config.DriveFileID {
				return nil, errors.New("Google response did not confirm the original File ID")
			}
			attempt["returnedFileIDMatchesOriginal"] = true
		}
		return response, nil
	})
	defer func() { http.DefaultTransport = original }()
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Minute)
	defer cancel()
	completed := 0
	for i := 0; i < 2; i++ {
		if err = collectAndPublish(ctx, config, defaultPipeline()); err != nil {
			break
		}
		completed++
	}
	if evidence := os.Getenv("CODEX_MONITOR_DRIVE_LIVE_EVIDENCE"); evidence != "" {
		result := "PASS"
		if err != nil {
			result = "FAIL"
		}
		report := map[string]any{"capturedAt": time.Now().UTC().Format(time.RFC3339), "requestedScope": config.GoogleScope, "originalFileID": "[REDACTED]", "result": result, "completedUpdates": completed, "attempts": attempts, "deleteOrCreateRequests": 0}
		if err != nil {
			report["collectorError"] = strings.ReplaceAll(err.Error(), config.DriveFileID, "[REDACTED FILE ID]")
		}
		data, marshalErr := json.MarshalIndent(report, "", "  ")
		if marshalErr != nil {
			t.Fatal(marshalErr)
		}
		if mkdirErr := os.MkdirAll(filepath.Dir(evidence), 0755); mkdirErr != nil {
			t.Fatal(mkdirErr)
		}
		if writeErr := os.WriteFile(evidence, append(data, '\n'), 0600); writeErr != nil {
			t.Fatal(writeErr)
		}
	}
	if err != nil {
		t.Fatal(fmt.Errorf("live Drive publication failed: %w", err))
	}
	if completed != 2 || len(attempts) != 2 {
		t.Fatal("two updates to the original File ID were not confirmed")
	}
	t.Log("Two production-pipeline updates confirmed the same File ID; public HTTPS and old-file failure verification remain separate gates")
}
