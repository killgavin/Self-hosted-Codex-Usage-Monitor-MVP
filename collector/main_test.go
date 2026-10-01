package main

import (
	"bytes"
	"context"
	"errors"
	"testing"
)

func fixturePipeline(t *testing.T) pipeline {
	t.Helper()
	steps := defaultPipeline()
	steps.read = func(context.Context, string) (map[string]any, map[string]any, error) {
		return loggedIn(t), decodeMap(t, `{"rateLimits":{"primary":{"usedPercent":3}}}`), nil
	}
	return steps
}
func TestPipelineFailureDoesNotPublish(t *testing.T) {
	sentinel := errors.New("test stage failure")
	for _, stage := range []string{"codex", "logged-out", "rate-read", "normalization", "serialize", "encrypt"} {
		t.Run(stage, func(t *testing.T) {
			cfg := Config{AESKey: []byte("0123456789abcdef")}
			steps := fixturePipeline(t)
			switch stage {
			case "codex", "rate-read":
				steps.read = func(context.Context, string) (map[string]any, map[string]any, error) { return nil, nil, sentinel }
			case "logged-out":
				steps.read = func(context.Context, string) (map[string]any, map[string]any, error) {
					return map[string]any{"account": nil, "requiresOpenaiAuth": true}, map[string]any{"rateLimits": map[string]any{}}, nil
				}
			case "normalization":
				steps.read = func(context.Context, string) (map[string]any, map[string]any, error) {
					return loggedIn(t), map[string]any{"rateLimits": map[string]any{"primary": map[string]any{}}}, nil
				}
			case "serialize":
				steps.marshal = func(Payload) ([]byte, error) { return nil, sentinel }
			case "encrypt":
				cfg.AESKey = nil
			}
			publications := 0
			steps.publish = func(context.Context, Config, []byte) error { publications++; return nil }
			if err := collectAndPublish(context.Background(), cfg, steps); err == nil || publications != 0 {
				t.Fatalf("stage %s published invalid data (%d): %v", stage, publications, err)
			}
		})
	}
}
func TestPipelinePublishesOneCompleteAuthenticatedPackage(t *testing.T) {
	cfg := Config{AESKey: []byte("0123456789abcdef")}
	steps := fixturePipeline(t)
	publications := 0
	var content []byte
	steps.publish = func(ctx context.Context, cfg Config, data []byte) error {
		publications++
		if _, err := validatePackage(data, cfg.AESKey); err != nil {
			t.Fatal(err)
		}
		content = append([]byte(nil), data...)
		return nil
	}
	if err := collectAndPublish(context.Background(), cfg, steps); err != nil || publications != 1 {
		t.Fatalf("publication: %v", err)
	}
	old := append([]byte(nil), content...)
	steps.publish = func(context.Context, Config, []byte) error { publications++; return errors.New("upload failed") }
	if err := collectAndPublish(context.Background(), cfg, steps); err == nil || publications != 2 || !bytes.Equal(old, content) {
		t.Fatal("failed update changed previous content or retried")
	}
}
