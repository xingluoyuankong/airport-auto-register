#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""51trojan 深度逆向分析"""
import sys,os,io,json,time
os.environ['HTTP_PROXY']='http://127.0.0.1:7897'
os.environ['HTTPS_PROXY']='http://127.0.0.1:7897'
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b=p.chromium.launch(channel="msedge",headless=False,
        args=["--proxy-server=http://127.0.0.1:7897","--ignore-certificate-errors","--no-sandbox"])
    c=b.new_context(viewport={"width":1280,"height":960},ignore_https_errors=True,locale="zh-CN")
    pg=c.new_page();pg.set_default_timeout(30000)
    pg.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>false});")
    
    print("=== 51trojan 深度分析 ===",flush=True)
    pg.goto("https://sub.51trojan.com/",wait_until="networkidle",timeout=60000)
    time.sleep(5)
    
    body=pg.evaluate("()=>document.body.innerText")
    print(f"URL:{pg.url}",flush=True)
    print(f"全部文字:\n{body[:3000]}",flush=True)
    pg.screenshot(path="51trojan_home.png")
    
    inputs=pg.evaluate("""()=>Array.from(document.querySelectorAll('input,select,textarea'))
        .map(e=>({tag:e.tagName,t:e.type||'',p:e.placeholder||'',id:e.id||'',name:e.name||''}))""")
    print(f"\nInputs({len(inputs)}):{json.dumps(inputs,ensure_ascii=False,indent=2)}",flush=True)
    
    btns=pg.evaluate("""()=>Array.from(document.querySelectorAll('button,a[role]'))
        .map(e=>({t:(e.textContent||'').trim().substring(0,60),cls:(e.className||'').substring(0,50)}))""")
    print(f"\nButtons({len(btns)}):{json.dumps(btns,ensure_ascii=False,indent=2)}",flush=True)
    
    links=pg.evaluate("""()=>Array.from(document.querySelectorAll('a[href]'))
        .filter(a=>a.textContent.trim()).map(a=>({t:a.textContent.trim().substring(0,60),h:a.href.substring(0,120)}))""")
    print(f"\nLinks({len(links)}):{json.dumps(links,ensure_ascii=False,indent=2)}",flush=True)
    
    print("\n✅ 分析完成，浏览器保持30秒",flush=True)
    time.sleep(30)
    b.close()
