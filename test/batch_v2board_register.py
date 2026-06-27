# -*- coding: utf-8 -*-
"""批量V2Board机场注册 - API+Graph验证码"""
import requests, json, re, time, os

# ===== 配置 =====
GRAPH_TOKEN_URL = "https://login.microsoftonline.com/consumers/oauth2/v2.0/token"
GRAPH_API = "https://graph.microsoft.com/v1.0/me"

# 读取所有combo token文件
TOKEN_DIR = r"E:\.Outlook邮箱\批量注册邮箱\已经使用\1"
token_accounts = []
for f in sorted(os.listdir(TOKEN_DIR)):
    if f.endswith("_combo.txt"):
        with open(os.path.join(TOKEN_DIR, f), encoding="utf-8") as fp:
            parts = fp.read().strip().split("----")
            if len(parts) >= 4:
                token_accounts.append({
                    "email": parts[0].lower(),
                    "password": parts[1],
                    "cid": parts[2],
                    "rt": parts[3],
                    "file": f
                })

REGISTER_EMAIL = "mxc60da9b316@hotmail.com"
REGISTER_PASSWORD = "VpnTest2026!"

# ===== V2Board机场列表 =====
AIRPORTS = [
    ("雨燕云", "https://yuyan.online", "", "[8h 1G免费]"),
    ("FSCloud", "https://dash.fscloud.app", "", "[3天试用]"),
    ("奈云", "https://www.v2ny.com", "", "[3天5G]"),
    ("NOW加速", "https://nowjiasu.com", "", ""),
    ("瞬云", "https://shunyun.xyz", "", ""),
    ("仙路湾", "https://xianluwan.com", "", ""),
    ("山水云", "https://shanshuiyun.com", "", ""),
    ("NICE加速", "https://nicejiasu.com", "", ""),
    ("锦云", "https://jinyun.pro", "", ""),
    ("寰宇云", "https://huanyuyun.com", "", ""),
    ("秒秒云", "https://miaomiaoyun.com", "", ""),
    ("SKYLUMO", "https://skylumo.com", "", ""),
    ("宇宙云", "https://yuzhouyun.com", "", ""),
    ("光年梯", "https://guangnianti.com", "", ""),
    ("besnow", "https://besnow.me", "", ""),
    ("泰山Net", "https://www.taishan.pro", "", ""),
    ("69云", "https://69yun69.com", "", ""),
    ("一元机场old", "https://xn--4gq62f52gdss.top", "", ""),
    ("aiguobit", "https://a.aiguobit.com", "", "[1天试用]"),
    ("hidexx", "https://a.hidexx.com", "", "[1天试用]"),
]

# ===== Graph API =====
def get_access_token(token_info):
    """用refresh_token换取access_token"""
    r = requests.post(GRAPH_TOKEN_URL, data={
        "client_id": token_info["cid"],
        "grant_type": "refresh_token",
        "refresh_token": token_info["rt"],
        "scope": "offline_access https://graph.microsoft.com/Mail.Read"
    }, timeout=15)
    if r.status_code == 200:
        return r.json().get("access_token")
    return None

def get_code_from_outlook(email_addr, token_info, wait_seconds=45):
    """用Graph API轮询获取验证码"""
    at = get_access_token(token_info)
    if not at:
        print("    Graph token failed")
        return None
    
    deadline = time.time() + wait_seconds
    last_ids = set()
    
    while time.time() < deadline:
        try:
            resp = requests.get(
                f"{GRAPH_API}/messages?$top=10&$select=id,subject,from,bodyPreview,body,receivedDateTime&$orderby=receivedDateTime desc",
                headers={"Authorization": f"Bearer {at}"},
                timeout=10
            )
            if resp.status_code == 401:
                at = get_access_token(token_info)
                if not at: break
                continue
            if resp.status_code != 200:
                time.sleep(3)
                continue
            
            messages = resp.json().get("value", [])
            for msg in messages:
                mid = msg.get("id")
                if mid in last_ids:
                    continue
                last_ids.add(mid)
                
                subject = msg.get("subject", "")
                body_text = (msg.get("bodyPreview", "") or "") + " " + (msg.get("body", {}).get("content", "") or "")
                full_text = subject + " " + body_text
                
                patterns = [
                    r"(?:验证码|激活码|注册码|代码为)\D{0,20}?(\d{4,8})",
                    r"(?:verification|security|confirmation)\s*(?:code|pin)?\D{0,10}(\d{4,8})",
                    r"code\s*(?:is|:|：)\s*(\d{4,8})",
                    r"\b(\d{6})\b",
                ]
                for pat in patterns:
                    m = re.search(pat, full_text, re.IGNORECASE)
                    if m:
                        code = m.group(1)
                        if 4 <= len(code) <= 8:
                            print(f"    [CODE] {code} (from: {subject[:40]})")
                            return code
            time.sleep(3)
        except Exception as e:
            print(f"    Graph err: {e}")
            time.sleep(3)
    
    return None

# ===== V2Board注册 =====
def try_register_v2board(name, base_url, email, password, invite_code, token_info):
    """两步注册"""
    api = base_url.rstrip("/") + "/api/v1/passport/auth/register"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Origin": base_url,
        "Referer": base_url + "/",
    }
    
    payload = {
        "email": email,
        "password": password,
        "email_code": "",
        "invite_code": invite_code,
        "recaptcha_data": ""
    }
    
    try:
        r1 = requests.post(api, json=payload, headers=headers, timeout=15)
        status = r1.status_code
        text = r1.text[:200]
        print(f"    Step1: {status}")
        
        # 非200/400 = API不存在或不同
        if status not in [200, 400, 422, 429]:
            print(f"    API not found or blocked ({status})")
            return None, None
        
        # 200 = 可能直接成功或返回提示
        if status == 200:
            data = r1.json().get("data", {})
            token = data.get("token") or data.get("auth_data")
            if token:
                print(f"    Registered directly! token={token[:30]}...")
                sub = get_subscribe_link(base_url, token)
                return sub, token
        
        # 400/422 = 需要验证码或其他错误
        print(f"    Need code, waiting...")
        code = get_code_from_outlook(email, token_info, wait_seconds=60)
        if not code:
            print(f"    No code received")
            return None, None
        
        # 带码重试
        payload["email_code"] = code
        r2 = requests.post(api, json=payload, headers=headers, timeout=15)
        print(f"    Step2: {r2.status_code} | {r2.text[:80]}")
        
        if r2.status_code == 200:
            data = r2.json().get("data", {})
            token = data.get("token") or data.get("auth_data")
            if token:
                print(f"    Registered!")
                sub = get_subscribe_link(base_url, token)
                return sub, token
        
        return None, None
        
    except requests.exceptions.ConnectionError:
        print(f"    Connection failed (blocked)")
        return None, None
    except Exception as e:
        print(f"    Error: {e}")
        return None, None

def get_subscribe_link(base_url, auth_token):
    api = base_url.rstrip("/") + "/api/v1/user/getSubscribe"
    try:
        r = requests.get(api, headers={
            "Authorization": auth_token,
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json"
        }, timeout=10)
        if r.status_code == 200:
            data = r.json().get("data", {})
            sub = data.get("subscribe_url", "")
            return sub if sub else None
    except:
        pass
    return None

# ===== 主流程 =====
if __name__ == "__main__":
    print("=" * 60)
    print("V2Board Batch Register (API + Graph Code)")
    print("=" * 60)
    
    token_map = {t["email"]: t for t in token_accounts}
    print(f"Tokens: {len(token_map)}, Register email: {REGISTER_EMAIL}")
    
    # 找token
    ti = token_map.get(REGISTER_EMAIL)
    if not ti:
        print(f"No token for {REGISTER_EMAIL}, using first available")
        ti = list(token_map.values())[0] if token_map else None
    
    if not ti:
        print("FATAL: No token available")
        exit(1)
    
    print(f"Using token: {ti['email']} ({ti['file']})")
    
    results = []
    
    for name, base_url, invite, note in AIRPORTS:
        print(f"\n{'='*40}")
        print(f"[{name}] {base_url} {note}")
        
        sub_url, token = try_register_v2board(name, base_url, REGISTER_EMAIL, REGISTER_PASSWORD, invite, ti)
        
        if sub_url:
            results.append({"name": name, "url": base_url, "email": REGISTER_EMAIL, "sub": sub_url, "token": token[:40] if token else ""})
            print(f"    SUB: {sub_url}")
        elif token:
            results.append({"name": name, "url": base_url, "email": REGISTER_EMAIL, "sub": "", "token": token[:40]})
            print(f"    Token: {token[:40]}...")
        
        time.sleep(1.5)
    
    # 最终汇总
    print(f"\n{'='*60}")
    print(f"RESULTS: {len([r for r in results if r['sub']])}/{len(results)} with subscribe URL")
    print(f"{'='*60}")
    for r in results:
        status = "[SUB]" if r["sub"] else "[TOKEN]"
        print(f"  {status} {r['name']:<12} {r['email']} {r['sub'][:60] if r['sub'] else r['token']}")
    
    # 保存结果
    with open(os.path.join(os.path.dirname(__file__), "..", "register_results", "v2board_batch_results.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nSaved to register_results/v2board_batch_results.json")
