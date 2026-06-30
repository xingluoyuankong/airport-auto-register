#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FSCloud 登录+提取订阅 V2"""
import sys, os, time, io, re, json, random
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from playwright.sync_api import sync_playwright

EMAIL = "fscloud_test_2026@gmail.com"
PASSWORD = "Fscloud2026"
BASE = "https://web.fscloud.cc"

def extract_sub(page):
    sub = page.evaluate("""async () => {
        let old = navigator.clipboard.writeText;
        window.__sub = '';
        navigator.clipboard.writeText = function(t) { window.__sub = t; return old?old.call(navigator.clipboard,t):Promise.resolve(); };
        let btns = document.querySelectorAll('button, span, div[role="button"]');
        for (let b of btns) {
            let t = b.textContent || '';
            if (t.includes('复制订阅') || t.includes('一键订阅') || t.includes('Clash') || t.includes('Subscribe')) {
                b.click(); break;
            }
        }
        await new Promise(r=>setTimeout(r,800));
        return window.__sub || '';
    }""")
    if sub: return sub
    sub = page.evaluate("""() => {
        let html = document.documentElement.outerHTML;
        let m = html.match(/https?:\\/\\/[^\\s"']+token=[^\\s"']{10,}/i);
        if (m) return m[0];
        let m2 = html.match(/https?:\\/\\/[^\\s"']+subscribe[^\\s"']*/i);
        if (m2) return m2[0];
        return '';
    }""")
    return sub

print("="*60)
print("  FSCloud 登录+提取 V2")
print("="*60)

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=False,
        args=["--ignore-certificate-errors","--no-sandbox",
              "--proxy-server=http://127.0.0.1:7897"])
    ctx = browser.new_context(viewport={"width":1280,"height":900},
        ignore_https_errors=True, locale="zh-CN")
    page = ctx.new_page()
    page.set_default_timeout(10000)
    
    page.add_init_script("""
        Object.defineProperty(navigator,'webdriver',{get:()=>false});
        Object.defineProperty(navigator,'plugins',{get:()=>[1,2,3,4,5]});
    """)
    
    try:
        # 打开登录页
        print("\n[1] 登录页...", flush=True)
        page.goto(f"{BASE}/#/login", wait_until="networkidle", timeout=25000)
        time.sleep(3)
        
        # 找input
        inputs = page.evaluate("""() => Array.from(document.querySelectorAll('input'))
            .map(i => ({type:i.type, name:i.name, id:i.id, placeholder:i.placeholder}))""")
        print(f"   Inputs: {inputs}", flush=True)
        
        # 填表 - React SPA，用type定位
        email_inputs = page.locator('input[type="email"], input[name="email"], input[placeholder*="邮箱"]').first
        pw_inputs = page.locator('input[type="password"], input[name="password"], input[placeholder*="密码"]').first
        
        email_inputs.click()
        time.sleep(0.2)
        email_inputs.fill("")
        email_inputs.type(EMAIL, delay=random.randint(20, 60))
        time.sleep(0.3)
        
        pw_inputs.click()
        time.sleep(0.1)
        pw_inputs.type(PASSWORD, delay=random.randint(20, 60))
        time.sleep(0.5)
        
        page.screenshot(path=os.path.join(os.path.dirname(__file__), "fscloud_v2_filled.png"))
        
        # 点击登录
        login_btn = page.locator('button:has-text("登录")').first
        if login_btn.count() == 0:
            login_btn = page.locator('button[type="submit"]').first
        print(f"   点击登录...", flush=True)
        login_btn.click()
        
        time.sleep(5)
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except:
            pass
        
        print(f"   URL: {page.url}", flush=True)
        body = page.evaluate("() => document.body.innerText")
        print(f"   页面(400): {body[:400]}", flush=True)
        page.screenshot(path=os.path.join(os.path.dirname(__file__), "fscloud_v2_after_login.png"))
        
        # 检查是否登录成功
        if "邮箱" in body[:100] or "密码" in body[:100] or "不正确" in body:
            print("   ❌ 登录失败!", flush=True)
            time.sleep(30)
            browser.close()
            exit(1)
        
        # 导航dashboard
        if "dashboard" not in page.url.lower() and "/user" not in page.url.lower():
            print("[2] 到dashboard...", flush=True)
            page.goto(f"{BASE}/#/dashboard", wait_until="networkidle", timeout=20000)
            time.sleep(4)
            print(f"   URL: {page.url}", flush=True)
            body = page.evaluate("() => document.body.innerText")
            print(f"   页面(500): {body[:500]}", flush=True)
            page.screenshot(path=os.path.join(os.path.dirname(__file__), "fscloud_v2_dashboard.png"))
        
        # 提取订阅
        print("\n[3] 提取订阅...", flush=True)
        sub = extract_sub(page)
        print(f"   剪贴板: {sub}", flush=True)
        
        if not sub:
            body = page.evaluate("() => document.body.innerText")
            urls = re.findall(r'https?://[^\s]+token=[^\s]+', body)
            if urls:
                sub = urls[0]
        
        if not sub:
            html = page.evaluate("() => document.documentElement.outerHTML")
            urls = re.findall(r'https?://[^\s"\'<>]+token=[^\s"\'<>]{10,}', html)
            if urls:
                sub = urls[0]
        
        if sub:
            result = {"airport":"FSCloud","email":EMAIL,"password":PASSWORD,"subscribe_url":sub}
            out = os.path.join(os.path.dirname(__file__), "../register_results/fscloud_sub.json")
            os.makedirs(os.path.dirname(out), exist_ok=True)
            with open(out,"w",encoding="utf-8") as f:
                json.dump(result,f,ensure_ascii=False,indent=2)
            print(f"\n{'='*60}")
            print(f"  🎉 FSCloud: {sub}")
            print(f"{'='*60}")
        else:
            print("\n⚠️ 未提取到订阅，手动查看浏览器")
            html = page.evaluate("() => document.documentElement.outerHTML")
            with open(os.path.join(os.path.dirname(__file__),"fscloud_v2_html.txt"),"w",encoding="utf-8") as f:
                f.write(html[:50000])
            print("   HTML已保存")
        
        time.sleep(30)
        
    except Exception as e:
        print(f"异常: {e}", flush=True)
        import traceback; traceback.print_exc()
        page.screenshot(path=os.path.join(os.path.dirname(__file__),"fscloud_v2_crash.png"))
    finally:
        browser.close()
