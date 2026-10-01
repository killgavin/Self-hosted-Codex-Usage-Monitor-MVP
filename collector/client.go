package main

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"time"
	"unicode/utf8"
)

const maxDownloadSize = 4 * 1024 * 1024

func validateHTTPSURL(value string) error {
	parsed, err := url.Parse(value)
	if err != nil || parsed.Scheme != "https" || parsed.Host == "" || parsed.Hostname() == "" || parsed.Opaque != "" || parsed.User != nil {
		return fmt.Errorf("測試 Client 僅接受有效 HTTPS URL")
	}
	return nil
}
func DownloadAndValidate(ctx context.Context, value string, key []byte) (Payload, error) {
	client := &http.Client{Transport: http.DefaultTransport, Timeout: 30 * time.Second}
	return downloadAndValidate(ctx, value, key, client)
}
func downloadAndValidate(ctx context.Context, value string, key []byte, client *http.Client) (Payload, error) {
	if err := validateHTTPSURL(value); err != nil {
		return Payload{}, err
	}
	safeClient := *client
	safeClient.CheckRedirect = func(request *http.Request, via []*http.Request) error {
		if len(via) >= 10 {
			return fmt.Errorf("HTTPS redirect 過多")
		}
		if err := validateHTTPSURL(request.URL.String()); err != nil {
			return err
		}
		if client.CheckRedirect != nil {
			return client.CheckRedirect(request, via)
		}
		return nil
	}
	request, err := http.NewRequestWithContext(ctx, http.MethodGet, value, nil)
	if err != nil {
		return Payload{}, err
	}
	response, err := safeClient.Do(request)
	if err != nil {
		return Payload{}, fmt.Errorf("HTTPS Download: %w", err)
	}
	defer response.Body.Close()
	if response.StatusCode < 200 || response.StatusCode >= 300 {
		return Payload{}, fmt.Errorf("HTTPS Download HTTP %d", response.StatusCode)
	}
	data, err := io.ReadAll(io.LimitReader(response.Body, maxDownloadSize+1))
	if err != nil {
		return Payload{}, err
	}
	if len(data) > maxDownloadSize {
		return Payload{}, fmt.Errorf("Binary 超過下載大小限制")
	}
	return validatePackage(data, key)
}
func validatePackage(data, key []byte) (Payload, error) {
	plain, err := DecryptPackage(data, key)
	if err != nil {
		return Payload{}, err
	}
	if !utf8.Valid(plain) {
		return Payload{}, fmt.Errorf("UTF-8 Decode 失敗")
	}
	var payload Payload
	if err := json.Unmarshal(plain, &payload); err != nil {
		return Payload{}, fmt.Errorf("JSON Parse 失敗: %w", err)
	}
	if payload.Version != 1 {
		return Payload{}, fmt.Errorf("不支援 JSON Version: %d", payload.Version)
	}
	if err := validateRequiredFields(plain); err != nil {
		return Payload{}, err
	}
	if _, err := timeParseRFC3339(payload.GeneratedAt); err != nil {
		return Payload{}, fmt.Errorf("generatedAt 非合法 ISO 8601")
	}
	if !payload.Account.Authenticated {
		return Payload{}, fmt.Errorf("必要 Account 狀態無效")
	}
	if len(payload.Limits) == 0 {
		return Payload{}, fmt.Errorf("必要欄位 limits 缺失")
	}
	for _, limit := range payload.Limits {
		for _, window := range []*Window{limit.Primary, limit.Secondary} {
			if window == nil {
				continue
			}
			remaining, err := remainingPercent(window.UsedPercent)
			if err != nil || remaining != window.RemainingPercent {
				return Payload{}, fmt.Errorf("Window 百分比無效")
			}
			if window.ResetAt != nil {
				if _, err := timeParseRFC3339(*window.ResetAt); err != nil {
					return Payload{}, fmt.Errorf("resetAt 無效")
				}
			}
		}
	}
	if payload.ResetCredits != nil {
		if payload.ResetCredits.AvailableCount < 0 {
			return Payload{}, fmt.Errorf("availableCount 無效")
		}
		if payload.ResetCredits.Credits != nil {
			for _, credit := range *payload.ResetCredits.Credits {
				if _, err := timeParseRFC3339(credit.GrantedAt); err != nil {
					return Payload{}, fmt.Errorf("grantedAt 無效")
				}
				if credit.ExpiresAt != nil {
					if _, err := timeParseRFC3339(*credit.ExpiresAt); err != nil {
						return Payload{}, fmt.Errorf("expiresAt 無效")
					}
				}
			}
		}
	}
	// V1 specification explicitly excludes a stale threshold.
	return payload, nil
}
func requiredObject(raw json.RawMessage, fields ...string) (map[string]json.RawMessage, error) {
	var object map[string]json.RawMessage
	if err := json.Unmarshal(raw, &object); err != nil || object == nil {
		return nil, fmt.Errorf("必要 JSON object 無效")
	}
	for _, field := range fields {
		if _, ok := object[field]; !ok {
			return nil, fmt.Errorf("必要欄位 %s 缺失", field)
		}
	}
	return object, nil
}
func nonNull(object map[string]json.RawMessage, fields ...string) error {
	for _, field := range fields {
		if string(object[field]) == "null" {
			return fmt.Errorf("必要欄位 %s 不得為 null", field)
		}
	}
	return nil
}
func validateRequiredFields(plain []byte) error {
	root, err := requiredObject(plain, "version", "generatedAt", "account", "limits", "resetCredits")
	if err != nil {
		return err
	}
	if err := nonNull(root, "version", "generatedAt", "account", "limits"); err != nil {
		return err
	}
	account, err := requiredObject(root["account"], "authenticated", "authMode", "planType")
	if err != nil {
		return err
	}
	if err := nonNull(account, "authenticated"); err != nil {
		return err
	}
	var limits []json.RawMessage
	if err := json.Unmarshal(root["limits"], &limits); err != nil {
		return err
	}
	for _, raw := range limits {
		limit, err := requiredObject(raw, "id", "name", "primary", "secondary", "reachedType")
		if err != nil {
			return err
		}
		for _, field := range []string{"primary", "secondary"} {
			if string(limit[field]) == "null" {
				continue
			}
			window, err := requiredObject(limit[field], "usedPercent", "remainingPercent", "windowDurationMinutes", "resetAt")
			if err != nil {
				return err
			}
			if err := nonNull(window, "usedPercent", "remainingPercent"); err != nil {
				return err
			}
		}
	}
	if string(root["resetCredits"]) == "null" {
		return nil
	}
	credits, err := requiredObject(root["resetCredits"], "availableCount", "credits")
	if err != nil {
		return err
	}
	if err := nonNull(credits, "availableCount"); err != nil {
		return err
	}
	if string(credits["credits"]) == "null" {
		return nil
	}
	var details []json.RawMessage
	if err := json.Unmarshal(credits["credits"], &details); err != nil {
		return err
	}
	for _, raw := range details {
		credit, err := requiredObject(raw, "id", "status", "grantedAt", "expiresAt", "title", "description")
		if err != nil {
			return err
		}
		if err := nonNull(credit, "id", "status", "grantedAt"); err != nil {
			return err
		}
	}
	return nil
}
