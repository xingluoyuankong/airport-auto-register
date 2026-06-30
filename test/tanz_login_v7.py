#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TANZCLOUD 登录+提取 V7 — 用V24正确凭据"""
import sys, os, time, io, re, json, random
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from playwright.sync_api import sync_playwright

# V24实际注册的账号（来自v24_subscriptions.txt）
EMAIL = "freetest2026_mqxx0w6g@outlook.com"
PASSWORD = "VpnTest2026!"
BASE = "https://www.tanz.website"

def extract_sub(page):
    """把剪贴板劫持+页面搜 combo"""
    sub = page.evaluate("""async () => {
        let old = navigator.clipboard.writeText;
        window.__tanz_sub = '';
        navigator.clipboard.writeText = function(t) {
            window.__tanz_sub = t;
            return old ? old.call(navigator.clipboard, t) : Promise.resolve();
        };
        let btns = document.querySelectorAll('button');
        for (let b of btns) {
            let t = b.textContent || '';
            if (t.includes('Clash') || t.includes('订阅链接') || t.includes('复制订阅') || t.includes('一键订阅')) {
                b.click();
                break;
            }
        }
        await new Promise(r => setTimeout(r, 1000));
        return window.__tanz_sub || '';
    }""")
    if sub: return sub
    sub = page.evaluate("""() => {
        let html = document.documentElement.outerHTML;
        let m = html.match(/https?:\\/\\/[^\\s"']+token=[^\\s"']+/i);
        if (m) return m[0];
        let links = document.querySelectorAll('a');
        for (let a of links) {
            if (a.href && (a.href.includes('subscribe') || a.href.includes('/sub/') || a.href.includes('/link/')))
                return a.href;
        }
        return '';
    }""")
    return sub

print("="*60)
print("  TANZCLOUD 登录+提取 V7")
print(f"  邮箱: {EMAIL}")
print("="*60)

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=False,
        args=["--ignore-certificate-errors", "--no-sandbox",
              "--proxy-server=http://127.0.0.1:7897"])
    ctx = browser.new_context(viewport={"width": 1280, "height": 900},
        ignore_https_errors=True, locale="zh-CN")
    page = ctx.new_page()
    page.set_default_timeout(10000)
    
    page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {get: () => false});
        Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
    """)
    
    try:
        print("\n[1] 登录...", flush=True)
        page.goto(f"{BASE}/auth/login", wait_until="networkidle", timeout=25000)
        time.sleep(2)
        
        page.locator('input[name="email"]').first.fill(EMAIL)
        time.sleep(0.2)
        page.locator('input[name="password"]').first.fill(PASSWORD)
        time.sleep(0.5)
        
        page.screenshot(path=os.path.join(os.path.dirname(__file__), "tanz_v7_filled.png"))
        
        page.locator('button[type="submit"]').first.click()
        time.sleep(5)
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except:
            pass
        
        body = page.evaluate("() => document.body.innerText")
        print(f"   URL: {page.url}", flush=True)
        print(f"   页面(300): {body[:300]}", flush=True)
        page.screenshot(path=os.path.join(os.path.dirname(__file__), "tanz_v7_after_login.png"))
        
        if "/user" not in page.url and "/dashboard" not in page.url:
            if "密码或邮箱不正确" in body:
                print("   ❌ 密码错误 — 账号可能已被清理", flush=True)
            elif "验证" in body or "geetest" in body.lower():
                print("   ⚠️ 需要验证,尝试手动拖滑块", flush=True)
                # 简化滑块绕过
                slider = page.query_selector('.geetest_slider_button')
                if slider:
                    box = slider.bounding_box()
                    if box:
                        sx, sy = box['x']+box['width']/2, box['y']+box['height']/2
                        page.mouse.move(sx, sy); page.mouse.down()
                        for i in range(30):
                            page.mouse.move(sx+8*(i+1), sy+random.uniform(-3,3))
                            time.sleep(0.01)
                        page.mouse.up()
                        time.sleep(2)
                        page.locator('button[type="submit"]').first.click()
                        time.sleep(5)
                        page.screenshot(path=os.path.join(os.path.dirname(__file__), "tanz_v7_after_slider.png"))
            else:
                print(f"   ❌ 登录后URL异常: {page.url}", flush=True)
            if "/user" not in page.url:
                print("   登录失败", flush=True)
                time.sleep(30)
                browser.close()
                exit(1)
        
        print("   ✅ 登录成功!", flush=True)
        
        # 提取订阅
        print("\n[2] 提取订阅...", flush=True)
        page.goto(f"{BASE}/user", wait_until="networkidle", timeout=20000)
        time.sleep(4)
        
        full = page.evaluate("() => document.body.innerText")
        print(f"   User页(600): {full[:600]}", flush=True)
        page.screenshot(path=os.path.join(os.path.dirname(__file__), "tanz_v7_user.png"))
        
        sub = extract_sub(page)
        print(f"   剪贴板劫持: {sub}", flush=True)
        
        if not sub:
            # 去订阅页
            page.goto(f"{BASE}/user/subscribe", wait_until="networkidle", timeout=20000)
            time.sleep(4)
            sub_text = page.evaluate("() => document.body.innerText")
            print(f"   订阅页(800): {sub_text[:800]}", flush=True)
            page.screenshot(path=os.path.join(os.path.dirname(__file__), "tanz_v7_subpage.png"))
            
            urls = re.findall(r'https?://[^\s]+token=[^\s]+', sub_text)
            if urls:
                sub = urls[0]
            else:
                html = page.evaluate("() => document.documentElement.outerHTML")
                urls = re.findall(r'https?://[^\s"\'<>]+token=[^\s"\'<>]+', html)
                if urls:
                    sub = urls[0]
            
            if not sub:
                all_links = page.evaluate("""() => Array.from(document.querySelectorAll('a[href]'))
                    .map(a => ({t:(a.textContent||'').slice(0,30), h:a.href.slice(0,200)}))
                    .filter(x => x.h.includes('http'))""")
                print(f"   链接: {all_links}", flush=True)
        
        if sub:
            result = {"airport":"TANZCLOUD","panel":"tanz.website","email":EMAIL,"password":PASSWORD,"subscribe_url":sub}
            out = os.path.join(os.path.dirname(__file__), "../register_results/tanzcloud_sub.json")
            os.makedirs(os.path.dirname(out), exist_ok=True)
            with open(out, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"\n{'='*60}")
            print(f"  🎉 订阅链接: {sub}")
            print(f"  保存到: register_results/tanzcloud_sub.json")
            print(f"{'='*60}")
        else:
            print("\n⚠️ 登录成功但没提取到订阅链接，请手动查看浏览器")
        
        time.sleep(30)
        
    except Exception as e:
        print(f"\n异常: {e}", flush=True)
        import traceback; traceback.print_exc()
        page.screenshot(path=os.path.join(os.path.dirname(__file__), "tanz_v7_crash.png"))
    finally:
        browser.close()
