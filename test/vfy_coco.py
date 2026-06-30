#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""COCODUCK 验证 - 需从主页进入登录"""
import sys,os,io,json,time,re
os.environ['HTTP_PROXY']='http://127.0.0.1:7897';os.environ['HTTPS_PROXY']='http://127.0.0.1:7897'
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
from playwright.sync_api import sync_playwright

EMAIL="floraide3rb1508k2xlbbi@hotmail.com"
PASS="VpnTest2026!"

with sync_playwright() as p:
    b=p.chromium.launch(channel="msedge",headless=False,args=["--proxy-server=http://127.0.0.1:7897","--ignore-certificate-errors","--no-sandbox"])
    c=b.new_context(viewport={"width":1280,"height":900},ignore_https_errors=True,locale="zh-CN")
    pg=c.new_page();pg.set_default_timeout(15000)
    try:
        print("=== COCODUCK ===",flush=True)
        # Go to main page, click login link
        pg.goto("https://cocoduck.cc/",wait_until="domcontentloaded",timeout=45000)
        time.sleep(3)
        # COCODUCK custom SPA - click login button in nav
        pg.click('a.button.-small:has-text("登录")')
        time.sleep(4)
        # Now should be on login page
        inp=pg.evaluate('''()=>Array.from(document.querySelectorAll('input,button')).map(e=>({tag:e.tagName,t:e.type||'',p:e.placeholder||'',id:e.id||'',txt:(e.textContent||'').trim().substring(0,25)}))''')
        body=pg.evaluate("()=>document.body.innerText")
        print(f"URL:{pg.url}\nBody:{body[:400]}\nINPUTS:{json.dumps(inp,ensure_ascii=False)}",flush=True)
        pg.screenshot(path="coco_vfy_login.png")

        # Fill by ID pattern
        email_input=pg.query_selector('#email') or pg.query_selector('input[type="email"]')
        pass_input=pg.query_selector('#password') or pg.query_selector('input[type="password"]')
        if email_input and pass_input:
            email_input.fill(EMAIL)
            pass_input.fill(PASS)
            pg.screenshot(path="coco_vfy_filled.png")
            pg.click('button:has-text("登录")')
            time.sleep(6)
            body2=pg.evaluate("()=>document.body.innerText")
            print(f"After login:{body2[:400]}",flush=True)
            pg.screenshot(path="coco_vfy_dash.png")
            # Extract
            m=re.search(r'https?://[^\s]*sub[^\s]+',body2,re.I)
            if m:
                print(f"✅ COCODUCK SUB:{m.group(0)}",flush=True)
            else:
                print("NO SUB in body - check manually",flush=True)
        else:
            print("No email/password found",flush=True)

        time.sleep(3)
    except Exception as e: print(f"e:{e}",flush=True)
    finally: b.close()
