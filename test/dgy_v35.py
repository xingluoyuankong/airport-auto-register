#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""大哥云 v2 — 关弹窗+获取订阅"""
import sys, os, time, io, re, base64
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
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
    page.set_default_timeout(8000)

    print("[1] 登录...", flush=True)
    page.goto(f"{URL}/#/login", wait_until="networkidle", timeout=25000)
    time.sleep(4)
    
    # SVG验证码
    captcha_img = page.locator('img[alt="点击刷新"]').first
    if captcha_img.is_visible():
        src = captcha_img.get_attribute('src')
        code = solve_svg(src) if src and 'base64' in src else ""
        print(f"   验证码: {code}", flush=True)
    else:
        code = ""
    
    page.locator('[placeholder="邮箱"]').first.fill(EMAIL)
    page.locator('[placeholder="密码"]').first.fill(PASSWORD)
    if captcha_img.is_visible() and code:
        page.locator('[placeholder="验证码"]').first.fill(code)
    page.locator('button:has-text("登入")').first.click()
    
    time.sleep(6)
    page.wait_for_load_state("networkidle", timeout=15000)
    print(f"   URL: {page.url}", flush=True)
    
    body = page.evaluate("() => document.body.innerText.substring(0, 400)")
    if "dashboard" not in page.url.lower():
        print(f"   页面: {body[:300]}", flush=True)
    
    print("\n[2] 关闭弹窗...", flush=True)
    
    # 找所有可见弹窗并关闭
    closed = page.evaluate("""() => {
        let modals = document.querySelectorAll('.ant-modal-wrap, .ant-modal-mask, .modal, .dialog');
        let count = 0;
        modals.forEach(m => {
            // 点关闭按钮
            let close = m.querySelector('.ant-modal-close, .ant-modal-close-x, .modal-close, button[aria-label="Close"], button[aria-label="close"]');
            if (close) { close.click(); count++; }
        });
        // 如果没找到关闭按钮,点击遮罩
        if (count === 0) {
            document.querySelectorAll('.ant-modal-mask').forEach(m => m.click());
        }
        return count;
    }""")
    print(f"   关闭弹窗: {closed}个", flush=True)
    time.sleep(1)
    
    # 备用: 按ESC
    page.keyboard.press("Escape")
    time.sleep(1)
    
    page.screenshot(path=os.path.join(os.path.dirname(__file__), "dgy_v35_step1.png"))
    
    print("\n[3] 提取订阅链接...", flush=True)
    
    # 先点"订阅"导航
    sub_nav = page.locator('a:has-text("订阅"), span:has-text("订阅"), div:has-text("订阅")').first
    if sub_nav.is_visible():
        try:
            sub_nav.click(force=True, timeout=5000)
            time.sleep(2)
            print("   点击了订阅导航", flush=True)
        except:
            pass
    
    page.wait_for_load_state("networkidle", timeout=10000)
    page.screenshot(path=os.path.join(os.path.dirname(__file__), "dgy_v35_step2_subpage.png"))
    
    # 页面文本搜URL
    all_text = page.evaluate("() => document.body.innerText")
    subs = re.findall(r'https?://[^\s]+(?:subscribe|sub|token|link)[^\s]*', all_text)
    print(f"   文本URL: {subs}", flush=True)
    
    # 找所有带链接的a标签
    all_links = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('a[href]')).map(a => ({
            text: (a.textContent||'').substring(0,30),
            href: a.href?.substring(0,200)
        })).filter(x => x.href && x.href.length > 20);
    }""")
    print(f"   页面链接({len(all_links)}个):", flush=True)
    for l in all_links:
        print(f"      {l['text'][:20]:20s} {l['href']}", flush=True)
    
    # 点"复制订阅"按钮
    copy_btns = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('button, a, span')).filter(e => {
            let t = (e.textContent||'').trim();
            return t.includes('复制') || t.includes('Clash') || t.includes('clash') || t.includes('订阅地址') || t.includes('一键');
        }).slice(0,5).map(e => ({tag: e.tagName, text: t=e.textContent?.substring(0,30), class: e.className?.substring(0,30)}));
    }""")
    print(f"   订阅按钮: {copy_btns}", flush=True)
    
    # 拦截剪贴板
    page.evaluate("""() => {
        window.__sub = '';
        let old = navigator.clipboard.writeText;
        navigator.clipboard.writeText = function(t) {
            window.__sub = t;
            return Promise.resolve();
        };
    }""")
    
    # 点击所有可能的复制/订阅按钮
    for btn_info in copy_btns:
        tag = btn_info['tag'].lower()
        if tag == 'button':
            sel = f'button:has-text("{btn_info["text"][:10]}")'
        elif tag == 'a':
            sel = f'a:has-text("{btn_info["text"][:10]}")'
        else:
            sel = f'span:has-text("{btn_info["text"][:10]}")'
        
        try:
            el = page.locator(sel).first
            if el.is_visible():
                el.click(force=True, timeout=3000)
                time.sleep(1)
        except:
            pass
    
    time.sleep(1)
    copied = page.evaluate("() => window.__sub")
    print(f"   剪贴板拦截: {copied}", flush=True)
    
    # 如果没拿到，看data-clipboard
    clip_data = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('[data-clipboard-text]')).map(e => e.getAttribute('data-clipboard-text'));
    }""")
    print(f"   data-clipboard: {clip_data}", flush=True)
    
    # V2Board标准订阅URL模式
    api_urls = page.evaluate("""() => {
        let text = document.body.innerText;
        let matches = [];
        let re = /https?:\\/\\/\\S+\\/api\\/v1\\/client\\/subscribe\\?token=\\S+/g;
        let m;
        while (m = re.exec(text)) {
            matches.push(m[0]);
            if (re.lastIndex === m.index) re.lastIndex++;
        }
        return matches;
    }""")
    print(f"   API订阅URL: {api_urls}", flush=True)
    
    # 最终保存截图
    page.screenshot(path=os.path.join(os.path.dirname(__file__), "dgy_v35_final.png"), full_page=True)
    
    print("\n✅ 完成!", flush=True)
    time.sleep(10)
    browser.close()
