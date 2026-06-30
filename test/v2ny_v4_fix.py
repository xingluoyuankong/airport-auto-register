#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v2ny/奈云 — 完整邮箱 + NaiveUI面板"""
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
                            print(f"  ✅ 验证码={code} subj={msg.get('subject','')[:60]}", flush=True)
                            return code, None
            time.sleep(4)
        except Exception as e: 
            print(f"  异常: {e}", flush=True); time.sleep(5)
    return None, "timeout"

EMAIL = "bfloresrsg7qheo5tgr8hhk@outlook.com"
PASS = "VpnTest2026!"

print("=" * 60)
print(f"  v2ny/奈云 修复版: {EMAIL}")
print("=" * 60)

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=False,
        args=["--proxy-server=http://127.0.0.1:7897", "--ignore-certificate-errors", "--no-sandbox"])
    ctx = browser.new_context(viewport={"width": 1280, "height": 900}, ignore_https_errors=True, locale="zh-CN")
    page = ctx.new_page(); page.set_default_timeout(30000)
    page.add_init_script("""
        Object.defineProperty(navigator,'webdriver',{get:()=>false});
        Object.defineProperty(MouseEvent.prototype,'screenX',{get:function(){return(this.clientX||0)+Math.floor(Math.random()*400)+80}});
    """)

    try:
        print("[1] 打开注册页...", flush=True)
        page.goto("https://www.v2ny.com/#/auth/register", wait_until="networkidle", timeout=60000)
        time.sleep(5)
        
        # 关键：v2ny是完整邮箱输入 reg-email (placeholder="you@example.com")
        print(f"[2] 填完整邮箱: {EMAIL}", flush=True)
        page.fill('#reg-email, input[type="email"]', EMAIL)
        time.sleep(0.5)

        # 密码 (reg-password)
        print(f"[3] 填密码: {PASS}", flush=True)
        page.fill('#reg-password, input[placeholder*="至少 8 位"]', PASS)
        time.sleep(0.5)

        # 发码
        print("[4] 发码...", flush=True)
        for t in ["发送", "获 取"]:
            try:
                page.click(f'button:has-text("{t}")', timeout=3000)
                print(f"  已点击 {t}", flush=True); time.sleep(2); break
            except: continue

        # 收码 — 需要精准匹配v2ny发来的
        print("[5] 收码(60s内)...", flush=True)
        code, err = wait_code(EMAIL, timeout=90)
        if not code: print(f"❌ {err}"); browser.close(); exit(1)

        print(f"[6] 填码: {code}", flush=True)
        page.fill('#reg-code, input[placeholder*="验证码"]', code)
        time.sleep(0.5)

        # 创建账户
        print("[7] 创建账户...", flush=True)
        for t in ["创建账户", "创建", "注册"]:
            try:
                page.click(f'button:has-text("{t}")', timeout=3000)
                print(f"  已点击 {t}", flush=True); break
            except: continue

        time.sleep(8)
        try: page.wait_for_load_state("networkidle", timeout=15000)
        except: pass

        print(f"  注册后URL: {page.url}", flush=True)
        body2 = page.evaluate("()=>document.body.innerText")
        print(f"  页面(500):\n{body2[:500]}", flush=True)
        page.screenshot(path=os.path.join(os.path.dirname(__file__), "v2ny_v4_after.png"))

        # 检查是否注册成功或跳到登录
        if "登录" in body2 or "/auth/login" in page.url:
            print("[8] 自动登录...", flush=True)
            page.fill('#reg-email, input[type="email"]', EMAIL)
            time.sleep(0.3)
            page.fill('input[type="password"]', PASS)
            time.sleep(0.3)
            for t in ["登录", "登 录", "Login"]:
                try: page.click(f'button:has-text("{t}")', timeout=3000); time.sleep(5); break
                except: continue
            print(f"  登录后URL: {page.url}", flush=True)
            body3 = page.evaluate("()=>document.body.innerText")
            print(f"  页面(500):\n{body3[:500]}", flush=True)

        # 如果已经在dashboard
        if "仪表盘" in body2 or "dashboard" in body2.lower() or "用户" in body2:
            print("[9] 已在Dashboard，提取订阅...", flush=True)
        else:
            # 尝试导航到user页
            try:
                page.goto("https://www.v2ny.com/#/user", wait_until="networkidle", timeout=15000)
                time.sleep(3)
                body3 = page.evaluate("()=>document.body.innerText")
                print(f"  /user页面: {body3[:300]}", flush=True)
            except: pass

        # 提取
        print("[10] 提取订阅...", flush=True)
        raw = page.evaluate("localStorage.getItem('VUE_NAIVE_ACCESS_TOKEN')")
        if not raw:
            # NaiveUI可能用别的key
            raw = page.evaluate("""
                (()=>{for(let i=0;i<localStorage.length;i++){let k=localStorage.key(i);
                let v=localStorage.getItem(k);if(v&&v.includes('token'))return v;}return''})()
            """)
        print(f"  TOKEN: {(raw or 'NONE')[:200]}", flush=True)

        if raw:
            resp = page.evaluate("""
                (()=>{let r=localStorage.getItem('VUE_NAIVE_ACCESS_TOKEN');
                if(!r){for(let i=0;i<localStorage.length;i++){let k=localStorage.key(i);
                let v=localStorage.getItem(k);if(v&&v.includes('token')){r=v;break}}}
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
                result = {"airport":"v2ny","panel":"v2ny.com","email":EMAIL,"password":PASS,"subscribe_url":sub_url}
                with open(os.path.join(os.path.dirname(__file__),f"v2ny_{EMAIL.split('@')[0]}.json"),"w",encoding="utf-8") as f:
                    json.dump(result,f,ensure_ascii=False,indent=2)
                time.sleep(5); browser.close(); exit(0)

        # 最后找文本中订阅URL
        body_text = page.evaluate("()=>document.body.innerText")
        m = re.search(r'https?://[^\s]+(?:subscribe|sub|token|link)[^\s]+', body_text, re.I)
        print(f"  文本中URL: {m.group(0) if m else '未找到'}", flush=True)
        time.sleep(20)

    except Exception as e:
        print(f"异常: {e}", flush=True)
        import traceback; traceback.print_exc()
    finally:
        browser.close()
