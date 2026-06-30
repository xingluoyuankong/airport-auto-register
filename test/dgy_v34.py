#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""大哥云 登录+订阅提取 — 简化版"""
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
    ns = {'svg': 'http://www.w3.org/2000/svg'}
    return ''.join(t.text or '' for t in tree.findall('.//{http://www.w3.org/2000/svg}text'))

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=False,
        args=["--ignore-certificate-errors", "--no-sandbox",
              "--proxy-server=http://127.0.0.1:7897"])
    ctx = browser.new_context(viewport={"width": 1280, "height": 900},
        ignore_https_errors=True)
    page = ctx.new_page()
    page.set_default_timeout(15000)

    print("[1] 打开登录页...", flush=True)
    page.goto(f"{URL}/#/login", wait_until="networkidle", timeout=25000)
    time.sleep(4)
    print(f"   URL: {page.url}", flush=True)
    
    # 截图+分析
    page.screenshot(path=os.path.join(os.path.dirname(__file__), "dgy_v34_step1.png"))
    
    # 获取页面结构
    body = page.evaluate("() => document.body.innerText.substring(0, 600)")
    print(f"   文本: {body[:400]}", flush=True)
    
    # 获取所有input和button
    elements = page.evaluate("""() => {
        return {
            inputs: Array.from(document.querySelectorAll('input')).map(e => ({
                type: e.type, placeholder: e.placeholder, name: e.name, id: e.id,
                className: e.className?.substring(0,40)
            })),
            buttons: Array.from(document.querySelectorAll('button')).map(e => ({
                text: (e.textContent||'').substring(0,30), className: e.className?.substring(0,40)
            })),
            imgs: Array.from(document.querySelectorAll('img')).map(e => ({
                alt: e.alt, src: e.src?.substring(0,80), className: e.className?.substring(0,40)
            }))
        };
    }""")
    print(f"   Inputs: {elements['inputs']}", flush=True)
    print(f"   Buttons: {elements['buttons']}", flush=True)
    print(f"   Images: {elements['imgs']}", flush=True)
    
    # 尝试找验证码图片
    captcha_img = page.locator('img[alt="点击刷新"], img[alt*="验证码"], img[alt*="captcha"]').first
    if captcha_img.is_visible():
        src = captcha_img.get_attribute('src')
        print(f"\n[2] 验证码图片: {src[:100]}", flush=True)
        
        if src and 'base64' in src:
            code = solve_svg(src)
            print(f"   破解验证码: {code}", flush=True)
        else:
            print("   非base64格式!", flush=True)
            code = ""
    else:
        print(f"\n[2] 无验证码图片", flush=True)
        # 看看所有img
        all_imgs = page.evaluate("() => Array.from(document.querySelectorAll('img')).map(e => ({src: e.src.substring(0,100), alt: e.alt}))")
        print(f"   所有图片: {all_imgs}", flush=True)
        code = ""
    
    # 填表
    print(f"\n[3] 填表+登录...", flush=True)
    
    # 大哥云用placeholder定位
    email_input = page.locator('[placeholder="邮箱"]').first
    if email_input.is_visible():
        email_input.fill(EMAIL)
        print("   邮箱已填", flush=True)
    
    pwd_input = page.locator('[placeholder="密码"]').first
    if pwd_input.is_visible():
        pwd_input.fill(PASSWORD)
        print("   密码已填", flush=True)
    
    if captcha_img.is_visible() and code:
        captcha_input = page.locator('[placeholder="验证码"]').first
        if captcha_input.is_visible():
            captcha_input.fill(code)
            print(f"   验证码已填: {code}", flush=True)
    
    # 点击登录
    login_btn = page.locator('button:has-text("登入"), button:has-text("登录")').first
    if login_btn.is_visible():
        login_btn.click()
        print("   已点登录", flush=True)
    
    time.sleep(5)
    page.wait_for_load_state("networkidle", timeout=15000)
    print(f"   登录后URL: {page.url}", flush=True)
    page.screenshot(path=os.path.join(os.path.dirname(__file__), "dgy_v34_step2.png"))
    
    body2 = page.evaluate("() => document.body.innerText.substring(0, 500)")
    print(f"   结果: {body2[:400]}", flush=True)
    
    if "dashboard" in page.url.lower() or "一键订阅" in body2:
        print("\n✅ 登录成功!", flush=True)
        
        # 关弹窗
        try:
            time.sleep(2)
            close_btn = page.locator('button:has-text("Close"), button:has-text("关闭"), .modal-header button').first
            if close_btn.is_visible():
                close_btn.click()
                time.sleep(1)
        except:
            pass
        
        # 一键订阅
        print("\n[4] 点一键订阅...", flush=True)
        sub_btn = page.locator('text=一键订阅').first
        if sub_btn.is_visible():
            sub_btn.click()
            time.sleep(3)
            page.screenshot(path=os.path.join(os.path.dirname(__file__), "dgy_v34_step3_sub.png"))
        else:
            # 尝试直接到订阅页
            nav_items = page.evaluate("""() => {
                return Array.from(document.querySelectorAll('a, li, span, div')).filter(e => {
                    let t = (e.textContent||'').trim();
                    return t.includes('订阅') || t.includes('sub');
                }).slice(0,5).map(e => ({tag: e.tagName, text: e.textContent?.substring(0,30), href: e.href}));
            }""")
            print(f"   导航: {nav_items}", flush=True)
        
        # 深度扫描订阅URL
        print("\n[5] 扫描订阅链接...", flush=True)
        
        # 全部页面文本
        all_text = page.evaluate("() => document.body.innerText")
        subs_in_text = re.findall(r'https?://[^\s]+(?:subscribe|sub|token|link)[^\s]*', all_text)
        print(f"   文本中URL: {subs_in_text}", flush=True)
        
        # data-clipboard
        clips = page.evaluate("""() => {
            return Array.from(document.querySelectorAll('[data-clipboard-text]')).map(e => e.getAttribute('data-clipboard-text'));
        }""")
        print(f"   data-clipboard: {clips}", flush=True)
        
        # 所有带URL的链接
        all_links = page.evaluate("""() => {
            return Array.from(document.querySelectorAll('a[href]')).filter(a => {
                let h = a.href || '';
                return h.includes('sub') || h.includes('token') || h.includes('link') || h.includes('api/');
            }).map(a => a.href.substring(0, 150));
        }""")
        print(f"   订阅相关链接: {all_links}", flush=True)
        
        # 点击复制订阅地址
        copy_btn = page.locator('text=复制订阅地址').first
        if copy_btn.is_visible():
            copy_btn.click()
            time.sleep(2)
            
            # 读剪贴板
            copied = page.evaluate("() => navigator.clipboard.readText().catch(() => 'clipboard denied')")
            print(f"   剪贴板: {copied}", flush=True)
        
        # 截图保存
        page.screenshot(path=os.path.join(os.path.dirname(__file__), f"dgy_v34_final.png"))
    else:
        print(f"\n❌ 登录失败", flush=True)
    
    print("\n✅ 完成!", flush=True)
    time.sleep(15)
    browser.close()
