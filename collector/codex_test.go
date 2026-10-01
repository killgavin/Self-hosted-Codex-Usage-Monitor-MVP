package main

import (
	"bufio"
	"context"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"strings"
	"testing"
	"time"
)

func TestCodexHelperProcess(t *testing.T) {
	if os.Getenv("GO_WANT_CODEX_HELPER_PROCESS") != "1" {
		return
	}
	scenario := os.Args[len(os.Args)-1]
	scanner := bufio.NewScanner(os.Stdin)
	initialized := false
	for scanner.Scan() {
		var request struct {
			ID     int    `json:"id"`
			Method string `json:"method"`
		}
		if err := json.Unmarshal(scanner.Bytes(), &request); err != nil {
			os.Exit(3)
		}
		if request.Method == "initialized" {
			initialized = true
			continue
		}
		switch scenario {
		case "timeout":
			time.Sleep(time.Minute)
		case "exit":
			os.Exit(7)
		case "malformed":
			fmt.Println("{")
			time.Sleep(time.Minute)
		case "oversized":
			fmt.Println(strings.Repeat("x", 4*1024*1024+1))
			time.Sleep(time.Minute)
		case "rpc-error":
			fmt.Printf("{\"id\":%d,\"error\":{\"code\":-32000,\"message\":\"test-error\"}}\n", request.ID)
			continue
		}
		// Drain-heavy stderr must not delay the response.
		fmt.Fprintln(os.Stderr, strings.Repeat("test diagnostic ", 10000))
		fmt.Println(`{"method":"account/updated","params":{}}`)
		fmt.Printf("{\"id\":%d,\"method\":\"server/request\",\"params\":{}}\n", request.ID)
		fmt.Println(`{"id":999,"result":{"unrelated":true}}`)
		var result any = map[string]any{"padding": strings.Repeat("x", 100000)}
		if request.Method == "account/read" {
			if !initialized {
				os.Exit(8)
			}
			result = map[string]any{"requiresOpenaiAuth": true, "account": map[string]any{"type": "chatgpt", "planType": "test-plan"}}
		}
		if request.Method == "account/rateLimits/read" {
			// A number that cannot survive float64 parsing unchanged.
			fmt.Printf("{\"id\":%d,\"result\":{\"rateLimits\":{\"primary\":{\"usedPercent\":99.999999999999999999}}}}\n", request.ID)
			continue
		}
		data, _ := json.Marshal(map[string]any{"id": request.ID, "result": result})
		fmt.Println(string(data))
	}
	os.Exit(0)
}
func helperClient(t *testing.T, scenario string) *CodexClient {
	t.Helper()
	command := exec.Command(os.Args[0], "-test.run=^TestCodexHelperProcess$", "--", scenario)
	command.Env = append(os.Environ(), "GO_WANT_CODEX_HELPER_PROCESS=1")
	client, err := startCodexCommand(command)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(client.Close)
	return client
}
func TestCodexDispatcherSequenceNumbersAndClose(t *testing.T) {
	client := helperClient(t, "success")
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if _, err := client.request(ctx, "initialize", nil); err != nil {
		t.Fatal(err)
	}
	if err := client.notify("initialized"); err != nil {
		t.Fatal(err)
	}
	account, err := client.request(ctx, "account/read", nil)
	if err != nil {
		t.Fatal(err)
	}
	rates, err := client.request(ctx, "account/rateLimits/read", nil)
	if err != nil {
		t.Fatal(err)
	}
	payload, err := normalize(account, rates, testTime())
	if err != nil || payload.Limits[0].Primary.RemainingPercent != "0.000000000000000001" {
		t.Fatalf("number precision/protocol: %v", err)
	}
	client.Close()
	client.Close()
	select {
	case <-client.done:
	default:
		t.Fatal("process not reaped")
	}
	if client.cmd.ProcessState == nil {
		t.Fatal("cmd.Wait was not called")
	}
}
func TestCodexDispatcherFailures(t *testing.T) {
	for _, scenario := range []string{"rpc-error", "exit", "malformed", "oversized", "timeout"} {
		t.Run(scenario, func(t *testing.T) {
			client := helperClient(t, scenario)
			ctx, cancel := context.WithTimeout(context.Background(), time.Second)
			defer cancel()
			_, err := client.request(ctx, "initialize", nil)
			if err == nil {
				t.Fatal("failure not reported")
			}
			if scenario == "rpc-error" && !strings.Contains(err.Error(), "-32000") {
				t.Fatal("RPC code lost")
			}
			if scenario == "exit" && !strings.Contains(err.Error(), "exit status 7") {
				t.Fatalf("exit status lost: %v", err)
			}
			if scenario == "malformed" && !strings.Contains(err.Error(), "JSONL") {
				t.Fatalf("parser error lost: %v", err)
			}
			client.Close()
		})
	}
}
func TestCodexCloseWithUnconsumedResponses(t *testing.T) {
	client := helperClient(t, "success")
	for i := 0; i < 25; i++ {
		if err := client.write(map[string]any{"id": i + 1, "method": "initialize"}); err != nil {
			t.Fatal(err)
		}
	}
	closed := make(chan struct{})
	go func() { client.Close(); close(closed) }()
	select {
	case <-closed:
	case <-time.After(5 * time.Second):
		t.Fatal("Close deadlock with full response channel")
	}
}
