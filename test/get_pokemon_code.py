"""轮询Graph API获取宝可梦验证码 - mallenbb9qdjidg9y5tw1yqd@outlook.com"""
import requests
import re
import time

# Token文件
TOKEN_FILE = r"E:\.Outlook邮箱\批量注册邮箱\已经使用\1\tokens_mallenbb9qdjidg9y5tw1yqd@outlook.com_combo.txt"

with open(TOKEN_FILE) as f:
    parts = f.read().strip().split("----")
email, pwd, cid, rt = parts[0], parts[1], parts[2], parts[3]
print(f"邮箱: {email}")
print(f"ClientID: {cid}")

# 获取access_token
r = requests.post("https://login.microsoftonline.com/consumers/oauth2/v2.0/token",
    data={"client_id": cid, "grant_type": "refresh_token", "refresh_token": rt,
          "scope": "offline_access https://graph.microsoft.com/Mail.Read"}, timeout=15)
at = r.json().get("access_token")
if not at:
    print(f"获取token失败: {r.json()}")
    exit()
print(f"AccessToken获取成功 (长度{len(at)})")

# 轮询最新邮件，等验证码
print("\n开始轮询验证码，最多等90秒...")
found_codes = set()
for i in range(30):
    resp = requests.get(
        "https://graph.microsoft.com/v1.0/me/messages?$top=10&$select=subject,from,receivedDateTime,bodyPreview,body&$orderby=receivedDateTime desc",
        headers={"Authorization": "Bearer " + at}, timeout=10
    )
    msgs = resp.json().get("value", [])
    
    for m in msgs:
        subject = m.get("subject", "")
        body_preview = m.get("bodyPreview", "")
        body = m.get("body", {}).get("content", "")
        sender = m.get("from", {}).get("emailAddress", {}).get("name", "?")
        date = m.get("receivedDateTime", "?")
        
        # 找验证码：宝可梦/验证码相关
        all_text = subject + " " + body_preview + " " + body
        
        # 查找各种验证码格式
        patterns = [
            r'验证码[：:\s]*(\d{4,8})',
            r'verification code[：:\s]*(\d{4,8})',
            r'code[：:\s]*(\d{4,8})',
            r'验证码[：:\s]*[（(]?\s*(\d{4,8})\s*[)）]?',
            r'\b(\d{4,8})\b.*验证码',
            r'\[宝可梦.*?\]\s*(\d{4,8})',
            r'(\d{4,8})',
        ]
        for pat in patterns:
            matches = re.findall(pat, all_text, re.IGNORECASE)
            for code in matches:
                if len(code) >= 4 and code not in found_codes:
                    found_codes.add(code)
                    print(f"\n{'='*50}")
                    print(f"发现验证码: {code}")
                    print(f"发件人: {sender} | 时间: {date}")
                    print(f"主题: {subject}")
                    print(f"预览: {body_preview[:200]}")
                    print(f"{'='*50}")
    
    if i == 0:
        print(f"\n当前收件箱最新{len(msgs)}封邮件:")
        for m in msgs[:5]:
            subject = m.get("subject", "无主题")
            sender = m.get("from", {}).get("emailAddress", {}).get("name", "?")
            date = m.get("receivedDateTime", "?")
            print(f"  [{date}] {sender}: {subject}")
    
    print(f"[{i+1}/30] 等待中... (第{i*3}秒)")
    time.sleep(3)

print(f"\n总共发现 {len(found_codes)} 个验证码: {found_codes}")
