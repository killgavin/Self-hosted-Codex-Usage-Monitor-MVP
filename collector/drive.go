package main

import(
 "bytes"
 "context"
 "encoding/json"
 "fmt"
 "io"
 "net"
 "net/http"
 "os"
 "time"
 "golang.org/x/oauth2"
 "golang.org/x/oauth2/google"
)

const driveFileScope="https://www.googleapis.com/auth/drive.file"
const oauthCallback="http://127.0.0.1:53682/oauth2/callback"

func oauthConfig(cfg Config)*oauth2.Config{return &oauth2.Config{ClientID:cfg.GoogleClientID,ClientSecret:cfg.GoogleSecret,Scopes:[]string{driveFileScope},Endpoint:google.Endpoint,RedirectURL:oauthCallback}}
func loadToken(path string)(*oauth2.Token,error){b,e:=os.ReadFile(path);if e!=nil{return nil,e};var t oauth2.Token;if e=json.Unmarshal(b,&t);e!=nil{return nil,e};return &t,nil}
func saveToken(path string,t *oauth2.Token)error{b,e:=json.Marshal(t);if e!=nil{return e};return os.WriteFile(path,b,0600)}

// EnsureToken 使用 Desktop App loopback redirect。首次需人工在瀏覽器授權；callback 只監聽 127.0.0.1。
func EnsureToken(ctx context.Context,cfg Config)(*oauth2.Token,error){
 if t,e:=loadToken(cfg.TokenFile);e==nil{return t,nil}
 listener,e:=net.Listen("tcp","127.0.0.1:53682");if e!=nil{return nil,fmt.Errorf("啟動 OAuth loopback callback: %w",e)};defer listener.Close()
 codeCh:=make(chan string,1);errCh:=make(chan error,1)
 mux:=http.NewServeMux();server:=&http.Server{Handler:mux,ReadHeaderTimeout:5*time.Second}
 mux.HandleFunc("/oauth2/callback",func(w http.ResponseWriter,r *http.Request){
  if x:=r.URL.Query().Get("error");x!=""{errCh<-fmt.Errorf("Google OAuth: %s",x);http.Error(w,"Authorization failed",http.StatusBadRequest);return}
  code:=r.URL.Query().Get("code");if code==""{errCh<-fmt.Errorf("OAuth callback 缺少 code");http.Error(w,"Missing code",http.StatusBadRequest);return}
  codeCh<-code;_,_=io.WriteString(w,"Codex Usage Monitor authorization completed. You may close this window.")
 })
 go func(){if e:=server.Serve(listener);e!=nil&&e!=http.ErrServerClosed{errCh<-e}}()
 oc:=oauthConfig(cfg);url:=oc.AuthCodeURL("codex-monitor-v1",oauth2.AccessTypeOffline)
 fmt.Printf("首次授權：請在本機瀏覽器開啟以下網址：\n%s\n",url)
 var code string
 select{case code=<-codeCh:case e:=<-errCh:return nil,e;case<-ctx.Done():return nil,ctx.Err()}
 shutdownCtx,cancel:=context.WithTimeout(context.Background(),2*time.Second);defer cancel();_=server.Shutdown(shutdownCtx)
 t,e:=oc.Exchange(ctx,code);if e!=nil{return nil,fmt.Errorf("OAuth code exchange: %w",e)}
 if e=saveToken(cfg.TokenFile,t);e!=nil{return nil,fmt.Errorf("保存 OAuth token: %w",e)}
 return t,nil
}

// UpdateDriveFile 只 PATCH 指定 File ID；不搜尋檔名、不 Delete/Create。
func UpdateDriveFile(ctx context.Context,cfg Config,data []byte)error{
 t,err:=EnsureToken(ctx,cfg);if err!=nil{return err};oc:=oauthConfig(cfg);fresh,err:=oc.TokenSource(ctx,t).Token();if err!=nil{return fmt.Errorf("更新 access token: %w",err)}
 if fresh.AccessToken!=t.AccessToken||fresh.Expiry!=t.Expiry{if e:=saveToken(cfg.TokenFile,fresh);e!=nil{return fmt.Errorf("保存更新後 OAuth token: %w",e)}}
 u:="https://www.googleapis.com/upload/drive/v3/files/"+cfg.DriveFileID+"?uploadType=media"
 req,err:=http.NewRequestWithContext(ctx,http.MethodPatch,u,bytes.NewReader(data));if err!=nil{return err};req.Header.Set("Authorization","Bearer "+fresh.AccessToken);req.Header.Set("Content-Type","application/octet-stream")
 resp,err:=http.DefaultClient.Do(req);if err!=nil{return fmt.Errorf("Google Drive Update: %w",err)};defer resp.Body.Close()
 if resp.StatusCode<200||resp.StatusCode>=300{body,_:=io.ReadAll(io.LimitReader(resp.Body,4096));return fmt.Errorf("Google Drive Update HTTP %d: %s",resp.StatusCode,string(body))}
 return nil
}
