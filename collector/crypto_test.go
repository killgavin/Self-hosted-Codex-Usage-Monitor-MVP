package main

import (
	"bytes"
	"testing"
)

func TestEncryptDecryptAndIntegrity(t *testing.T) {
	key := []byte("0123456789abcdef")
	plain := []byte(`{"version":1,"generatedAt":"2026-09-30T23:00:00+08:00"}`)
	a, e := EncryptPackage(plain, key)
	if e != nil {
		t.Fatal(e)
	}
	b, e := EncryptPackage(plain, key)
	if e != nil {
		t.Fatal(e)
	}
	if bytes.Equal(a[5:17], b[5:17]) {
		t.Fatal("每次加密必須使用新的 nonce")
	}
	if bytes.Equal(a[17:], b[17:]) {
		t.Fatal("ciphertext 必須不同")
	}
	if len(a) != 4+1+12+len(plain)+16 {
		t.Fatal("Binary Layout / tag length 不符")
	}
	got, e := DecryptPackage(a, key)
	if e != nil || !bytes.Equal(got, plain) {
		t.Fatalf("round trip 失敗: %v", e)
	}
	x := append([]byte(nil), a...)
	x[17] ^= 1
	if _, e = DecryptPackage(x, key); e == nil {
		t.Fatal("修改 ciphertext 後必須失敗")
	}
	x = append([]byte(nil), a...)
	x[len(x)-1] ^= 1
	if _, e = DecryptPackage(x, key); e == nil {
		t.Fatal("修改 tag 後必須失敗")
	}
	if _, e = DecryptPackage(a, []byte("fedcba9876543210")); e == nil {
		t.Fatal("錯誤 key 必須失敗")
	}
}

func TestTruncatedBinaryAndInvalidKeys(t *testing.T) {
	key := []byte("0123456789abcdef")
	data, err := EncryptPackage([]byte("{}"), key)
	if err != nil {
		t.Fatal(err)
	}
	for length := 0; length < len(data); length++ {
		if _, err := DecryptPackage(data[:length], key); err == nil {
			t.Fatalf("truncated length %d accepted", length)
		}
	}
	for _, invalid := range [][]byte{nil, make([]byte, 15), make([]byte, 17), make([]byte, 24), make([]byte, 32)} {
		if _, err := EncryptPackage([]byte("{}"), invalid); err == nil {
			t.Fatal("invalid encryption key accepted")
		}
		if _, err := DecryptPackage(data, invalid); err == nil {
			t.Fatal("invalid decryption key accepted")
		}
	}
	if _, err := EncryptPackage(nil, key); err == nil {
		t.Fatal("empty ciphertext violates minimum length")
	}
	for i := 17; i < len(data)-16; i++ {
		changed := append([]byte(nil), data...)
		changed[i] ^= 1
		if _, err := DecryptPackage(changed, key); err == nil {
			t.Fatalf("tampered ciphertext byte %d accepted", i)
		}
	}
}
func TestBinaryValidation(t *testing.T) {
	key := []byte("0123456789abcdef")
	data, _ := EncryptPackage([]byte("{}"), key)
	x := append([]byte(nil), data...)
	x[0] = 'X'
	if _, e := DecryptPackage(x, key); e == nil {
		t.Fatal("錯誤 Magic 必須失敗")
	}
	x = append([]byte(nil), data...)
	x[4] = 2
	if _, e := DecryptPackage(x, key); e == nil {
		t.Fatal("不支援版本必須失敗")
	}
}
