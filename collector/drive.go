package main

import (
	"bytes"
	"context"
	"crypto/rand"
	"crypto/subtle"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"regexp"
	"sync/atomic"
	"time"

	"golang.org/x/oauth2"
	"golang.org/x/oauth2/google"
)

const driveFileScope = "https://www.googleapis.com/auth/drive.file"

var fileIDPattern = regexp.MustCompile(`^[A-Za-z0-9_-]+$`)

func oauthConfig(cfg Config) *oauth2.Config {
	return &oauth2.Config{ClientID: cfg.GoogleClientID, ClientSecret: cfg.GoogleSecret, Scopes: []string{driveFileScope}, Endpoint: google.Endpoint}
}
func loadToken(path string) (*oauth2.Token, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var token oauth2.Token
	if err = json.Unmarshal(data, &token); err != nil {
		return nil, errors.New("本機 OAuth token JSON 無效")
	}
	if token.AccessToken == "" && token.RefreshToken == "" {
		return nil, errors.New("本機 OAuth token 缺少 token")
	}
	return &token, nil
}
func saveToken(path string, token *oauth2.Token) error {
	data, err := json.Marshal(token)
	if err != nil {
		return err
	}
	file, err := os.CreateTemp(filepath.Dir(path), ".google-token-*.json.tmp")
	if err != nil {
		return err
	}
	name := file.Name()
	defer os.Remove(name)
	if _, err = file.Write(data); err != nil {
		_ = file.Close()
		return err
	}
	if err = file.Sync(); err != nil {
		_ = file.Close()
		return err
	}
	if err = file.Close(); err != nil {
		return err
	}
	return os.Rename(name, path)
}

type oauthResult struct {
	code string
	err  error
}

func randomOAuthState() (string, error) {
	data := make([]byte, 32)
	if _, err := rand.Read(data); err != nil {
		return "", err
	}
	return hex.EncodeToString(data), nil
}
func oauthCallbackHandler(state string, results chan<- oauthResult) http.Handler {
	var received atomic.Bool
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/" {
			http.NotFound(w, r)
			return
		}
		if r.Method != http.MethodGet {
			http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
			return
		}
		supplied := r.URL.Query().Get("state")
		if supplied == "" || subtle.ConstantTimeCompare([]byte(supplied), []byte(state)) != 1 {
			http.Error(w, "Invalid OAuth state", http.StatusBadRequest)
			return
		}
		result := oauthResult{code: r.URL.Query().Get("code")}
		if r.URL.Query().Get("error") != "" {
			result.err = errors.New("Google OAuth 授權遭拒絕")
		}
		if result.err == nil && result.code == "" {
			http.Error(w, "Missing code", http.StatusBadRequest)
			return
		}
		if !received.CompareAndSwap(false, true) {
			http.Error(w, "Callback already received", http.StatusConflict)
			return
		}
		select {
		case results <- result:
			if result.err != nil {
				http.Error(w, "Authorization failed", http.StatusBadRequest)
				return
			}
			_, _ = io.WriteString(w, "Codex Usage Monitor authorization completed. You may close this window.")
		default:
			http.Error(w, "Callback already received", http.StatusConflict)
		}
	})
}

// Desktop OAuth listens on a random loopback port. No login is started if an
// existing token file is corrupt; report the error without silently replacing it.
func EnsureToken(ctx context.Context, cfg Config) (*oauth2.Token, error) {
	token, err := loadToken(cfg.TokenFile)
	if err == nil {
		return token, nil
	}
	if !os.IsNotExist(err) {
		return nil, err
	}
	authCtx, cancel := context.WithTimeout(ctx, 5*time.Minute)
	defer cancel()
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		return nil, fmt.Errorf("OAuth loopback: %w", err)
	}
	defer listener.Close()
	state, err := randomOAuthState()
	if err != nil {
		return nil, err
	}
	results := make(chan oauthResult, 1)
	server := &http.Server{Handler: oauthCallbackHandler(state, results), ReadHeaderTimeout: 5 * time.Second}
	defer server.Close()
	serveError := make(chan error, 1)
	go func() {
		err := server.Serve(listener)
		if err != nil && !errors.Is(err, http.ErrServerClosed) {
			serveError <- err
		}
	}()
	config := oauthConfig(cfg)
	config.RedirectURL = "http://" + listener.Addr().String()
	verifier := oauth2.GenerateVerifier()
	authURL := config.AuthCodeURL(state, oauth2.AccessTypeOffline, oauth2.S256ChallengeOption(verifier))
	fmt.Printf("首次授權：請在本機瀏覽器開啟以下網址：\n%s\n", authURL)
	var result oauthResult
	select {
	case result = <-results:
		if result.err != nil {
			return nil, result.err
		}
	case err := <-serveError:
		return nil, err
	case <-authCtx.Done():
		return nil, authCtx.Err()
	}
	// Exchange errors can contain token endpoint bodies. Do not echo credentials.
	token, err = config.Exchange(authCtx, result.code, oauth2.VerifierOption(verifier))
	if err != nil {
		return nil, errors.New("OAuth code exchange 失敗")
	}
	if token.RefreshToken == "" {
		return nil, errors.New("OAuth 未回傳 refresh token，無法完成離線授權")
	}
	if err := saveToken(cfg.TokenFile, token); err != nil {
		return nil, fmt.Errorf("保存 OAuth token: %w", err)
	}
	return token, nil
}
func refreshedToken(ctx context.Context, cfg Config, token *oauth2.Token) (*oauth2.Token, error) {
	fresh, err := oauthConfig(cfg).TokenSource(ctx, token).Token()
	if err != nil {
		return nil, errors.New("更新 access token 失敗")
	}
	if fresh.RefreshToken == "" {
		fresh.RefreshToken = token.RefreshToken
	}
	if fresh.AccessToken != token.AccessToken || !fresh.Expiry.Equal(token.Expiry) || fresh.RefreshToken != token.RefreshToken {
		if err := saveToken(cfg.TokenFile, fresh); err != nil {
			return nil, fmt.Errorf("保存更新後 OAuth token: %w", err)
		}
	}
	return fresh, nil
}

// UpdateDriveFile sends one complete encrypted body to one fixed ID, using PATCH.
func UpdateDriveFile(ctx context.Context, cfg Config, data []byte) error {
	if !fileIDPattern.MatchString(cfg.DriveFileID) {
		return errors.New("Drive File ID 格式無效")
	}
	if _, err := DecryptPackage(data, cfg.AESKey); err != nil {
		return fmt.Errorf("拒絕發布無效 Binary: %w", err)
	}
	token, err := EnsureToken(ctx, cfg)
	if err != nil {
		return err
	}
	fresh, err := refreshedToken(ctx, cfg, token)
	if err != nil {
		return err
	}
	endpoint := "https://www.googleapis.com/upload/drive/v3/files/" + url.PathEscape(cfg.DriveFileID) + "?uploadType=media"
	request, err := http.NewRequestWithContext(ctx, http.MethodPatch, endpoint, bytes.NewReader(data))
	if err != nil {
		return err
	}
	request.Header.Set("Authorization", "Bearer "+fresh.AccessToken)
	request.Header.Set("Content-Type", "application/octet-stream")
	client := &http.Client{Transport: http.DefaultTransport, Timeout: 30 * time.Second, CheckRedirect: func(*http.Request, []*http.Request) error { return errors.New("Drive upload redirect 被拒絕") }}
	response, err := client.Do(request)
	if err != nil {
		return errors.New("Google Drive Update transport 失敗")
	}
	defer response.Body.Close()
	if response.StatusCode < 200 || response.StatusCode >= 300 {
		var apiError struct {
			Error struct {
				Code   int `json:"code"`
				Errors []struct {
					Reason string `json:"reason"`
				} `json:"errors"`
			} `json:"error"`
		}
		_ = json.NewDecoder(io.LimitReader(response.Body, 4096)).Decode(&apiError)
		// Preserve status and machine-readable reason, without logging arbitrary bodies.
		reason := "unknown"
		if len(apiError.Error.Errors) > 0 && fileIDPattern.MatchString(apiError.Error.Errors[0].Reason) {
			reason = apiError.Error.Errors[0].Reason
		}
		return fmt.Errorf("Google Drive Update HTTP %d; reason=%s", response.StatusCode, reason)
	}
	return nil
}
