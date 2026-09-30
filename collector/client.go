package main

import(
 "context"
 "encoding/json"
 "fmt"
 "io"
 "net/http"
 "unicode/utf8"
)

// DownloadAndValidate 實作 V1 測試 Client 的完整讀取順序。
// 只接受 HTTPS；任何 HTTP、Binary、GCM、UTF-8 或 JSON Schema 錯誤都整份拒絕。
func DownloadAndValidate(ctx context.Context,url string,key []byte)(Payload,error){
 if len(url)<8||url[:8]!="https://"{return Payload{},fmt.Errorf("測試 Client 僅接受 HTTPS URL")}
 req,err:=http.NewRequestWithContext(ctx,http.MethodGet,url,nil);if err!=nil{return Payload{},err}
 resp,err:=http.DefaultClient.Do(req);if err!=nil{return Payload{},fmt.Errorf("HTTPS Download: %w",err)};defer resp.Body.Close()
 if resp.StatusCode<200||resp.StatusCode>=300{return Payload{},fmt.Errorf("HTTPS Download HTTP %d",resp.StatusCode)}
 data,err:=io.ReadAll(io.LimitReader(resp.Body,4*1024*1024));if err!=nil{return Payload{},err}
 plain,err:=DecryptPackage(data,key);if err!=nil{return Payload{},err}
 if !utf8.Valid(plain){return Payload{},fmt.Errorf("UTF-8 Decode 失敗")}
 var p Payload;if err=json.Unmarshal(plain,&p);err!=nil{return Payload{},fmt.Errorf("JSON Parse 失敗: %w",err)}
 if p.Version!=1{return Payload{},fmt.Errorf("不支援 JSON Version: %d",p.Version)}
 if p.GeneratedAt==""{return Payload{},fmt.Errorf("必要欄位 generatedAt 缺失")}
 if _,err=timeParseRFC3339(p.GeneratedAt);err!=nil{return Payload{},fmt.Errorf("generatedAt 非合法 ISO 8601: %w",err)}
 if !p.Account.Authenticated{return Payload{},fmt.Errorf("必要 Account 狀態無效")}
 if len(p.Limits)==0{return Payload{},fmt.Errorf("必要欄位 limits 缺失")}
 return p,nil
}
