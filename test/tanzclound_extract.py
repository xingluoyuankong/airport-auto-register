#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TANZCLOUD 登录+订阅提取 — Python Playwright版
直接登录已有账号提取订阅，含Geetest绕过
"""
import sys, os, json, time, io, math, random
try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from playwright.sync_api import sync_playwright

EMAIL = "hendricktamm95v80awzaxli@outlook.com"
PASSWORD = "VpnTest2026!"
PASSWORD2 = "@^NdxP5KN#s9G2Hqu0!"

def geetest_bypass(page):
    """尝试多种方法绕过Geetest"""
    # 方法1: 检查是否可以移除验证
    try:
        result = page.evaluate("""() => {
            // 尝试移除Geetest iframe
            let iframe = document.querySelector('iframe[src*="geetest"]');
            if (iframe) {
                iframe.remove();
                return 'iframe_removed';
            }
            return 'no_iframe';
        }""")
        print(f"  Geetest iframe: {result}", flush=True)
    except:
        pass
    
    # 方法2: 寻找滑块并拖拽
    slider_selectors = [
        '.geetest_slider_button',
        '.geetest_btn', 
        '.gt_slider_knob',
        '[class*="geetest_slide"]',
        '.gt_slider',
    ]
    
    for sel in slider_selectors:
        slider = page.query_selector(sel)
        if slider and slider.is_visible():
            print(f"  找到Geetest滑块: {sel}", flush=True)
            box = slider.bounding_box()
            if box:
                sx = box['x'] + box['width'] / 2
                sy = box['y'] + box['height'] / 2
                
                # 真人轨迹拖拽
                page.mouse.move(sx, sy)
                time.sleep(random.uniform(0.05, 0.15))
                page.mouse.down()
                time.sleep(random.uniform(0.03, 0.08))
                
                target_x = sx + 250 + random.randint(-20, 20)
                steps = random.randint(25, 45)
                for i in range(steps):
                    progress = (i + 1) / steps
                    eased = 1 - math.pow(1 - progress, 3)
                    nx = sx + (target_x - sx) * eased + random.uniform(-2, 2)
                    ny = sy + random.uniform(-3, 3)
                    page.mouse.move(nx, ny)
                    time.sleep(random.uniform(0.005, 0.025))
                
                page.mouse.up()
                time.sleep(1)
                
                # 检查结果
                body = page.evaluate("() => document.body.innerText")
                if "验证成功" in body or "请完成验证" not in body:
                    print("  Geetest验证通过!", flush=True)
                    return True
                else:
                    print("  Geetest验证未通过，继续尝试...", flush=True)
                    return False
    
    return False

def extract_sub(page):
    """提取订阅链接 — SSPANEL方法"""
    # 方法1: 点击Clash按钮劫持剪贴板
    sub = page.evaluate("""async () => {
        let old = navigator.clipboard.writeText;
        window.__sub_captured = '';
        navigator.clipboard.writeText = function(t) {
            window.__sub_captured = t;
            return old.call(navigator.clipboard, t);
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
        return window.__sub_captured || '';
    }""")
    
    if sub:
        return sub
    
    # 方法2: 从页面找订阅URL
    sub = page.evaluate("""() => {
        // 找含subscribe的a标签
        let links = document.querySelectorAll('a');
        for (let a of links) {
            if (a.href && (a.href.includes('/link/') || a.href.includes('subscribe') || a.href.includes('/sub/'))) {
                return a.href;
            }
        }
        
        // 找文本中的URL
        let text = document.body.innerText;
        let m = text.match(/https?:\\/\\/[^\\s]+(?:subscribe|sub|link)[^\\s]+/i);
        if (m) return m[0];
        
        // 找token
        m = text.match(/(?:订阅|subscribe)[\\s:：]*([a-f0-9]{20,})/i);
        if (m) return m[1];
        
        return '';
    }""")
    
    return sub

def main():
    print("=" * 60)
    print("  TANZCLOUD 订阅提取")
    print("=" * 60)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=False,
            args=["--ignore-certificate-errors",
                  "--disable-blink-features=AutomationControlled",
                  "--no-sandbox"])
        ctx = browser.new_context(viewport={"width": 1280, "height": 900},
            ignore_https_errors=True, locale="zh-CN")
        page = ctx.new_page()
        
        # 注入反检测
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => false});
            Object.defineProperty(MouseEvent.prototype, 'screenX', {
                get: function() { return (this.clientX || 0) + Math.floor(Math.random() * 400) + 80; }
            });
            Object.defineProperty(MouseEvent.prototype, 'screenY', {
                get: function() { return (this.clientY || 0) + Math.floor(Math.random() * 200) + 60; }
            });
        """)
        
        try:
            # 登录
            print("\n[1/3] 登录...", flush=True)
            page.goto("https://www.tanz.website/auth/login", 
                     wait_until="domcontentloaded", timeout=20000)
            time.sleep(2)
            
            page.locator('#email, input[name="email"]').first.fill(EMAIL)
            
            # 尝试两个密码
            logged_in = False
            for pwd, label in [(PASSWORD, "VpnTest2026!"), (PASSWORD2, "@^NdxP5KN#s9G2Hqu0!")]:
                if logged_in:
                    break
                print(f"  尝试密码: {label}", flush=True)
                page.locator('#passwd, input[name="passwd"]').first.fill(pwd)
                page.locator('button:has-text("登录")').first.click()
                page.wait_for_load_state("networkidle", timeout=10000)
                time.sleep(2)
                
                if "/user" in page.url:
                    logged_in = True
                    print(f"  登录成功! URL: {page.url}", flush=True)
                else:
                    # 检查错误
                    error_elem = page.query_selector('.alert-danger, .invalid-feedback, [class*=error]')
                    if error_elem:
                        print(f"  登录失败: {error_elem.inner_text()}", flush=True)
                    page.goto("https://www.tanz.website/auth/login", 
                             wait_until="domcontentloaded", timeout=10000)
                    time.sleep(1)
            
            if not logged_in:
                print("\n  [FAIL] 两个密码都登录失败!", flush=True)
                page.screenshot(path=os.path.join(os.path.dirname(__file__), "tanz_fail.png"))
                browser.close()
                return
            
            # 提取订阅
            print("\n[2/3] 提取订阅链接...", flush=True)
            page.screenshot(path=os.path.join(os.path.dirname(__file__), "tanz_dashboard.png"))
            sub = extract_sub(page)
            
            if sub:
                print(f"\n  订阅链接: {sub}", flush=True)
                
                # 保存结果
                result = {
                    "airport": "TANZCLOUD",
                    "panel": "tanz.website",
                    "email": EMAIL,
                    "subscribe_url": sub
                }
                
                os.makedirs(os.path.join(os.path.dirname(__file__), "../register_results"), exist_ok=True)
                with open(os.path.join(os.path.dirname(__file__), 
                         "../register_results/tanzclound_sub.json"), "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                
                print("  结果已保存!", flush=True)
            else:
                print("  [FAIL] 未能提取到订阅链接", flush=True)
                # 保存页面截图和文本
                text = page.evaluate("() => document.body.innerText")
                with open(os.path.join(os.path.dirname(__file__), "tanz_page_text.txt"), "w", encoding="utf-8") as f:
                    f.write(text)
                print("  页面文本已保存到 tanz_page_text.txt", flush=True)
            
            print("\n[3/3] 完成!", flush=True)
            
        except Exception as e:
            print(f"  异常: {e}", flush=True)
            import traceback
            traceback.print_exc()
        finally:
            time.sleep(3)
            browser.close()

if __name__ == "__main__":
    main()
