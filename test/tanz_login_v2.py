#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TANZCLOUD — 尝试两套密码登录+注册"""
import sys, os, time, io, re, random
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from playwright.sync_api import sync_playwright

EMAIL = "hendricktamm95v80awzaxli@outlook.com"
PASSWORDS = ["VpnTest2026!", "@^NdxP5KN#s9G2Hqu0!", "VpnTest2026"]
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
    page.set_default_timeout(15000)

    logged_in = False
    correct_pwd = None

    for pwd in PASSWORDS:
        print(f"\n尝试密码: {pwd}", flush=True)
        page.goto(f"{BASE}/auth/login", wait_until="domcontentloaded", timeout=20000)
        time.sleep(2)
        
        page.locator('input[name="email"]').first.fill(EMAIL)
        page.locator('input[name="passwd"]').first.fill(pwd)
        page.locator('button:has-text("登录")').first.click()
        
        time.sleep(5)
        page.wait_for_load_state("networkidle", timeout=15000)
        print(f"  URL: {page.url}", flush=True)
        
        if "/user" in page.url:
            logged_in = True
            correct_pwd = pwd
            print(f"  ✅ 登录成功! 密码: {pwd}", flush=True)
            break
        else:
            body = page.evaluate("() => document.body.innerText.substring(0, 200)")
            if "密码或邮箱不正确" in body or "出错了" in body:
                print(f"  ❌ 密码错误", flush=True)
            else:
                print(f"  状态: {body[:100]}", flush=True)

    if not logged_in:
        print("\n" + "="*60)
        print("  所有密码都失败! 尝试重新注册...")
        print("="*60)
        
        new_email = f"tanz{random.randint(1000,9999)}vpn@outlook.com"
        print(f"  新邮箱: {new_email}", flush=True)
        
        page.goto(f"{BASE}/auth/register?code=ssfJ", wait_until="domcontentloaded", timeout=20000)
        time.sleep(3)
        print(f"  注册页URL: {page.url}", flush=True)
        print(f"  标题: {page.title()}", flush=True)
        
        body = page.evaluate("() => document.body.innerText.substring(0, 600)")
        print(f"  页面: {body[:400]}", flush=True)
        
        # 检查是否有注册表单
        inputs = page.evaluate("""() => {
            return Array.from(document.querySelectorAll('input')).map(e => ({
                name: e.name, id: e.id, type: e.type, placeholder: e.placeholder
            }));
        }""")
        print(f"  Inputs: {inputs}", flush=True)
        
        # 检查是否有验证码
        has_captcha = page.evaluate("""() => {
            return {
                geetest: !!document.querySelector('[class*="geetest"]'),
                turnstile: !!document.querySelector('[class*="turnstile"]'),
                recaptcha: !!document.querySelector('[class*="g-recaptcha"]'),
                has_iframe: document.querySelectorAll('iframe').length
            };
        }""")
        print(f"  验证码: {has_captcha}", flush=True)
        
        page.screenshot(path=os.path.join(os.path.dirname(__file__), "tanz_register_page.png"))
        
    else:
        # 进入user页提取订阅
        print("\n[提取订阅]", flush=True)
        page.goto(f"{BASE}/user", wait_until="domcontentloaded", timeout=20000)
        time.sleep(3)
        page.screenshot(path=os.path.join(os.path.dirname(__file__), "tanz_dashboard_now.png"))
        
        body = page.evaluate("() => document.body.innerText")
        print(f"  Dashboard文本: {body[:800]}", flush=True)
        
        # 找订阅
        print("\n  扫描订阅链接...", flush=True)
        
        # 找按钮
        buttons = page.evaluate("""() => {
            return Array.from(document.querySelectorAll('button')).map(b => ({
                text: (b.textContent || '').substring(0, 60),
                class: b.className?.substring(0, 40),
                visible: b.offsetParent !== null
            }));
        }""")
        print(f"  按钮: {buttons[:20]}", flush=True)
        
        # 劫持剪贴板点击订阅按钮
        sub = page.evaluate("""async () => {
            let old = navigator.clipboard.writeText;
            window.__sub = '';
            navigator.clipboard.writeText = function(t) {
                window.__sub = t;
                return Promise.resolve();
            };
            
            // 点击订阅按钮
            let btns = document.querySelectorAll('button');
            for (let b of btns) {
                let t = b.textContent || '';
                if (t.includes('Clash') || t.includes('复制') || t.includes('一键') || t.includes('订阅')) {
                    b.click();
                    await new Promise(r => setTimeout(r, 500));
                    break;
                }
            }
            await new Promise(r => setTimeout(r, 1000));
            return window.__sub || '';
        }""")
        print(f"  剪贴板订阅: {sub}", flush=True)
        
        # 备用：找链接
        links = page.evaluate("""() => {
            return Array.from(document.querySelectorAll('a')).filter(a => 
                a.href && (a.href.includes('/sub/') || a.href.includes('/link/') || a.href.includes('subscribe') || a.href.includes('token'))
            ).map(a => ({text: a.textContent?.substring(0,30), href: a.href.substring(0,120)}));
        }""")
        print(f"  订阅链接: {links}", flush=True)
        
        # 找文本中的URL
        urls = re.findall(r'https?://[^\s]+(?:subscribe|sub|token|link)[^\s]*', body)
        print(f"  文本URL: {urls}", flush=True)

    print("\n✅ 完成! 浏览器保持打开30秒", flush=True)
    time.sleep(30)
    browser.close()
