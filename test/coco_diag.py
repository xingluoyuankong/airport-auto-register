#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""COCODuck 登录诊断"""
import sys,os,io,time,json
os.environ['HTTP_PROXY']='http://127.0.0.1:7897';os.environ['HTTPS_PROXY']='http://127.0.0.1:7897'
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
from playwright.sync_api import sync_playwright

EMAIL="floraide3rb1508k2xlbbi@hotmail.com"
PASS="VpnTest2026!"

with sync_playwright() as p:
    b=p.chromium.launch(channel="msedge",headless=False,
        args=["--proxy-server=http://127.0.0.1:7897","--ignore-certificate-errors","--no-sandbox"])
    c=b.new_context(viewport={"width":1280,"height":900},ignore_https_errors=True,locale="zh-CN")
    pg=c.new_page();pg.set_default_timeout(15000)
    try:
        # Navigate to login page directly
        pg.goto("https://cocoduck.cc/#/login",wait_until="domcontentloaded",timeout=45000)
        time.sleep(5)
        body=pg.evaluate("()=>document.body.innerText")
        print(f"Body after #/login:\n{body[:600]}",flush=True)

        # Check if it redirected
        try: pg.wait_for_url("**/#/login",timeout=10000)
        except: pass
        print(f"URL:{pg.url}",flush=True)

        # Try clicking login button
        # Search for login button with text "登录" or "登 录"
        pg.click('a.button.-small.btn-optional:has-text("登录")')
        time.sleep(5)
        body2=pg.evaluate("()=>document.body.innerText")
        inp2=pg.evaluate("()=>Array.from(document.querySelectorAll('input,select')).map(e=>({t:e.tagName,ty:e.type||'',p:e.placeholder||'',id:e.id||''}))")
        print(f"After click:\nURL:{pg.url}\nBody:{body2[:400]}\nINPUTS:{json.dumps(inp2,ensure_ascii=False)}",flush=True)
        pg.screenshot(path="coco_vfy_final.png")

        # Try fill + login if form visible
        if inp2:
            email_input=pg.query_selector('#email') or pg.query_selector('input[type="email"]')
            pass_input=pg.query_selector('#password') or pg.query_selector('input[type="password"]')
            if email_input and pass_input:
                email_input.fill(EMAIL)
                pass_input.fill(PASS)
                pg.click('button[type="submit"]')
                time.sleep(6)
                body3=pg.evaluate("()=>document.body.innerText")
                print(f"After login:{body3[:400]}",flush=True)
    except Exception as e:
        import traceback; traceback.print_exc()
    finally:
        time.sleep(3)
        b.close()
