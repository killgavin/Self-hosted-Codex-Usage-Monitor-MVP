package main

import (
	"bytes"
	"context"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"testing"
)

func validPlain(t *testing.T) []byte {
	t.Helper()
	p, err := normalize(loggedIn(t), decodeMap(t, `{"rateLimitsByLimitId":{"unknown":{"primary":{"usedPercent":99.9},"secondary":null}}}`), testTime())
	if err != nil {
		t.Fatal(err)
	}
	data, err := json.Marshal(p)
	if err != nil {
		t.Fatal(err)
	}
	return data
}
func TestHTTPSURLValidation(t *testing.T) {
	for _, value := range []string{"http://example.com", "example.com/file", "https://", "https:example.com", "https://%zz", "https://example.com:bad", "https://user:password@example.com", "https:///file", "://bad"} {
		if err := validateHTTPSURL(value); err == nil {
			t.Fatalf("invalid URL accepted: %s", value)
		}
	}
	for _, value := range []string{"https://example.com/file?x=1", "https://127.0.0.1:1234/file", "https://[::1]:1234/file"} {
		if err := validateHTTPSURL(value); err != nil {
			t.Fatalf("valid URL rejected: %v", err)
		}
	}
}
func TestClientHTTPSAndRejections(t *testing.T) {
	key := []byte("0123456789abcdef")
	valid := validPlain(t)
	cases := []struct {
		name      string
		plain     []byte
		mutate    func([]byte)
		wrongKey  bool
		status    int
		wantError bool
	}{
		{name: "valid", plain: valid, status: 200},
		{name: "old-payload-no-stale-threshold", plain: valid, status: 200},
		{name: "wrong-key", plain: valid, wrongKey: true, status: 200, wantError: true},
		{name: "ciphertext", plain: valid, mutate: func(b []byte) { b[17] ^= 1 }, status: 200, wantError: true},
		{name: "tag", plain: valid, mutate: func(b []byte) { b[len(b)-1] ^= 1 }, status: 200, wantError: true},
		{name: "magic", plain: valid, mutate: func(b []byte) { b[0] = 'X' }, status: 200, wantError: true},
		{name: "binary-version", plain: valid, mutate: func(b []byte) { b[4] = 2 }, status: 200, wantError: true},
		{name: "invalid-UTF8", plain: []byte{0xff}, status: 200, wantError: true},
		{name: "invalid-JSON", plain: []byte("{"), status: 200, wantError: true},
		{name: "HTTP-status", plain: valid, status: 403, wantError: true},
	}
	for _, test := range cases {
		t.Run(test.name, func(t *testing.T) {
			data, err := EncryptPackage(test.plain, key)
			if err != nil {
				t.Fatal(err)
			}
			if test.mutate != nil {
				test.mutate(data)
			}
			server := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				if r.Method != "GET" {
					t.Error("not GET")
				}
				w.WriteHeader(test.status)
				_, _ = w.Write(data)
			}))
			defer server.Close()
			actualKey := key
			if test.wrongKey {
				actualKey = []byte("fedcba9876543210")
			}
			_, err = downloadAndValidate(context.Background(), server.URL, actualKey, server.Client())
			if (err != nil) != test.wantError {
				t.Fatalf("result: %v", err)
			}
		})
	}
}
func TestClientSchemaRejectsMissingAndMalformedFields(t *testing.T) {
	key := []byte("0123456789abcdef")
	for _, test := range []struct {
		name   string
		change func(map[string]any)
	}{
		{"version", func(m map[string]any) { m["version"] = 2 }},
		{"generated-missing", func(m map[string]any) { delete(m, "generatedAt") }},
		{"generated-invalid", func(m map[string]any) { m["generatedAt"] = "yesterday" }},
		{"generated-null", func(m map[string]any) { m["generatedAt"] = nil }},
		{"account-missing", func(m map[string]any) { delete(m, "account") }},
		{"unauthenticated", func(m map[string]any) { m["account"].(map[string]any)["authenticated"] = false }},
		{"auth-mode-missing", func(m map[string]any) { delete(m["account"].(map[string]any), "authMode") }},
		{"authenticated-null", func(m map[string]any) { m["account"].(map[string]any)["authenticated"] = nil }},
		{"limits-missing", func(m map[string]any) { delete(m, "limits") }},
		{"limits-null", func(m map[string]any) { m["limits"] = nil }},
		{"limits-empty", func(m map[string]any) { m["limits"] = []any{} }},
		{"limit-null", func(m map[string]any) { m["limits"] = []any{nil} }},
		{"limit-identity-missing", func(m map[string]any) { delete(m["limits"].([]any)[0].(map[string]any), "id") }},
		{"window-required-field", func(m map[string]any) {
			delete(m["limits"].([]any)[0].(map[string]any)["primary"].(map[string]any), "remainingPercent")
		}},
		{"window-percentage-invalid", func(m map[string]any) {
			m["limits"].([]any)[0].(map[string]any)["primary"].(map[string]any)["usedPercent"] = "NaN"
		}},
		{"window-reset-invalid", func(m map[string]any) {
			m["limits"].([]any)[0].(map[string]any)["primary"].(map[string]any)["resetAt"] = "invalid"
		}},
		{"reset-credits-missing", func(m map[string]any) { delete(m, "resetCredits") }},
		{"credit-count-null", func(m map[string]any) { m["resetCredits"] = map[string]any{"availableCount": nil, "credits": nil} }},
		{"credit-count-missing", func(m map[string]any) { m["resetCredits"] = map[string]any{"credits": nil} }},
		{"credit-details-invalid", func(m map[string]any) {
			m["resetCredits"] = map[string]any{"availableCount": 1, "credits": []any{map[string]any{}}}
		}},
	} {
		t.Run(test.name, func(t *testing.T) {
			var object map[string]any
			if err := json.Unmarshal(validPlain(t), &object); err != nil {
				t.Fatal(err)
			}
			test.change(object)
			plain, err := json.Marshal(object)
			if err != nil {
				t.Fatal(err)
			}
			data, err := EncryptPackage(plain, key)
			if err != nil {
				t.Fatal(err)
			}
			if _, err := validatePackage(data, key); err == nil {
				t.Fatal("invalid schema accepted")
			}
		})
	}
	// Unknown optional fields do not redefine version 1.
	data := bytes.Replace(validPlain(t), []byte(`"version":1`), []byte(`"version":1,"futureOptional":true`), 1)
	encrypted, _ := EncryptPackage(data, key)
	if _, err := validatePackage(encrypted, key); err != nil {
		t.Fatal(err)
	}
}
func TestClientRefusesHTTPRedirectAndOversizedBinary(t *testing.T) {
	key := []byte("0123456789abcdef")
	requestedHTTP := false
	target := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { requestedHTTP = true }))
	defer target.Close()
	server := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/large" {
			_, _ = io.Copy(w, bytes.NewReader(make([]byte, maxDownloadSize+1)))
			return
		}
		if r.URL.Path == "/short" {
			_, _ = w.Write([]byte("MDF1"))
			return
		}
		http.Redirect(w, r, target.URL, http.StatusFound)
	}))
	defer server.Close()
	for _, path := range []string{"/redirect", "/large", "/short"} {
		if _, err := downloadAndValidate(context.Background(), server.URL+path, key, server.Client()); err == nil {
			t.Fatalf("%s accepted", path)
		}
	}
	if requestedHTTP {
		t.Fatal("HTTPS downgraded to HTTP")
	}
}
