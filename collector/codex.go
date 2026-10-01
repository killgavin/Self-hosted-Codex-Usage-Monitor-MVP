package main

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"os/exec"
	"sync"
	"time"
	"unicode/utf8"
)

type rpcResponse struct {
	ID     *int           `json:"id"`
	Method string         `json:"method"`
	Result map[string]any `json:"result"`
	Error  *struct {
		Code    int    `json:"code"`
		Message string `json:"message"`
	} `json:"error"`
}
type CodexClient struct {
	cmd         *exec.Cmd
	stdin       io.WriteCloser
	responses   chan rpcResponse
	stop        chan struct{}
	readerDone  chan struct{}
	done        chan struct{}
	closeOnce   sync.Once
	writeMu     sync.Mutex
	requestMu   sync.Mutex
	stateMu     sync.Mutex
	terminalErr error
	nextID      int
}

func StartCodex(ctx context.Context, executable string) (*CodexClient, error) {
	return startCodexCommand(exec.CommandContext(ctx, executable, "app-server", "--listen", "stdio://"))
}
func startCodexCommand(cmd *exec.Cmd) (*CodexClient, error) {
	cmd.WaitDelay = 2 * time.Second
	stdin, err := cmd.StdinPipe()
	if err != nil {
		return nil, err
	}
	stdout, err := cmd.StdoutPipe()
	if err != nil {
		_ = stdin.Close()
		return nil, err
	}
	c := &CodexClient{cmd: cmd, stdin: stdin, responses: make(chan rpcResponse, 16), stop: make(chan struct{}), readerDone: make(chan struct{}), done: make(chan struct{})}
	// Drain stderr without retaining untrusted credential-bearing diagnostics.
	cmd.Stderr = io.Discard
	if err = cmd.Start(); err != nil {
		_ = stdin.Close()
		_ = stdout.Close()
		return nil, fmt.Errorf("啟動 codex app-server: %w", err)
	}
	go c.readLoop(stdout)
	go func() {
		<-c.readerDone
		c.stateMu.Lock()
		readFailed := c.terminalErr != nil
		c.stateMu.Unlock()
		if readFailed {
			_ = cmd.Process.Kill()
		}
		if err := cmd.Wait(); err != nil {
			c.setTerminalError(fmt.Errorf("codex app-server process: %w", err))
		}
		close(c.done)
	}()
	return c, nil
}
func (c *CodexClient) setTerminalError(err error) {
	c.stateMu.Lock()
	defer c.stateMu.Unlock()
	if c.terminalErr == nil {
		c.terminalErr = err
	}
}
func (c *CodexClient) Close() {
	c.closeOnce.Do(func() {
		close(c.stop)
		_ = c.stdin.Close()
		if c.cmd.Process != nil {
			_ = c.cmd.Process.Kill()
		}
		<-c.done // cmd.Wait reaps the process and joins the stderr copier.
	})
}
func (c *CodexClient) readLoop(r io.Reader) {
	defer close(c.readerDone)
	defer close(c.responses)
	scanner := bufio.NewScanner(r)
	scanner.Buffer(make([]byte, 64*1024), 4*1024*1024)
	for scanner.Scan() {
		if !utf8.Valid(scanner.Bytes()) {
			c.setTerminalError(fmt.Errorf("codex stdout UTF-8 無效"))
			return
		}
		var response rpcResponse
		decoder := json.NewDecoder(bytes.NewReader(scanner.Bytes()))
		decoder.UseNumber()
		if err := decoder.Decode(&response); err != nil {
			c.setTerminalError(fmt.Errorf("codex stdout JSONL 無效"))
			return
		}
		var extra any
		if err := decoder.Decode(&extra); err != io.EOF {
			c.setTerminalError(fmt.Errorf("codex stdout JSONL 有多餘內容"))
			return
		}
		if response.Method != "" || response.ID == nil {
			continue
		} // Notifications and server requests are not responses.
		select {
		case c.responses <- response:
		case <-c.stop:
			return
		}
	}
	if err := scanner.Err(); err != nil {
		c.setTerminalError(fmt.Errorf("codex stdout Scanner: %w", err))
	}
}
func (c *CodexClient) write(v any) error {
	c.writeMu.Lock()
	defer c.writeMu.Unlock()
	data, err := json.Marshal(v)
	if err != nil {
		return err
	}
	_, err = c.stdin.Write(append(data, '\n'))
	return err
}
func (c *CodexClient) request(ctx context.Context, method string, params any) (map[string]any, error) {
	// Collector requests are sequential. Serialize callers so IDs and response
	// consumption remain coherent even if diagnostics call from multiple goroutines.
	c.requestMu.Lock()
	defer c.requestMu.Unlock()
	if err := ctx.Err(); err != nil {
		return nil, err
	}
	c.nextID++
	id := c.nextID
	request := map[string]any{"jsonrpc": "2.0", "id": id, "method": method}
	if params != nil {
		request["params"] = params
	}
	if err := c.write(request); err != nil {
		return nil, fmt.Errorf("codex stdin write: %w", err)
	}
	for {
		select {
		case <-ctx.Done():
			return nil, ctx.Err()
		case response, ok := <-c.responses:
			if !ok {
				// EOF can precede process termination; keep the caller's timeout active.
				select {
				case <-c.done:
				case <-ctx.Done():
					return nil, ctx.Err()
				}
				c.stateMu.Lock()
				err := c.terminalErr
				c.stateMu.Unlock()
				if err != nil {
					return nil, err
				}
				return nil, fmt.Errorf("codex app-server 已結束")
			}
			if *response.ID != id {
				continue
			}
			if response.Error != nil {
				return nil, fmt.Errorf("JSON-RPC %d: app-server request failed", response.Error.Code)
			}
			if response.Result == nil {
				return nil, fmt.Errorf("JSON-RPC result 缺失或非 object")
			}
			return response.Result, nil
		}
	}
}
func (c *CodexClient) notify(method string) error {
	return c.write(map[string]any{"jsonrpc": "2.0", "method": method})
}

// ReadCodexState keeps the official handshake and never starts a login flow.
func ReadCodexState(ctx context.Context, executable string) (map[string]any, map[string]any, error) {
	callCtx, cancel := context.WithTimeout(ctx, 30*time.Second)
	defer cancel()
	c, err := StartCodex(callCtx, executable)
	if err != nil {
		return nil, nil, err
	}
	defer c.Close()
	if _, err = c.request(callCtx, "initialize", map[string]any{"clientInfo": map[string]any{"name": "codex-usage-monitor-v1", "title": "Codex Usage Monitor", "version": "1.0"}}); err != nil {
		return nil, nil, fmt.Errorf("initialize: %w", err)
	}
	log.Print("Codex initialize 成功")
	if err = c.notify("initialized"); err != nil {
		return nil, nil, fmt.Errorf("initialized: %w", err)
	}
	log.Print("Codex initialized 已送出")
	account, err := c.request(callCtx, "account/read", map[string]any{"refreshToken": false})
	if err != nil {
		return nil, nil, fmt.Errorf("account/read: %w", err)
	}
	acct, _ := account["account"].(map[string]any)
	log.Printf("Codex account/read 成功；authenticated=%t", acct != nil)
	rates, err := c.request(callCtx, "account/rateLimits/read", nil)
	if err != nil {
		return nil, nil, fmt.Errorf("account/rateLimits/read: %w", err)
	}
	log.Print("Codex account/rateLimits/read 成功")
	return account, rates, nil
}
