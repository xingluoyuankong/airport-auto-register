#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""逐个验证机场注册API是否存活、是否支持免费注册"""
import requests
import json
import time
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AIRPORTS = [
    # V2Board类型的机场（用API验证）
    {"name": "FSCloud", "url": "https://dash.fscloud.app", "api": "/api/v1/passport/auth/register"},
    {"name": "奈云v2ny", "url": "https://www.v2ny.com", "api": "/api/v1/passport/auth/register"},
    {"name": "Speedy", "url": "https://cloud.speedypro.xyz", "api": "/api/v1/passport/auth/register"},
    {"name": "雨燕云", "url": "https://yuyan.online", "api": "/api/v1/passport/auth/register"},
    {"name": "逗猫", "url": "https://doucat.top", "api": "/api/v1/passport/auth/register"},
    {"name": "泰山Net", "url": "https://www.taishan.pro", "api": "/api/v1/passport/auth/register"},
    {"name": "一元机场", "url": "https://xn--4gq62f52gdss.top", "api": "/api/v1/passport/auth/register"},
    {"name": "魔戒", "url": "https://www.mojie.me", "api": "/api/v1/passport/auth/register"},
    {"name": "狗头加速", "url": "https://lksi.xyz", "api": "/api/v1/passport/auth/register"},
    {"name": "极光加速", "url": "https://jiguang.pro", "api": "/api/v1/passport/auth/register"},
    {"name": "besnow", "url": "https://besnow.me", "api": "/api/v1/passport/auth/register"},
    {"name": "tly", "url": "https://tly.one", "api": "/api/v1/passport/auth/register"},
    {"name": "寰宇云", "url": "https://huanyuyun.pro", "api": "/api/v1/passport/auth/register"},
    # 自定义面板类型（用GET验证主页）
    {"name": "GLaDOS", "url": "https://glados.rocks", "type": "custom"},
    {"name": "69云", "url": "https://69yun69.com", "type": "sspanel"},
    {"name": "aiguobit", "url": "https://a.aiguobit.com", "type": "hidexx"},
    {"name": "hidexx", "url": "https://a.hidexx.com", "type": "hidexx"},
    {"name": "大哥云", "url": "https://chinese.c-dageyun.com.cn", "type": "custom"},
    {"name": "一分机场", "url": "https://1yuan.surf", "type": "custom"},
    # GateRank机场
    {"name": "大象网络", "url": "https://www.elephant223.com", "type": "custom"},
    {"name": "NOW加速", "url": "https://nowjiasu.com", "type": "custom"},
    {"name": "瞬云", "url": "https://scloud.my", "type": "custom"},
    {"name": "COCODUCK", "url": "https://cocoduck.cc", "type": "custom"},
    {"name": "稳连云", "url": "https://wenlianyun.com", "type": "custom"},
    {"name": "山水云", "url": "https://xn--9kq015a4jm.com", "type": "custom"},
    {"name": "NICE加速", "url": "https://nisicloud.com", "type": "custom"},
]

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36"

def probe_v2board(name, url, api_path):
    """探测V2Board机场"""
    api_url = f"{url.rstrip('/')}{api_path}"
    
    # 用虚假邮箱POST探测，看响应
    payload = {"email": "test_probe_2026@outlook.com", "password": "ProbeTest123!"}
    headers = {
        "Content-Type": "application/json",
        "User-Agent": UA,
        "Accept": "application/json",
        "Origin": url,
    }
    
    result = {"name": name, "url": url, "api_url": api_url, "alive": False, "registerable": False, 
              "needs_verify": False, "needs_invite": False, "has_free": False, "message": "", "error": ""}
    
    # 先GET探测
    try:
        r = requests.get(api_url, headers={"User-Agent": UA}, timeout=10, allow_redirects=True)
        result["get_status"] = r.status_code
    except Exception as e:
        result["error"] = f"GET: {str(e)[:80]}"
        return result
    
    # POST探测
    try:
        r = requests.post(api_url, json=payload, headers=headers, timeout=15, allow_redirects=True)
        result["post_status"] = r.status_code
        
        if r.status_code in [200, 400, 422, 429]:
            result["alive"] = True
            try:
                data = r.json()
                msg = str(data.get("message", data.get("msg", "")))
                result["message"] = msg[:200]
                
                msg_lower = msg.lower()
                # 需要邮箱验证码 → 说明可以注册
                if any(kw in msg_lower for kw in ["email", "verify", "验证", "code", "发送", "send", "mail", "激活"]):
                    result["needs_verify"] = True
                    result["registerable"] = True
                    result["has_free"] = True  # 能注册就有免费额度（需进一步确认）
                # 需要邀请码 → 不能公开注册
                elif any(kw in msg_lower for kw in ["invite", "邀请", "referral", "close", "关闭", "disable", "禁止", "维护"]):
                    result["needs_invite"] = True
                    result["registerable"] = False
                # 其他情况
                else:
                    result["registerable"] = r.status_code in [200, 400]
            except:
                result["registerable"] = r.status_code in [200, 400]
                result["message"] = r.text[:200]
        elif r.status_code == 403:
            result["alive"] = True
            result["registerable"] = False
            result["message"] = "403 Cloudflare拦截"
        else:
            result["message"] = f"HTTP {r.status_code}"
    except requests.exceptions.Timeout:
        result["error"] = "POST超时"
    except requests.exceptions.ConnectionError:
        result["error"] = "连接失败（DNS/GFW拦截）"
    except Exception as e:
        result["error"] = f"POST: {str(e)[:80]}"
    
    return result

def probe_custom(name, url):
    """探测非V2Board机场（GET主页检查是否在线）"""
    result = {"name": name, "url": url, "alive": False, "has_register": False, "error": ""}
    
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=10, allow_redirects=True)
        result["alive"] = True
        result["status"] = r.status_code
        
        html_lower = r.text.lower()
        result["has_register"] = any(kw in html_lower for kw in ["register", "signup", "注册", "试用", "trial", "free"])
        result["has_free_hint"] = any(kw in html_lower for kw in ["免费", "试用", "free trial", "trial", "体验"])
        result["title"] = (r.text.split("<title>")[1].split("</title>")[0] if "<title>" in r.text else "")[:100]
        
    except requests.exceptions.Timeout:
        result["error"] = "超时"
    except requests.exceptions.ConnectionError:
        result["error"] = "连接失败/DNS/GFW拦截"
    except Exception as e:
        result["error"] = str(e)[:80]
    
    return result


def main():
    print(f"{'='*70}")
    print(f"  机场注册API验证 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}")
    
    v2board_results = []
    custom_results = []
    
    # 验证V2Board机场
    print("\n[V2Board API验证]")
    print("-" * 70)
    
    for ap in AIRPORTS:
        if ap.get("api"):
            print(f"\n>>> {ap['name']} ({ap['url']})")
            result = probe_v2board(ap['name'], ap['url'], ap['api'])
            v2board_results.append(result)
            
            status = "✅" if result["alive"] else "❌"
            reg = "🟢可注册" if result["registerable"] else "🔴不可注册"
            verify = "📧需验证码" if result["needs_verify"] else ""
            invite = "🎫需邀请码" if result["needs_invite"] else ""
            free = "🆓有免费" if result["has_free"] else ""
            
            print(f"  {status} {reg} {verify} {invite} {free}")
            if result.get("message"):
                print(f"  📝 {result['message'][:120]}")
            if result.get("error"):
                print(f"  ⚠️ {result['error'][:120]}")
            time.sleep(0.5)
    
    # 验证自定义面板
    print(f"\n\n[自定义面板验证]")
    print("-" * 70)
    
    for ap in AIRPORTS:
        if not ap.get("api"):
            print(f"\n>>> {ap['name']} ({ap['url']})")
            result = probe_custom(ap['name'], ap['url'])
            custom_results.append(result)
            
            status = "✅在线" if result["alive"] else "❌离线"
            reg = "🟢有注册" if result["has_register"] else ""
            free_hint = "🆓有免费字样" if result["has_free_hint"] else ""
            
            print(f"  {status} {reg} {free_hint}")
            if result.get("title"):
                print(f"  📄 {result['title'][:100]}")
            if result.get("error"):
                print(f"  ⚠️ {result['error'][:120]}")
            time.sleep(0.5)
    
    # 汇总
    print(f"\n\n{'='*70}")
    print(f"  验证汇总")
    print(f"{'='*70}")
    
    print("\n📊 V2Board可注册机场:")
    for r in v2board_results:
        if r["registerable"] and r["alive"]:
            tag = "📧需邮箱验证" if r["needs_verify"] else "可直接注册"
            print(f"  ✅ {r['name']}: {r['url']} ({tag})")
        elif r["alive"] and not r["registerable"]:
            tag = "🎫需邀请码" if r["needs_invite"] else "注册关闭"
            print(f"  ⚠️ {r['name']}: {r['url']} ({tag})")
        else:
            print(f"  ❌ {r['name']}: 不可达 - {r.get('error', r.get('message', ''))[:60]}")
    
    print("\n📊 自定义面板在线机场:")
    for r in custom_results:
        if r["alive"]:
            tag = ""
            if r["has_register"]: tag += "有注册入口 "
            if r["has_free_hint"]: tag += "有免费字样"
            print(f"  ✅ {r['name']}: {r['url']} {tag}")
        else:
            print(f"  ❌ {r['name']}: {r['url']} - {r.get('error', '')[:60]}")
    
    # 保存JSON
    all_results = v2board_results + custom_results
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f"verify_results_{ts}.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"\n📁 详细结果已保存: verify_results_{ts}.json")
    
    print(f"\n{'='*70}")
    print(f"  总计: {len(AIRPORTS)}个机场 | V2Board在线可注册: {sum(1 for r in v2board_results if r['registerable'])}个")
    print(f"{'='*70}")

if __name__ == "__main__":
    main()
