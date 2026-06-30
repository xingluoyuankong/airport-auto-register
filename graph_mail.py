#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Graph API Outlook验证码读取 — 共享模块
从 E:\.Outlook邮箱\批量注册邮箱\已经使用\1\ 加载token
"""
import os, re, time, requests, io, sys
try: sys.stdout.reconfigure(encoding='utf-8')
except: sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8') if hasattr(sys.stdout,'buffer') else open('CONOUT$','w',encoding='utf-8')

TOKEN_DIR = r"E:\.Outlook邮箱\批量注册邮箱\已经使用\1"

def load_all_tokens():
    """加载所有Graph API token"""
    tokens = {}
    if not os.path.exists(TOKEN_DIR):
        return tokens
    for f in sorted(os.listdir(TOKEN_DIR)):
        if f.endswith("_combo.txt"):
            fp = os.path.join(TOKEN_DIR, f)
            with open(fp, encoding="utf-8") as fh:
                parts = fh.read().strip().split("----")
                if len(parts) >= 4:
                    tokens[parts[0].lower()] = {
                        "email": parts[0],
                        "password": parts[1],
                        "cid": parts[2],
                        "rt": parts[3],
                    }
    return tokens

def get_access_token(token_info):
    """refresh_token -> access_token"""
    try:
        r = requests.post(
            "https://login.microsoftonline.com/consumers/oauth2/v2.0/token",
            data={
                "client_id": token_info["cid"],
                "grant_type": "refresh_token",
                "refresh_token": token_info["rt"],
                "scope": "offline_access https://graph.microsoft.com/Mail.Read",
            },
            timeout=15,
        )
        if r.status_code == 200:
            return r.json().get("access_token")
    except:
        pass
    return None

def wait_for_code(email_addr, timeout=90, interval=3):
    """轮询Outlook等待验证码，返回(code, None)或(None, error_msg)"""
    tokens = load_all_tokens()
    key = email_addr.lower()
    if key not in tokens:
        return None, f"未找到token: {email_addr}"
    token_info = tokens[key]
    
    deadline = time.time() + timeout
    seen_ids = set()
    access_token = None
    token_refreshed_at = 0
    
    print(f"[Graph] 等待 {email_addr[:25]}... 验证码", flush=True)
    
    while time.time() < deadline:
        if time.time() - token_refreshed_at > 1200 or not access_token:
            access_token = get_access_token(token_info)
            token_refreshed_at = time.time()
        if not access_token:
            time.sleep(interval)
            continue
        
        try:
            resp = requests.get(
                "https://graph.microsoft.com/v1.0/me/messages?$top=15&$select=id,subject,from,bodyPreview,body,receivedDateTime&$orderby=receivedDateTime desc",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10,
            )
            if resp.status_code == 401:
                access_token = get_access_token(token_info)
                continue
            if resp.status_code != 200:
                time.sleep(interval)
                continue
            
            for msg in resp.json().get("value", []):
                mid = msg.get("id")
                if mid in seen_ids:
                    continue
                seen_ids.add(mid)
                
                text = f"{msg.get('subject','')} {msg.get('bodyPreview','') or ''} {msg.get('body',{}).get('content','') or ''}"
                
                for pat in [
                    r"(?:验证码|激活码|注册码|代码为)\D{0,20}?(\d{4,8})",
                    r"(?:verification|security|confirmation)\s*(?:code|pin)?\D{0,10}(\d{4,8})",
                    r"code\s*(?:is|:|：)\s*(\d{4,8})",
                    r"\b(\d{6})\b",
                ]:
                    m = re.search(pat, text, re.IGNORECASE)
                    if m and 4 <= len(m.group(1)) <= 8:
                        code = m.group(1)
                        print(f"[Graph] 找到: {code} (来自 {msg.get('subject','')[:40]})", flush=True)
                        return code, None
            
            time.sleep(interval)
        except Exception as e:
            time.sleep(interval)
    
    return None, "timeout"


if __name__ == "__main__":
    import sys
    email = sys.argv[1] if len(sys.argv) > 1 else "bushuozaijian2026@outlook.com"
    code, err = wait_for_code(email, timeout=30)
    if code:
        print(f"验证码: {code}")
    else:
        print(f"失败: {err}")
