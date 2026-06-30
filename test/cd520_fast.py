#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cd520 快速版 — 码不过期 + 完整邮箱登录"""
import sys, os, io, json, time, re
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7897'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7897'
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests as req
from playwright.sync_api import sync_playwright

TK = r"E:\.Outlook邮箱\批量注册邮箱\已经使用\1"

def wait_code_fast(email, timeout=45):
    for f in os.listdir(TK):
        if email.lower() in f.lower() and f.endswith("_combo.txt"):
            with open(os.path.join(TK, f), encoding="utf-8") as fh:
                p = fh.read().strip().split("----")
                if len(p) >= 4: g = {"clientId": p[2], "refreshToken": p[3]}; break
    else: return None
    dl = time.time() + timeout; at = None; at_t = 0; seen = set()
    while time.time() < dl:
        try:
            now = time.time()
            if not at or now - at_t > 900:
                r = req.post("https://login.microsoftonline.com/consumers/oauth2/v2.0/token",
                    data={"client_id": g["clientId"], "grant_type": "refresh_token",
                          "refresh_token": g["refreshToken"],
                          "scope": "offline_access https://graph.microsoft.com/Mail.Read"}, timeout=10)
                if r.status_code == 200: at = r.json().get("access_token",""); at_t = now
                else: time.sleep(2); continue
            if not at: time.sleep(2); continue
            resp = req.get("https://graph.microsoft.com/v1.0/me/messages?$top=15&$orderby=receivedDateTime desc&$select=id,subject,bodyPreview",
                headers={"Authorization": f"Bearer {at}"}, timeout=10)
            if resp.status_code != 200: time.sleep(2); continue
            for msg in resp.json().get("value", []):
                mid = msg.get("id","");
                if mid in seen: continue
                seen.add(mid)
                combined = f"{msg.get('subject','')} {msg.get('bodyPreview','')}"
                for pat in [r"(?:验证码|激活码)\D{0,30}?(\d{4,8})", r"\b(\d{6})\b"]:
                    m = re.search(pat, combined, re.I)
                    if m:
                        code = m.group(1)
                        if code in ("000000","111111","222222","999999","123456","131452"): continue
                        if 5 <= len(code) <= 8:
                            elapsed = int(time.time() + timeout - dl)
                            print(f"  [{elapsed}s] code={code} subj={msg.get('subject','')[:40]}", flush=True)
                            return code
            time.sleep(2)
        except: time.sleep(2)
    return None

EMAIL = "mx738945e98b@outlook.com"
PASS = "VpnTest2026!"
prefix, suffix = EMAIL.split("@", 1); suffix = "@"+suffix

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=False,
        args=["--proxy-server=http://127.0.0.1:7897", "--ignore-certificate-errors", "--no-sandbox"])
    ctx = browser.new_context(viewport={"width": 1280, "height": 900}, ignore_https_errors=True, locale="zh-CN")
    page = ctx.new_page(); page.set_default_timeout(15000)
    page.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>false});")
    
    try:
        page.goto("https://cd520.xyz/#/register", wait_until="networkidle", timeout=45000)
        time.sleep(2)
        
        # Prefix + select + passwords
        page.fill('input[placeholder="邮箱"]', prefix)
        time.sleep(0.2)
        page.select_option('select', suffix)
        time.sleep(0.2)
        pws = page.query_selector_all('input[type="password"]')
        pws[0].fill(PASS); pws[1].fill(PASS)
        
        # 发码
        page.click('button:has-text("发送")')
        print("sent", flush=True)
        
        # 收码 (30s only)
        code = wait_code_fast(EMAIL, 30)
        if not code: print("NOCODE"); exit(1)
        
        # 填码+注册（5秒内完成）
        page.fill('input[placeholder="邮箱验证码"]', code)
        time.sleep(0.2)
        page.click('button:has-text("注册")')
        time.sleep(6)
        
        body = page.evaluate("()=>document.body.innerText")
        print(f"url={page.url}\nbody={body[:400]}", flush=True)
        page.screenshot(path=os.path.join(os.path.dirname(__file__), "cd520_fast.png"))
        
        # 登录（如需）
        if "/login" in page.url or "登入" in body:
            print("login...", flush=True)
            # 登录页可能用完整邮箱
            page.fill('input[placeholder*="邮箱"], input[type="email"], input[type="text"]', EMAIL)
            time.sleep(0.3)
            page.fill('input[type="password"]', PASS)
            time.sleep(0.3)
            for t in ["登录", "登入", "登 录", "Login"]:
                try: page.click(f'button:has-text("{t}")', timeout=2000); time.sleep(4); break
                except: continue
            body = page.evaluate("()=>document.body.innerText")
            print(f"after login: {page.url}\n{body[:300]}", flush=True)
        
        # 提取
        raw = page.evaluate("""()=>{let r=localStorage.getItem('VUE_NAIVE_ACCESS_TOKEN');
            if(!r){for(let i=0;i<localStorage.length;i++){let v=localStorage.getItem(localStorage.key(i));
            if(v&&v.includes('token')){r=v;break}}}
            return r||'NONE'}""")
        if raw and raw != 'NONE':
            resp = page.evaluate("""(()=>{let r=arguments[0];let t='';try{let p=JSON.parse(r);t=p.value||p.token||p}catch(e){t=r}
                let x=new XMLHttpRequest();x.open('GET','/api/v1/user/getSubscribe',false);
                x.setRequestHeader('Authorization',t);try{x.send()}catch(e){}return x.responseText})()""", raw)
            try: d=json.loads(resp); sub=d.get("data",{}).get("subscribe_url","") or d.get("subscribe_url","")
            except: urls=re.findall(r'subscribe_url["\s:]+(https?://[^"\s]+)',resp); sub=urls[0] if urls else ""
            if sub:
                print(f"✅ {sub}", flush=True)
                with open(os.path.join(os.path.dirname(__file__),f"cd520_{EMAIL.split('@')[0]}.json"),"w",encoding="utf-8") as f:
                    json.dump({"airport":"cd520","email":EMAIL,"password":PASS,"subscribe_url":sub},f,ensure_ascii=False,indent=2)
                time.sleep(3); browser.close(); exit(0)
        
        bt = page.evaluate("()=>document.body.innerText")
        m = re.search(r'https?://[^\s]+(?:sub|subscribe|token)[^\s]+', bt, re.I)
        print(f"text_url={m.group(0) if m else 'NONE'}", flush=True)
        time.sleep(10)
    except Exception as e:
        print(f"e:{e}", flush=True)
        import traceback; traceback.print_exc()
    finally:
        browser.close()
