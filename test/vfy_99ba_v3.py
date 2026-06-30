#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""99ba 验证V3 - 已注册账户直接登录提取订阅"""
import sys,os,io,json,time,re
os.environ['HTTP_PROXY']='http://127.0.0.1:7897'
os.environ['HTTPS_PROXY']='http://127.0.0.1:7897'
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
from playwright.sync_api import sync_playwright

EMAIL="aiden533ju9y2wx2bjmd@outlook.com"
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
        print("=== 99ba LOGIN ===",flush=True)
        pg.goto("https://a.99ba2026.fyi/#/login",wait_until="networkidle",timeout=45000)
        time.sleep(2)

        pg.fill('input[placeholder="邮箱"]', EMAIL)
        time.sleep(0.2)
        pw=pg.query_selector('input[type="password"]')
        if pw: pw.fill(PASS)
        time.sleep(0.2)
        pg.click('button:has-text("登入")')
        time.sleep(5)
        pg.wait_for_load_state("networkidle",timeout=10000)

        body=pg.evaluate("()=>document.body.innerText")
        print(f"Body:{body[:400]}",flush=True)
        pg.screenshot(path="99ba_dash.png")

        # Extract subscription using raw_token param
        raw=pg.evaluate('localStorage.getItem("VUE_NAIVE_ACCESS_TOKEN")')
        print(f"TOKEN: {(raw or 'NONE')[:80]}",flush=True)

        if raw:
            # Use page.evaluate with argument for cross-context token pass
            resp=pg.evaluate("(tok) => {let t='';try{let p=JSON.parse(tok);t=p.value||p.token||p}catch(e){t=tok};let x=new XMLHttpRequest();x.open('GET','/api/v1/user/getSubscribe',false);x.setRequestHeader('Authorization',t);try{x.send()}catch(e){}return x.responseText}",raw)
            print(f"getSubscribe:{resp[:300]}",flush=True)
            try:
                d=json.loads(resp)
                sub=d.get("data",{}).get("subscribe_url","") or d.get("subscribe_url","")
            except:
                urls=re.findall(r'subscribe_url["\s:]+(https?://[^"\s]+)',resp)
                sub=urls[0] if urls else ""
            if sub:
                print(f"✅ SUB:{sub}",flush=True)
            else:
                print("NO SUB in resp",flush=True)

        time.sleep(5)
    except Exception as e:
        print(f"e:{e}",flush=True)
        import traceback;traceback.print_exc()
    finally:
        b.close()
