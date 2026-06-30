# -*- coding: utf-8 -*-
"""FLYBIT — 登录+提取订阅链接(已注册账号)"""
import sys,io,os,json,time
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
from playwright.sync_api import sync_playwright

email_addr=sys.argv[1] if len(sys.argv)>1 else "landsanchehrqvrw49590ycpji@outlook.com"
reg_pass=sys.argv[2] if len(sys.argv)>2 else "VpnTest2026!"

with sync_playwright() as p:
    b=p.chromium.launch(channel="msedge",headless=False,
        args=["--proxy-server=http://127.0.0.1:7897","--ignore-certificate-errors","--no-sandbox"])
    ctx=b.new_context(viewport={"width":1280,"height":800},ignore_https_errors=True,locale="zh-CN")
    page=ctx.new_page()
    
    # 1. 登录
    print(f"login {email_addr}...")
    page.goto("https://flybit.vip/#/login",wait_until="networkidle",timeout=30000)
    time.sleep(2)
    page.fill('input[type="email"]',email_addr)
    pws=page.query_selector_all('input[type="password"]')
    if pws: pws[0].fill(reg_pass)
    login_btn=page.query_selector('button:has-text("登录"), button:has-text("Login")')
    if login_btn: 
        login_btn.click()
        time.sleep(5)
    
    cur=page.url
    print(f"URL after login: {cur}")
    
    # 2. 提取
    sub=page.evaluate("()=>{var r=localStorage.getItem('VUE_NAIVE_ACCESS_TOKEN');if(!r)return'NO_TOKEN';var t='';try{var p=JSON.parse(r);t=p.value||''}catch(e){t=r};return'TOKEN:'+t.substring(0,30)}")
    print(f"getSubscribe: {sub}")
    
    # 3. 直接在页面找订阅按钮
    btns=page.query_selector_all('button,a,span,div')
    for el in btns:
        try:
            t=(el.inner_text() or '').strip()[:80]
            if '订阅' in t or 'subscribe' in t.lower():
                print(f"found: {t}")
        except: pass
    
    page.screenshot(path="flybit_dashboard.png")
    print("screenshot: flybit_dashboard.png")
    b.close()
