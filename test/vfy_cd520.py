#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cd520 验证 — 用 cd520.xyz 域名"""
import sys,os,io,json,time,re
os.environ['HTTP_PROXY']='http://127.0.0.1:7897';os.environ['HTTPS_PROXY']='http://127.0.0.1:7897'
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
from playwright.sync_api import sync_playwright

EMAIL="hendricktamm95v80awzaxli@outlook.com"
PASS="VpnTest2026!"
prefix=EMAIL.split("@")[0]
suffix="@"+EMAIL.split("@")[1]

with sync_playwright() as p:
    b=p.chromium.launch(channel="msedge",headless=False,
        args=["--proxy-server=http://127.0.0.1:7897","--ignore-certificate-errors","--no-sandbox"])
    c=b.new_context(viewport={"width":1280,"height":900},ignore_https_errors=True,locale="zh-CN")
    pg=c.new_page();pg.set_default_timeout(15000)
    pg.add_init_script('Object.defineProperty(navigator,"webdriver",{get:()=>false});')
    try:
        print("=== cd520 ===",flush=True)
        # Use cd520.xyz (cd1314.xyz is dead)
        pg.goto("https://cd520.xyz/#/login",wait_until="domcontentloaded",timeout=45000)
        time.sleep(3)
        body=pg.evaluate("()=>document.body.innerText")
        inp=pg.evaluate('''()=>Array.from(document.querySelectorAll('input,select,button')).map(e=>({t:e.tagName,ty:e.type||"",p:e.placeholder||"",id:e.id||"",txt:(e.textContent||"").trim().substring(0,25)}))''')
        print(f"URL:{pg.url}\nBody:{body[:500]}\nINPUTS:{json.dumps(inp,ensure_ascii=False)}",flush=True)
        pg.screenshot(path="cd520_vfy_login.png")

        # cd520 login: complete email (no select on login page!)
        pg.fill('input[placeholder="邮箱"]',EMAIL)
        time.sleep(0.2)
        pws=pg.query_selector_all('input[type="password"]')
        if pws: pws[0].fill(PASS)
        time.sleep(0.2)
        pg.screenshot(path="cd520_vfy_filled.png")

        pg.click('button:has-text("登入")')  # cd520 uses "登入" too
        time.sleep(6)
        try: pg.wait_for_load_state("networkidle",timeout=10000)
        except: pass

        body2=pg.evaluate("()=>document.body.innerText")
        url2=pg.url
        print(f"AfterLogin URL:{url2}\nBody:{body2[:500]}",flush=True)
        pg.screenshot(path="cd520_vfy_dash.png")

        # Extract via API
        raw=pg.evaluate('localStorage.getItem("VUE_NAIVE_ACCESS_TOKEN")')
        print(f"TOKEN:{(raw or 'NONE')[:80]}",flush=True)
        if raw:
            resp=pg.evaluate("""(tok)=>{let t='';try{let p=JSON.parse(tok);t=p.value||p.token||p}catch(e){t=tok};let x=new XMLHttpRequest();x.open('GET','/api/v1/user/getSubscribe',false);x.setRequestHeader('Authorization',t);try{x.send()}catch(e){}return x.responseText}""",raw)
            print(f"API:{resp[:300]}",flush=True)
            try:
                d=json.loads(resp)
                sub=d.get("data",{}).get("subscribe_url","") or d.get("subscribe_url","")
            except: sub=""
            if sub: print(f"✅ cd520 SUB:{sub}",flush=True)
            else: print("NO SUB in API",flush=True)
        else:
            # Fallback: search body
            m=re.search(r'https?://[^\s]+subscribe[^\s]+',body2,re.I)
            if m: print(f"✅ cd520 SUB(from body):{m.group(0)}",flush=True)
    except Exception as e:
        import traceback; traceback.print_exc()
    finally:
        time.sleep(3)
        b.close()
