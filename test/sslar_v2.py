#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SSLAR v2 — 首页直接登录（首页已有邮箱/密码表单），优惠码激活 → 订阅提取"""
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

    # ===== STEP 1: 首页直接填表登录 =====
    print("[STEP 1] 首页登录...", flush=True)
    page.goto(BASE, wait_until="networkidle", timeout=25000)
    time.sleep(4)
    page.screenshot(path=os.path.join(os.path.dirname(__file__), "sslar_v2_home.png"))

    # 分析所有input字段
    inputs = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('input')).map(e => ({
            tag: e.tagName, name: e.name||'', type: e.type||'',
            placeholder: e.placeholder||'', id: e.id||'',
            label: (e.labels?.[0]?.textContent||'').trim().substring(0,30)
        }));
    }""")
    print(f"   Input字段: {inputs}", flush=True)

    # 首页有登录表单 - 填
    email_els = [inp for inp in inputs if inp['type'] == 'email' or inp.get('name','') == 'email']
    pwd_els = [inp for inp in inputs if inp['type'] == 'password']
    
    if email_els:
        sel = f'input[name="{email_els[0]["name"]}"]' if email_els[0]['name'] else 'input[type="email"]'
        el = page.locator(sel).first
        el.click(); time.sleep(0.2)
        el.type(EMAIL, delay=60)
        print(f"   填邮箱 ✓", flush=True)
    
    if pwd_els:
        sel = f'input[name="{pwd_els[0]["name"]}"]' if pwd_els[0]['name'] else 'input[type="password"]'
        el = page.locator(sel).first
        el.click(); time.sleep(0.2)
        el.type(PASSWORD, delay=60)
        print(f"   填密码 ✓", flush=True)
    
    page.screenshot(path=os.path.join(os.path.dirname(__file__), "sslar_v2_filled.png"))
    
    # 点登录按钮
    login_btn = page.locator('button:has-text("登录")').first
    if login_btn.is_visible():
        login_btn.click()
        print(f"   点击登录 ✓", flush=True)
    
    time.sleep(5)
    try: page.wait_for_load_state("networkidle", timeout=15000)
    except: pass
    
    print(f"   URL: {page.url}", flush=True)
    body = page.evaluate("() => document.body.innerText.substring(0, 600)")
    print(f"   Body: {body[:500]}", flush=True)
    page.screenshot(path=os.path.join(os.path.dirname(__file__), "sslar_v2_after_login.png"))

    # 检查是否登录成功
    if "仪表盘" in body or "dashboard" in body.lower() or "用户中心" in body or "/user" in page.url:
        print(f"\n   ✅ 登录成功!", flush=True)
    elif "错误" in body or "密码" in body or "error" in body.lower():
        print(f"\n   ❌ 登录失败: {body[:300]}", flush=True)
        browser.close(); exit()

    # ===== STEP 2: 优惠码激活 =====
    print(f"\n[STEP 2] 优惠码激活...", flush=True)
    page.goto(f"{BASE}/user", wait_until="networkidle", timeout=15000)
    time.sleep(3)
    
    dash = page.evaluate("() => document.body.innerText")
    print(f"   Dashboard(500): {dash[:500]}", flush=True)
    page.screenshot(path=os.path.join(os.path.dirname(__file__), "sslar_v2_dash.png"))

    # 关键：找优惠码输入路径
    # 先分析所有a标签和导航
    nav_links = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('a')).filter(a => {
            let t = (a.textContent||'').trim();
            return t && t.length < 30;
        }).map(a => ({
            text: (a.textContent||'').trim().substring(0,25),
            href: (a.href||'').substring(0,120),
            className: (a.className||'').substring(0,30)
        }));
    }""")
    print(f"   导航链接: {nav_links}", flush=True)

    # 找优惠码相关
    for link in nav_links:
        txt = link['text'].lower()
        if any(kw in txt for kw in ['优惠','兑换','redeem','coupon','激活','code','邀请','invite']):
            print(f"   → 点击: {link['text']} -> {link['href']}", flush=True)
            try:
                page.locator(f'a:has-text("{link["text"]}")').first.click(timeout=3000)
                time.sleep(3)
                break
            except: pass

    # 当前页面是否有输入框
    cur_inputs = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('input')).slice(0,10).map(e => ({
            name: e.name, placeholder: e.placeholder, type: e.type, id: e.id
        }));
    }""")
    print(f"   当前输入框: {cur_inputs}", flush=True)
    page.screenshot(path=os.path.join(os.path.dirname(__file__), "sslar_v2_coupon_page.png"))

    # 填优惠码
    for inp in cur_inputs:
        try:
            if inp['name']:
                el = page.locator(f'input[name="{inp["name"]}"]').first
            elif inp['placeholder']:
                el = page.locator(f'input[placeholder="{inp["placeholder"]}"]').first
            else: continue
            if el.is_visible():
                el.click(); time.sleep(0.2)
                el.fill(COUPON)
                print(f"   填优惠码 -> {inp['name'] or inp['placeholder']} = {COUPON}", flush=True)
                time.sleep(0.5)
                
                # 找提交按钮
                btns = page.evaluate("""() => {
                    return Array.from(document.querySelectorAll('button, input[type="submit"]')).slice(0,5).map(e => ({
                        text: (e.textContent||e.value||'').trim().substring(0,20),
                        type: e.type
                    }));
                }""")
                print(f"   按钮: {btns}", flush=True)
                
                for b in btns:
                    if any(kw in b['text'] for kw in ['兑换','提交','redeem','激活','确认','ok']):
                        page.locator(f'button:has-text("{b["text"]}")').first.click()
                        print(f"   点击 {b['text']}", flush=True)
                        time.sleep(3)
                        break
                break
        except: pass

    page.screenshot(path=os.path.join(os.path.dirname(__file__), "sslar_v2_after_coupon.png"))

    # ===== STEP 3: 提取订阅 =====
    print(f"\n[STEP 3] 提取订阅...", flush=True)
    page.goto(f"{BASE}/user", wait_until="networkidle", timeout=15000)
    time.sleep(3)
    
    # 全面搜订阅URL
    all_text = page.evaluate("() => document.body.innerText")
    subs = re.findall(r'https?://[^\s]+(?:subscribe|sub|token|link|api)[^\s]*', all_text)
    print(f"   文本中URL: {subs}", flush=True)
    
    html = page.evaluate("() => document.documentElement.outerHTML")
    api_subs = re.findall(r'https?://[^\s"\'<>]+/api/v1/client/subscribe\?token=[^\s"\'<>]+', html)
    simple_subs = re.findall(r'https?://[^\s"\'<>]+/sub/[^\s"\'<>]+', html)
    print(f"   API订阅: {api_subs}", flush=True)
    print(f"   /sub/: {simple_subs}", flush=True)

    # 劫持剪贴板
    page.evaluate("""() => {
        window.__sslar_sub = '';
        navigator.clipboard.writeText = function(t) { window.__sslar_sub = t; return Promise.resolve(); };
    }""")

    # 点所有订阅按钮
    sub_btns = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('button, a')).filter(e => {
            let t = (e.textContent||'').trim();
            return /订阅|Clash|clash|复制|一键|生成|Subscribe|链接/i.test(t);
        }).map(e => ({
            tag: e.tagName, text: (e.textContent||'').trim().substring(0,30),
            href: (e.href||'').substring(0,150)
        }));
    }""")
    print(f"   订阅按钮: {sub_btns}", flush=True)
    
    for b in sub_btns:
        try:
            el = page.locator(f'{b["tag"]}:has-text("{b["text"][:18]}")').first
            if el.is_visible():
                el.click(force=True, timeout=2500)
                time.sleep(1.2)
        except: pass

    sub = page.evaluate("() => window.__sslar_sub")
    if sub: print(f"   ✅ 剪贴板订阅: {sub}", flush=True)
    
    # data-clipboard
    clips = page.evaluate("() => Array.from(document.querySelectorAll('[data-clipboard-text]')).map(e => e.getAttribute('data-clipboard-text'))")
    if clips: print(f"   ✅ data-clipboard: {clips}", flush=True)

    page.screenshot(path=os.path.join(os.path.dirname(__file__), "sslar_v2_final.png"), full_page=True)
    
    # 最终全文本
    final_text = page.evaluate("() => document.body.innerText")
    print(f"\n   全页文本:\n{final_text[:2000]}", flush=True)

    print(f"\n✅ 完成!", flush=True)
    time.sleep(10)
    browser.close()
