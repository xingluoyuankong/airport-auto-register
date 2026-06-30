#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TANZCLOUD — 先深度分析登录页，再登录"""
import sys, os, time, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from playwright.sync_api import sync_playwright

EMAIL = "hendricktamm95v80awzaxli@outlook.com"
BASE = "https://www.tanz.website"

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=False,
        args=["--ignore-certificate-errors", "--no-sandbox"])
    ctx = browser.new_context(
        viewport={"width": 1280, "height": 900},
        ignore_https_errors=True, locale="zh-CN",
        proxy={"server": "http://127.0.0.1:7897"}
    )
    page = ctx.new_page()
    page.set_default_timeout(8000)

    print("[1] 深度分析登录页HTML...", flush=True)
    page.goto(f"{BASE}/auth/login", wait_until="networkidle", timeout=25000)
    time.sleep(3)
    
    # 获取所有input详细信息
    inputs = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('input')).map(e => ({
            name: e.getAttribute('name'),
            id: e.id,
            type: e.type,
            placeholder: e.placeholder,
            className: e.className?.substring(0, 50),
            autocomplete: e.autocomplete,
            outerHTML: e.outerHTML.substring(0, 200)
        }));
    }""")
    print("  INPUTS:", flush=True)
    for i, inp in enumerate(inputs):
        print(f"    [{i}] name={inp['name']} id={inp['id']} type={inp['type']} placeholder={inp['placeholder']}", flush=True)
        print(f"        HTML: {inp['outerHTML']}", flush=True)
    
    # 获取所有button
    btns = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('button, input[type="submit"]')).map(e => ({
            text: (e.textContent || e.value || '').substring(0, 40),
            type: e.type,
            className: e.className?.substring(0, 50),
            outerHTML: e.outerHTML.substring(0, 200)
        }));
    }""")
    print("\n  BUTTONS:", flush=True)
    for i, b in enumerate(btns):
        print(f"    [{i}] {b['text']} type={b['type']} HTML:{b['outerHTML'][:120]}", flush=True)
    
    # 获取表单HTML
    form_html = page.evaluate("""() => {
        let f = document.querySelector('form');
        return f ? f.outerHTML.substring(0, 1500) : 'NO FORM';
    }""")
    print(f"\n  FORM HTML:\n{form_html}", flush=True)
    
    page.screenshot(path=os.path.join(os.path.dirname(__file__), "tanz_login_analysis.png"))
    
    # 现在用CSS selector登录
    print("\n[2] 用通用selector登录...", flush=True)
    
    # 先填email - 找type=email或第一个input
    email_input = page.locator('input[type="email"]').first
    if not email_input.is_visible():
        email_input = page.locator('input').first
    email_input.fill(EMAIL)
    print(f"  邮箱已填到: {email_input.evaluate('e => e.name || e.id || e.placeholder')}", flush=True)
    
    # 填密码 - 找type=password
    pwd_input = page.locator('input[type="password"]').first
    if not pwd_input.is_visible():
        pwd_input = page.locator('input').nth(1)
    pwd_input.fill("VpnTest2026!")
    print(f"  密码已填到: {pwd_input.evaluate('e => e.name || e.id || e.placeholder')}", flush=True)
    
    # 点击登录
    login_btn = page.locator('button[type="submit"], button:has-text("登录"), input[type="submit"]').first
    if not login_btn.is_visible():
        login_btn = page.locator('button').first
    login_btn.click()
    print("  已点登录", flush=True)
    
    time.sleep(5)
    page.wait_for_load_state("networkidle", timeout=15000)
    print(f"  登录后URL: {page.url}", flush=True)
    
    body = page.evaluate("() => document.body.innerText.substring(0, 500)")
    print(f"  页面: {body[:400]}", flush=True)
    page.screenshot(path=os.path.join(os.path.dirname(__file__), "tanz_login_result.png"))
    
    if "/user" in page.url:
        print("\n✅ 登录成功!", flush=True)
    else:
        print(f"\n❌ 未登录成功", flush=True)
    
    time.sleep(30)
    browser.close()
