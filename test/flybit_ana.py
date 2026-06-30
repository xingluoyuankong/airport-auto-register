#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FLYBIT analyze"""
import sys,os,io,json,time
os.environ['HTTP_PROXY']='http://127.0.0.1:7897'; os.environ['HTTPS_PROXY']='http://127.0.0.1:7897'
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b=p.chromium.launch(channel="msedge",headless=False,args=["--proxy-server=http://127.0.0.1:7897","--ignore-certificate-errors","--no-sandbox"])
    c=b.new_context(viewport={"width":1280,"height":900},ignore_https_errors=True,locale="zh-CN")
    pg=c.new_page();pg.set_default_timeout(30000)
    pg.goto("https://s.fb.22na.cn/#/register",wait_until="networkidle",timeout=60000)
    time.sleep(4)
    body=pg.evaluate("()=>document.body.innerText")
    print(f"FLYBIT:{body[:600]}",flush=True)
    inputs=pg.evaluate("""()=>Array.from(document.querySelectorAll('input,select'))
        .map(e=>({t:e.type||'select',p:e.placeholder||'',id:e.id||'',tag:e.tagName}))""")
    print(f"Inputs:{json.dumps(inputs,ensure_ascii=False)}",flush=True)
    btns=pg.evaluate("""()=>Array.from(document.querySelectorAll('button'))
        .map(e=>({t:e.textContent.trim()})))""")
    print(f"Buttons:{json.dumps(btns,ensure_ascii=False)}",flush=True)
    pg.screenshot(path="flybit_ana.png")
    time.sleep(2);b.close()
