package main

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"os/exec"
	"sync"
	"time"
)

type rpcResponse struct {
	ID     int            `json:"id"`
	Result map[string]any `json:"result"`
	Error  *struct {
		Code    int    `json:"code"`
		Message string `json:"message"`
	} `json:"error"`
}
type CodexClient struct {
	cmd       *exec.Cmd
	stdin     io.WriteCloser
	responses chan rpcResponse
	stderr    bytes.Buffer
	mu        sync.Mutex
	nextID    int
}

func StartCodex(ctx context.Context, executable string) (*CodexClient, error) {
	cmd := exec.CommandContext(ctx, executable, "app-server", "--listen", "stdio://")
	stdin, err := cmd.StdinPipe()
	if err != nil {
		return nil, err
	}
	stdout, err := cmd.StdoutPipe()
	if err != nil {
		return nil, err
	}
	c := &CodexClient{cmd: cmd, stdin: stdin, responses: make(chan rpcResponse, 16)}
	cmd.Stderr = &c.stderr
	if err = cmd.Start(); err != nil {
		return nil, fmt.Errorf("啟動 codex app-server: %w", err)
	}
	go c.readLoop(stdout)
	return c, nil
}
func (c *CodexClient) Close() {
	if c.stdin != nil {
		_ = c.stdin.Close()
	}
	if c.cmd != nil && c.cmd.Process != nil {
		_ = c.cmd.Process.Kill()
		_, _ = c.cmd.Process.Wait()
	}
}
func (c *CodexClient) readLoop(r io.Reader) {
	s := bufio.NewScanner(r)
	s.Buffer(make([]byte, 64*1024), 4*1024*1024)
	for s.Scan() {
		var x rpcResponse
		if json.Unmarshal(s.Bytes(), &x) == nil && x.ID != 0 {
			c.responses <- x
		}
	}
	close(c.responses)
}
func (c *CodexClient) write(v any) error {
	c.mu.Lock()
	defer c.mu.Unlock()
	b, e := json.Marshal(v)
	if e != nil {
		return e
	}
	b = append(b, '\n')
	_, e = c.stdin.Write(b)
	return e
}
func (c *CodexClient) request(ctx context.Context, method string, params any) (map[string]any, error) {
	c.nextID++
	id := c.nextID
	req := map[string]any{"jsonrpc": "2.0", "id": id, "method": method}
	if params != nil {
		req["params"] = params
	}
	if err := c.write(req); err != nil {
		return nil, err
	}
	for {
		select {
		case <-ctx.Done():
			return nil, ctx.Err()
		case r, ok := <-c.responses:
			if !ok {
				return nil, fmt.Errorf("codex app-server 已結束: %s", c.stderr.String())
			}
			if r.ID != id {
				continue
			}
			if r.Error != nil {
				return nil, fmt.Errorf("JSON-RPC %d: %s", r.Error.Code, r.Error.Message)
			}
			return r.Result, nil
		}
	}
}
func (c *CodexClient) notify(method string) error {
	return c.write(map[string]any{"jsonrpc": "2.0", "method": method})
}

// ReadCodexState 嚴格依 initialize→initialized→account/read→account/rateLimits/read 執行。
// 任一步驟失敗即返回錯誤，呼叫端因此不會進入發布階段。
func ReadCodexState(ctx context.Context, executable string) (map[string]any, map[string]any, error) {
	c, err := StartCodex(ctx, executable)
	if err != nil {
		return nil, nil, err
	}
	defer c.Close()
	callCtx, cancel := context.WithTimeout(ctx, 30*time.Second)
	defer cancel()
	if _, err = c.request(callCtx, "initialize", map[string]any{"clientInfo": map[string]any{"name": "codex-usage-monitor-v1", "version": "1.0"}}); err != nil {
		return nil, nil, fmt.Errorf("initialize: %w", err)
	}
	if err = c.notify("initialized"); err != nil {
		return nil, nil, fmt.Errorf("initialized: %w", err)
	}
	account, err := c.request(callCtx, "account/read", map[string]any{"refreshToken": false})
	if err != nil {
		return nil, nil, fmt.Errorf("account/read: %w", err)
	}
	rates, err := c.request(callCtx, "account/rateLimits/read", nil)
	if err != nil {
		return nil, nil, fmt.Errorf("account/rateLimits/read: %w", err)
	}
	return account, rates, nil
}
