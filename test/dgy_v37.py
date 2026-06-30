#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""大哥云 登录+提取 — a03.dgy02.com"""
import sys, os, time, io, re, json, random
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from playwright.sync_api import sync_playwright

EMAIL = "dageyun_test_2026@outlook.com"
PASSWORD = "VpnTest2026!"
BASE = "https://a03.dgy02.com"

print("="*60)
print("  大哥云 登录+提取")
print("="*60)

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=False,
        args=["--ignore-certificate-errors","--no-sandbox",
              "--proxy-server=http://127.0.0.1:7897"])
    ctx = browser.new_context(viewport={"width":1280,"height":900},
        ignore_https_errors=True, locale="zh-CN")
    page = ctx.new_page()
    page.set_default_timeout(10000)
    
    page.add_init_script("""
        Object.defineProperty(navigator,'webdriver',{get:()=>false});
        Object.defineProperty(navigator,'plugins',{get:()=>[1,2,3,4,5]});
    """)
    
    try:
        # 打开首页
        page.goto(f"{BASE}/", wait_until="networkidle", timeout=25000)
        time.sleep(3)
        body = page.evaluate("() => document.body.innerText")
        print(f"   首页(500): {body[:500]}", flush=True)
        print(f"   URL: {page.url}", flush=True)
        page.screenshot(path=os.path.join(os.path.dirname(__file__),"dgy_v37_home.png"))
        
        # 找input和登录入口
        inputs = page.evaluate("""() => Array.from(document.querySelectorAll('input'))
            .map(i => ({type:i.type, name:i.name, id:i.id, placeholder:i.placeholder}))""")
        print(f"   Inputs: {inputs}", flush=True)
        
        # 找登录入口
        links = page.evaluate("""() => Array.from(document.querySelectorAll('a[href]'))
            .filter(a => a.href && a.href.includes('http'))
            .slice(0,30)
            .map(a => ({text:(a.textContent||'').trim().slice(0,50), href:a.href.slice(0,200)}))""")
        print(f"   链接: {links}", flush=True)
        
        # 尝试点登录
        try:
            login_el = page.locator('text=登录').first
            if login_el.is_visible():
                login_el.click()
                time.sleep(3)
                page.screenshot(path=os.path.join(os.path.dirname(__file__),"dgy_v37_login.png"))
        except:
            pass
        
        # 直接导航登录页
        for lp in ["/auth/login","/login","/user/login","/user"]:
            try:
                page.goto(f"{BASE}{lp}", wait_until="networkidle", timeout=15000)
                time.sleep(3)
                body = page.evaluate("() => document.body.innerText")
                if "邮箱" in body or "密码" in body:
                    print(f"   ✅ 登录页: {page.url}", flush=True)
                    page.screenshot(path=os.path.join(os.path.dirname(__file__),"dgy_v37_loginpage.png"))
                    break
            except:
                pass
        
        # 填表登录
        em = page.locator('input[name="email"], input[type="email"], input[placeholder*="邮箱"]').first
        pw = page.locator('input[name="password"], input[type="password"], input[placeholder*="密码"], input[name="passwd"]').first
        
        if em.count() > 0 and pw.count() > 0:
            em.click(); time.sleep(0.1); em.fill(EMAIL); time.sleep(0.3)
            pw.click(); time.sleep(0.1); pw.fill(PASSWORD); time.sleep(0.5)
            
            page.screenshot(path=os.path.join(os.path.dirname(__file__),"dgy_v37_filled.png"))
            
            btn = page.locator('button:has-text("登录"), button[type="submit"], button:has-text("登 录")').first
            if btn.count() > 0:
                btn.click()
                time.sleep(5)
                try: page.wait_for_load_state("networkidle", timeout=15000)
                except: pass
                print(f"   登录后URL: {page.url}", flush=True)
                body = page.evaluate("() => document.body.innerText")
                print(f"   页面(500): {body[:500]}", flush=True)
                page.screenshot(path=os.path.join(os.path.dirname(__file__),"dgy_v37_after_login.png"))
        
        # 提取订阅 — 大哥云面板可能有"一键订阅"按钮
        print("\n提取订阅...", flush=True)
        for sp in ["/user","/user/subscribe","/user/sub"]:
            try:
                page.goto(f"{BASE}{sp}", wait_until="networkidle", timeout=15000)
                time.sleep(3)
                body = page.evaluate("() => document.body.innerText")
                sub_match = re.findall(r'https?://[^\s]+(?:subscribe|sub|token|link)[^\s]*', body)
                if sub_match:
                    print(f"   ✅ {sp}: {sub_match[0]}", flush=True)
                    break
                print(f"   {sp}(300): {body[:300]}", flush=True)
            except:
                pass
        
        # 劫持剪贴板
        page.goto(f"{BASE}/user", wait_until="networkidle", timeout=15000)
        time.sleep(3)
        sub = page.evaluate("""async () => {
            window.__sub=''; 
            let old=navigator.clipboard.writeText; 
            navigator.clipboard.writeText=function(t){window.__sub=t;return old?old.call(navigator.clipboard,t):Promise.resolve();}; 
            let bs=document.querySelectorAll('button'); 
            for(let b of bs){if((b.textContent||'').includes('订阅')){b.click();break;}} 
            await new Promise(r=>setTimeout(r,800)); 
            return window.__sub||'';
        }""")
        print(f"   剪贴板: {sub}", flush=True)
        
        time.sleep(30)
        
    except Exception as e:
        print(f"异常: {e}", flush=True)
        import traceback; traceback.print_exc()
    finally:
        browser.close()
