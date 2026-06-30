#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""COCODUCK V2Board — 完整邮箱 + 获取按钮=V2Board特有"""
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
                if len(p) >= 4: return {"clientId": p[2], "refreshToken": p[3]}
    return None

def wait_code(email, timeout=120):
    tk = find_token(email)
    if not tk: return None, "no token"
    dl = time.time() + timeout; at = None; at_t = 0; seen = set()
    while time.time() < dl:
        try:
            if not at or time.time() - at_t > 900:
                r = req.post("https://login.microsoftonline.com/consumers/oauth2/v2.0/token",
                    data={"client_id": tk["clientId"], "grant_type": "refresh_token",
                          "refresh_token": tk["refreshToken"],
                          "scope": "offline_access https://graph.microsoft.com/Mail.Read"}, timeout=20)
                if r.status_code == 200: at = r.json().get("access_token",""); at_t = time.time()
                else: time.sleep(5); continue
            if not at: time.sleep(5); continue
            resp = req.get("https://graph.microsoft.com/v1.0/me/messages?$top=15&$select=id,subject,bodyPreview,receivedDateTime&$orderby=receivedDateTime desc",
                headers={"Authorization": f"Bearer {at}"}, timeout=15)
            if resp.status_code != 200: time.sleep(4); continue
            for msg in resp.json().get("value", []):
                mid = msg.get("id","");
                if mid in seen: continue
                seen.add(mid)
                combined = f"{msg.get('subject','')} {msg.get('bodyPreview','')}"
                for pat in [r"(?:验证码|激活码|verification.code)\D{0,30}?(\d{4,8})", r"code[:=]\s*(\d{4,8})", r"\b(\d{6})\b"]:
                    m = re.search(pat, combined, re.I)
                    if m:
                        code = m.group(1)
                        if code in ("000000","111111","222222","999999","123456"): continue
                        if 4 <= len(code) <= 8:
                            print(f"  ✅ 验证码={code}", flush=True)
                            return code, None
            time.sleep(4)
        except Exception as e: print(f"  异常: {e}", flush=True); time.sleep(5)
    return None, "timeout"

EMAIL = "caleb79rj61irjsiuhm4n@outlook.com"
PASS = "VpnTest2026!"

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=False,
        args=["--proxy-server=http://127.0.0.1:7897", "--ignore-certificate-errors", "--no-sandbox"])
    ctx = browser.new_context(viewport={"width": 1280, "height": 900}, ignore_https_errors=True, locale="zh-CN")
    page = ctx.new_page(); page.set_default_timeout(30000)

    page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {get: ()=>false});
        Object.defineProperty(MouseEvent.prototype, 'screenX', {
            get: function(){ return (this.clientX||0) + Math.floor(Math.random()*400)+80; }
        });
    """)

    try:
        print("[1] 打开注册页...", flush=True)
        page.goto("https://www.cocoduck.live/auth/register?code=8c1073605d", wait_until="networkidle", timeout=60000)
        time.sleep(5)

        # CSRF token
        csrf = page.evaluate("""()=>{
            let m=document.querySelector('meta[name=csrf-token]');
            return m ? m.getAttribute('content') : '';
        }""")
        print(f"  CSRF: {csrf[:80] if csrf else 'NONE'}", flush=True)

        # 填完整邮箱
        print(f"[2] 填邮箱: {EMAIL}", flush=True)
        page.fill('input[type="email"], input#email', EMAIL)
        time.sleep(0.5)

        # 密码
        page.fill('#passwd, input[placeholder="登录密码"]', PASS)
        time.sleep(0.3)
        page.fill('#repasswd, input[placeholder="重复登录密码"]', PASS)
        time.sleep(0.3)

        page.screenshot(path=os.path.join(os.path.dirname(__file__), "cocoduck_v5_filled.png"))

        # 点"获取"按钮发验证码（V2Board特有）
        print('[3] 发码(点击"获取")...', flush=True)
        page.click('#email-verify, button:has-text("获取")')
        print("  已点击获取", flush=True)
        time.sleep(2)

        # 收码
        print("[4] 收码...", flush=True)
        code, err = wait_code(EMAIL, timeout=120)
        if not code: print(f"❌ {err}"); browser.close(); exit(1)

        print(f"[5] 填码: {code}", flush=True)
        page.fill('#emailcode, input[placeholder*="收不到邮件"]', code)
        time.sleep(0.5)

        # checkbox
        cb = page.query_selector('#tos, input[type="checkbox"]')
        if cb and not cb.is_checked():
            try: cb.check(force=True); time.sleep(0.3)
            except: pass

        # 注册
        print("[6] 注册...", flush=True)
        page.click('#confirm-register, button:has-text("注册新账户")')
        time.sleep(8)
        try: page.wait_for_load_state("networkidle", timeout=15000)
        except: pass

        print(f"  URL: {page.url}", flush=True)
        body2 = page.evaluate("() => document.body.innerText")
        print(f"  页面(500):\n{body2[:500]}", flush=True)
        page.screenshot(path=os.path.join(os.path.dirname(__file__), "cocoduck_v5_after_register.png"))

        # 如果出现成功弹窗
        if "好" in body2 or "确认" in body2:
            for t in ["好", "确认"]:
                try: page.click(f'text="{t}"', timeout=3000); time.sleep(3); break
                except: continue

        # 如果需要登录
        if "/login" in page.url or "登录" in body2:
            print("[7] 登录...", flush=True)
            page.fill('input[type="email"], input#email', EMAIL)
            time.sleep(0.3)
            page.fill('input[type="password"], input#passwd', PASS)
            time.sleep(0.3)
            for t in ["登录", "登 录"]:
                try: page.click(f'button:has-text("{t}")', timeout=3000); time.sleep(5); break
                except: continue
            print(f"  登录后URL: {page.url}", flush=True)
        
        # 提取
        print("[8] 提取...", flush=True)
        raw = page.evaluate("localStorage.getItem('VUE_NAIVE_ACCESS_TOKEN')") or page.evaluate("localStorage.getItem('access_token')")
        print(f"  TOKEN: {(raw or 'NONE')[:200]}", flush=True)

        if raw:
            resp = page.evaluate("""
                (()=>{let r=localStorage.getItem('VUE_NAIVE_ACCESS_TOKEN')||localStorage.getItem('access_token');
                if(!r)return'NO_TOKEN';let t='';try{let p=JSON.parse(r);t=p.value||p.token||p}catch(e){t=r}
                let x=new XMLHttpRequest();x.open('GET','/api/v1/user/getSubscribe',false);
                x.setRequestHeader('Authorization',t);try{x.send()}catch(e){return x.responseText}
                return x.responseText})()
            """)
            print(f"  getSubscribe: {resp}", flush=True)
            try:
                d = json.loads(resp)
                sub_url = d.get("data",{}).get("subscribe_url","") or d.get("subscribe_url","")
            except:
                urls = re.findall(r'subscribe_url["\s:]+(https?://[^"\s]+)', resp)
                sub_url = urls[0] if urls else ""
            if sub_url:
                print(f"  ✅ 订阅: {sub_url}", flush=True)
                result = {"airport":"COCODUCK","panel":"cocoduck.live","email":EMAIL,"password":PASS,"subscribe_url":sub_url}
                with open(os.path.join(os.path.dirname(__file__),f"cocoduck_{EMAIL.split('@')[0]}.json"),"w",encoding="utf-8") as f:
                    json.dump(result,f,ensure_ascii=False,indent=2)
                time.sleep(5); browser.close(); exit(0)

        sub_url = page.evaluate("""()=>{let t=document.body.innerText;let m=t.match(/https?:\\/\\/[^\\s]+(?:subscribe|sub|token)\\S+/i);return m?m[0]:''})""")
        print(f"  备用: {sub_url[:200] if sub_url else '未找到'}", flush=True)
        time.sleep(20)

    except Exception as e:
        print(f"异常: {e}", flush=True)
        import traceback; traceback.print_exc()
    finally:
        browser.close()
