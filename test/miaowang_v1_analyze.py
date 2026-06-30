#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""喵喵网络 — 深度浏览分析 V1"""
import sys, os, time, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=False,
        args=["--ignore-certificate-errors","--no-sandbox",
              "--proxy-server=http://127.0.0.1:7897"])
    ctx = browser.new_context(viewport={"width":1280,"height":900},
        ignore_https_errors=True, locale="zh-CN")
    page = ctx.new_page()
    page.set_default_timeout(10000)
    
    try:
        # Step 1: 注册页
        print("[1] 注册页...", flush=True)
        page.goto("https://www.miaonetwork.com/#/register?code=v3fkHXqC", 
                  wait_until="networkidle", timeout=25000)
        time.sleep(4)
        
        body = page.evaluate("() => document.body.innerText")
        title = page.title()
        url = page.url
        
        print(f"   URL: {url}", flush=True)
        print(f"   标题: {title}", flush=True)
        print(f"   文本(800):\n{body[:800]}", flush=True)
        
        # 深度分析
        inputs = page.evaluate("""() => Array.from(document.querySelectorAll('input'))
            .map(i => ({type:i.type, name:i.name, id:i.id, placeholder:i.placeholder, className:i.className?.slice(0,40)}))""")
        print(f"\n   Inputs: {json.dumps(inputs, ensure_ascii=False, indent=2)}", flush=True)
        
        selects = page.evaluate("""() => Array.from(document.querySelectorAll('select'))
            .map(s => ({name:s.name, id:s.id, options:Array.from(s.querySelectorAll('option')).map(o=>o.value)}))""")
        print(f"   Selects: {json.dumps(selects, ensure_ascii=False)}", flush=True)
        
        buttons = page.evaluate("""() => Array.from(document.querySelectorAll('button'))
            .map(b => ({text:(b.textContent||'').trim().slice(0,40), type:b.type, className:b.className?.slice(0,40)}))""")
        print(f"   Buttons: {json.dumps(buttons, ensure_ascii=False)}", flush=True)
        
        links = page.evaluate("""() => Array.from(document.querySelectorAll('a[href]'))
            .filter(a => a.href && a.href.includes('http'))
            .slice(0,20)
            .map(a => ({t:(a.textContent||'').trim().slice(0,40), h:a.href.slice(0,200)}))""")
        print(f"   Links: {json.dumps(links, ensure_ascii=False)}", flush=True)
        
        page.screenshot(path=os.path.join(os.path.dirname(__file__), "miaowang_v1_register.png"))
        
        # 找邮箱后缀
        suffix_els = page.evaluate("""() => {
            let s = document.querySelector('select');
            if (!s) return null;
            return Array.from(s.querySelectorAll('option')).map(o => ({value:o.value, text:o.textContent}));
        }""")
        print(f"\n   邮箱后缀: {suffix_els}", flush=True)
        
        # 有注册表单吗？
        has_form = any(i['type'] in ['email','text'] for i in inputs)
        print(f"\n   有表单: {has_form}", flush=True)
        
        # 如果有outlook.com后缀就填表注册
        has_outlook = suffix_els and any('outlook' in str(o.get('value','')).lower() for o in suffix_els)
        print(f"   有Outlook后缀: {has_outlook}", flush=True)
        
        print("\n✅ 分析完成，浏览器保持打开30秒", flush=True)
        time.sleep(30)
        
    except Exception as e:
        print(f"异常: {e}", flush=True)
        import traceback; traceback.print_exc()
    finally:
        browser.close()
