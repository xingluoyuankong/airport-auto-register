#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iKuuu v2 - Geetest突破版登录+提取
使用 ddddocr 绕过极验点击式验证
email: kebukeyi2026@outlook.com / VpnTest2026!
"""
import sys, os, json, time, io
try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from playwright.sync_api import sync_playwright
from geetest_solver import GeetestSolver

EMAIL = "kebukeyi2026@outlook.com"
PASSWORD = "VpnTest2026!"
# 试用多个域名
DOMAINS = ["https://ikuuu.fyi", "https://ikuuu.one"]

def main():
    print("=" * 60)
    print("  iKuuu v2 订阅提取 (Geetest突破版)")
    print(f"  邮箱: {EMAIL}")
    print("=" * 60)
    
    solver = GeetestSolver()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=False,
            args=["--ignore-certificate-errors",
                  "--disable-blink-features=AutomationControlled",
                  "--no-sandbox", "--disable-features=OscpStapling"])
        ctx = browser.new_context(viewport={"width": 1280, "height": 900},
            ignore_https_errors=True, locale="zh-CN")
        page = ctx.new_page()
        
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => false});
            Object.defineProperty(MouseEvent.prototype, 'screenX', {
                get: function() { return (this.clientX || 0) + Math.floor(Math.random() * 400) + 80; }
            });
            Object.defineProperty(MouseEvent.prototype, 'screenY', {
                get: function() { return (this.clientY || 0) + Math.floor(Math.random() * 200) + 60; }
            });
        """)
        
        logged_in = False
        
        for domain in DOMAINS:
            if logged_in:
                break
            
            try:
                login_url = f"{domain}/auth/login"
                print(f"\n  尝试域名: {domain}", flush=True)
                page.goto(login_url, wait_until="domcontentloaded", timeout=20000)
                time.sleep(3)
                
                title = page.title()
                print(f"  标题: {title}", flush=True)
                
                # 检查是否为真正的登录页
                if "域名" in title or "最新域名" in title:
                    print("  这是域名导航页，跳过", flush=True)
                    continue
                
                # 填表
                page.locator('#email, input[name="email"], input[placeholder="邮箱"]').first.fill(EMAIL)
                page.locator('#passwd, input[name="passwd"], input[placeholder="密码"]').first.fill(PASSWORD)
                
                # 处理Geetest
                print("  处理验证...", flush=True)
                
                # 检测验证类型
                has_click = page.query_selector('[class*="geetest_item"], .geetest_item_img')
                has_slider = page.query_selector('.geetest_slider_button, .geetest_btn')
                
                if has_slider or page.evaluate("() => document.body.innerText.includes('滑块')"):
                    print("  滑块验证", flush=True)
                    geetest_btn = page.locator('[class*="geetest_btn"], [aria-label*="验证"]').first
                    if geetest_btn.is_visible():
                        geetest_btn.click()
                        time.sleep(2)
                    solver.solve_slider(page, max_retries=3)
                
                elif has_click:
                    print("  点击验证", flush=True)
                    solver.solve_click_captcha(page, max_retries=3)
                
                else:
                    print("  无可见Geetest验证元素", flush=True)
                
                time.sleep(1)
                
                # 登录
                page.locator('button:has-text("登录")').first.click()
                time.sleep(5)
                page.wait_for_load_state("networkidle", timeout=15000)
                
                current_url = page.url
                print(f"  登录后URL: {current_url}", flush=True)
                
                if "/user" in current_url or "dashboard" in current_url:
                    logged_in = True
                    print("  登录成功!", flush=True)
                else:
                    # 检查错误
                    body = page.evaluate("() => document.body.innerText")
                    if "密码" in body and "不正确" in body:
                        print("  密码错误!", flush=True)
                    else:
                        print(f"  登录失败: {body[:100]}", flush=True)
                    
            except Exception as e:
                print(f"  异常: {e}", flush=True)
        
        if not logged_in:
            print("\n  [FAIL] 所有域名登录失败!", flush=True)
            page.screenshot(path=os.path.join(os.path.dirname(__file__),
                "screenshots", "ikuuu_login_fail.png"))
            browser.close()
            return None
        
        # 提取订阅
        print("\n  提取订阅链接...", flush=True)
        page.screenshot(path=os.path.join(os.path.dirname(__file__),
            "screenshots", "ikuuu_dashboard.png"))
        
        sub = page.evaluate("""async () => {
            let old = navigator.clipboard.writeText;
            window.__ikuuu_sub = '';
            navigator.clipboard.writeText = function(t) {
                window.__ikuuu_sub = t;
                return Promise.resolve();
            };
            
            let btns = document.querySelectorAll('button');
            for (let b of btns) {
                let t = b.textContent || '';
                if (t.includes('Clash') || t.includes('订阅') || t.includes('一键')) {
                    b.click();
                    break;
                }
            }
            
            await new Promise(r => setTimeout(r, 800));
            return window.__ikuuu_sub || '';
        }""")
        
        if not sub:
            sub = page.evaluate("""() => {
                // V2Board方式
                try {
                    let raw = localStorage.getItem('VUE_NAIVE_ACCESS_TOKEN');
                    if (raw) {
                        let token = JSON.parse(raw).value;
                        return 'TOKEN:' + token;
                    }
                } catch(e) {}
                
                let links = document.querySelectorAll('a');
                for (let a of links) {
                    if (a.href && (a.href.includes('/link/') || a.href.includes('/sub/') || a.href.includes('subscribe'))) {
                        return a.href;
                    }
                }
                return '';
            }""")
        
        if sub:
            print(f"  ✅ 订阅: {sub}", flush=True)
            
            result = {
                "airport": "iKuuu",
                "domain": domain,
                "email": EMAIL,
                "password": PASSWORD,
                "subscribe_url": sub
            }
            
            os.makedirs(os.path.join(os.path.dirname(__file__), "register_results"), exist_ok=True)
            with open(os.path.join(os.path.dirname(__file__),
                     "register_results/ikuuu_sub.json"), "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            saved_sub = f"https://ikuuu.fyi/link/{sub}?sub=1" if "TOKEN:" in sub else sub
            if "TOKEN:" in sub:
                token = sub.replace("TOKEN:", "")
                result["subscribe_url"] = saved_sub
                with open(os.path.join(os.path.dirname(__file__),
                         "register_results/ikuuu_sub.json"), "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                print(f"  订阅URL: {saved_sub}", flush=True)
            
            return result["subscribe_url"]
        
        print("  ⚠️ 未能提取订阅")
        return None

if __name__ == "__main__":
    os.makedirs(os.path.join(os.path.dirname(__file__), "screenshots"), exist_ok=True)
    result = main()
    if result:
        print(f"\n{'='*60}")
        print(f"  🎉 iKuuu提取成功!")
        print(f"  订阅: {result}")
        print(f"{'='*60}")
        sys.exit(0)
    else:
        print(f"\n  提取失败")
        sys.exit(1)
