import requests,re,os
d=r"E:\.Outlook邮箱\批量注册邮箱\已经使用\1"
for fn in os.listdir(d):
    if "mx4496f269fa" in fn:
        with open(os.path.join(d,fn),"r",encoding="utf-8") as f:
            p=f.read().strip().split("----")
        email,cid,rt=p[0],p[2],p[3]
        break
r=requests.post("https://login.microsoftonline.com/consumers/oauth2/v2.0/token",
    data={"client_id":cid,"grant_type":"refresh_token","refresh_token":rt,
          "scope":"offline_access https://graph.microsoft.com/Mail.Read"},timeout=15)
at=r.json()["access_token"]
resp=requests.get("https://graph.microsoft.com/v1.0/me/messages?$top=3&$select=subject,from,bodyPreview,body&$orderby=receivedDateTime desc",
    headers={"Authorization":"Bearer "+at},timeout=10)
for m in resp.json().get("value",[]):
    subj=m.get("subject","")
    frm=m.get("from",{}).get("emailAddress",{}).get("address","")
    if "glados" in str(frm).lower():
        body=m.get("body",{}).get("content","")
        preview=m.get("bodyPreview","") or ""
        # Print full text content
        print("=== RAW BODY ===")
        print(body[:1500])
        break
