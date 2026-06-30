#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SSLAR v3 — SPA路由登录+优惠码激活 → 订阅提取"""
import sys, os, time, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from playwright.sync_api import sync_playwright

EMAIL = "mallenbb9qdjidg9y5tw1yqd@outlook.com"
PASSWORD = "VpnTest2026!"
COUPON = "iZcnBXiM"
BASE = "https://1.sslar.cn"

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=False,
        args=["--ignore-certificate-errors", "--no-sandbox",
              "--proxy-server=http://127.0.0.1:7897"])
    ctx = browser.new_context(viewport={"width": 1280, "height": 900},
        ignore_https_errors=True, locale="zh-CN")
    page = ctx.new_page()
    page.set_default_timeout(10000)

    # ===== STEP 1: 首页登录 =====
    print("[STEP 1] 登录", flush=True)
    page.goto(BASE, wait_until="networkidle", timeout=25000)
    time.sleep(4)
    
    page.locator('input[placeholder="请输入邮箱地址"]').first.type(EMAIL, delay=60)
    page.locator('input[placeholder="请输入密码"]').first.type(PASSWORD, delay=60)
    page.locator('button:has-text("登录")').first.click()
    time.sleep(5)
    try: page.wait_for_load_state("networkidle", timeout=10000)
    except: pass
    
    print(f"   URL: {page.url}", flush=True)
    body = page.evaluate("() => document.body.innerText || ''")
    
    if "无有效的套餐" in body or "仪表盘" in body:
        print(f"   ✅ 登录成功!", flush=True)
    else:
        print(f"   ❌ 登录未确认: {body[:200]}", flush=True)
        browser.close(); exit()

    page.screenshot(path=os.path.join(os.path.dirname(__file__), "sslar_v3_loggedin.png"))

    # ===== STEP 2: 遍历SPA路由找优惠码入口 =====
    print(f"\n[STEP 2] 遍历SPA路由...", flush=True)
    
    spa_routes = [
        "/#/shop", "/#/store",
        "/#/invite", "/#/invitation",
        "/#/code", "/#/coupon", "/#/redeem",
        "/#/user/code", "/#/user/invite", 
        "/#/user/coupon", "/#/user/redeem",
        "/#/user",
    ]
    
    code_page_found = None
    for route in spa_routes:
        try:
            print(f"   {route}...", end=" ", flush=True)
            page.goto(f"{BASE}{route}", wait_until="networkidle", timeout=12000)
            time.sleep(2)
            txt = page.evaluate("() => document.body.innerText || ''")
            
            if any(kw in txt for kw in ['优惠','兑换','redeem','coupon','激活','邀请','invite','推荐']):
                # 找输入框
                inputs = page.evaluate("""() => {
                    return Array.from(document.querySelectorAll('input')).filter(e => e.type != 'hidden' && e.type != 'checkbox' && e.offsetParent != null).map(e => ({
                        name: e.name||'', placeholder: e.placeholder||'', type: e.type, id: e.id||''
                    }));
                }""")
                print(f"✅ 输入框={inputs}", flush=True)
                if inputs:
                    code_page_found = route
                    page.screenshot(path=os.path.join(os.path.dirname(__file__), f"sslar_v3_{route.replace('#','').replace('/','_')}.png"))
                    
                    # 填优惠码
                    for inp in inputs:
                        sel = None
                        if inp['placeholder']: sel = f'input[placeholder="{inp["placeholder"]}"]'
                        elif inp['name']: sel = f'input[name="{inp["name"]}"]'
                        else: continue
                        el = page.locator(sel).first
                        if el.is_visible():
                            el.click(); time.sleep(0.2)
                            el.type(COUPON, delay=50)
                            print(f"   填: {inp['placeholder']} = {COUPON}", flush=True)
                            time.sleep(0.5)
                            
                            # 找提交按钮
                            page.locator('button').first.click()
                            time.sleep(3)
                            try: page.wait_for_load_state("networkidle", timeout=8000)
                            except: pass
                            
                            result = page.evaluate("() => document.body.innerText || ''")
                            print(f"   结果: {result[:200]}", flush=True)
                            page.screenshot(path=os.path.join(os.path.dirname(__file__), f"sslar_v3_after_code.png"))
                            break
                    break
            else:
                print(f"跳过 ({len(txt)}字)", flush=True)
        except Exception as e:
            print(f"错误 {e}", flush=True)

    if not code_page_found:
        print(f"\n   遍历完成，未找到优惠码输入页", flush=True)
        # 打印所有SPA路由内容
        for route in spa_routes:
            try:
                page.goto(f"{BASE}{route}", wait_until="networkidle", timeout=8000)
                time.sleep(1)
                txt = page.evaluate("() => document.body.innerText || ''")
                print(f"   {route}: {txt[:100]}", flush=True)
            except: pass

    # ===== STEP 3: 回Dashboard提取订阅 =====
    print(f"\n[STEP 3] 提取订阅...", flush=True)
    page.goto(f"{BASE}/#/user", wait_until="networkidle", timeout=12000)
    time.sleep(3)
    
    full_text = page.evaluate("() => document.body.innerText || ''")
    page.screenshot(path=os.path.join(os.path.dirname(__file__), "sslar_v3_dashboard.png"))
    
    # HTML搜订阅
    html = page.evaluate("() => document.documentElement.outerHTML")
    api_subs = re.findall(r'https?://[^\s"\'<>]+/api/v1/client/subscribe\?token=[^\s"\'<>]+', html)
    sub_urls = re.findall(r'https?://[^\s"\'<>]+/sub/[^\s"\'<>]+', html)
    link_urls = re.findall(r'https?://[^\s"\'<>]+/link/[^\s"\'<>]+', html)
    
    if api_subs: print(f"   ✅ API订阅: {api_subs}", flush=True)
    if sub_urls: print(f"   ✅ /sub/: {sub_urls}", flush=True)
    if link_urls: print(f"   ✅ /link/: {link_urls}", flush=True)
    
    # 也搜文本
    text_urls = re.findall(r'https?://[^\s]+(?:subscribe|sub|token|link)[^\s]*', full_text)
    if text_urls: print(f"   文本URL: {text_urls}", flush=True)
    
    # 劫持剪贴板
    page.evaluate("""() => {
        window.__sslar_sub = '';
        navigator.clipboard.writeText = function(t) { window.__sslar_sub = t; return Promise.resolve(); };
    }""")
    
    # 点所有按钮
    btns = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('button, a')).filter(e => {
            let t = (e.textContent||'').trim();
            return /订阅|Clash|clash|复制|一键|生成|Subscribe|链接|url/i.test(t);
        }).map(e => ({
            tag: e.tagName, text: (e.textContent||'').trim().substring(0,30),
            href: (e.href||'').substring(0,200)
        }));
    }""")
    print(f"   订阅按钮: {btns}", flush=True)
    
    for b in btns:
        try:
            el = page.locator(f'{b["tag"]}:has-text("{b["text"][:16]}")').first
            if el.is_visible():
                el.click(force=True, timeout=2500)
                time.sleep(1)
        except: pass

    sub = page.evaluate("() => window.__sslar_sub")
    clips = page.evaluate("() => Array.from(document.querySelectorAll('[data-clipboard-text]')).map(e => e.getAttribute('data-clipboard-text'))")
    
    if sub: print(f"   ✅ 剪贴板: {sub}", flush=True)
    if clips: print(f"   ✅ clipboard-attr: {clips}", flush=True)
    
    # 也直接从页面找API token
    tokens = page.evaluate("""() => {
        let scriptText = Array.from(document.querySelectorAll('script')).map(s => (s.textContent||'')).join('\\n');
        let matches = scriptText.match(/token["'\\s:=]+([a-f0-9]{20,})/gi);
        if (matches) return matches;
        return [];
    }""")
    print(f"   JS token: {tokens}", flush=True)

    print(f"\n   全Dashboard文本:\n{full_text[:2000]}", flush=True)

    print(f"\n✅ 完成!", flush=True)
    time.sleep(15)
    browser.close()
