package main

import (
	"bytes"
	"context"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"net/url"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"golang.org/x/oauth2"
)

type roundTripFunc func(*http.Request) (*http.Response, error)

func (f roundTripFunc) RoundTrip(r *http.Request) (*http.Response, error) { return f(r) }
func fakeResponse(status int, body string) *http.Response {
	return &http.Response{StatusCode: status, Header: make(http.Header), Body: io.NopCloser(strings.NewReader(body))}
}
func TestOAuthStateAndCallbacks(t *testing.T) {
	first, err := randomOAuthState()
	if err != nil {
		t.Fatal(err)
	}
	second, err := randomOAuthState()
	if err != nil || first == second || len(first) != 64 {
		t.Fatal("state must be random")
	}
	results := make(chan oauthResult, 1)
	handler := oauthCallbackHandler(first, results)
	for _, query := range []string{"code=test", "state=wrong&code=test", "state=" + first} {
		recorder := httptest.NewRecorder()
		handler.ServeHTTP(recorder, httptest.NewRequest("GET", "http://127.0.0.1/?"+query, nil))
		if recorder.Code != http.StatusBadRequest || len(results) != 0 {
			t.Fatal("invalid callback accepted")
		}
	}
	for i := 0; i < 3; i++ {
		recorder := httptest.NewRecorder()
		handler.ServeHTTP(recorder, httptest.NewRequest("GET", "http://127.0.0.1/?state="+first+"&code=test-code", nil))
		if i == 0 && recorder.Code != 200 {
			t.Fatal("valid callback rejected")
		}
		if i > 0 && recorder.Code != 409 {
			t.Fatal("duplicate callback not rejected")
		}
	}
	if result := <-results; result.code != "test-code" || result.err != nil {
		t.Fatal("code not returned")
	}
	denied := make(chan oauthResult, 1)
	recorder := httptest.NewRecorder()
	oauthCallbackHandler(first, denied).ServeHTTP(recorder, httptest.NewRequest("GET", "http://127.0.0.1/?state="+first+"&error=access_denied", nil))
	if recorder.Code != 400 || (<-denied).err == nil {
		t.Fatal("OAuth denial not surfaced")
	}
}
func TestOAuthDesktopRequestContract(t *testing.T) {
	config := oauthConfig(Config{GoogleClientID: "test-client", GoogleSecret: "test-secret"})
	config.RedirectURL = "http://127.0.0.1:12345"
	verifier := oauth2.GenerateVerifier()
	parsed, err := url.Parse(config.AuthCodeURL("random-state", oauth2.AccessTypeOffline, oauth2.S256ChallengeOption(verifier)))
	if err != nil {
		t.Fatal(err)
	}
	query := parsed.Query()
	if query.Get("scope") != driveFileScope || query.Get("redirect_uri") != config.RedirectURL || query.Get("state") != "random-state" || query.Get("access_type") != "offline" || query.Get("code_challenge_method") != "S256" || query.Get("code_challenge") == "" {
		t.Fatal("desktop request contract incorrect")
	}
}
func TestTokenRefreshAndFixedFileUpdate(t *testing.T) {
	cfg := Config{AESKey: []byte("0123456789abcdef"), DriveFileID: "fixed-test-id", GoogleClientID: "test-client", GoogleSecret: "test-only", TokenFile: filepath.Join(t.TempDir(), "google-token.json")}
	token := &oauth2.Token{AccessToken: "expired-test-token", RefreshToken: "test-refresh", Expiry: time.Now().Add(-time.Hour)}
	if err := saveToken(cfg.TokenFile, token); err != nil {
		t.Fatal(err)
	}
	updates, refreshes := 0, 0
	oldContent := []byte("previous-valid-binary")
	failUpload := false
	transport := roundTripFunc(func(request *http.Request) (*http.Response, error) {
		if request.URL.Host == "oauth2.googleapis.com" {
			refreshes++
			if err := request.ParseForm(); err != nil {
				t.Fatal(err)
			}
			if request.Form.Get("grant_type") != "refresh_token" || request.Form.Get("refresh_token") != "test-refresh" {
				t.Fatal("refresh contract incorrect")
			}
			response := fakeResponse(200, `{"access_token":"fresh-test-token","token_type":"Bearer","expires_in":3600}`)
			response.Header.Set("Content-Type", "application/json")
			return response, nil
		}
		updates++
		if request.Method != "PATCH" || request.URL.String() != "https://www.googleapis.com/upload/drive/v3/files/fixed-test-id?uploadType=media" || request.Header.Get("Content-Type") != "application/octet-stream" || request.Header.Get("Authorization") != "Bearer fresh-test-token" {
			t.Fatal("fixed ID PATCH contract incorrect")
		}
		data, err := io.ReadAll(request.Body)
		if err != nil {
			t.Fatal(err)
		}
		if len(data) == 0 {
			t.Fatal("empty update body")
		}
		if failUpload {
			return fakeResponse(403, `{"error":{"code":403,"errors":[{"reason":"insufficientFilePermissions"}]}}`), nil
		}
		oldContent = data
		return fakeResponse(200, `{"id":"fixed-test-id"}`), nil
	})
	original := http.DefaultTransport
	http.DefaultTransport = transport
	t.Cleanup(func() { http.DefaultTransport = original })
	ctx := context.WithValue(context.Background(), oauth2.HTTPClient, &http.Client{Transport: transport})
	for i := 0; i < 2; i++ {
		data, err := EncryptPackage(validPlain(t), cfg.AESKey)
		if err != nil {
			t.Fatal(err)
		}
		if err := UpdateDriveFile(ctx, cfg, data); err != nil {
			t.Fatal(err)
		}
	}
	cached, err := loadToken(cfg.TokenFile)
	if err != nil || cached.AccessToken != "fresh-test-token" || cached.RefreshToken != "test-refresh" || refreshes != 1 || updates != 2 {
		t.Fatalf("refresh persistence/count: %v", err)
	}
	before := append([]byte(nil), oldContent...)
	failUpload = true
	data, _ := EncryptPackage(validPlain(t), cfg.AESKey)
	if err := UpdateDriveFile(ctx, cfg, data); err == nil || !strings.Contains(err.Error(), "HTTP 403") || !strings.Contains(err.Error(), "insufficientFilePermissions") {
		t.Fatalf("upload error evidence: %v", err)
	}
	if !bytes.Equal(before, oldContent) || updates != 3 {
		t.Fatal("failed upload cleared old content or issued extra operation")
	}
}
func TestPublisherRejectsInvalidInputAndCorruptToken(t *testing.T) {
	cfg := Config{AESKey: []byte("0123456789abcdef"), DriveFileID: "fixed-id", TokenFile: filepath.Join(t.TempDir(), "google-token.json")}
	if err := os.WriteFile(cfg.TokenFile, []byte("{"), 0600); err != nil {
		t.Fatal(err)
	}
	data, _ := EncryptPackage(validPlain(t), cfg.AESKey)
	if _, err := EnsureToken(context.Background(), cfg); err == nil {
		t.Fatal("corrupt token accepted")
	}
	if err := UpdateDriveFile(context.Background(), cfg, data); err == nil {
		t.Fatal("corrupt token allowed publication")
	}
	if err := UpdateDriveFile(context.Background(), cfg, []byte("invalid")); err == nil {
		t.Fatal("invalid binary published")
	}
	cfg.DriveFileID = "../other?uploadType=multipart"
	if err := UpdateDriveFile(context.Background(), cfg, data); err == nil {
		t.Fatal("invalid file ID accepted")
	}
}
func TestTokenRefreshFailureDoesNotUpload(t *testing.T) {
	cfg := Config{AESKey: []byte("0123456789abcdef"), DriveFileID: "fixed-id", TokenFile: filepath.Join(t.TempDir(), "google-token.json")}
	token := &oauth2.Token{AccessToken: "expired", RefreshToken: "test-refresh", Expiry: time.Now().Add(-time.Hour)}
	if err := saveToken(cfg.TokenFile, token); err != nil {
		t.Fatal(err)
	}
	requests := 0
	transport := roundTripFunc(func(request *http.Request) (*http.Response, error) {
		requests++
		if request.URL.Host != "oauth2.googleapis.com" {
			t.Fatal("upload attempted after refresh failure")
		}
		response := fakeResponse(400, `{"error":"invalid_grant"}`)
		response.Header.Set("Content-Type", "application/json")
		return response, nil
	})
	ctx := context.WithValue(context.Background(), oauth2.HTTPClient, &http.Client{Transport: transport})
	data, _ := EncryptPackage(validPlain(t), cfg.AESKey)
	if err := UpdateDriveFile(ctx, cfg, data); err == nil || requests == 0 {
		t.Fatal("refresh failure ignored")
	}
	saved, err := os.ReadFile(cfg.TokenFile)
	if err != nil {
		t.Fatal(err)
	}
	var loaded oauth2.Token
	if err := json.Unmarshal(saved, &loaded); err != nil || loaded.RefreshToken != token.RefreshToken {
		t.Fatal("failed refresh corrupted token")
	}
}
