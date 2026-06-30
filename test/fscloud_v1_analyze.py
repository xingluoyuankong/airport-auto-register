#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FSCloud 登录+提取 — Gmail已有验证码待收"""
import sys, os, time, io, re, json, random
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from playwright.sync_api import sync_playwright

EMAIL = "fscloud_test_2026@gmail.com"
PASSWORD = "Fscloud2026"
BASE = "https://web.fscloud.cc"

print("="*60)
print("  FSCloud 登录")
print(f"  邮箱: {EMAIL}")
print("="*60)

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=False,
        args=["--ignore-certificate-errors", "--no-sandbox",
              "--proxy-server=http://127.0.0.1:7897"])
    ctx = browser.new_context(viewport={"width":1280,"height":900},
        ignore_https_errors=True, locale="zh-CN")
    page = ctx.new_page()
    page.set_default_timeout(10000)
    
    page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {get:()=>false});
        Object.defineProperty(navigator, 'plugins', {get:()=>[1,2,3,4,5]});
    """)
    
    try:
        # 打开首页，看有没有登录表单
        print("\n[1] 打开首页...", flush=True)
        page.goto(f"{BASE}/", wait_until="networkidle", timeout=25000)
        time.sleep(3)
        print(f"   URL: {page.url}", flush=True)
        print(f"   标题: {page.title()}", flush=True)
        
        body = page.evaluate("() => document.body.innerText")
        print(f"   文本(600): {body[:600]}", flush=True)
        
        page.screenshot(path=os.path.join(os.path.dirname(__file__), "fscloud_v1_home.png"))
        
        # 找所有链接
        links = page.evaluate("""() => Array.from(document.querySelectorAll('a[href]'))
            .filter(a => a.href && a.href.includes('http'))
            .slice(0,30)
            .map(a => ({text:(a.textContent||'').trim().slice(0,50), href:a.href.slice(0,200)}))""")
        print(f"   链接: {links}", flush=True)
        
        # 找input
        inputs = page.evaluate("""() => Array.from(document.querySelectorAll('input'))
            .map(i => ({type:i.type, name:i.name, id:i.id, placeholder:i.placeholder}))""")
        print(f"   Inputs: {inputs}", flush=True)
        
        # 找登录入口
        has_login = any(kw in body for kw in ['登录', 'Login', 'login', 'Sign in'])
        has_register = any(kw in body for kw in ['注册', 'Register', 'register'])
        print(f"   登录入口: {has_login}, 注册入口: {has_register}", flush=True)
        
        # 如果有登录链接，点击
        login_found = False
        for link_text in ['登录', 'Login', '登录/注册', 'SIGN IN', '控制台']:
            try:
                btn = page.locator(f'text={link_text}').first
                if btn.is_visible():
                    print(f"   点击: {link_text}", flush=True)
                    btn.click()
                    time.sleep(3)
                    page.wait_for_load_state("networkidle", timeout=10000)
                    print(f"   跳转: {page.url}", flush=True)
                    body = page.evaluate("() => document.body.innerText")
                    print(f"   页面(500): {body[:500]}", flush=True)
                    login_found = True
                    break
            except:
                pass
        
        # 尝试直接打开/login
        if not login_found:
            for lp in ["/auth/login", "/login", "/user/login", "/signin"]:
                try:
                    print(f"   尝试: {BASE}{lp}", flush=True)
                    page.goto(f"{BASE}{lp}", wait_until="networkidle", timeout=15000)
                    time.sleep(3)
                    body = page.evaluate("() => document.body.innerText")
                    if "邮箱" in body or "email" in body.lower() or "密码" in body or "password" in body.lower():
                        print(f"   ✅ 登录页: {page.url}", flush=True)
                        login_found = True
                        break
                    else:
                        print(f"   不是登录页", flush=True)
                except:
                    pass
        
        if not login_found:
            print("   ❌ 找不到登录入口", flush=True)
            page.screenshot(path=os.path.join(os.path.dirname(__file__), "fscloud_v1_nologin.png"))
        
        time.sleep(30)
        
    except Exception as e:
        print(f"异常: {e}", flush=True)
        import traceback; traceback.print_exc()
        page.screenshot(path=os.path.join(os.path.dirname(__file__), "fscloud_v1_crash.png"))
    finally:
        browser.close()
