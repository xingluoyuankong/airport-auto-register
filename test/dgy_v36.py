#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""大哥云 v3 — 深度分析+API直接获取订阅"""
import sys, os, time, io, re, base64, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import requests
from playwright.sync_api import sync_playwright
import xml.etree.ElementTree as ET

EMAIL = "dageyun_test_2026@outlook.com"
PASSWORD = "VpnTest2026"
URL = "https://a03.dgy02.com"

def solve_svg(svg_b64):
    raw = base64.b64decode(svg_b64.split(',')[1] if ',' in svg_b64 else svg_b64)
    tree = ET.fromstring(raw)
    return ''.join(t.text or '' for t in tree.findall('.//{http://www.w3.org/2000/svg}text'))

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=False,
        args=["--ignore-certificate-errors", "--no-sandbox",
              "--proxy-server=http://127.0.0.1:7897"])
    ctx = browser.new_context(viewport={"width": 1280, "height": 900},
        ignore_https_errors=True)
    page = ctx.new_page()
    page.set_default_timeout(10000)

    print("[1] 登录...", flush=True)
    page.goto(f"{URL}/#/login", wait_until="networkidle", timeout=30000)
    time.sleep(5)
    
    # 深度分析登录页
    html = page.evaluate("() => document.documentElement.outerHTML.substring(0, 3000)")
    print(f"   HTML开头: {html[:500]}", flush=True)
    
    captcha_img = page.locator('img[alt="点击刷新"]').first
    code = ""
    if captcha_img.is_visible():
        src = captcha_img.get_attribute('src')
        if src and 'base64' in src:
            code = solve_svg(src)
            print(f"   验证码: {code}", flush=True)
    
    page.locator('[placeholder="邮箱"]').first.fill(EMAIL)
    page.locator('[placeholder="密码"]').first.fill(PASSWORD)
    if captcha_img.is_visible() and code:
        page.locator('[placeholder="验证码"]').first.fill(code)
    page.locator('button:has-text("登入")').first.click()
    
    time.sleep(6)
    page.wait_for_load_state("networkidle", timeout=15000)
    print(f"   URL: {page.url}", flush=True)
    
    # 获取完整的DOM
    full_html = page.evaluate("() => document.documentElement.outerHTML.substring(0, 8000)")
    
    # 提取localStorage
    ls = page.evaluate("""() => {
        let items = {};
        for (let i = 0; i < localStorage.length; i++) {
            let k = localStorage.key(i);
            items[k] = (localStorage.getItem(k) || '').substring(0, 100);
        }
        return items;
    }""")
    print(f"   localStorage keys: {list(ls.keys())}", flush=True)
    
    # 提取cookies
    cookies = ctx.cookies()
    print(f"   Cookies: {[(c['name'], c['value'][:20]) for c in cookies]}", flush=True)
    
    # 找API endpoints
    api_calls = page.evaluate("""() => {
        let scripts = Array.from(document.querySelectorAll('script[src]'));
        return scripts.map(s => s.src).filter(s => s.length > 0).slice(0, 20);
    }""")
    
    # 搜页面中的所有完整URL
    all_urls = page.evaluate("""() => {
        let html = document.documentElement.outerHTML;
        let result = [];
        let m = html.match(/https?:[^"'<>\\s]+/gi);
        if (m) {
            result = m.filter(u => /subscribe|sub|token|node|api|clash|v2ray/i.test(u)).slice(0, 20);
        }
        return result;
    }""")
    print(f"   HTML中的URL: {all_urls}", flush=True)
    
    # 重点：抓取网络请求中的API
    print(f"\n[2] 监听网络请求...", flush=True)
    
    # 先清除所有弹窗
    page.evaluate("""() => {
        document.querySelectorAll('.ant-modal').forEach(m => m.remove());
        document.querySelectorAll('.ant-modal-mask').forEach(m => m.remove());
        document.querySelectorAll('[role="dialog"]').forEach(m => m.remove());
    }""")
    time.sleep(1)
    
    # 导航到订阅管理页
    for target in ["/user/subscribe", "/user/sub", "/user#subscribe", "/#/subscribe", "/#/user/subscribe", "/#/subscribe"]:
        print(f"\n   尝试: {URL}{target}", flush=True)
        page.goto(f"{URL}{target}", wait_until="networkidle", timeout=15000)
        time.sleep(3)
        
        body = page.evaluate("() => document.body.innerText")
        subs = re.findall(r'https?://[^\s]+(?:subscribe|sub|token|link)[^\s]*', body)
        if subs:
            print(f"   ✅ 找到: {subs}", flush=True)
            break
        
        # 也搜HTML
        html2 = page.evaluate("() => document.documentElement.outerHTML")
        subs2 = re.findall(r'https?://[^\s"\'<>]+token=[^\s"\'<>]+', html2)
        if subs2:
            print(f"   ✅ HTML找到: {subs2}", flush=True)
            break
        
        print(f"   页面: {body[:200]}", flush=True)
    
    # 最后手段：等页面加载完，逐个点击导航栏
    print(f"\n[3] 点导航...", flush=True)
    page.goto(f"{URL}/#/", wait_until="networkidle", timeout=15000)
    time.sleep(5)
    
    # 拦截剪贴板
    page.evaluate("""() => {
        window.__dgy_sub = '';
        let oldWrite = navigator.clipboard.writeText;
        navigator.clipboard.writeText = function(t) {
            window.__dgy_sub = t;
            console.log('SUB:', t);
            return Promise.resolve();
        };
    }""")
    
    # 点击"订阅"导航项
    nav_items = page.evaluate("""() => {
        let items = Array.from(document.querySelectorAll('a, li, div, span, button')).filter(e => {
            let t = (e.textContent||'').trim();
            return ['订阅', '一键订阅', 'subscribe', '我的订阅'].includes(t);
        }).slice(0,5).map(e => ({
            tag: e.tagName, text: (e.textContent||'').trim().substring(0,30),
            className: e.className?.substring(0,40),
            onclick: (e.onclick?.toString()||'').substring(0,80)
        }));
        return items;
    }""")
    print(f"   导航项: {nav_items}", flush=True)
    
    for item in nav_items:
        try:
            sel = f'{item["tag"]}:has-text("{item["text"]}")'
            el = page.locator(sel).first
            if el.is_visible():
                el.click(force=True, timeout=3000)
                time.sleep(2)
        except:
            pass
    
    # 等一会后检查剪贴板
    for i in range(10):
        time.sleep(1)
        sub = page.evaluate("() => window.__dgy_sub")
        if sub:
            print(f"   ✅ 剪贴板: {sub}", flush=True)
            break
        if i == 9:
            print(f"   ❌ 超时未获取到订阅", flush=True)
    
    # 最终全页截图
    page.screenshot(path=os.path.join(os.path.dirname(__file__), f"dgy_v36_final.png"), full_page=True)
    
    # 打印当前页面全部文本
    all_text = page.evaluate("() => document.body.innerText")
    print(f"\n   最大页面文本(2000字):\n{all_text[:2000]}", flush=True)
    
    print("\n✅ 完成!", flush=True)
    time.sleep(10)
    browser.close()
