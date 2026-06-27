#!/usr/bin/env python3
import requests, json, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

proxies = {'http': 'http://127.0.0.1:7897', 'https': 'http://127.0.0.1:7897'}
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/131.0.0.0 Safari/537.36'

AIRPORTS = [
    ("FSCloud", "https://dash.fscloud.app"),
    ("奈云v2ny", "https://www.v2ny.com"),
    ("Speedy", "https://cloud.speedypro.xyz"),
    ("雨燕云", "https://yuyan.online"),
    ("逗猫", "https://doucat.top"),
    ("泰山Net", "https://www.taishan.pro"),
    ("一元机场", "https://xn--4gq62f52gdss.top"),
    ("魔戒", "https://www.mojie.me"),
    ("狗头加速", "https://lksi.xyz"),
    ("极光加速", "https://jiguang.pro"),
    ("besnow", "https://besnow.me"),
    ("tly", "https://tly.one"),
    ("寰宇云", "https://huanyuyun.pro"),
    ("GLaDOS", "https://glados.rocks"),
    ("69云", "https://69yun69.com"),
    ("aiguobit", "https://a.aiguobit.com"),
    ("hidexx", "https://a.hidexx.com"),
    ("大哥云", "https://chinese.c-dageyun.com.cn"),
    ("一分机场", "https://1yuan.surf"),
    ("大象网络", "https://www.elephant223.com"),
    ("NOW加速", "https://nowjiasu.com"),
    ("瞬云", "https://scloud.my"),
    ("COCODUCK", "https://cocoduck.cc"),
    ("稳连云", "https://wenlianyun.com"),
    ("山水云", "https://xn--9kq015a4jm.com"),
]

results = []

for name, base_url in AIRPORTS:
    api_url = f"{base_url.rstrip('/')}/api/v1/passport/auth/register"
    print(f"\n>>> {name}: {base_url}")
    
    result = {"name": name, "url": base_url, "alive": False, "registerable": False, 
              "needs_verify": False, "needs_invite": False, "has_free_trial": False, "msg": ""}
    
    try:
        # GET
        r = requests.get(api_url, headers={"User-Agent": UA}, proxies=proxies, timeout=10, allow_redirects=True)
        get_status = r.status_code
        
        # POST with fake email
        payload = {"email": "probe_test_2026@outlook.com", "password": "ProbeTest123456!"}
        r2 = requests.post(api_url, json=payload, 
                          headers={"Content-Type": "application/json", "User-Agent": UA, "Origin": base_url},
                          proxies=proxies, timeout=12, allow_redirects=True)
        post_status = r2.status_code
        
        result["alive"] = True
        result["get_status"] = get_status
        result["post_status"] = post_status
        
        try:
            data = r2.json()
            msg = data.get("message", data.get("msg", ""))
        except:
            msg = r2.text[:200]
        
        result["msg"] = str(msg)[:200]
        msg_lower = str(msg).lower()
        
        if any(k in msg_lower for k in ["email", "verify", "验证", "code", "send", "发送", "mail", "激活", "sent"]):
            result["needs_verify"] = True
            result["registerable"] = True
            result["has_free_trial"] = True
            print(f"  [OK] 在线 可注册(需邮箱验证) -> {str(msg)[:100]}")
        elif any(k in msg_lower for k in ["invite", "邀请", "close", "关闭", "disable", "禁止", "维护", "required"]):
            result["needs_invite"] = True
            print(f"  [WARN] 在线 但需邀请码/已关闭 -> {str(msg)[:100]}")
        elif post_status in [200, 400, 422]:
            result["registerable"] = True
            print(f"  [OK] 在线 HTTP{post_status} -> {str(msg)[:100]}")
        else:
            print(f"  [WARN] HTTP{post_status} -> {str(msg)[:100]}")
            
    except requests.exceptions.Timeout:
        print(f"  [ERR] 超时")
        result["msg"] = "超时"
    except requests.exceptions.ConnectionError as e:
        print(f"  [ERR] 连接失败: {str(e)[:60]}")
        result["msg"] = f"连接失败: {str(e)[:60]}"
    except Exception as e:
        print(f"  [ERR] {str(e)[:80]}")
        result["msg"] = str(e)[:80]
    
    results.append(result)
    time.sleep(0.3)

# Summary
print(f"\n\n{'='*60}")
print(f"  验证结果汇总")
print(f"{'='*60}")

online = [r for r in results if r["alive"]]
registerable = [r for r in results if r["registerable"]]
needs_verify = [r for r in results if r["needs_verify"]]
offline = [r for r in results if not r["alive"]]

print(f"\n在线且可注册(需邮箱验证): {len(needs_verify)}个")
for r in needs_verify:
    print(f"  [V2Board] {r['name']}: {r['url']}")

print(f"\n在线但需邀请码/已关闭: {len([r for r in online if r['needs_invite']])}个")
for r in online:
    if r["needs_invite"]:
        print(f"  [INVITE] {r['name']}: {r['url']}")

print(f"\n离线/不可达: {len(offline)}个")
for r in offline:
    print(f"  [OFFLINE] {r['name']}: {r['url']} - {r['msg'][:60]}")

# Save
with open("probe_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"\n结果已保存: probe_results.json")
