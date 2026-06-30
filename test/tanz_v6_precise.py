#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TANZCLOUD 精确登录+订阅提取 — HTML字段名是password不是passwd"""
import sys, os, time, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from playwright.sync_api import sync_playwright

EMAIL = "hendricktamm95v80awzaxli@outlook.com"
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

    print("[1] 打开登录页", flush=True)
    page.goto(f"{BASE}/auth/login", wait_until="networkidle", timeout=25000)
    time.sleep(3)

    # 深层分析HTML
    email_html = page.evaluate("""() => document.querySelector('input[name="email"]')?.outerHTML || 'NOT FOUND'""")
    pwd_html = page.evaluate("""() => document.querySelector('input[name="password"]')?.outerHTML || 'NOT FOUND'""")
    print(f"   email字段: {email_html}", flush=True)
    print(f"   password字段: {pwd_html}", flush=True)

    # 关键：用click+type代替fill，触发完整JS事件
    print(f"\n[2] 输入邮箱 (type方式)", flush=True)
    email_el = page.locator('input[name="email"]').first
    email_el.click()
    time.sleep(0.3)
    email_el.fill("")  # 清空
    time.sleep(0.2)
    email_el.type(EMAIL, delay=80)  # 逐字符输入
    print(f"   邮箱值={email_el.input_value()}", flush=True)

    print(f"\n[3] 输入密码 (type方式)", flush=True)
    pwd_el = page.locator('input[name="password"]').first
    pwd_el.click()
    time.sleep(0.3)
    pwd_el.fill("")
    time.sleep(0.2)
    pwd_el.type(PASSWORD, delay=80)
    print(f"   密码已输入", flush=True)

    page.screenshot(path=os.path.join(os.path.dirname(__file__), "tanz_v6_filled.png"))

    print(f"\n[4] 点击登录", flush=True)
    login_btn = page.locator('button[type="submit"]').first
    login_btn.click()
    print(f"   已点击", flush=True)

    # 等响应
    time.sleep(5)
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except:
        pass

    print(f"   URL: {page.url}", flush=True)
    page.screenshot(path=os.path.join(os.path.dirname(__file__), "tanz_v6_after_click.png"))
    
    body = page.evaluate("() => document.body.innerText.substring(0, 500)")
    print(f"   页面内容: {body[:400]}", flush=True)

    if "/user" in page.url:
        print(f"\n   ✅✅✅ 登录成功!!!", flush=True)
    elif "密码或邮箱不正确" in body or "出错了" in body:
        print(f"\n   ❌ 密码错误! 试试备用密码", flush=True)
        # 刷新重试备用密码
        page.goto(f"{BASE}/auth/login", wait_until="networkidle", timeout=15000)
        time.sleep(2)
        page.locator('input[name="email"]').first.type(EMAIL, delay=50)
        page.locator('input[name="password"]').first.type("@^NdxP5KN#s9G2Hqu0!", delay=50)
        page.locator('button[type="submit"]').first.click()
        time.sleep(5)
        page.wait_for_load_state("networkidle", timeout=10000)
        print(f"   备用密码后URL: {page.url}", flush=True)
        body2 = page.evaluate("() => document.body.innerText.substring(0, 300)")
        print(f"   备用密码结果: {body2[:200]}", flush=True)
    else:
        print(f"   未知状态，URL={page.url}", flush=True)

    if "/user" in page.url:
        # ====== 提取订阅 ======
        print(f"\n[5] 提取订阅链接...", flush=True)
        page.goto(f"{BASE}/user", wait_until="networkidle", timeout=15000)
        time.sleep(3)
        page.screenshot(path=os.path.join(os.path.dirname(__file__), "tanz_v6_dashboard.png"))
        
        user_text = page.evaluate("() => document.body.innerText")
        print(f"   Dashboard文本(800): {user_text[:800]}", flush=True)
        
        # 找所有a标签+按钮
        all_elems = page.evaluate("""() => {
            let as = Array.from(document.querySelectorAll('a[href]')).filter(a => {
                let h = a.href || '';
                return h.length > 30;
            }).slice(0,30).map(a => ({tag:'a', text:(a.textContent||'').trim().substring(0,30), href:a.href.substring(0,150)}));
            let bs = Array.from(document.querySelectorAll('button')).slice(0,10).map(b => ({tag:'button', text:(b.textContent||'').trim().substring(0,30)}));
            return as.concat(bs);
        }""")
        print(f"   所有元素:", flush=True)
        for e in all_elems:
            print(f"      [{e['tag']}] {e['text'][:25]:25s} {e.get('href','')}", flush=True)
        
        # 去订阅页面
        print(f"\n   导航到订阅管理页...", flush=True)
        for sub_path in ["/user/subscribe", "/user#subscribe"]:
            try:
                page.goto(f"{BASE}{sub_path}", wait_until="networkidle", timeout=12000)
                time.sleep(3)
                sub_html = page.evaluate("() => document.documentElement.outerHTML")
                # 搜V2Board API订阅URL
                api_urls = re.findall(r'https?://\S+/api/v1/client/subscribe\?token=\S+', sub_html)
                if api_urls:
                    print(f"   ✅ API订阅URL: {api_urls}", flush=True)
                    break
                
                # 搜/sub/模式
                sub_urls = re.findall(r'https?://[^\s"\'<>]+/sub/[^\s"\'<>]+', sub_html)
                if sub_urls:
                    print(f"   ✅ 订阅URL: {sub_urls}", flush=True)
                    break
                    
                sub_text = page.evaluate("() => document.body.innerText")
                print(f"   {sub_path} 文本(300): {sub_text[:300]}", flush=True)
            except Exception as e:
                print(f"   {sub_path}: {e}", flush=True)
        
        # 截取剪贴板
        page.evaluate("""() => {
            window.__tanz_sub = '';
            navigator.clipboard.writeText = function(t) {
                window.__tanz_sub = t;
                return Promise.resolve();
            };
        }""")
        
        # 点击所有含"订阅"、"Clash"、"复制"的按钮
        btns = page.evaluate("""() => {
            let result = [];
            document.querySelectorAll('button, a').forEach(e => {
                let t = (e.textContent||'').trim();
                if (/订阅|Clash|clash|复制|一键|subscribe/i.test(t)) {
                    result.push({tag:e.tagName, text:t.substring(0,30)});
                }
            });
            return result;
        }""")
        print(f"   订阅相关按钮: {btns}", flush=True)
        
        for b in btns:
            try:
                sel = f'{b["tag"].lower()}:has-text("{b["text"][:15]}")'
                el = page.locator(sel).first
                if el.is_visible():
                    el.click(force=True, timeout=3000)
                    time.sleep(1)
            except:
                pass
        
        sub = page.evaluate("() => window.__tanz_sub")
        if sub:
            print(f"   ✅ 剪贴板订阅: {sub}", flush=True)
        
        # data-clipboard
        clips = page.evaluate("""() => Array.from(document.querySelectorAll('[data-clipboard-text]')).map(e => e.getAttribute('data-clipboard-text'))""")
        if clips:
            print(f"   ✅ data-clipboard: {clips}", flush=True)
        
        page.screenshot(path=os.path.join(os.path.dirname(__file__), "tanz_v6_final.png"), full_page=True)

    else:
        # 未登录成功，检查Geetest
        print(f"\n   检查Geetest验证...", flush=True)
        geetest = page.evaluate("""() => {
            let iframes = Array.from(document.querySelectorAll('iframe')).map(f => f.src?.substring(0,80));
            let captcha = !!document.querySelector('[class*="geetest"], [class*="captcha"], [class*="g-recaptcha"]');
            return {iframes, captcha};
        }""")
        print(f"   Geetest: {geetest}", flush=True)

    print(f"\n✅ 完成! 浏览器保持15秒", flush=True)
    time.sleep(15)
    browser.close()
