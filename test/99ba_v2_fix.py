#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""99吧 修复版注册 — 套用 FLYBIT 成功模式"""
import sys, os, io, json, time, re
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7897'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7897'
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests as req
from playwright.sync_api import sync_playwright

TD = r"E:\.Outlook邮箱\批量注册邮箱\已经使用\1"

def find_token(email):
    for f in os.listdir(TD):
        if email.lower() in f.lower() and f.endswith("_combo.txt"):
            with open(os.path.join(TD, f), encoding="utf-8") as fh:
                p = fh.read().strip().split("----")
                if len(p) >= 4:
                    return {"clientId": p[2], "refreshToken": p[3]}
    return None

def wait_code(email_addr, timeout=120):
    tk = find_token(email_addr)
    if not tk: return None, "no token file"
    deadline = time.time() + timeout
    at = None; at_time = 0; seen = set()
    print(f"  [Graph] 等待验证码...", flush=True)
    while time.time() < deadline:
        try:
            if not at or time.time() - at_time > 900:
                r = req.post("https://login.microsoftonline.com/consumers/oauth2/v2.0/token",
                    data={"client_id": tk["clientId"], "grant_type": "refresh_token",
                          "refresh_token": tk["refreshToken"],
                          "scope": "offline_access https://graph.microsoft.com/Mail.Read"},
                    timeout=20)
                if r.status_code == 200:
                    at = r.json().get("access_token", "")
                    at_time = time.time()
                else:
                    time.sleep(5); continue
            if not at: time.sleep(5); continue
            
            resp = req.get("https://graph.microsoft.com/v1.0/me/messages?$top=15&$select=id,subject,bodyPreview,receivedDateTime&$orderby=receivedDateTime desc",
                headers={"Authorization": f"Bearer {at}"}, timeout=15)
            if resp.status_code != 200: time.sleep(4); continue
            
            for msg in resp.json().get("value", []):
                mid = msg.get("id", "")
                if mid in seen: continue
                seen.add(mid)
                combined = f"{msg.get('subject','')} {msg.get('bodyPreview','')}"
                for pat in [r"(?:验证码|激活码|verification.code)\D{0,30}?(\d{4,8})", r"code[:=]\s*(\d{4,8})", r"\b(\d{6})\b"]:
                    m = re.search(pat, combined, re.I)
                    if m:
                        code = m.group(1)
                        if code in ("000000","111111","222222","999999","123456"): continue
                        if 4 <= len(code) <= 8:
                            print(f"  [Graph] ✅ 验证码={code}", flush=True)
                            return code, None
            time.sleep(4)
        except Exception as e:
            print(f"  [Graph] 异常: {e}", flush=True)
            time.sleep(5)
    return None, "timeout"

EMAIL = "broomilerfhecolvl7jsm@outlook.com"
PASS = "VpnTest2026!"
prefix, suffix = EMAIL.split("@", 1)
suffix = "@" + suffix

print("=" * 60)
print(f"  99吧 修复版: {EMAIL}")
print("=" * 60)

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=False,
        args=["--proxy-server=http://127.0.0.1:7897", "--ignore-certificate-errors", "--no-sandbox"])
    ctx = browser.new_context(viewport={"width": 1280, "height": 900},
        ignore_https_errors=True, locale="zh-CN")
    page = ctx.new_page()
    page.set_default_timeout(20000)
    
    page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {get: ()=>false});
        Object.defineProperty(MouseEvent.prototype, 'screenX', {
            get: function(){ return (this.clientX||0) + Math.floor(Math.random()*400)+80; }
        });
    """)
    
    try:
        print("\n[1] 打开注册页...", flush=True)
        page.goto("https://a.99ba2026.fyi/#/register", wait_until="networkidle", timeout=45000)
        time.sleep(4)
        body = page.evaluate("() => document.body.innerText")
        print(f"  页面(400):\n{body[:400]}", flush=True)
        
        # 填邮箱前缀 (99ba用 placeholder*="邮箱")
        print(f"\n[2] 填前缀: {prefix}", flush=True)
        page.fill('input[placeholder*="邮箱"]', prefix)
        time.sleep(0.5)
        
        print(f"  选后缀: {suffix}", flush=True)
        page.click(".n-base-selection-label")
        time.sleep(1)
        page.click(f"text={suffix}")
        time.sleep(1)
        
        # 密码
        print("[3] 密码...", flush=True)
        pws = page.query_selector_all('input[type="password"]')
        for pw in pws:
            try: pw.fill(PASS); time.sleep(0.3)
            except: pass
        
        # 发码
        print("[4] 发码...", flush=True)
        for t in ["发送", "获 取"]:
            try:
                page.click(f'button:has-text("{t}")', timeout=3000)
                print(f"  已点击 {t}", flush=True)
                time.sleep(2); break
            except: continue
        
        # 收码
        print("[5] 收码...", flush=True)
        code, err = wait_code(EMAIL, timeout=120)
        if not code: print(f"❌ {err}"); browser.close(); exit(1)
        
        # 填码
        print(f"[6] 填码: {code}", flush=True)
        page.fill('input[placeholder*="验证码"], input[name*="code"]', code)
        time.sleep(0.5)
        
        # 注册
        print("[7] 注册...", flush=True)
        for t in ["注册", "注 册"]:
            try:
                page.click(f'button:has-text("{t}")', timeout=3000)
                print(f"  已点击 {t}", flush=True)
                break
            except: continue
        
        time.sleep(8)
        try: page.wait_for_load_state("networkidle", timeout=15000)
        except: pass
        
        print(f"  注册后URL: {page.url}", flush=True)
        body2 = page.evaluate("() => document.body.innerText")
        print(f"  页面(500):\n{body2[:500]}", flush=True)
        
        # 如果有登录页
        if "/login" in page.url or "登录" in body2:
            print("  → 自动登录...", flush=True)
            page.fill('input[placeholder*="邮箱"]', prefix)
            time.sleep(0.3)
            try:
                page.click(".n-base-selection-label"); time.sleep(0.5)
                page.click(f"text={suffix}"); time.sleep(0.5)
            except: pass
            page.fill('input[type="password"]', PASS)
            time.sleep(0.3)
            for t in ["登录", "登 录"]:
                try:
                    page.click(f'button:has-text("{t}")', timeout=3000)
                    time.sleep(5); break
                except: continue
            print(f"  登录后URL: {page.url}", flush=True)
        
        # 提取
        print("[8] 提取订阅...", flush=True)
        raw = page.evaluate("localStorage.getItem('VUE_NAIVE_ACCESS_TOKEN')")
        print(f"  TOKEN: {(raw or 'NONE')[:200]}", flush=True)
        
        if raw:
            resp = page.evaluate("""
                (() => {
                    let raw = localStorage.getItem('VUE_NAIVE_ACCESS_TOKEN');
                    if (!raw) return 'NO_TOKEN';
                    let tok = '';
                    try { let p = JSON.parse(raw); tok = p.value || p.token || p; } catch(e) { tok = raw; }
                    let x = new XMLHttpRequest();
                    x.open('GET', '/api/v1/user/getSubscribe', false);
                    x.setRequestHeader('Authorization', tok);
                    try { x.send(); } catch(e) { return x.responseText; }
                    return x.responseText;
                })()
            """)
            print(f"  getSubscribe: {resp}", flush=True)
            
            try:
                d = json.loads(resp)
                sub_url = d.get("data", {}).get("subscribe_url", "") or d.get("subscribe_url", "")
            except:
                urls = re.findall(r'subscribe_url["\s:]+(https?://[^"\s]+)', resp)
                sub_url = urls[0] if urls else ""
            
            if sub_url:
                print(f"  ✅ 订阅: {sub_url}", flush=True)
                result = {"airport":"99ba","panel":"a.99ba2026.fyi","email":EMAIL,"password":PASS,"subscribe_url":sub_url}
                with open(os.path.join(os.path.dirname(__file__), f"99ba_{prefix}.json"), "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                time.sleep(5)
                browser.close()
                exit(0)
        
        # 备用查找
        sub_url = page.evaluate("""
            (()=>{let t=document.body.innerText;let m=t.match(/https?:\\/\\/[^\\s]+(?:subscribe|sub|token)\\S+/i);return m?m[0]:''})()
        """)
        print(f"  备用: {sub_url[:200] if sub_url else '未找到'}", flush=True)
        time.sleep(10)
        
    except Exception as e:
        print(f"异常: {e}", flush=True)
        import traceback; traceback.print_exc()
    finally:
        browser.close()
