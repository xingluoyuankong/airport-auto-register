#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证 FLYBIT 全部6个机场的脚本"""
import sys,os,io,json,time,re
os.environ['HTTP_PROXY']='http://127.0.0.1:7897'; os.environ['HTTPS_PROXY']='http://127.0.0.1:7897'
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
from playwright.sync_api import sync_playwright

# FLYBIT: 注册页是前缀+select后缀，登录页也是前缀+select
EMAIL="colemanbroovp9xyduj92hubhn@outlook.com"
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
        print("=== FLYBIT VERIFY ===",flush=True)

        # Try www.flybit.vip instead
        pg.goto("https://www.flybit.vip/#/login",wait_until="domcontentloaded",timeout=45000)
        time.sleep(3)
        body=pg.evaluate("()=>document.body.innerText")
        url=pg.url
        print(f"URL:{url}\nBody:{body[:400]}",flush=True)

        pg.fill('input[placeholder="邮箱"]',prefix)
        time.sleep(0.2)
        pg.select_option('select',suffix)
        time.sleep(0.2)
        pw=pg.query_selector('input[type="password"]')
        if pw: pw.fill(PASS)
        time.sleep(0.2)
        pg.click('button:has-text("登录")')
        time.sleep(5)
        try: pg.wait_for_load_state("networkidle",timeout=10000)
        except: pass

        body2=pg.evaluate("()=>document.body.innerText")
        url=pg.url
        print(f"AfterLogin URL:{url}\nBody:{body2[:400]}",flush=True)
        pg.screenshot(path="flybit_vfy_dash.png")

        # Extract
        raw=pg.evaluate('localStorage.getItem("VUE_NAIVE_ACCESS_TOKEN")')
        print(f"TOKEN:{(raw or 'NONE')[:80]}",flush=True)

        if raw:
            resp=pg.evaluate("(tok) => {let t='';try{let p=JSON.parse(tok);t=p.value||p.token||p}catch(e){t=tok};let x=new XMLHttpRequest();x.open('GET','/api/v1/user/getSubscribe',false);x.setRequestHeader('Authorization',t);try{x.send()}catch(e){}return x.responseText}",raw)
            print(f"getSubscribe:{resp[:300]}",flush=True)
            try:
                d=json.loads(resp)
                sub=d.get("data",{}).get("subscribe_url","") or d.get("subscribe_url","")
            except:
                urls=re.findall(r'subscribe_url["\s:]+(https?://[^"\s]+)',resp)
                sub=urls[0] if urls else ""
            if sub:
                print(f"✅ FLYBIT SUB:{sub}",flush=True)
            else:
                print("NO SUB",flush=True)

        time.sleep(5)
    except Exception as e:
        print(f"e:{e}",flush=True)
        import traceback;traceback.print_exc()
    finally:
        b.close()
