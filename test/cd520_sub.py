#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cd520 订阅提取 — v1.7.1面板"""
import sys,os,io,json,time,re
os.environ['HTTP_PROXY']='http://127.0.0.1:7897';os.environ['HTTPS_PROXY']='http://127.0.0.1:7897'
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
from playwright.sync_api import sync_playwright

EMAIL="hendricktamm95v80awzaxli@outlook.com"
PASS="VpnTest2026!"

with sync_playwright() as p:
    b=p.chromium.launch(channel="msedge",headless=False,
        args=["--proxy-server=http://127.0.0.1:7897","--ignore-certificate-errors","--no-sandbox"])
    c=b.new_context(viewport={"width":1280,"height":900},ignore_https_errors=True,locale="zh-CN")
    pg=c.new_page();pg.set_default_timeout(15000)
    pg.add_init_script('Object.defineProperty(navigator,"webdriver",{get:()=>false});')
    try:
        print("=== cd520 SUB ===",flush=True)
        pg.goto("https://cd520.xyz/#/login",wait_until="domcontentloaded",timeout=45000)
        time.sleep(3)
        pg.fill('input[placeholder="邮箱"]',EMAIL)
        pg.fill('input[placeholder="密码"]',PASS)
        pg.click('button:has-text("登入")')
        time.sleep(6)
        try: pg.wait_for_load_state("networkidle",timeout=10000)
        except: pass

        # Close modal with ESC, then navigate to sub page directly
        pg.keyboard.press("Escape")
        time.sleep(2)
        # Navigate via URL hash instead of clicking blocked nav
        pg.evaluate("window.location.hash='#/dashboard'")
        time.sleep(2)
        # Now go to subscription page
        pg.click('a:has-text("订阅")', force=True)
        time.sleep(4)
        body=pg.evaluate("()=>document.body.innerText")
        print(f"SubPage Body:{body[:600]}",flush=True)
        pg.screenshot(path="cd520_sub_page.png")

        # Try getting subscribe URL from page or API
        # Method 1: Click "一键订阅" or "导入" button
        for btn_text in ["一键订阅","复制订阅","Clash","导入","通用订阅","复制"]:
            btns=pg.query_selector_all(f'button:has-text("{btn_text}")')
            if btns:
                print(f"Clicking {btn_text}...",flush=True)
                btns[0].click()
                time.sleep(2)
                # Check clipboard or modal
                body2=pg.evaluate("()=>document.body.innerText")
                m=re.search(r'https?://[^\s]+(?:subscribe|token|link|sub)[^\s]*',body2,re.I)
                if m:
                    sub=m.group(0).rstrip(',.')
                    print(f"✅ cd520 SUB:{sub}",flush=True)
                    break

        # Method 2: Check localStorage keys
        ks=pg.evaluate('()=>Object.keys(localStorage)')
        print(f"localStorage keys:{ks}",flush=True)
        for k in ks:
            v=pg.evaluate(f'localStorage.getItem("{k}")')
            if v and 'token' in v.lower():
                print(f"  {k}: {v[:120]}",flush=True)

        # Method 3: Navigate to /api/v1/user/getSubscribe
        resp=pg.evaluate('''async()=>{
            let r=await fetch("/api/v1/user/getSubscribe",{headers:{"Accept":"application/json"}});
            return r.status+" "+await r.text()}''')
        print(f"getSubscribe:{resp[:300]}",flush=True)

        # Method 4: Direct subscribe URL from links
        links=pg.evaluate('''()=>Array.from(document.querySelectorAll('a')).filter(a=>/sub|token|link/.test(a.href)).map(a=>({t:a.textContent?.trim()?.substring(0,20),h:a.href}))''')
        print(f"SubLinks:{json.dumps(links,ensure_ascii=False)}",flush=True)

    except Exception as e:
        import traceback; traceback.print_exc()
    finally:
        time.sleep(5)
        b.close()
