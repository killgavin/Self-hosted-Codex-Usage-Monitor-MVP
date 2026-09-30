package main

import(
 "bytes"
 "context"
 "encoding/json"
 "fmt"
 "io"
 "net/http"
 "os"
 "golang.org/x/oauth2"
 "golang.org/x/oauth2/google"
)

const driveFileScope="https://www.googleapis.com/auth/drive.file"
func oauthConfig(cfg Config)*oauth2.Config{return &oauth2.Config{ClientID:cfg.GoogleClientID,ClientSecret:cfg.GoogleSecret,Scopes:[]string{driveFileScope},Endpoint:google.Endpoint,RedirectURL:"http://localhost"}}
func loadToken(path string)(*oauth2.Token,error){b,e:=os.ReadFile(path);if e!=nil{return nil,e};var t oauth2.Token;if e=json.Unmarshal(b,&t);e!=nil{return nil,e};return &t,nil}
func saveToken(path string,t *oauth2.Token)error{b,e:=json.Marshal(t);if e!=nil{return e};return os.WriteFile(path,b,0600)}

// EnsureToken 只在首次執行要求人工 Desktop OAuth 授權；後續使用 refresh token。
func EnsureToken(ctx context.Context,cfg Config)(*oauth2.Token,error){
 if t,e:=loadToken(cfg.TokenFile);e==nil{return t,nil}
 oc:=oauthConfig(cfg);url:=oc.AuthCodeURL("codex-monitor-v1",oauth2.AccessTypeOffline)
 fmt.Printf("首次授權：請開啟以下網址並貼回 authorization code：\n%s\nCode: ",url)
 var code string;if _,e:=fmt.Scanln(&code);e!=nil{return nil,e};t,e:=oc.Exchange(ctx,code);if e!=nil{return nil,fmt.Errorf("OAuth code exchange: %w",e)}
 if e=saveToken(cfg.TokenFile,t);e!=nil{return nil,fmt.Errorf("保存 OAuth token: %w",e)};return t,nil
}

// UpdateDriveFile 只 PATCH 指定 File ID；不搜尋檔名、不 Delete/Create。
func UpdateDriveFile(ctx context.Context,cfg Config,data []byte)error{
 t,err:=EnsureToken(ctx,cfg);if err!=nil{return err};oc:=oauthConfig(cfg);fresh,err:=oc.TokenSource(ctx,t).Token();if err!=nil{return fmt.Errorf("更新 access token: %w",err)}
 if fresh.AccessToken!=t.AccessToken||fresh.Expiry!=t.Expiry{_=saveToken(cfg.TokenFile,fresh)}
 u:="https://www.googleapis.com/upload/drive/v3/files/"+cfg.DriveFileID+"?uploadType=media"
 req,err:=http.NewRequestWithContext(ctx,http.MethodPatch,u,bytes.NewReader(data));if err!=nil{return err};req.Header.Set("Authorization","Bearer "+fresh.AccessToken);req.Header.Set("Content-Type","application/octet-stream")
 resp,err:=http.DefaultClient.Do(req);if err!=nil{return fmt.Errorf("Google Drive Update: %w",err)};defer resp.Body.Close()
 if resp.StatusCode<200||resp.StatusCode>=300{body,_:=io.ReadAll(io.LimitReader(resp.Body,4096));return fmt.Errorf("Google Drive Update HTTP %d: %s",resp.StatusCode,string(body))}
 return nil
}
