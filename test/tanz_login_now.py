#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TANZCLOUD 登录+订阅提取 — 即跑版"""
import sys, os, time, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from playwright.sync_api import sync_playwright

EMAIL = "hendricktamm95v80awzaxli@outlook.com"
PASSWORD = "VpnTest2026!"
BASE = "https://www.tanz.website"

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=False,
        args=["--ignore-certificate-errors", "--no-sandbox"])
    ctx = browser.new_context(
        viewport={"width": 1280, "height": 900},
        ignore_https_errors=True,
        locale="zh-CN",
        proxy={"server": "http://127.0.0.1:7897"}
    )
    page = ctx.new_page()
    page.set_default_timeout(15000)

    try:
        print("[1] 打开登录页...", flush=True)
        page.goto(f"{BASE}/auth/login", wait_until="domcontentloaded", timeout=25000)
        time.sleep(3)
        print(f"    URL: {page.url}", flush=True)
        print(f"    标题: {page.title()}", flush=True)
        page.screenshot(path=os.path.join(os.path.dirname(__file__), "tanz_login_page.png"))
        
        # 检查页面是否有登录表单
        body = page.evaluate("() => document.body.innerText.substring(0, 500)")
        print(f"    页面文本: {body[:300]}", flush=True)
        
        has_form = page.evaluate("""() => {
            let inputs = document.querySelectorAll('input');
            return inputs.length;
        }""")
        print(f"    input数量: {has_form}", flush=True)
        
        print("\n[2] 填写邮箱...", flush=True)
        email_input = page.locator('input[name="email"], input#email, input[type="email"], input[placeholder*="邮箱"], input[placeholder*="email"]').first
        if email_input.is_visible():
            email_input.fill(EMAIL)
            print("    邮箱已填", flush=True)
        else:
            print("    没找到邮箱输入框!", flush=True)
            # 列出所有input
            types = page.evaluate("""() => {
                return Array.from(document.querySelectorAll('input')).map(e => ({
                    name: e.name, id: e.id, type: e.type, placeholder: e.placeholder
                }));
            }""")
            print(f"    所有input: {types}", flush=True)
        
        print("\n[3] 填写密码...", flush=True)
        pwd_input = page.locator('input[name="passwd"], input#passwd, input[type="password"]').first
        if pwd_input.is_visible():
            pwd_input.fill(PASSWORD)
            print("    密码已填", flush=True)
        
        print("\n[4] 点击登录...", flush=True)
        login_btn = page.locator('button:has-text("登录"), button:has-text("登入"), button[type="submit"], input[type="submit"]').first
        if login_btn.is_visible():
            login_btn.click()
            print("    已点击登录", flush=True)
        
        time.sleep(5)
        page.wait_for_load_state("networkidle", timeout=20000)
        print(f"    登录后URL: {page.url}", flush=True)
        page.screenshot(path=os.path.join(os.path.dirname(__file__), "tanz_after_login.png"))
        
        if "/user" in page.url or "user" in page.url:
            print("\n[5] ✅ 已登录到用户面板!", flush=True)
        else:
            print(f"\n    ⚠️ 未跳转到用户面板, 检查页面...", flush=True)
            body2 = page.evaluate("() => document.body.innerText.substring(0, 500)")
            print(f"    页面: {body2[:400]}", flush=True)
        
        # 尝试提取订阅
        print("\n[6] 提取订阅链接...", flush=True)
        
        # 方法1: 打开user页面
        page.goto(f"{BASE}/user", wait_until="domcontentloaded", timeout=20000)
        time.sleep(3)
        print(f"    user页URL: {page.url}", flush=True)
        page.screenshot(path=os.path.join(os.path.dirname(__file__), "tanz_user_page.png"))
        
        # 扫描页面
        page_text = page.evaluate("() => document.body.innerText")
        print(f"    user页文本(前500): {page_text[:500]}", flush=True)
        
        # 找订阅链接
        subs = page.evaluate("""() => {
            let results = [];
            // 找所有包含subscribe/sub的a标签
            document.querySelectorAll('a').forEach(a => {
                let href = a.href || '';
                if (href.includes('subscribe') || href.includes('/sub/') || href.includes('/link/')) {
                    results.push({type: 'link', url: href, text: a.textContent?.substring(0, 30)});
                }
            });
            // 找按钮
            document.querySelectorAll('button').forEach(b => {
                let t = (b.textContent || '').substring(0, 50);
                if (t.includes('订阅') || t.includes('Clash') || t.includes('一键')) {
                    results.push({type: 'btn', text: t});
                }
            });
            // 找文本中的订阅URL
            let text = document.body.innerText;
            let matches = text.match(/https?:\\/\\/[^\\s]+(?:subscribe|sub|token)[^\\s]+/gi);
            if (matches) matches.forEach(m => results.push({type: 'text_url', url: m}));
            return results;
        }""")
        print(f"    找到订阅相关: {subs}", flush=True)
        
        print("\n[7] ✅ 完成! 浏览器保持打开以便手动查看", flush=True)
        
    except Exception as e:
        print(f"  ❌ 异常: {e}", flush=True)
        import traceback
        traceback.print_exc()
        try:
            page.screenshot(path=os.path.join(os.path.dirname(__file__), "tanz_error.png"))
        except:
            pass
    
    # 保持打开
    print("\n浏览器保持打开60秒...", flush=True)
    time.sleep(60)
    browser.close()
