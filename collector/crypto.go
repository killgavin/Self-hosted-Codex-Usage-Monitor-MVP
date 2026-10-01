package main

import (
	"bytes"
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"errors"
	"fmt"
)

var magic = []byte("MDF1")

const binaryVersion byte = 1
const nonceSize = 12
const tagSize = 16
const minBinarySize = 4 + 1 + nonceSize + 1 + tagSize

// EncryptPackage 將完整 UTF-8 JSON 一次以 AES-128-GCM 加密。
// Seal 產生 ciphertext||tag，再依規格封裝 MDF1|version|nonce|ciphertext|tag。
func EncryptPackage(plaintext, key []byte) ([]byte, error) {
	if len(plaintext) == 0 {
		return nil, errors.New("plaintext 不得為空")
	}
	if len(key) != 16 {
		return nil, errors.New("AES-128 key 必須正好 16 bytes")
	}
	block, err := aes.NewCipher(key)
	if err != nil {
		return nil, err
	}
	gcm, err := cipher.NewGCMWithNonceSize(block, nonceSize)
	if err != nil {
		return nil, err
	}
	nonce := make([]byte, nonceSize)
	if _, err = rand.Read(nonce); err != nil {
		return nil, fmt.Errorf("產生 nonce: %w", err)
	}
	sealed := gcm.Seal(nil, nonce, plaintext, nil)
	out := make([]byte, 0, 5+nonceSize+len(sealed))
	out = append(out, magic...)
	out = append(out, binaryVersion)
	out = append(out, nonce...)
	out = append(out, sealed...)
	return out, nil
}

// DecryptPackage 是測試 Client 的核心驗證器；格式或 GCM 驗證錯誤均直接失敗。
func DecryptPackage(data, key []byte) ([]byte, error) {
	if len(data) < minBinarySize {
		return nil, errors.New("binary 長度不足")
	}
	if !bytes.Equal(data[:4], magic) {
		return nil, errors.New("Magic 不符")
	}
	if data[4] != binaryVersion {
		return nil, errors.New("不支援的 Binary Format Version")
	}
	if len(key) != 16 {
		return nil, errors.New("AES-128 key 必須正好 16 bytes")
	}
	block, err := aes.NewCipher(key)
	if err != nil {
		return nil, err
	}
	gcm, err := cipher.NewGCMWithNonceSize(block, nonceSize)
	if err != nil {
		return nil, err
	}
	plain, err := gcm.Open(nil, data[5:17], data[17:], nil)
	if err != nil {
		return nil, errors.New("AES-GCM 驗證失敗")
	}
	return plain, nil
}
