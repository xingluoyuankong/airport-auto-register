"""通用Outlook验证码读取模块 - 供所有注册脚本复用"""
import requests, re, time, os

TOKEN_DIR = r"E:\.Outlook邮箱\批量注册邮箱\已经使用\1"

def load_all_tokens():
    """加载所有Graph API token"""
    tokens = {}
    for f in sorted(os.listdir(TOKEN_DIR)):
        if f.endswith("_combo.txt"):
            with open(os.path.join(TOKEN_DIR, f), encoding="utf-8") as fp:
                parts = fp.read().strip().split("----")
                if len(parts) >= 4:
                    tokens[parts[0].lower()] = {
                        "email": parts[0], "password": parts[1],
                        "cid": parts[2], "rt": parts[3]
                    }
    return tokens

def get_access_token(token_info):
    """refresh_token -> access_token"""
    r = requests.post(
        "https://login.microsoftonline.com/consumers/oauth2/v2.0/token",
        data={
            "client_id": token_info["cid"],
            "grant_type": "refresh_token",
            "refresh_token": token_info["rt"],
            "scope": "offline_access https://graph.microsoft.com/Mail.Read"
        }, timeout=15
    )
    if r.status_code == 200:
        return r.json().get("access_token")
    return None

def wait_for_code(email_addr, token_info, timeout=90, interval=3):
    """轮询Outlook等待验证码，返回(code, None)或(None, error_msg)"""
    deadline = time.time() + timeout
    seen_ids = set()
    token_refreshed_at = 0
    
    while time.time() < deadline:
        # 每20分钟刷新token
        if time.time() - token_refreshed_at > 1200:
            at = get_access_token(token_info)
            token_refreshed_at = time.time()
        if not at:
            at = get_access_token(token_info)
            if not at:
                time.sleep(interval)
                continue
        
        try:
            resp = requests.get(
                "https://graph.microsoft.com/v1.0/me/messages?$top=15&$select=id,subject,from,bodyPreview,body,receivedDateTime&$orderby=receivedDateTime desc",
                headers={"Authorization": f"Bearer {at}"}, timeout=10
            )
            if resp.status_code == 401:
                at = get_access_token(token_info)
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
                        return m.group(1), None
            
            time.sleep(interval)
        except Exception as e:
            time.sleep(interval)
    
    return None, "timeout"

# 邮箱池 - 用于分配未使用邮箱
AVAILABLE_EMAILS = [
    "mxc60da9b316@hotmail.com",
]
