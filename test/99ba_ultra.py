#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""99吧 极速版 — 先启动收码监听，再发码，秒收秒填"""
import sys, os, io, json, time, re, threading
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7897'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7897'
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests as req
from playwright.sync_api import sync_playwright

TK = r"E:\.Outlook邮箱\批量注册邮箱\已经使用\1"

def find_token(email):
    for f in os.listdir(TK):
        if email.lower() in f.lower() and f.endswith("_combo.txt"):
            with open(os.path.join(TK, f), encoding="utf-8") as fh:
                p = fh.read().strip().split("----")
                if len(p) >= 4: return {"clientId": p[2], "refreshToken": p[3]}
    return None

def poll_code(email, result, stop):
    """持续轮询直到stop或找到码"""
    g = find_token(email)
    if not g: return
    at = None; at_t = 0; seen = set()
    while not stop.is_set():
        try:
            now = time.time()
            if not at or now - at_t > 600:
                r = req.post("https://login.microsoftonline.com/consumers/oauth2/v2.0/token",
                    data={"client_id": g["clientId"], "grant_type": "refresh_token",
                          "refresh_token": g["refreshToken"],
                          "scope": "offline_access https://graph.microsoft.com/Mail.Read"}, timeout=8)
                if r.status_code == 200: at = r.json().get("access_token",""); at_t = now
                else: time.sleep(2); continue
            if not at: time.sleep(2); continue
            resp = req.get("https://graph.microsoft.com/v1.0/me/messages?$top=10&$orderby=receivedDateTime desc&$select=id,subject,bodyPreview",
                headers={"Authorization": f"Bearer {at}"}, timeout=8)
            if resp.status_code != 200: time.sleep(2); continue
            for msg in resp.json().get("value", []):
                mid = msg.get("id","");
                if mid in seen: continue
                seen.add(mid)
                combined = f"{msg.get('subject','')} {msg.get('bodyPreview','')}"
                for pat in [r"\b(\d{6})\b", r"(?:验证码|激活码)\D{0,30}?(\d{4,8})"]:
                    m = re.search(pat, combined, re.I)
                    if m and len(m.group(1)) >= 5 and m.group(1) not in ("000000","111111","222222","999999","123456"):
                        result[0] = m.group(1)
                        stop.set()
                        print(f"  ✅ code={result[0]} ({msg.get('subject','')[:40]})", flush=True)
                        return
            time.sleep(1.5)
        except: time.sleep(2)

EMAILS = ["lilparkevgpa0ns1k4f6xw@outlook.com", "mxvh76gyv2la4auu2t@outlook.com", "colemanbroovp9xyduj92hubhn@outlook.com"]
PASS = "VpnTest2026!"

for EMAIL in EMAILS:
    result = [None]; stop = threading.Event()
    t = threading.Thread(target=poll_code, args=(EMAIL, result, stop)); t.start()
    time.sleep(1)  # 给轮询线程1秒预热
    
    prefix, suffix = EMAIL.split("@", 1); suffix = "@"+suffix
    print(f"\n99ba: {EMAIL}", flush=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=False,
            args=["--proxy-server=http://127.0.0.1:7897", "--ignore-certificate-errors", "--no-sandbox"])
        ctx = browser.new_context(viewport={"width": 1280, "height": 900}, ignore_https_errors=True, locale="zh-CN")
        page = ctx.new_page(); page.set_default_timeout(15000)
        page.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>false});")
        
        try:
            page.goto("https://a.99ba2026.fyi/#/register", wait_until="networkidle", timeout=45000)
            time.sleep(2)
            
            # 填表
            page.fill('input[placeholder*="邮箱"]', prefix)
            time.sleep(0.2)
            page.click(".n-base-selection-label")
            time.sleep(0.5)
            page.click(f'text={suffix}')
            time.sleep(0.2)
            pws = page.query_selector_all('input[type="password"]')
            pws[0].fill(PASS); pws[1].fill(PASS)
            
            # 发码
            page.click('button:has-text("发送")')
            print("  发码...", flush=True)
            
            # 等轮询线程收到码
            t.join(20)
            code = result[0]
            if not code:
                stop.set()
                print("  ❌ 无码", flush=True)
                browser.close()
                continue
            
            # 秒填
            page.fill('input[placeholder*="验证码"]', code)
            time.sleep(0.15)
            page.click('button:has-text("注册")')
            
            time.sleep(5)
            try: page.wait_for_load_state("networkidle", timeout=10000)
            except: pass
            
            body = page.evaluate("()=>document.body.innerText")
            print(f"  URL:{page.url}\n  body:{body[:300]}", flush=True)
            
            # 已注册→登录
            if "/login" in page.url or "登入" in body:
                print("  登录...", flush=True)
                page.fill('input[placeholder*="邮箱"]', prefix)
                time.sleep(0.2)
                page.click(".n-base-selection-label"); time.sleep(0.5)
                page.click(f'text={suffix}'); time.sleep(0.2)
                pw = page.query_selector('input[type="password"]')
                if pw: pw.fill(PASS)
                for t in ["登录","登入"]:
                    try: page.click(f'button:has-text("{t}")', timeout=2000); time.sleep(4); break
                    except: continue
                body = page.evaluate("()=>document.body.innerText")
                print(f"  登录后:{body[:300]}", flush=True)
            
            # 提取
            raw = page.evaluate("localStorage.getItem('VUE_NAIVE_ACCESS_TOKEN')")
            if raw:
                resp = page.evaluate("""
                    (()=>{let r=arguments[0];let t='';try{let p=JSON.parse(r);t=p.value||p.token||p}catch(e){t=r}
                    let x=new XMLHttpRequest();x.open('GET','/api/v1/user/getSubscribe',false);
                    x.setRequestHeader('Authorization',t);try{x.send()}catch(e){}return x.responseText})()
                """, raw)
                try:
                    d=json.loads(resp)
                    sub=d.get("data",{}).get("subscribe_url","") or d.get("subscribe_url","")
                except:
                    urls=re.findall(r'subscribe_url["\s:]+(https?://[^"\s]+)',resp)
                    sub=urls[0] if urls else ""
                if sub:
                    print(f"  ✅ {sub}", flush=True)
                    with open(os.path.join(os.path.dirname(__file__),f"99ba_{EMAIL.split('@')[0]}.json"),"w",encoding="utf-8") as f:
                        json.dump({"airport":"99ba","email":EMAIL,"password":PASS,"subscribe_url":sub},f,ensure_ascii=False,indent=2)
                    browser.close()
                    continue
            
            bt = page.evaluate("()=>document.body.innerText")
            m = re.search(r'https?://[^\s]+(?:sub|subscribe|token)[^\s]+', bt, re.I)
            print(f"  文本URL:{m.group(0) if m else '无'}", flush=True)
            
        except Exception as e:
            print(f"  e:{e}", flush=True)
        finally:
            stop.set()
            browser.close()

print("\nDone")
