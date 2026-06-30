#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""COCODUCK 最终版 - 鼠标悬停触发React导航，然后登录"""
import sys,os,io,json,time,re
os.environ['HTTP_PROXY']='http://127.0.0.1:7897'
os.environ['HTTPS_PROXY']='http://127.0.0.1:7897'
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
from playwright.sync_api import sync_playwright

EMAIL="floraide3rb1508k2xlbbi@hotmail.com"
PASS="VpnTest2026!"

with sync_playwright() as p:
    b=p.chromium.launch(channel="msedge",headless=False,
        args=["--proxy-server=http://127.0.0.1:7897","--ignore-certificate-errors","--no-sandbox"])
    c=b.new_context(viewport={"width":1280,"height":900},ignore_https_errors=True,locale="zh-CN")
    pg=c.new_page();pg.set_default_timeout(15000)
    pg.add_init_script('Object.defineProperty(navigator,"webdriver",{get:()=>false});')
    try:
        print("=== COCODUCK FINAL ===",flush=True)
        pg.goto("https://cocoduck.cc/",wait_until="domcontentloaded",timeout=45000)
        time.sleep(4)
        # MOUSEOVER to trigger React menu
        login_link=pg.locator('a:has-text("登录")').first
        login_link.hover()
        time.sleep(2)
        login_link.click(force=True)
        time.sleep(5)
        pg.wait_for_load_state("networkidle",timeout=15000)
        url=pg.url
        body=pg.evaluate("()=>document.body.innerText")
        print(f"URL after click: {url}\nBody: {body[:500]}",flush=True)
        pg.screenshot(path="coco_final_afterclick.png")

        # If still on main page, try direct hash navigation
        if "/#/" not in url and "login" not in url:
            print("  Trying direct hash navigation...",flush=True)
            pg.evaluate("window.location.hash='#/login'")
            time.sleep(5)
            body2=pg.evaluate("()=>document.body.innerText")
            url2=pg.url
            print(f"  URL2: {url2}\n  Body2: {body2[:500]}",flush=True)
            pg.screenshot(path="coco_final_hash.png")

        # Fill login form
        # Try by id first
        email_input=pg.query_selector('#email') or pg.query_selector('input[type="email"]') or pg.query_selector('input[placeholder*="邮箱"]') or pg.query_selector('input[placeholder*="Email"]')
        pass_input=pg.query_selector('#password') or pg.query_selector('input[type="password"]')
        print(f"  email_input: {email_input}",flush=True)
        print(f"  pass_input: {pass_input}",flush=True)
        if email_input and pass_input:
            email_input.fill(EMAIL)
            pass_input.fill(PASS)
            time.sleep(0.5)
            pg.screenshot(path="coco_final_filled.png")
            # Click login button
            btn=pg.locator('button:has-text("登录")').first
            btn.click()
            time.sleep(6)
            pg.wait_for_load_state("networkidle",timeout=15000)
            body3=pg.evaluate("()=>document.body.innerText")
            print(f"  After login body: {body3[:500]}",flush=True)
            pg.screenshot(path="coco_final_dash.png")

            # Extract subscription
            raw=pg.evaluate('localStorage.getItem("VUE_NAIVE_ACCESS_TOKEN")')
            print(f"  TOKEN: {(raw or 'NONE')[:100]}",flush=True)
            if raw:
                resp=pg.evaluate("""(tok) => {
                    let t='';
                    try{ let p=JSON.parse(tok); t=p.value||p.token||p } catch(e){ t=tok }
                    let x=new XMLHttpRequest();
                    x.open('GET','/api/v1/user/getSubscribe',false);
                    x.setRequestHeader('Authorization',t);
                    try{x.send()}catch(e){}
                    return x.responseText;
                }""", raw)
                print(f"  getSubscribe: {resp[:300]}",flush=True)
                try:
                    d=json.loads(resp)
                    sub=d.get("data",{}).get("subscribe_url","") or d.get("subscribe_url","")
                except:
                    m=re.search(r'"subscribe_url":"([^"]+)"',resp)
                    sub=m.group(1) if m else ""
                if sub:
                    print(f"  ✅ SUB: {sub}",flush=True)
                else:
                    print("  NO SUB in response",flush=True)
        else:
            # Dump all inputs
            inputs=pg.evaluate("""()=>Array.from(document.querySelectorAll('input,button,select')).map(e=>({
                t:e.tagName,type:e.type||'',ph:e.placeholder||'',txt:(e.textContent||'').trim().substring(0,30),id:e.id||'',cls:(e.className||'').substring(0,30)
            }))""")
            print(f"  INPUTS NOT FOUND! Dump: {json.dumps(inputs,ensure_ascii=False)[:1000]}",flush=True)

        time.sleep(5)
    except Exception as e:
        print(f"  ERR: {e}",flush=True)
        import traceback;traceback.print_exc()
    finally:
        b.close()
