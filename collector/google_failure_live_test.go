package main

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

// This opt-in gate injects an invalid bearer credential into one actual PATCH.
// Its body is the existing valid Binary, so even unexpected success cannot
// replace the content with a different or corrupt package. Synthetic credentials
// are never persisted; normal access-token refresh still uses the real token.
func TestLiveGoogleDriveFailureGate(t *testing.T) {
	if os.Getenv("CODEX_MONITOR_DRIVE_FAILURE_LIVE_GATE") != "1" {
		t.Skip("opt-in real Drive failure and previous-content preservation gate")
	}
	config, err := googleDesktopConfig(os.Getenv("CODEX_MONITOR_GOOGLE_CREDENTIALS_FILE"), os.Getenv("CODEX_MONITOR_GOOGLE_TOKEN_FILE"))
	if err != nil {
		t.Fatal(err)
	}
	config.DriveFileID = os.Getenv("CODEX_MONITOR_DRIVE_FILE_ID")
	config.AESKey, err = LoadAESKey()
	if err != nil || !fileIDPattern.MatchString(config.DriveFileID) {
		t.Fatal("a valid AES key and explicit Drive File ID are required")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Minute)
	defer cancel()
	token, err := loadToken(config.TokenFile)
	if err != nil {
		t.Fatal("an existing authorized token is required")
	}
	token, err = refreshedToken(ctx, config, token)
	if err != nil {
		t.Fatal(err)
	}
	original := http.DefaultTransport
	client := &http.Client{Transport: original, Timeout: 30 * time.Second, CheckRedirect: func(*http.Request, []*http.Request) error {
		return errors.New("unexpected authenticated media redirect")
	}}
	readRemote := func() []byte {
		t.Helper()
		request, err := http.NewRequestWithContext(ctx, http.MethodGet, "https://www.googleapis.com/drive/v3/files/"+config.DriveFileID+"?alt=media", nil)
		if err != nil {
			t.Fatal(err)
		}
		request.Header.Set("Authorization", "Bearer "+token.AccessToken)
		response, err := client.Do(request)
		if err != nil {
			t.Fatal("authenticated Binary download failed")
		}
		defer response.Body.Close()
		if response.StatusCode != http.StatusOK {
			t.Fatalf("authenticated Binary download HTTP %d", response.StatusCode)
		}
		data, err := io.ReadAll(io.LimitReader(response.Body, maxDownloadSize+1))
		if err != nil || len(data) > maxDownloadSize {
			t.Fatal("invalid downloaded Binary size")
		}
		if _, err := validatePackage(data, config.AESKey); err != nil {
			t.Fatal("remote content is not a valid authenticated V1 package")
		}
		return data
	}
	before := readRemote()
	requests, status := 0, 0
	var responseBody json.RawMessage
	http.DefaultTransport = roundTripFunc(func(request *http.Request) (*http.Response, error) {
		if request.URL.Scheme == "https" && request.URL.Host == "oauth2.googleapis.com" {
			return original.RoundTrip(request)
		}
		if request.Method != http.MethodPatch || request.URL.Scheme != "https" || request.URL.Host != "www.googleapis.com" || request.URL.Path != "/upload/drive/v3/files/"+config.DriveFileID || request.URL.Query().Get("uploadType") != "media" {
			return nil, errors.New("failure gate refused an unexpected Drive request")
		}
		requests++
		request.Header.Set("Authorization", "Bearer synthetic-invalid-live-gate-token")
		response, err := original.RoundTrip(request)
		if err != nil {
			return nil, err
		}
		status = response.StatusCode
		body, err := io.ReadAll(io.LimitReader(response.Body, 4096))
		_ = response.Body.Close()
		if err != nil {
			return nil, err
		}
		response.Body = io.NopCloser(bytes.NewReader(body))
		masked := []byte(strings.ReplaceAll(string(body), config.DriveFileID, "[REDACTED FILE ID]"))
		if json.Valid(masked) {
			responseBody = masked
		}
		return response, nil
	})
	defer func() { http.DefaultTransport = original }()
	updateError := UpdateDriveFile(ctx, config, before)
	http.DefaultTransport = original
	after := readRemote()
	beforeHash, afterHash := sha256.Sum256(before), sha256.Sum256(after)
	passed := updateError != nil && requests == 1 && status == http.StatusUnauthorized && bytes.Equal(before, after)
	if evidence := os.Getenv("CODEX_MONITOR_DRIVE_FAILURE_LIVE_EVIDENCE"); evidence != "" {
		result := "FAIL"
		if passed {
			result = "PASS"
		}
		report := map[string]any{
			"capturedAt": time.Now().UTC().Format(time.RFC3339), "result": result,
			"fileID": "[REDACTED]", "requestedScope": config.GoogleScope,
			"faultInjection": "replace bearer credential on one real media PATCH; retain existing valid Binary body",
			"patchRequests":  requests, "httpStatus": status, "response": responseBody,
			"beforeSHA256": hex.EncodeToString(beforeHash[:]), "afterSHA256": hex.EncodeToString(afterHash[:]),
			"remoteBytesUnchanged": bytes.Equal(before, after), "beforeAndAfterPackagesValidated": true,
			"tokenFileReplacedByFault": false, "deleteOrCreateRequests": 0,
		}
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
	if !passed {
		t.Fatalf("expected one rejected PATCH and unchanged remote content: requests=%d HTTP=%d error=%t same=%t", requests, status, updateError != nil, bytes.Equal(before, after))
	}
	t.Log("Real Google HTTP 401; same File ID still downloads the identical, valid encrypted Binary")
}
