import requests, re, time, os

# Load kebukeyi2026 token
token_dir = r"E:\.Outlook邮箱\批量注册邮箱\已经使用\1"
for fname in os.listdir(token_dir):
    if "kebukeyi" in fname:
        with open(os.path.join(token_dir, fname), "r", encoding="utf-8") as f:
            parts = f.read().strip().split("----")
        email, client_id, refresh_token = parts[0], parts[2], parts[3]
        print(f"Email: {email}")
        break

token_url = "https://login.microsoftonline.com/consumers/oauth2/v2.0/token"
scope = "offline_access https://graph.microsoft.com/Mail.Read"
seen = set()
deadline = time.time() + 90

while time.time() < deadline:
    try:
        r = requests.post(token_url, data={
            "client_id": client_id, "grant_type": "refresh_token",
            "refresh_token": refresh_token, "scope": scope
        }, timeout=15)
        at = r.json().get("access_token")
        if not at: time.sleep(3); continue

        resp = requests.get(
            "https://graph.microsoft.com/v1.0/me/messages?$top=10&$select=subject,from,receivedDateTime,bodyPreview,body",
            headers={"Authorization": f"Bearer {at}"}, timeout=10
        )
        msgs = resp.json().get("value", [])
        
        for msg in msgs:
            received = msg.get("receivedDateTime", "")
            subject = msg.get("subject", "") or ""
            body = (msg.get("body", {}).get("content", "") or "") + " " + (msg.get("bodyPreview", "") or "")
            combined = subject + " " + body
            
            # Only recent emails (last 5 min)
            m = re.search(r"(?:verification|security|验证|code|激活|speedy|Speedy|注册).*?(\d{6})", combined, re.I)
            if not m:
                m = re.search(r"(\d{6})", combined)
            if m and not re.search(r"\d{7}", m.group(0)):
                code = m.group(1)
                if code not in seen:
                    print(f"FOUND CODE: {code} | Subject: {subject[:50]} | Time: {received}")
                    exit(0)
                seen.add(code)
        
        print(f"Polling... {len(msgs)} msgs, no new code yet")
        time.sleep(5)
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(3)

print("TIMEOUT - no code found")
