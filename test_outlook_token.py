import sys, os, json, requests, re

# Load token from combo file
token_dir = r"E:\.Outlook邮箱\批量注册邮箱\已经使用\1"
accounts = []

for fname in os.listdir(token_dir):
    if not fname.endswith("_combo.txt"):
        continue
    fpath = os.path.join(token_dir, fname)
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read().strip()
    parts = content.split("----")
    if len(parts) >= 4:
        accounts.append({
            "email": parts[0],
            "password": parts[1],
            "client_id": parts[2],
            "refresh_token": parts[3],
            "source": fname,
        })

print(f"共加载 {len(accounts)} 个token账户")

# Test each one
for acc in accounts:
    email = acc["email"]
    client_id = acc["client_id"]
    refresh_token = acc["refresh_token"]
    
    print(f"\n测试: {email[:30]}...")
    
    token_url = "https://login.microsoftonline.com/consumers/oauth2/v2.0/token"
    try:
        r = requests.post(token_url, data={
            "client_id": client_id,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "scope": "offline_access https://graph.microsoft.com/Mail.Read",
        }, timeout=15)
        data = r.json()
        
        if data.get("access_token"):
            # Read inbox
            resp = requests.get(
                "https://graph.microsoft.com/v1.0/me/messages?$top=3&$select=subject,from,receivedDateTime,bodyPreview",
                headers={"Authorization": f"Bearer {data['access_token']}"},
                timeout=10
            )
            msgs = resp.json()
            msgs_list = msgs.get("value", [])
            print(f"  OK! 收件箱: {len(msgs_list)}封")
            for m in msgs_list[:3]:
                subj = m.get("subject", "")[:40]
                sender = m.get("from", {}).get("emailAddress", {}).get("address", "")[:30]
                print(f"    {subj} | {sender}")
            acc["works"] = True
        else:
            error = data.get("error_description", data.get("error", str(data)[:100]))
            print(f"  失败: {error}")
            acc["works"] = False
    except Exception as e:
        print(f"  错误: {e}")
        acc["works"] = False

# Summary
working = [a for a in accounts if a.get("works")]
print(f"\n\n共 {len(working)}/{len(accounts)} 个可用")
for a in working:
    print(f"  {a['email']}")
