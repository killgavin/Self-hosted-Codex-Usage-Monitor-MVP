package main

import (
	"encoding/json"
	"fmt"
	"math/big"
	"sort"
	"strconv"
	"strings"
	"time"
)

type Window struct {
	UsedPercent           string  `json:"usedPercent"`
	RemainingPercent      string  `json:"remainingPercent"`
	WindowDurationMinutes *int64  `json:"windowDurationMinutes"`
	ResetAt               *string `json:"resetAt"`
}
type Limit struct {
	ID          *string `json:"id"`
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

// Preserve the verified MVP contract, including decimal strings and nullable identity.
// requiresOpenaiAuth describes the provider, not whether the account is logged in.
func normalize(accountResp, rateResp map[string]any, now time.Time) (Payload, error) {
	acct, ok := accountResp["account"].(map[string]any)
	if !ok || acct == nil {
		return Payload{}, fmt.Errorf("Codex 尚未登入或 account 無效")
	}
	authMode, err := optionalString(acct["type"])
	if err != nil {
		return Payload{}, err
	}
	planType, err := optionalString(acct["planType"])
	if err != nil {
		return Payload{}, err
	}
	limits := make([]Limit, 0)
	if by, present := rateResp["rateLimitsByLimitId"]; present && by != nil {
		keyed, ok := by.(map[string]any)
		if !ok {
			return Payload{}, fmt.Errorf("rateLimitsByLimitId 格式無效")
		}
		ids := make([]string, 0, len(keyed))
		for id := range keyed {
			ids = append(ids, id)
		}
		sort.Strings(ids)
		for _, id := range ids {
			limit, err := normalizeLimit(keyed[id], &id)
			if err != nil {
				return Payload{}, fmt.Errorf("Limit %s: %w", id, err)
			}
			limits = append(limits, limit)
		}
	}
	if len(limits) == 0 {
		limit, err := normalizeLimit(rateResp["rateLimits"], nil)
		if err != nil {
			return Payload{}, fmt.Errorf("Rate Limit response: %w", err)
		}
		limits = append(limits, limit)
	}
	// The output identity, rather than map iteration, defines stable ordering.
	sort.SliceStable(limits, func(i, j int) bool {
		return stringValue(limits[i].ID) < stringValue(limits[j].ID)
	})
	credits, err := normalizeCredits(rateResp["rateLimitResetCredits"])
	if err != nil {
		return Payload{}, fmt.Errorf("Reset Credits: %w", err)
	}
	generated := now.UTC().Format(time.RFC3339Nano)
	if _, err := timeParseRFC3339(generated); err != nil {
		return Payload{}, fmt.Errorf("generatedAt: %w", err)
	}
	return Payload{Version: 1, GeneratedAt: generated, Account: Account{true, authMode, planType}, Limits: limits, ResetCredits: credits}, nil
}
func stringValue(s *string) string {
	if s == nil {
		return ""
	}
	return *s
}

func normalizeLimit(v any, fallback *string) (Limit, error) {
	m, ok := v.(map[string]any)
	if !ok || m == nil {
		return Limit{}, fmt.Errorf("Limit 必須為 object")
	}
	id, err := optionalString(m["limitId"])
	if err != nil {
		return Limit{}, err
	}
	if id == nil {
		id = fallback
	}
	name, err := optionalString(m["limitName"])
	if err != nil {
		return Limit{}, err
	}
	reached, err := optionalString(m["rateLimitReachedType"])
	if err != nil {
		return Limit{}, err
	}
	primary, err := normalizeWindow(m["primary"])
	if err != nil {
		return Limit{}, fmt.Errorf("primary: %w", err)
	}
	secondary, err := normalizeWindow(m["secondary"])
	if err != nil {
		return Limit{}, fmt.Errorf("secondary: %w", err)
	}
	return Limit{id, name, primary, secondary, reached}, nil
}
func normalizeWindow(v any) (*Window, error) {
	if v == nil {
		return nil, nil
	}
	m, ok := v.(map[string]any)
	if !ok {
		return nil, fmt.Errorf("Window 必須為 object 或 null")
	}
	used, ok := numberText(m["usedPercent"])
	if !ok {
		return nil, fmt.Errorf("usedPercent 缺失或無效")
	}
	remaining, err := remainingPercent(used)
	if err != nil {
		return nil, err
	}
	var duration *int64
	if v := m["windowDurationMins"]; v != nil {
		n, ok := int64Value(v)
		if !ok {
			return nil, fmt.Errorf("windowDurationMins 必須為整數")
		}
		duration = &n
	}
	reset, err := unixISO(m["resetsAt"])
	if err != nil {
		return nil, err
	}
	return &Window{used, remaining, duration, reset}, nil
}

// Exact decimal subtraction uses only the standard library. Bound exponent size
// before allocating big integers; quota values have no reason to require huge exponents.
func remainingPercent(text string) (string, error) {
	if len(text) > 128 || !json.Valid([]byte(text)) {
		return "", fmt.Errorf("usedPercent 非有限十進位數值")
	}
	var number json.Number
	if err := json.Unmarshal([]byte(text), &number); err != nil || text == "null" {
		return "", fmt.Errorf("usedPercent 無效")
	}
	mantissa := text
	exponent := 0
	if i := strings.IndexAny(text, "eE"); i >= 0 {
		var err error
		exponent, err = strconv.Atoi(text[i+1:])
		if err != nil || exponent < -1000 || exponent > 1000 {
			return "", fmt.Errorf("usedPercent exponent 無效")
		}
		mantissa = text[:i]
	}
	used, ok := new(big.Rat).SetString(text)
	if !ok {
		return "", fmt.Errorf("usedPercent 無效")
	}
	hundred := big.NewRat(100, 1)
	if used.Sign() <= 0 {
		return "100", nil
	}
	if used.Cmp(hundred) >= 0 {
		return "0", nil
	}
	scale := -exponent
	if i := strings.IndexByte(mantissa, '.'); i >= 0 {
		scale += len(mantissa) - i - 1
	}
	if scale < 0 {
		scale = 0
	}
	result := new(big.Rat).Sub(hundred, used).FloatString(scale)
	if strings.Contains(result, ".") {
		result = strings.TrimRight(strings.TrimRight(result, "0"), ".")
	}
	return result, nil
}
func normalizeCredits(v any) (*ResetCredits, error) {
	if v == nil {
		return nil, nil
	}
	m, ok := v.(map[string]any)
	if !ok {
		return nil, fmt.Errorf("summary 必須為 object 或 null")
	}
	count, ok := int64Value(m["availableCount"])
	if !ok || count < 0 || int64(int(count)) != count {
		return nil, fmt.Errorf("availableCount 缺失或無效")
	}
	result := &ResetCredits{AvailableCount: int(count)}
	if m["credits"] == nil {
		return result, nil
	}
	raw, ok := m["credits"].([]any)
	if !ok {
		return nil, fmt.Errorf("credits 必須為 array 或 null")
	}
	items := make([]ResetCredit, 0, len(raw))
	for _, v := range raw {
		c, ok := v.(map[string]any)
		if !ok {
			return nil, fmt.Errorf("credit 必須為 object")
		}
		id, ok := c["id"].(string)
		if !ok {
			return nil, fmt.Errorf("credit id 缺失")
		}
		status, ok := c["status"].(string)
		if !ok {
			return nil, fmt.Errorf("credit status 缺失")
		}
		granted, err := unixISO(c["grantedAt"])
		if err != nil || granted == nil {
			return nil, fmt.Errorf("credit grantedAt 無效")
		}
		expires, err := unixISO(c["expiresAt"])
		if err != nil {
			return nil, err
		}
		title, err := optionalString(c["title"])
		if err != nil {
			return nil, err
		}
		description, err := optionalString(c["description"])
		if err != nil {
			return nil, err
		}
		items = append(items, ResetCredit{id, status, *granted, expires, title, description})
	}
	result.Credits = &items
	return result, nil
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
func int64Value(v any) (int64, bool) {
	text, ok := numberText(v)
	if !ok {
		return 0, false
	}
	n, err := strconv.ParseInt(text, 10, 64)
	return n, err == nil
}
func unixISO(v any) (*string, error) {
	if v == nil {
		return nil, nil
	}
	n, ok := int64Value(v)
	if !ok {
		return nil, fmt.Errorf("Unix timestamp 無效")
	}
	value := time.Unix(n, 0).UTC().Format(time.RFC3339)
	if _, err := timeParseRFC3339(value); err != nil {
		return nil, fmt.Errorf("Unix timestamp 超出 ISO 8601 範圍")
	}
	return &value, nil
}
func optionalString(v any) (*string, error) {
	if v == nil {
		return nil, nil
	}
	value, ok := v.(string)
	if !ok {
		return nil, fmt.Errorf("Optional string 型別無效")
	}
	return &value, nil
}
