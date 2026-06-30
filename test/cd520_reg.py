#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cd520 注册 — 前缀+select后缀 A型V2Board"""
import sys, os, io, json, time, re, threading
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7897'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7897'
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests as req
from playwright.sync_api import sync_playwright

TK = r"E:\.Outlook邮箱\批量注册邮箱\已经使用\1"

def get_token(email):
    for f in os.listdir(TK):
        if email.lower() in f.lower() and f.endswith("_combo.txt"):
            with open(os.path.join(TK, f), encoding="utf-8") as fh:
                p = fh.read().strip().split("----")
                if len(p) >= 4: return {"clientId": p[2], "refreshToken": p[3]}
    return None

def wait_code(email, timeout=90):
    g = get_token(email)
    if not g: return None, "no token"
    dl = time.time() + timeout; at = None; at_t = 0; seen = set()
    time.sleep(5)
    while time.time() < dl:
        try:
            now = time.time()
            if not at or now - at_t > 900:
                r = req.post("https://login.microsoftonline.com/consumers/oauth2/v2.0/token",
                    data={"client_id": g["clientId"], "grant_type": "refresh_token",
                          "refresh_token": g["refreshToken"],
                          "scope": "offline_access https://graph.microsoft.com/Mail.Read"}, timeout=15)
                if r.status_code == 200: at = r.json().get("access_token",""); at_t = now
                else: time.sleep(3); continue
            if not at: time.sleep(3); continue
            resp = req.get("https://graph.microsoft.com/v1.0/me/messages?$top=15&$orderby=receivedDateTime desc&$select=id,subject,bodyPreview",
                headers={"Authorization": f"Bearer {at}"}, timeout=15)
            if resp.status_code != 200: time.sleep(3); continue
            for msg in resp.json().get("value", []):
                mid = msg.get("id","");
                if mid in seen: continue
                seen.add(mid)
                combined = f"{msg.get('subject','')} {msg.get('bodyPreview','')}"
                for pat in [r"(?:验证码|激活码)\D{0,30}?(\d{4,8})", r"code[:=]\s*(\d{4,8})", r"\b(\d{6})\b"]:
                    m = re.search(pat, combined, re.I)
                    if m:
                        code = m.group(1)
                        if code in ("000000","111111","222222","999999","123456"): continue
                        if 5 <= len(code) <= 8:
                            elapsed = time.time() - dl + timeout
                            print(f"  ✅ [{elapsed:.0f}s] code={code}", flush=True)
                            return code, None
            time.sleep(3)
        except Exception as e: print(f"  e:{e}", flush=True); time.sleep(3)
    return None, "timeout"

EMAIL = "mx9433499602@outlook.com"
PASS = "VpnTest2026!"
prefix, suffix = EMAIL.split("@", 1); suffix = "@"+suffix

print(f"cd520: {EMAIL}", flush=True)

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
        page.goto("https://cd520.xyz/#/register", wait_until="networkidle", timeout=60000)
        time.sleep(4)
        
        # A型: 前缀到第一个input，选select中@outlook.com
        print(f"填前缀:{prefix}", flush=True)
        page.fill('input[placeholder="邮箱"]', prefix)
        time.sleep(0.3)
        page.select_option('select', suffix)
        time.sleep(0.3)
        
        # 密码
        pws = page.query_selector_all('input[type="password"]')
        pws[0].fill(PASS); time.sleep(0.2)
        pws[1].fill(PASS); time.sleep(0.2)
        
        # 先发码
        print("发码...", flush=True)
        page.click('button:has-text("发送")')
        time.sleep(2)
        
        # 再收码
        code, _ = wait_code(EMAIL, 60)
        if not code: print("❌ 无码"); browser.close(); exit(1)
        
        print(f"填码:{code}", flush=True)
        page.fill('input[placeholder="邮箱验证码"]', code)
        time.sleep(0.3)
        
        print("注册...", flush=True)
        page.click('button:has-text("注册")')
        time.sleep(6)
        try: page.wait_for_load_state("networkidle", timeout=12000)
        except: pass
        
        body = page.evaluate("()=>document.body.innerText")
        print(f"URL:{page.url}\nBody(400):\n{body[:400]}", flush=True)
        page.screenshot(path=os.path.join(os.path.dirname(__file__), "cd520_result.png"))
        
        # 如果需要登录
        if "/login" in page.url or "登入" in body:
            print("自动登录...", flush=True)
            page.fill('input[placeholder="邮箱"]', EMAIL)
            time.sleep(0.2)
            page.fill('input[type="password"]', PASS)
            time.sleep(0.2)
            for t in ["登录", "登入", "登 录"]:
                try: page.click(f'button:has-text("{t}")', timeout=3000); time.sleep(5); break
                except: continue
        
        # 提取
        raw = page.evaluate("""()=>{let r=localStorage.getItem('VUE_NAIVE_ACCESS_TOKEN');
            if(!r){for(let i=0;i<localStorage.length;i++){let v=localStorage.getItem(localStorage.key(i));
            if(v&&v.includes('token')){r=v;break}}}
            return r||'NONE'}""")
        print(f"TOKEN:{raw[:200] if raw and raw!='NONE' else raw}", flush=True)
        
        if raw and raw != 'NONE':
            resp = page.evaluate("""
                (()=>{let r=arguments[0];let t='';try{let p=JSON.parse(r);t=p.value||p.token||p}catch(e){t=r}
                let x=new XMLHttpRequest();x.open('GET','/api/v1/user/getSubscribe',false);
                x.setRequestHeader('Authorization',t);try{x.send()}catch(e){return x.responseText}
                return x.responseText})()
            """, raw)
            print(f"getSubscribe:{resp}", flush=True)
            try:
                d = json.loads(resp)
                sub_url = d.get("data",{}).get("subscribe_url","") or d.get("subscribe_url","")
            except:
                urls = re.findall(r'subscribe_url["\s:]+(https?://[^"\s]+)', resp)
                sub_url = urls[0] if urls else ""
            if sub_url:
                print(f"✅ 订阅:{sub_url}", flush=True)
                result = {"airport":"cd520","email":EMAIL,"password":PASS,"subscribe_url":sub_url}
                with open(os.path.join(os.path.dirname(__file__),f"cd520_{EMAIL.split('@')[0]}.json"),"w",encoding="utf-8") as f:
                    json.dump(result,f,ensure_ascii=False,indent=2)
                time.sleep(5); browser.close(); exit(0)
        
        bt = page.evaluate("()=>document.body.innerText")
        m = re.search(r'https?://[^\s]+(?:sub|subscribe|token)[^\s]+', bt, re.I)
        print(f"文本URL:{m.group(0) if m else '无'}", flush=True)
        time.sleep(15)
        
    except Exception as e:
        print(f"异常:{e}", flush=True)
        import traceback; traceback.print_exc()
    finally:
        browser.close()
