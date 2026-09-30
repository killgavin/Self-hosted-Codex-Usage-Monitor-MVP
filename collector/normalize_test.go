package main

import (
	"encoding/json"
	"strings"
	"testing"
	"time"
)

func decodeMap(t *testing.T, s string) map[string]any {
	t.Helper()
	d := json.NewDecoder(strings.NewReader(s))
	d.UseNumber()
	var m map[string]any
	if e := d.Decode(&m); e != nil {
		t.Fatal(e)
	}
	return m
}
func TestNormalizeVerifiedContract(t *testing.T) {
	a := decodeMap(t, `{"requiresOpenaiAuth":false,"account":{"type":"chatgpt","planType":"plus"}}`)
	r := decodeMap(t, `{"rateLimits":{"primary":{"usedPercent":3}},"rateLimitsByLimitId":{"codex":{"limitId":"codex","limitName":"Codex","primary":{"usedPercent":3,"windowDurationMins":300,"resetsAt":1790784000},"secondary":{"usedPercent":87,"windowDurationMins":10080,"resetsAt":1791388800}}},"rateLimitResetCredits":{"availableCount":0,"credits":[]}}`)
	p, e := normalize(a, r, time.Date(2026, 9, 30, 23, 0, 0, 0, time.FixedZone("CST", 8*3600)))
	if e != nil {
		t.Fatal(e)
	}
	if p.Version != 1 || p.GeneratedAt != "2026-09-30T23:00:00+08:00" || len(p.Limits) != 1 {
		t.Fatalf("payload 不符: %+v", p)
	}
	if p.Limits[0].Primary.RemainingPercent != "97" {
		t.Fatalf("remaining percent 不符: %+v", p.Limits[0].Primary)
	}
}
func TestNormalizeRejectsLoggedOut(t *testing.T) {
	a := decodeMap(t, `{"requiresOpenaiAuth":true,"account":null}`)
	r := decodeMap(t, `{"rateLimits":{}}`)
	if _, e := normalize(a, r, time.Now()); e == nil {
		t.Fatal("未登入不得產生有效 Payload")
	}
}
