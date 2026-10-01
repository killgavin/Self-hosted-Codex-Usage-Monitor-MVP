package main

import (
	"bytes"
	"encoding/json"
	"math"
	"testing"
	"time"
)

func testTime() time.Time { return time.Date(2000, 1, 1, 0, 0, 0, 0, time.UTC) }

func loggedIn(t *testing.T) map[string]any {
	return decodeMap(t, `{"requiresOpenaiAuth":true,"account":{"type":"chatgpt","planType":"future-plan"}}`)
}
func TestNormalizeOrderingAndOptionalFields(t *testing.T) {
	source := decodeMap(t, `{"rateLimits":{"primary":{"usedPercent":99}},"rateLimitsByLimitId":{"z":{"limitId":"z","primary":{"usedPercent":99.9}},"a":{"secondary":{"usedPercent":53,"windowDurationMins":10080,"resetsAt":0},"rateLimitReachedType":"future-state"}}}`)
	var expected []byte
	for i := 0; i < 50; i++ {
		p, err := normalize(loggedIn(t), source, time.Unix(0, 0))
		if err != nil {
			t.Fatal(err)
		}
		if len(p.Limits) != 2 || *p.Limits[0].ID != "a" || *p.Limits[1].ID != "z" {
			t.Fatal("ordering/fallback identity incorrect")
		}
		if p.Limits[0].Primary != nil || p.Limits[0].Name != nil || p.ResetCredits != nil {
			t.Fatal("absent optional data invented")
		}
		if *p.Limits[0].Secondary.ResetAt != "1970-01-01T00:00:00Z" || *p.Limits[0].ReachedType != "future-state" {
			t.Fatal("source metadata lost")
		}
		data, err := json.Marshal(p)
		if err != nil {
			t.Fatal(err)
		}
		if i == 0 {
			expected = data
		} else if !bytes.Equal(data, expected) {
			t.Fatal("non-deterministic JSON")
		}
	}
	legacy, err := normalize(loggedIn(t), decodeMap(t, `{"rateLimits":{"primary":null,"secondary":null}}`), time.Now())
	if err != nil || legacy.Limits[0].ID != nil {
		t.Fatalf("legacy unknown identity must be null: %v", err)
	}
}
func TestPercentageBoundaries(t *testing.T) {
	for _, test := range []struct{ used, remaining string }{
		{"0", "100"}, {"3", "97"}, {"53", "47"}, {"87", "13"}, {"99.9", "0.1"}, {"100", "0"}, {"101", "0"}, {"-1", "100"}, {"1e-1", "99.9"}, {"99.999999999999999999", "0.000000000000000001"},
	} {
		t.Run(test.used, func(t *testing.T) {
			window, err := normalizeWindow(map[string]any{"usedPercent": json.Number(test.used)})
			if err != nil || window.UsedPercent != test.used || window.RemainingPercent != test.remaining {
				t.Fatalf("percentage: %+v %v", window, err)
			}
		})
	}
	for _, used := range []any{math.NaN(), math.Inf(1), json.Number("null"), json.Number("true"), json.Number("1e999999999"), "3", nil} {
		if _, err := normalizeWindow(map[string]any{"usedPercent": used}); err == nil {
			t.Fatalf("invalid percentage accepted: %v", used)
		}
	}
}
func TestResetCreditNullEmptyPopulated(t *testing.T) {
	for _, test := range []struct{ name, source, want string }{
		{"absent", `{}`, `null`},
		{"null", `{"rateLimitResetCredits":null}`, `null`},
		{"count-only", `{"rateLimitResetCredits":{"availableCount":2}}`, `{"availableCount":2,"credits":null}`},
		{"empty", `{"rateLimitResetCredits":{"availableCount":0,"credits":[]}}`, `{"availableCount":0,"credits":[]}`},
		{"populated", `{"rateLimitResetCredits":{"availableCount":2,"credits":[{"id":"credit","status":"future","grantedAt":0,"expiresAt":1,"title":null,"description":null,"resetType":"upstream-only"}]}}`, `{"availableCount":2,"credits":[{"id":"credit","status":"future","grantedAt":"1970-01-01T00:00:00Z","expiresAt":"1970-01-01T00:00:01Z","title":null,"description":null}]}`},
	} {
		t.Run(test.name, func(t *testing.T) {
			source := decodeMap(t, test.source)
			source["rateLimits"] = map[string]any{"primary": nil}
			p, err := normalize(loggedIn(t), source, time.Now())
			if err != nil {
				t.Fatal(err)
			}
			data, err := json.Marshal(p.ResetCredits)
			if err != nil || string(data) != test.want {
				t.Fatalf("credits %s: %v", data, err)
			}
		})
	}
}
func TestNormalizeMalformedSourceFails(t *testing.T) {
	for _, source := range []string{
		`{}`, `{"rateLimitsByLimitId":{"bad":null}}`,
		`{"rateLimits":{"primary":{}}}`,
		`{"rateLimits":{"primary":{"usedPercent":3,"windowDurationMins":1.5}}}`,
		`{"rateLimits":{"primary":{"usedPercent":3,"resetsAt":"invalid"}}}`,
		`{"rateLimits":{},"rateLimitResetCredits":{}}`,
		`{"rateLimits":{},"rateLimitResetCredits":{"availableCount":1,"credits":[{}]}}`,
		`{"rateLimits":{},"rateLimitResetCredits":{"availableCount":null}}`,
	} {
		if _, err := normalize(loggedIn(t), decodeMap(t, source), time.Now()); err == nil {
			t.Fatalf("malformed source accepted: %s", source)
		}
	}
}
