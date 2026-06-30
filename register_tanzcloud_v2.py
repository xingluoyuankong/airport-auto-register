#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TANZCLOUD v2 - Geetest突破版注册机
使用 ddddocr + 拟人轨迹 绕过极验滑块验证
email: mx4496f269fa@hotmail.com / VpnTest2026!
"""
import sys, os, json, time, io, random
try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from playwright.sync_api import sync_playwright
from geetest_solver import GeetestSolver

EMAIL = "mx4496f269fa@hotmail.com"
PASSWORD = "VpnTest2026!"
REGISTER_URL = "https://www.tanz.website/auth/register?code=ssfJ"
LOGIN_URL = "https://www.tanz.website/auth/login"

def extract_sub(page):
    """SSPanel订阅提取"""
    sub = page.evaluate("""async () => {
        let old = navigator.clipboard.writeText;
        window.__tanz_sub = '';
        navigator.clipboard.writeText = function(t) {
            window.__tanz_sub = t;
            return Promise.resolve();
        };
        
        let btns = document.querySelectorAll('button');
        for (let b of btns) {
            let t = b.textContent || '';
            if (t.includes('Clash') || t.includes('订阅链接')) {
                b.click();
                break;
            }
        }
        
        await new Promise(r => setTimeout(r, 800));
        return window.__tanz_sub || '';
    }""")
    
    if sub: return sub
    
    # 备用
    sub = page.evaluate("""() => {
        let links = document.querySelectorAll('a');
        for (let a of links) {
            if (a.href && (a.href.includes('/link/') || a.href.includes('/sub/'))) {
                return a.href;
            }
        }
        let t = document.body.innerText;
        let m = t.match(/https?:\\/\\/[^\\s]+(?:subscribe|sub|link)[^\\s]+/i);
        return m ? m[0] : '';
    }""")
    return sub

def main():
    print("=" * 60)
    print("  TANZCLOUD v2 注册机 (Geetest突破版)")
    print(f"  邮箱: {EMAIL}")
    print("=" * 60)
    
    solver = GeetestSolver()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=False,
            args=["--ignore-certificate-errors",
                  "--disable-blink-features=AutomationControlled",
                  "--no-sandbox"])
        ctx = browser.new_context(viewport={"width": 1280, "height": 900},
            ignore_https_errors=True, locale="zh-CN")
        page = ctx.new_page()
        
        # 反检测
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => false});
            Object.defineProperty(MouseEvent.prototype, 'screenX', {
                get: function() { return (this.clientX || 0) + Math.floor(Math.random() * 400) + 80; }
            });
            Object.defineProperty(MouseEvent.prototype, 'screenY', {
                get: function() { return (this.clientY || 0) + Math.floor(Math.random() * 200) + 60; }
            });
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
        """)
        
        try:
            # ===== STEP 1: 注册 =====
            print("\n[1/5] 加载注册页...", flush=True)
            page.goto(REGISTER_URL, wait_until="domcontentloaded", timeout=20000)
            time.sleep(3)
            print(f"  标题: {page.title()}", flush=True)
            
            # 填表
            print("[2/5] 填表...", flush=True)
            page.locator('#name, input[name="name"]').first.fill("雷霆战士" + str(random.randint(100, 999)))
            page.locator('#email, input[name="email"], input[placeholder="邮箱"]').first.fill("mx4496f269fa")
            
            # 选@hotmail.com
            sel = page.locator('#email_postfix, select').first
            sel.select_option('@hotmail.com')
            time.sleep(0.3)
            
            page.locator('#passwd, input[placeholder="密码"], input[type="password"]').first.fill(PASSWORD)
            page.locator('#repasswd, input[placeholder="确认密码"]').nth(0).fill(PASSWORD)
            
            time.sleep(0.5)
            
            # ===== STEP 3: Geetest突破 =====
            print("[3/5] Geetest突破...", flush=True)
            
            # 先触发Geetest
            geetest_btn = page.locator('[class*="geetest_btn"], .geetest_btn_click, [aria-label*="点击按钮开始验证"]').first
            if geetest_btn.is_visible():
                geetest_btn.click()
            else:
                page.locator('text=点击按钮进行验证').first.click()
            time.sleep(2)
            
            page.screenshot(path=os.path.join(os.path.dirname(__file__),
                "screenshots", "tanzclound_geetest.png"))
            
            # 调用突破器
            print("  开始突破Geetest...", flush=True)
            solved = solver.solve_slider(page, max_retries=3)
            
            if not solved:
                print("  [FAIL] Geetest未能突破!", flush=True)
                page.screenshot(path=os.path.join(os.path.dirname(__file__),
                    "screenshots", "tanzclound_geetest_fail.png"))
                browser.close()
                return None
            
            time.sleep(1)
            
            # ===== STEP 4: 提交注册 =====
            print("[4/5] 提交注册...", flush=True)
            
            # 确保checkbox勾选
            checkbox = page.locator('input[type="checkbox"]').first
            if checkbox.is_visible() and not checkbox.is_checked():
                checkbox.check(force=True)
            
            page.screenshot(path=os.path.join(os.path.dirname(__file__),
                "screenshots", "tanzclound_before_submit.png"))
            
            reg_btn = page.locator('button:has-text("注册"), button[type="submit"]').first
            if reg_btn.is_visible():
                reg_btn.click()
                print("  已提交注册", flush=True)
            
            time.sleep(5)
            page.wait_for_load_state("networkidle", timeout=15000)
            
            current_url = page.url
            print(f"  注册后URL: {current_url}", flush=True)
            
            page.screenshot(path=os.path.join(os.path.dirname(__file__),
                "screenshots", "tanzclound_after_register.png"))
            
            # ===== STEP 5: 登录+提取 =====
            print("[5/5] 提取订阅...", flush=True)
            
            # 如果注册后跳到登录页，执行登录
            if "/auth/login" in current_url or "/login" in current_url:
                print("  注册成功，自动登录...", flush=True)
                page.locator('#email, input[name="email"]').first.fill(EMAIL)
                page.locator('#passwd, input[name="passwd"]').first.fill(PASSWORD)
                page.locator('button:has-text("登录")').first.click()
                time.sleep(5)
                page.wait_for_load_state("networkidle", timeout=15000)
                print(f"  登录后URL: {page.url}", flush=True)
            
            # 确保在user面板
            if "/user" not in page.url:
                page.goto("https://www.tanz.website/user", wait_until="networkidle", timeout=15000)
                time.sleep(2)
            
            page.screenshot(path=os.path.join(os.path.dirname(__file__),
                "screenshots", "tanzclound_dashboard.png"))
            
            # 提取订阅
            sub = extract_sub(page)
            
            if sub:
                print(f"\n  ✅ 订阅链接: {sub}", flush=True)
                
                # 保存
                result = {
                    "airport": "TANZCLOUD",
                    "panel": "tanz.website",
                    "email": EMAIL,
                    "password": PASSWORD,
                    "subscribe_url": sub
                }
                
                os.makedirs(os.path.join(os.path.dirname(__file__), "register_results"), exist_ok=True)
                with open(os.path.join(os.path.dirname(__file__),
                         f"register_results/tanzcloud_{EMAIL.split('@')[0]}.json"),
                         "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                
                print(f"  结果已保存!", flush=True)
                return sub
            else:
                print("  ⚠️ 未能自动提取，请手动查看浏览器", flush=True)
                # 保存页面文本
                text = page.evaluate("() => document.body.innerText")
                with open(os.path.join(os.path.dirname(__file__), 
                         "tanz_page_dump.txt"), "w", encoding="utf-8") as f:
                    f.write(text)
                print("  页面文本已保存", flush=True)
                return None
                
        except Exception as e:
            print(f"  异常: {e}", flush=True)
            import traceback
            traceback.print_exc()
            try:
                page.screenshot(path=os.path.join(os.path.dirname(__file__),
                    "screenshots", "tanzclound_error.png"))
            except:
                pass
            return None
        finally:
            time.sleep(5)
            browser.close()

if __name__ == "__main__":
    os.makedirs(os.path.join(os.path.dirname(__file__), "screenshots"), exist_ok=True)
    result = main()
    
    if result:
        print(f"\n{'='*60}")
        print(f"  🎉 TANZCLOUD注册成功!")
        print(f"  订阅: {result}")
        print(f"{'='*60}")
        sys.exit(0)
    else:
        print(f"\n  注册失败")
        sys.exit(1)
