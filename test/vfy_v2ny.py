#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v2ny/奈云 验证 - id填表"""
import sys,os,io,json,time,re
os.environ['HTTP_PROXY']='http://127.0.0.1:7897';os.environ['HTTPS_PROXY']='http://127.0.0.1:7897'
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
from playwright.sync_api import sync_playwright

EMAIL="averymorga4g0jfbs6q2up@outlook.com"
PASS="VpnTest2026!"

with sync_playwright() as p:
    b=p.chromium.launch(channel="msedge",headless=False,args=["--proxy-server=http://127.0.0.1:7897","--ignore-certificate-errors","--no-sandbox"])
    c=b.new_context(viewport={"width":1280,"height":900},ignore_https_errors=True,locale="zh-CN")
    pg=c.new_page();pg.set_default_timeout(15000)
    try:
        print("=== v2ny ===",flush=True)
        pg.goto("https://www.v2ny.com/#/auth/login",wait_until="domcontentloaded",timeout=45000)
        time.sleep(3)
        pg.fill("#login-email",EMAIL)
        pg.fill("#login-password",PASS)
        time.sleep(0.2)
        pg.screenshot(path="v2ny_vfy_filled.png")
        pg.click('button:has-text("登录")')
        time.sleep(6)
        try: pg.wait_for_load_state("networkidle",timeout=10000)
        except: pass
        body=pg.evaluate("()=>document.body.innerText")
        print(f"After login:{body[:300]}",flush=True)
        pg.screenshot(path="v2ny_vfy_dash.png")

        # v2ny用的是 #dashboard 页直接可见订阅URL
        m=re.search(r'https?://[^\s]+/sleep/\w+',body)
        if m:
            sub=m.group(0)
            print(f"✅ v2ny SUB:{sub}",flush=True)
        else:
            # 尝试API
            raw=pg.evaluate('localStorage.getItem("VUE_NAIVE_ACCESS_TOKEN")')
            if raw:
                resp=pg.evaluate("(tok)=>{let t='';try{let p=JSON.parse(tok);t=p.value||p.token||p}catch(e){t=tok};let x=new XMLHttpRequest();x.open('GET','/api/v1/user/getSubscribe',false);x.setRequestHeader('Authorization',t);try{x.send()}catch(e){}return x.responseText}",raw)
                print(f"API:{resp[:300]}",flush=True)
                try:
                    d=json.loads(resp)
                    sub=d.get("data",{}).get("subscribe_url","")
                except: sub=""
                if sub: print(f"✅ v2ny SUB:{sub}",flush=True)
        time.sleep(3)
    except Exception as e: print(f"e:{e}",flush=True)
    finally: b.close()
