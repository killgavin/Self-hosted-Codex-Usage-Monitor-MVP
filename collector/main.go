package main

import (
 "context"
 "encoding/json"
 "fmt"
 "log"
 "os"
 "time"
)

func run(ctx context.Context)error{
 log.Print("Collector 啟動")
 cfg,err:=LoadConfig();if err!=nil{return err}
 account,rates,err:=ReadCodexState(ctx,cfg.CodexExecutable);if err!=nil{return err}
 log.Print("Codex App Server / Account / Rate Limit 取得成功")
 payload,err:=normalize(account,rates,time.Now());if err!=nil{return fmt.Errorf("Normalization: %w",err)}
 log.Print("Normalization 成功")
 plain,err:=json.Marshal(payload);if err!=nil{return fmt.Errorf("JSON Serialize: %w",err)}
 binary,err:=EncryptPackage(plain,cfg.AESKey);if err!=nil{return fmt.Errorf("Encryption: %w",err)}
 log.Print("Encryption 成功")
 if err=UpdateDriveFile(ctx,cfg,binary);err!=nil{return err}
 log.Printf("Google Drive Upload 成功；固定 File ID 已更新: %s",cfg.DriveFileID)
 return nil
}
func main(){
 cfg,err:=LoadConfig()
 if len(os.Args)==3&&os.Args[1]=="--test-url"{
  if err!=nil{log.Printf("測試 Client 設定失敗: %v",err);os.Exit(1)}
  p,e:=DownloadAndValidate(context.Background(),os.Args[2],cfg.AESKey);if e!=nil{log.Printf("測試 Client 驗證失敗: %v",e);os.Exit(1)}
  log.Printf("測試 Client 驗證成功：version=%d generatedAt=%s limits=%d",p.Version,p.GeneratedAt,len(p.Limits));return
 }
 if err:=run(context.Background());err!=nil{log.Printf("本輪執行失敗: %v",err);os.Exit(1)};log.Print("本輪執行成功")
}
