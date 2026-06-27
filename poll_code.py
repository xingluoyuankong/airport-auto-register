import requests, re, time, os, sys

# Load token for kebukeyi2026
token_dir = r"E:\.Outlook邮箱\批量注册邮箱\已经使用\1"
for fname in os.listdir(token_dir):
    if "kebukeyi" in fname:
        with open(os.path.join(token_dir, fname), "r", encoding="utf-8") as f:
            parts = f.read().strip().split("----")
        email, cid, rt = parts[0], parts[2], parts[3]
        break

token_url = "https://login.microsoftonline.com/consumers/oauth2/v2.0/token"
r = requests.post(token_url, data={
    "client_id": cid, "grant_type": "refresh_token",
    "refresh_token": rt, "scope": "offline_access https://graph.microsoft.com/Mail.Read"
}, timeout=15)
at = r.json()["access_token"]

# Get recent messages (last 10 min)
filter_time = "2026-06-27T14:55:00Z"
url = (
    "https://graph.microsoft.com/v1.0/me/messages"
    "?$top=10"
    "&$select=subject,from,receivedDateTime,bodyPreview"
    "&$filter=receivedDateTime ge " + filter_time
    "&$orderby=receivedDateTime desc"
)
resp = requests.get(url, headers={"Authorization": f"Bearer {at}"}, timeout=10)
msgs = resp.json().get("value", [])

print(f"Recent msgs (after {filter_time}): {len(msgs)}")
for m in msgs:
    subj = m.get("subject", "")[:60]
    frm_addr = m.get("from", {}).get("emailAddress", {}).get("address", "")[:40]
    rcvd = m.get("receivedDateTime", "")
    preview = (m.get("bodyPreview", "") or "")[:80]
    
    # Try to extract code
    code = None
    m1 = re.search(r"(?:verification|验证|code|激活|speedy|Speedy).*?(\d{6})", subj + " " + preview, re.I)
    if not m1:
        m1 = re.search(r"(\d{6})", subj + " " + preview)
    if m1:
        code = m1.group(1)
    
    print(f"  [{rcvd[-12:]}] {subj} | {frm_addr}")
    if code:
        print(f"    CODE: {code} | {preview}")
    else:
        print(f"    {preview}")
