# -*- coding: utf-8 -*-
"""
批量机场注册 - 纯 urllib (无需 requests 模块)
代理: 127.0.0.1:7897 (Clash Verge HTTP)
"""
import json, os, time, re, ssl, urllib.request, urllib.error, http.client

PROXY_HOST = "127.0.0.1"
PROXY_PORT = 7897

EMAILS = [
    ("sanchezquinncu3w1kkhtuc74@outlook.com", "3pKPx5!rE9%9nJDLJC"),
    ("hendricktamm95v80awzaxli@outlook.com", "@^NdxP5KN#s9G2Hqu0!"),
    ("parker738403dcp34kfdl6j@outlook.com", "oo^5v=Q%&RU$pdDrax"),
]

AIRPORTS = [
    {"name": "奈云v2ny", "url": "https://www.v2ny.com/api/v1/passport/auth/register", "trial": "3天5G"},
    {"name": "Speedy", "url": "https://cloud.speedypro.xyz/api/v1/passport/auth/register", "trial": "7天10G"},
    {"name": "雨燕云", "url": "https://yuyan.online/api/v1/passport/auth/register", "trial": "8h1G"},
    {"name": "逗猫", "url": "https://doucat.top/api/v1/passport/auth/register", "trial": "1天3G"},
    {"name": "泰山Net", "url": "https://www.taishan.pro/api/v1/passport/auth/register", "trial": "7天10G"},
    {"name": "一元机场", "url": "https://xn--4gq62f52gdss.top/api/v1/passport/auth/register", "trial": "11元/年"},
    {"name": "besnow", "url": "https://besnow.me/api/v1/passport/auth/register", "trial": "3天9G"},
    {"name": "魔戒", "url": "https://www.mojie.me/api/v1/passport/auth/register", "trial": "1元2G"},
    {"name": "FSCloud", "url": "https://dash.fscloud.app/api/v1/passport/auth/register", "trial": "3天10G"},
    {"name": "狗头加速", "url": "https://lksi.xyz/api/v1/passport/auth/register", "trial": "5天5G"},
    {"name": "GLaDOS", "url": "https://glados.space/api/user/register", "trial": "4天+签到续"},
]

OUTPUT_DIR = r"E:\API获取工具\自动集成免费代理服务\01-机场VPN注册机\register_results"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 不验证 SSL
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def proxy_post(url_str, data_bytes, content_type="application/json"):
    """通过 HTTP 代理发 POST 请求"""
    p = urllib.parse.urlparse(url_str)
    # 创建到代理的 HTTPS 连接
    conn = http.client.HTTPSConnection(PROXY_HOST, PROXY_PORT, context=ctx, timeout=15)
    conn.set_tunnel(p.hostname, p.port)
    
    headers = {
        "Host": p.hostname,
        "Content-Type": content_type,
        "Content-Length": str(len(data_bytes)),
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0",
        "Accept": "application/json",
        "Origin": f"{p.scheme}://{p.hostname}",
        "Referer": f"{p.scheme}://{p.hostname}/",
    }
    
    try:
        conn.request("POST", p.path + ("?" + p.query if p.query else ""), 
                    body=data_bytes, headers=headers)
        resp = conn.getresponse()
        body = resp.read().decode("utf-8", errors="replace")
        conn.close()
        return resp.status, body
    except Exception as e:
        try:
            conn.close()
        except:
            pass
        raise e


def proxy_get(url_str):
    """通过 HTTP 代理发 GET 请求"""
    p = urllib.parse.urlparse(url_str)
    conn = http.client.HTTPSConnection(PROXY_HOST, PROXY_PORT, context=ctx, timeout=15)
    conn.set_tunnel(p.hostname, p.port)
    
    headers = {
        "Host": p.hostname,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0",
        "Accept": "application/json",
    }
    
    try:
        conn.request("GET", p.path + ("?" + p.query if p.query else ""), 
                    headers=headers)
        resp = conn.getresponse()
        body = resp.read().decode("utf-8", errors="replace")
        conn.close()
        return resp.status, body
    except Exception as e:
        try:
            conn.close()
        except:
            pass
        raise e


def register_v2board(airport, email, password):
    """V2Board API 注册"""
    # 尝试多种payload变体
    variants = [
        {"email": email, "password": password},
        {"email": email, "password": password, "invite_code": ""},
        {"email": email, "password": password, "email_code": "", "invite_code": "", "recaptcha_data": ""},
    ]
    
    last_err = "unknown"
    for i, payload in enumerate(variants):
        try:
            data = json.dumps(payload).encode("utf-8")
            status, body = proxy_post(airport["url"], data)
            print(f"  POST v{i} -> {status} | {body[:200]}")
            
            if status == 200:
                try:
                    d = json.loads(body)
                except:
                    return {"status": "not_json", "reason": body[:100]}
                
                if "data" in d and d["data"]:
                    token = d["data"].get("token", "")
                    return {"status": "ok", "token": token, "raw": body[:300]}
                
                msg = d.get("message", "") or d.get("msg", "")
                if msg and ("成功" in msg or "success" in msg.lower()):
                    return {"status": "ok", "msg": msg}
                
                # 邮箱已存在
                if "已存在" in msg or "exist" in msg.lower() or "registered" in msg.lower():
                    return {"status": "duplicate", "reason": msg[:100]}
                
                return {"status": "refused", "reason": msg[:150]}
            
            if status == 422:
                try:
                    d = json.loads(body)
                except:
                    d = {}
                msg = d.get("message", "") or d.get("msg", "") or body[:100]
                if "已存在" in msg or "exist" in msg.lower():
                    return {"status": "duplicate", "reason": msg[:100]}
                return {"status": "validation", "reason": msg[:200]}
            
            if status in (403, 429):
                return {"status": "blocked", "reason": f"HTTP_{status}"}
            
        except Exception as e:
            last_err = str(e)[:100]
            # 继续尝试其他变体
            continue
    
    return {"status": "net_err", "reason": last_err}


def get_subscription(base_url, token):
    """获取订阅链接"""
    sub_paths = ["/api/v1/user/getSubscribe", "/api/v1/user/getSubUrl"]
    for sp in sub_paths:
        try:
            p = urllib.parse.urlparse(base_url)
            conn = http.client.HTTPSConnection(PROXY_HOST, PROXY_PORT, context=ctx, timeout=10)
            conn.set_tunnel(p.hostname, p.port)
            headers = {
                "Host": p.hostname,
                "Authorization": f"Bearer {token}",
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json",
            }
            conn.request("GET", sp, headers=headers)
            resp = conn.getresponse()
            body = resp.read().decode("utf-8", errors="replace")
            conn.close()
            
            if resp.status == 200:
                try:
                    d = json.loads(body)
                    data = d.get("data", {})
                    if isinstance(data, str) and "://" in data:
                        return data
                    sub = data.get("subscribe_url", "")
                    if sub and "://" in sub:
                        return sub
                except:
                    pass
        except:
            pass
    return None


def main():
    results = []
    
    for ap in AIRPORTS:
        name = ap["name"]
        base = re.sub(r'/api/.*', '', ap["url"])
        print(f"\n{'='*60}")
        print(f"[{name}] {ap.get('trial','')} | {ap['url'][:60]}")
        
        for email, password in EMAILS:
            print(f"\n  [EMAIL] {email[:30]}...")
            
            result = register_v2board(ap, email, password)
            print(f"  -> {result['status']}: {result.get('reason','')[:80]}")
            
            entry = {
                "airport": name, "url": ap["url"], "email": email,
                "password": password, "status": result["status"],
            }
            
            if result["status"] == "ok":
                token = result.get("token", "")
                entry["token"] = token
                if token:
                    sub_url = get_subscription(base, token)
                    if sub_url:
                        entry["subscribe_url"] = sub_url
                        print(f"  SUB: {sub_url[:80]}")
                        with open(os.path.join(OUTPUT_DIR, f"{name}_subscriptions.txt"), "a", encoding="utf-8") as f:
                            f.write(f"{email} | {sub_url}\n")
                results.append(entry)
            
            elif result["status"] == "duplicate":
                print(f"  (邮箱已存在该机场)")
                results.append(entry)
            
            else:
                results.append(entry)
            
            time.sleep(2)
        
        time.sleep(3)
    
    # 输出汇总
    print("\n\n" + "="*60)
    print("REGISTER RESULTS SUMMARY")
    print("="*60)
    success = [r for r in results if r["status"] == "ok"]
    dup = [r for r in results if r["status"] == "duplicate"]
    fail = [r for r in results if r["status"] not in ("ok", "duplicate")]
    
    print(f"\nSUCCESS: {len(success)}")
    for r in success:
        print(f"  + {r['airport']}: {r['email'][:30]} | sub={r.get('subscribe_url','N/A')[:60]}")
    
    print(f"\nDUPLICATE: {len(dup)}")
    for r in dup:
        print(f"  = {r['airport']}: {r['email'][:30]}")
    
    print(f"\nFAILED: {len(fail)}")
    fail_map = {}
    for r in fail:
        k = r.get("reason", "unknown")[:60]
        fail_map[k] = fail_map.get(k, 0) + 1
    for k, v in sorted(fail_map.items(), key=lambda x: -x[1]):
        print(f"  - {k}: x{v}")
    
    json_path = os.path.join(OUTPUT_DIR, f"full_results_{int(time.time())}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nFULL RESULTS: {json_path}")


if __name__ == "__main__":
    import urllib.parse
    main()
