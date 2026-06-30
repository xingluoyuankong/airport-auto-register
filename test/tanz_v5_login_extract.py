#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TANZCLOUD — 用API注册获取的新账号登录提取订阅"""
import sys, os, time, io, re, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from playwright.sync_api import sync_playwright

# 新注册账号
EMAIL = "mx4496f269fa@hotmail.com"
PASSWORD = "VpnTest2026!"
BASE = "https://www.tanz.website"

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=False,
        args=["--ignore-certificate-errors", "--no-sandbox",
              "--proxy-server=http://127.0.0.1:7897"])
    ctx = browser.new_context(viewport={"width": 1280, "height": 900},
        ignore_https_errors=True, locale="zh-CN")
    page = ctx.new_page()
    page.set_default_timeout(10000)

    print("[1] 登录...", flush=True)
    page.goto(f"{BASE}/auth/login", wait_until="networkidle", timeout=25000)
    time.sleep(3)
    
    page.locator('input[name="email"]').first.fill(EMAIL)
    page.locator('input[name="password"]').first.fill(PASSWORD)
    page.locator('button[type="submit"]').first.click()
    
    time.sleep(5)
    page.wait_for_load_state("networkidle", timeout=15000)
    print(f"   URL: {page.url}", flush=True)
    
    body = page.evaluate("() => document.body.innerText.substr(0, 300)")
    print(f"   页面: {body[:200]}", flush=True)
    page.screenshot(path=os.path.join(os.path.dirname(__file__), "tanz_v5_login.png"))
    
    if "/user" not in page.url:
        print(f"   ❌ 登录失败! 页面: {body}", flush=True)
        browser.close()
        exit(1)
    
    print(f"   ✅ 登录成功!", flush=True)
    
    print("\n[2] 找订阅链接...", flush=True)
    page.goto(f"{BASE}/user", wait_until="networkidle", timeout=20000)
    time.sleep(4)
    page.screenshot(path=os.path.join(os.path.dirname(__file__), "tanz_v5_user.png"))
    
    user_text = page.evaluate("() => document.body.innerText")
    print(f"   User页文本: {user_text[:500]}", flush=True)
    
    # 找订阅URL的所有方式
    # 1. 文本搜
    subs = re.findall(r'https?://[^\s]+(?:subscribe|sub|token|link)[^\s]*', user_text)
    print(f"   文本URL: {subs}", flush=True)
    
    # 2. a标签
    links = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('a[href]')).filter(a => {
            let h = a.href || '';
            return h.includes('sub') || h.includes('token') || h.includes('/api/');
        }).map(a => ({text: (a.textContent||'').substring(0,30), href: a.href.substring(0,200)}));
    }""")
    print(f"   链接: {links}", flush=True)
    
    # 3. 订阅页面
    for sub_path in ["/user/subscribe", "/user#subscribe", "/user/sub", "/user/subscription"]:
        print(f"\n   尝试: {BASE}{sub_path}", flush=True)
        try:
            page.goto(f"{BASE}{sub_path}", wait_until="networkidle", timeout=12000)
            time.sleep(3)
            sub_text = page.evaluate("() => document.body.innerText")
            
            urls = re.findall(r'https?://[^\s]+(?:subscribe|sub|token|link)[^\s]*', sub_text)
            if urls:
                print(f"   ✅ 找到: {urls}", flush=True)
                break
            
            # 从HTML搜
            html = page.evaluate("() => document.documentElement.outerHTML")
            urls2 = re.findall(r'https?://[^\s"\'<>]+token=[^\s"\'<>]+', html)
            if urls2:
                print(f"   ✅ HTML找到: {urls2}", flush=True)
                break
                
            print(f"   文本(300): {sub_text[:300]}", flush=True)
        except Exception as e:
            print(f"   错误: {e}", flush=True)
    
    # 4. 劫持剪贴板点一键订阅按钮
    print(f"\n[3] 剪贴板拦截...", flush=True)
    page.goto(f"{BASE}/user", wait_until="networkidle", timeout=15000)
    time.sleep(2)
    
    page.evaluate("""() => {
        window.__tanz_sub = '';
        navigator.clipboard.writeText = function(t) {
            window.__tanz_sub = t;
            return Promise.resolve();
        };
    }""")
    
    # 找所有按钮
    btns = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('button, a.btn, span.btn')).map(b => ({
            text: (b.textContent||'').trim().substring(0,50),
            href: b.href||''
        }));
    }""")
    print(f"   按钮: {btns}", flush=True)
    
    # 点击每个可能的按钮
    for b in btns:
        txt = b['text']
        if any(kw in txt for kw in ['订阅', 'Clash', 'clash', '一键', '复制', '生成', 'Subscribe']):
            try:
                sel = f'text={txt}'
                el = page.locator(sel).first
                if el.is_visible():
                    el.click(timeout=3000)
                    time.sleep(1.5)
            except:
                pass
    
    sub = page.evaluate("() => window.__tanz_sub")
    print(f"   剪贴板: {sub}", flush=True)
    
    # 5. data属性
    data = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('[data-clipboard-text]')).map(e => e.getAttribute('data-clipboard-text'));
    }""")
    print(f"   data-clipboard: {data}", flush=True)
    
    # 6. V2Board AJAX API
    print(f"\n[4] 尝试V2Board API...", flush=True)
    page.goto(f"{BASE}/user/subscribe", wait_until="networkidle", timeout=20000)
    time.sleep(3)
    page.screenshot(path=os.path.join(os.path.dirname(__file__), "tanz_v5_subpage.png"))
    
    api_url = page.evaluate("""() => {
        let html = document.documentElement.outerHTML;
        // 搜V2Board标准订阅URL模式
        let m = html.match(/https?:\\/\\/\\S+\\/api\\/v1\\/client\\/subscribe\\?token=\\S+/);
        if (m) return m[0];
        
        // 搜base64 token
        let m2 = html.match(/token=([a-zA-Z0-9_\\-]{20,})/);
        if (m2) return m2[0];
        
        // 搜/sub/ token
        let m3 = html.match(/https?:\\/\\/\\S+\\/sub\\/\\S+/);
        if (m3) return m3[0];
        
        return '';
    }""")
    print(f"   API URL: {api_url}", flush=True)
    
    sub_text = page.evaluate("() => document.body.innerText")
    print(f"   订阅页文本(800):\n{sub_text[:800]}", flush=True)
    
    print(f"\n✅ 完成!", flush=True)
    time.sleep(15)
    browser.close()
