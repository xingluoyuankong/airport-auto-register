#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""51trojan 路径暴力扫描"""
import sys,os,io,time,json
os.environ['HTTP_PROXY']='http://127.0.0.1:7897'
os.environ['HTTPS_PROXY']='http://127.0.0.1:7897'
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
from playwright.sync_api import sync_playwright

URLS=[
    "https://sub.51trojan.com/#/register",
    "https://sub.51trojan.com/#/login",
    "https://sub.51trojan.com/#/dashboard",
    "https://sub.51trojan.com/#/user",
    "https://sub.51trojan.com/register",
    "https://sub.51trojan.com/login",
    "https://www.51trojan.com/#/register",
    "https://www.51trojan.com/",
    "https://51trojan.com/#/register",
    "https://51trojan.com/",
]

with sync_playwright() as p:
    b=p.chromium.launch(channel="msedge",headless=False,
        args=["--proxy-server=http://127.0.0.1:7897","--ignore-certificate-errors","--no-sandbox"])
    c=b.new_context(viewport={"width":1280,"height":960},ignore_https_errors=True,locale="zh-CN")
    pg=c.new_page();pg.set_default_timeout(30000)
    pg.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>false});")
    
    for url in URLS:
        try:
            pg.goto(url,wait_until="domcontentloaded",timeout=20000)
            time.sleep(3)
            body=pg.evaluate("()=>(document.body?.innerText||'').substring(0,300)")
            title=pg.title()
            cur=pg.url
            print(f"[{cur}] title={title}\n  body={body[:200]}\n",flush=True)
            pg.screenshot(path=f"51trojan_{url.split('/')[-1].replace('#','').replace('?','_')}.png")
        except Exception as e:
            print(f"[{url}] ❌ {str(e)[:100]}\n",flush=True)
    
    b.close()
