#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""99ba 深度分析 - 保持浏览器打开"""
import sys,os,io,json,time
os.environ['HTTP_PROXY']='http://127.0.0.1:7897'; os.environ['HTTPS_PROXY']='http://127.0.0.1:7897'
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b=p.chromium.launch(channel="msedge",headless=False,args=["--proxy-server=http://127.0.0.1:7897","--ignore-certificate-errors","--no-sandbox"])
    c=b.new_context(viewport={"width":1280,"height":900},ignore_https_errors=True,locale="zh-CN")
    pg=c.new_page();pg.set_default_timeout(30000)
    pg.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>false});")
    
    pg.goto("https://a.99ba2026.fyi/#/register",wait_until="networkidle",timeout=60000)
    time.sleep(4)
    
    body=pg.evaluate("()=>document.body.innerText")
    print(f"Body(600):\n{body[:600]}\n",flush=True)
    
    # 深度分析: 所有input/select
    inputs=pg.evaluate("""()=>Array.from(document.querySelectorAll('input,select'))
        .map(e=>({t:e.type||'select',placeholder:e.placeholder||'',id:e.id||'',name:e.name||'',className:e.className?.substring(0,60)||''}))""")
    print(f"Inputs: {json.dumps(inputs,ensure_ascii=False,indent=2)}\n",flush=True)
    
    # 深度分析: 按钮
    btns=pg.evaluate("""()=>Array.from(document.querySelectorAll('button'))
        .map(e=>({text:e.textContent?.trim()||'',className:e.className?.substring(0,60)||''}))""")
    print(f"Buttons: {json.dumps(btns,ensure_ascii=False,indent=2)}\n",flush=True)
    
    # 打开下拉看有哪些邮箱后缀
    pg.click(".n-base-selection-label")
    time.sleep(1)
    options=pg.evaluate("""()=>Array.from(document.querySelectorAll('.n-base-select-option,.n-option'))
        .map(e=>({text:e.textContent?.trim()||''}))""")
    print(f"Email options: {json.dumps(options,ensure_ascii=False,indent=2)}\n",flush=True)
    
    # 截图
    pg.screenshot(path="99ba_deep.png")
    print("screenshot saved; keep open 60s",flush=True)
    time.sleep(60)
    b.close()
