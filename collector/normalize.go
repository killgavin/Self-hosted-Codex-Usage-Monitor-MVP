package main

import (
	"encoding/json"
	"fmt"
	"strconv"
	"time"
)

type Window struct {
	UsedPercent           string  `json:"usedPercent"`
	RemainingPercent      string  `json:"remainingPercent"`
	WindowDurationMinutes *int64  `json:"windowDurationMinutes"`
	ResetAt               *string `json:"resetAt"`
}
type Limit struct {
	ID          string  `json:"id"`
	Name        *string `json:"name"`
	Primary     *Window `json:"primary"`
	Secondary   *Window `json:"secondary"`
	ReachedType *string `json:"reachedType"`
}
type ResetCredit struct {
	ID          string  `json:"id"`
	Status      string  `json:"status"`
	GrantedAt   string  `json:"grantedAt"`
	ExpiresAt   *string `json:"expiresAt"`
	Title       *string `json:"title"`
	Description *string `json:"description"`
}
type ResetCredits struct {
	AvailableCount int            `json:"availableCount"`
	Credits        *[]ResetCredit `json:"credits"`
}
type Account struct {
	Authenticated bool    `json:"authenticated"`
	AuthMode      *string `json:"authMode"`
	PlanType      *string `json:"planType"`
}
type Payload struct {
	Version      int           `json:"version"`
	GeneratedAt  string        `json:"generatedAt"`
	Account      Account       `json:"account"`
	Limits       []Limit       `json:"limits"`
	ResetCredits *ResetCredits `json:"resetCredits"`
}

// normalize 沿用舊 MVP 已驗證的公開 contract；來源不存在的 optional 欄位保持 null，不猜值。
func normalize(accountResp, rateResp map[string]any, now time.Time) (Payload, error) {
	acct, _ := accountResp["account"].(map[string]any)
	requires, _ := accountResp["requiresOpenaiAuth"].(bool)
	if acct == nil || requires {
		return Payload{}, fmt.Errorf("Codex 尚未登入")
	}
	account := Account{Authenticated: true, AuthMode: stringPtr(acct["type"]), PlanType: stringPtr(acct["planType"])}
	type rawLimit struct {
		id string
		v  map[string]any
	}
	raw := []rawLimit{}
	if by, ok := rateResp["rateLimitsByLimitId"].(map[string]any); ok && len(by) > 0 {
		for id, v := range by {
			if m, ok := v.(map[string]any); ok {
				raw = append(raw, rawLimit{id, m})
			}
		}
	} else if m, ok := rateResp["rateLimits"].(map[string]any); ok {
		raw = append(raw, rawLimit{"", m})
	}
	if len(raw) == 0 {
		return Payload{}, fmt.Errorf("Rate Limit response 無可正規化資料")
	}
	limits := make([]Limit, 0, len(raw))
	for _, item := range raw {
		id := stringValue(item.v["limitId"])
		if id == "" {
			id = item.id
		}
		limits = append(limits, Limit{ID: id, Name: stringPtr(item.v["limitName"]), Primary: normalizeWindow(item.v["primary"]), Secondary: normalizeWindow(item.v["secondary"]), ReachedType: stringPtr(item.v["rateLimitReachedType"])})
	}
	return Payload{Version: 1, GeneratedAt: now.Format(time.RFC3339), Account: account, Limits: limits, ResetCredits: normalizeCredits(rateResp["rateLimitResetCredits"])}, nil
}
func normalizeWindow(v any) *Window {
	m, ok := v.(map[string]any)
	if !ok {
		return nil
	}
	used, ok := numberText(m["usedPercent"])
	if !ok {
		return nil
	}
	f, e := strconv.ParseFloat(used, 64)
	if e != nil {
		return nil
	}
	remaining := 100 - f
	if remaining < 0 {
		remaining = 0
	}
	if remaining > 100 {
		remaining = 100
	}
	var duration *int64
	if x, ok := int64Value(m["windowDurationMins"]); ok {
		duration = &x
	}
	return &Window{UsedPercent: used, RemainingPercent: strconv.FormatFloat(remaining, 'f', -1, 64), WindowDurationMinutes: duration, ResetAt: unixISO(m["resetsAt"])}
}
func normalizeCredits(v any) *ResetCredits {
	m, ok := v.(map[string]any)
	if !ok {
		return nil
	}
	count := 0
	if x, ok := int64Value(m["availableCount"]); ok {
		count = int(x)
	}
	r := &ResetCredits{AvailableCount: count}
	if raw, exists := m["credits"]; exists {
		if raw == nil {
			r.Credits = nil
		} else if a, ok := raw.([]any); ok {
			items := make([]ResetCredit, 0, len(a))
			for _, v := range a {
				if c, ok := v.(map[string]any); ok {
					items = append(items, ResetCredit{ID: stringValue(c["id"]), Status: stringValue(c["status"]), GrantedAt: valueISO(c["grantedAt"]), ExpiresAt: unixISO(c["expiresAt"]), Title: stringPtr(c["title"]), Description: stringPtr(c["description"])})
				}
			}
			r.Credits = &items
		}
	}
	return r
}
func numberText(v any) (string, bool) {
	switch n := v.(type) {
	case json.Number:
		return n.String(), true
	case float64:
		return strconv.FormatFloat(n, 'f', -1, 64), true
	default:
		return "", false
	}
}
func unixISO(v any) *string {
	s, ok := numberText(v)
	if !ok {
		return nil
	}
	n, e := strconv.ParseInt(s, 10, 64)
	if e != nil {
		return nil
	}
	x := time.Unix(n, 0).UTC().Format(time.RFC3339)
	return &x
}
func valueISO(v any) string {
	if p := unixISO(v); p != nil {
		return *p
	}
	return ""
}
func stringValue(v any) string { s, _ := v.(string); return s }
func stringPtr(v any) *string {
	s, ok := v.(string)
	if !ok {
		return nil
	}
	return &s
}

func int64Value(v any) (int64, bool) {
	s, ok := numberText(v)
	if !ok {
		return 0, false
	}
	if x, e := strconv.ParseInt(s, 10, 64); e == nil {
		return x, true
	}
	if f, e := strconv.ParseFloat(s, 64); e == nil {
		return int64(f), true
	}
	return 0, false
}
