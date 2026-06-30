#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SSLAR — 登录 → 优惠码激活 → 提取订阅"""
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

    # ========== STEP 1: 打开首页，分析结构 ==========
    print("[STEP 1] 分析首页...", flush=True)
    page.goto(BASE, wait_until="networkidle", timeout=25000)
    time.sleep(3)
    page.screenshot(path=os.path.join(os.path.dirname(__file__), "sslar_v1_home.png"))
    
    body = page.evaluate("() => document.body.innerText.substring(0, 500)")
    print(f"   首页: {body[:300]}", flush=True)
    
    # 找登录入口
    nav = page.evaluate("""() => {
        let items = Array.from(document.querySelectorAll('a, button, li, span')).filter(e => {
            let t = (e.textContent||'').trim();
            return ['登录','登陆','sign in','login','注册','register'].includes(t);
        }).slice(0,10).map(e => ({
            tag: e.tagName, text: (e.textContent||'').trim().substring(0,20),
            href: e.href?.substring(0,100) || '',
            id: e.id, className: (e.className||'').substring(0,30)
        }));
        return items;
    }""")
    print(f"   导航入口: {nav}", flush=True)
    
    # ========== STEP 2: 登录 ==========
    print(f"\n[STEP 2] 登录...", flush=True)
    page.goto(f"{BASE}/auth/login", wait_until="networkidle", timeout=20000)
    time.sleep(3)
    page.screenshot(path=os.path.join(os.path.dirname(__file__), "sslar_v1_login.png"))
    
    login_body = page.evaluate("() => document.body.innerText.substring(0, 400)")
    print(f"   登录页: {login_body[:300]}", flush=True)
    
    # 深度分析登录表单HTML
    form_html = page.evaluate("""() => {
        let fs = document.querySelectorAll('input, button, select, form');
        return Array.from(fs).slice(0,15).map(e => ({
            tag: e.tagName, name: e.name||'', type: e.type||'',
            placeholder: e.placeholder||'', id: e.id||'',
            autocomplete: e.autocomplete||''
        }));
    }""")
    print(f"   表单字段: {form_html}", flush=True)
    
    # 精准填表
    email_el = page.locator('input[name="email"]').first
    email_el.click(); time.sleep(0.3)
    email_el.type(EMAIL, delay=60)
    
    pwd_el = page.locator('input[name="passwd"], input[name="password"]').first
    pwd_el.click(); time.sleep(0.3)
    pwd_el.type(PASSWORD, delay=60)
    
    page.screenshot(path=os.path.join(os.path.dirname(__file__), "sslar_v1_filled.png"))
    
    page.locator('button[type="submit"]').first.click()
    time.sleep(5)
    try: page.wait_for_load_state("networkidle", timeout=15000)
    except: pass
    
    print(f"   登录后URL: {page.url}", flush=True)
    login_result = page.evaluate("() => document.body.innerText.substring(0, 400)")
    print(f"   结果: {login_result[:300]}", flush=True)
    page.screenshot(path=os.path.join(os.path.dirname(__file__), "sslar_v1_after_login.png"))
    
    if "/user" in page.url:
        print(f"\n   ✅ 登录成功!", flush=True)
        
        # ========== STEP 3: 激活优惠码 ==========
        print(f"\n[STEP 3] 优惠码激活...", flush=True)
        page.goto(f"{BASE}/user", wait_until="networkidle", timeout=15000)
        time.sleep(3)
        dash = page.evaluate("() => document.body.innerText.substring(0, 600)")
        print(f"   Dashboard: {dash[:500]}", flush=True)
        
        # 找优惠码入口
        coupon_links = page.evaluate("""() => {
            return Array.from(document.querySelectorAll('a, button')).filter(e => {
                let t = (e.textContent||'').trim();
                return /优惠|兑换|redeem|coupon|激活|code|invite|邀请/i.test(t);
            }).map(e => ({
                tag: e.tagName, text: t.substring(0,30),
                href: (e.href||'').substring(0,100),
                className: (e.className||'').substring(0,30)
            }));
            let t;
        }""")
        print(f"   优惠码入口: {coupon_links}", flush=True)
        
        # 导航到优惠码/激活页面
        for path in ["/user/code", "/user/redeem", "/user/coupon", "/user/invite"]:
            try:
                page.goto(f"{BASE}{path}", wait_until="networkidle", timeout=10000)
                time.sleep(2)
                page_text = page.evaluate("() => document.body.innerText.substring(0, 300)")
                if "优惠" in page_text or "兑换" in page_text or "激活" in page_text or "code" in page_text.lower():
                    print(f"   ✅ 优惠码页: {path} — {page_text[:200]}", flush=True)
                    break
                print(f"   {path}: {page_text[:100]}", flush=True)
            except:
                pass
        
        # 找输入框填优惠码
        code_inputs = page.evaluate("""() => {
            return Array.from(document.querySelectorAll('input')).filter(e => {
                let n = (e.name||'').toLowerCase() + (e.placeholder||'').toLowerCase();
                return /code|coupon|优惠|redeem|邀请|激活/.test(n);
            }).map(e => ({
                name: e.name, placeholder: e.placeholder, type: e.type, id: e.id
            }));
        }""")
        print(f"   优惠码输入框: {code_inputs}", flush=True)
        
        if code_inputs:
            el = page.locator('input').first
            for ci in code_inputs:
                sel = f'input[name="{ci["name"]}"]' if ci['name'] else f'input[placeholder="{ci["placeholder"]}"]'
                try:
                    el = page.locator(sel).first
                    if el.is_visible(): break
                except: pass
            
            el.click(); time.sleep(0.2)
            el.type(COUPON, delay=60)
            time.sleep(0.5)
            
            # 找提交按钮
            submit_btns = page.evaluate("""() => {
                return Array.from(document.querySelectorAll('button, input[type="submit"]')).filter(e => {
                    let t = (e.textContent||e.value||'').trim();
                    return /兑换|提交|redeem|激活|submit|ok/i.test(t);
                }).slice(0,5).map(e => t.substring(0,20));
            }""")
            print(f"   提交按钮: {submit_btns}", flush=True)
            
            page.locator('button').first.click()
            time.sleep(3)
        
        page.screenshot(path=os.path.join(os.path.dirname(__file__), "sslar_v1_coupon.png"))
        
        # ========== STEP 4: 提取订阅 ==========
        print(f"\n[STEP 4] 提取订阅...", flush=True)
        page.goto(f"{BASE}/user", wait_until="networkidle", timeout=15000)
        time.sleep(3)
        
        # 搜索订阅URL
        all_text = page.evaluate("() => document.body.innerText")
        subs = re.findall(r'https?://[^\s]+(?:subscribe|sub|token|link|api)[^\s]*', all_text)
        print(f"   文本中的URL: {subs}", flush=True)
        
        # HTML搜
        html = page.evaluate("() => document.documentElement.outerHTML")
        subs2 = re.findall(r'https?://[^\s"\'<>]+/api/v1/client/subscribe\?token=[^\s"\'<>]+', html)
        subs3 = re.findall(r'https?://[^\s"\'<>]+/sub/[^\s"\'<>]+', html)
        print(f"   API订阅: {subs2}", flush=True)
        print(f"   /sub/: {subs3}", flush=True)
        
        # 劫持剪贴板
        page.evaluate("""() => {
            window.__sslar_sub = '';
            navigator.clipboard.writeText = function(t) {
                window.__sslar_sub = t;
                return Promise.resolve();
            };
        }""")
        
        # 点击订阅相关按钮
        btns = page.evaluate("""() => {
            return Array.from(document.querySelectorAll('button, a')).filter(e => {
                let t = (e.textContent||'').trim();
                return /订阅|Clash|clash|复制|一键|生成|Subscribe/i.test(t);
            }).map(e => ({
                tag: e.tagName, text: (e.textContent||'').trim().substring(0,30),
                href: (e.href||'').substring(0,120)
            }));
        }""")
        print(f"   订阅按钮: {btns}", flush=True)
        
        for b in btns:
            try:
                el = page.locator(f'{b["tag"]}:has-text("{b["text"][:15]}")').first
                if el.is_visible():
                    el.click(force=True, timeout=3000)
                    time.sleep(1.5)
            except: pass
        
        sub = page.evaluate("() => window.__sslar_sub")
        print(f"   剪贴板: {sub}", flush=True)
        
        page.screenshot(path=os.path.join(os.path.dirname(__file__), "sslar_v1_final.png"), full_page=True)
        
    else:
        # 登录失败分析
        print(f"\n   ❌ 登录未跳转到/user!", flush=True)
        errors = page.evaluate("""() => {
            let errs = document.querySelectorAll('[class*=error], [class*=alert], .invalid-feedback');
            return Array.from(errs).map(e => e.textContent?.trim()).join('|');
        }""")
        print(f"   错误信息: {errors}", flush=True)

    print(f"\n✅ 完成!", flush=True)
    time.sleep(10)
    browser.close()
