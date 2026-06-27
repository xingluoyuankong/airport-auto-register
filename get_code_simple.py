import requests, re, os

token_dir = r"E:\.Outlook邮箱\批量注册邮箱\已经使用\1"
for fn in os.listdir(token_dir):
    if "kebukeyi" in fn:
        with open(os.path.join(token_dir, fn),"r",encoding="utf-8") as f:
            p = f.read().strip().split("----")
        email, cid, rt = p[0], p[2], p[3]
        break

r = requests.post("https://login.microsoftonline.com/consumers/oauth2/v2.0/token",
    data={"client_id":cid,"grant_type":"refresh_token","refresh_token":rt,"scope":"offline_access https://graph.microsoft.com/Mail.Read"}, timeout=15)
at = r.json()["access_token"]

resp = requests.get("https://graph.microsoft.com/v1.0/me/messages?$top=15&$select=subject,from,receivedDateTime,bodyPreview&$orderby=receivedDateTime desc",
    headers={"Authorization":"Bearer "+at}, timeout=10)

for m in resp.json().get("value",[]):
    subj = m.get("subject","")[:60]
    frm = m.get("from",{}).get("emailAddress",{}).get("address","")[:35]
    rcvd = m.get("receivedDateTime","")
    prev = (m.get("bodyPreview","") or "")[:60]
    txt = subj + " " + prev
    code = None
    mm = re.search(r"(\d{6})", txt)
    if mm: code = mm.group(1)
    tag = f" [CODE:{code}]" if code else ""
    print(f"{rcvd[-19:]} | {frm} | {subj}{tag}")
