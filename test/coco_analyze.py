#!/usr/bin/env python3
"""Quick analysis of COCODUCK register page buttons/structure"""
import os; os.environ['HTTP_PROXY']='http://127.0.0.1:7897'; os.environ['HTTPS_PROXY']='http://127.0.0.1:7897'
from playwright.sync_api import sync_playwright
import time, json

with sync_playwright() as p:
    b=p.chromium.launch(channel="msedge",headless=False,args=["--proxy-server=http://127.0.0.1:7897","--ignore-certificate-errors","--no-sandbox"])
    c=b.new_context(viewport={"width":1280,"height":900},ignore_https_errors=True)
    pg=c.new_page(); pg.set_default_timeout(30000)
    pg.goto("https://www.cocoduck.live/auth/register?code=8c1073605d",wait_until="networkidle",timeout=60000)
    time.sleep(5)

    # All clickable elements
    btns=pg.evaluate("""()=>Array.from(document.querySelectorAll('button,a,input[type=submit],input[type=button]'))
        .map(e=>({tag:e.tagName,t:(e.textContent||e.value||'').trim().substring(0,60),
        cls:(e.className||'').substring(0,80),id:e.id||''}))""")
    for bb in btns:
        if bb["t"]: print(json.dumps(bb,ensure_ascii=False))

    # Form HTML
    html=pg.evaluate("""()=>{
        let f=document.querySelector('form');
        return f ? f.outerHTML.substring(0,2500) : 'no-form';
    }""")
    print("FORM:", html[:2500])

    # Email input attr
    email_attrs=pg.evaluate("""()=>{
        let e=document.querySelector('input[type=email]');
        if(!e) e=document.querySelector('input#email');
        if(!e) e=document.querySelector('input[placeholder*=\"电子\"]');
        return e ? {type:e.type,id:e.id,name:e.name,placeholder:e.placeholder,className:e.className} : 'not-found';
    }""")
    print("EMAIL_INPUT:", json.dumps(email_attrs, ensure_ascii=False))

    pg.screenshot(path="cocoduck_analyze.png")
    time.sleep(5); b.close()
