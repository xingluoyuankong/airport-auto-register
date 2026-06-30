#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TANZCLOUD 注册机 — 处理Geetest验证"""
import sys, os, json, time, io, random, math
try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from playwright.sync_api import sync_playwright

EMAIL = "mx4496f269fa@hotmail.com"
PASSWORD = "VpnTest2026!"

def human_like_drag(page, slider_selector, target_distance=260):
    """真人轨迹拖拽Geetest滑块"""
    slider = page.query_selector(slider_selector)
    if not slider:
        print("  找不到滑块!", flush=True)
        return False
    
    box = slider.bounding_box()
    if not box:
        return False
    
    start_x = box['x'] + box['width'] / 2
    start_y = box['y'] + box['height'] / 2
    
    # 使用page.mouse进行真实拖拽
    page.mouse.move(start_x, start_y)
    time.sleep(0.1 + random.random() * 0.15)
    page.mouse.down()
    time.sleep(0.05 + random.random() * 0.1)
    
    # 贝塞尔轨迹拖动
    steps = random.randint(30, 50)
    current_x = start_x
    target_x = start_x + target_distance
    
    for i in range(steps):
        progress = (i + 1) / steps
        # 添加缓动效果
        eased = 1 - math.pow(1 - progress, 3)
        next_x = start_x + (target_x - start_x) * eased + random.uniform(-2, 2)
        next_y = start_y + random.uniform(-3, 3)
        
        page.mouse.move(next_x, next_y)
        time.sleep(random.uniform(0.005, 0.02))
        
        current_x = next_x
    
    # 到达目标位置后再微调
    for _ in range(3):
        page.mouse.move(target_x + random.uniform(-1, 1), start_y + random.uniform(-2, 2))
        time.sleep(0.03)
    
    time.sleep(random.uniform(0.05, 0.15))
    page.mouse.up()
    time.sleep(0.5)
    
    return True

def run():
    print(f"\n{'='*60}\n  TANZCLOUD 注册  邮箱: {EMAIL}\n{'='*60}", flush=True)
    
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
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
        """)
        
        try:
            # 1. 打开注册页
            print("[1] 加载注册页...", flush=True)
            page.goto("https://www.tanz.website/auth/register?code=ssfJ", 
                     wait_until="domcontentloaded", timeout=20000)
            time.sleep(3)
            
            print(f"  标题: {page.title()}", flush=True)
            
            # 2. 填表
            print("[2] 填表...", flush=True)
            nick = page.locator('input[placeholder="昵称"]').first
            nick.fill("极光猎人" + str(random.randint(100, 999)))
            
            email_input = page.locator('input[placeholder="邮箱"]').first
            email_input.fill("mx4496f269fa")
            
            # 选@hotmail.com
            sel = page.locator('select').first
            sel.select_option('@hotmail.com')
            time.sleep(0.5)
            
            page.locator('input[placeholder="密码"]').first.fill(PASSWORD)
            page.locator('input[placeholder="确认密码"]').first.fill(PASSWORD)
            
            # 3. 触发Geetest
            print("[3] 触发Geetest验证...", flush=True)
            geetest_area = page.locator('.geetest_btn, [class*="geetest"], [class*="captcha"]').first
            if geetest_area.is_visible():
                geetest_area.click()
                time.sleep(2)
            else:
                # 尝试点击verify按钮
                page.locator('text=点击按钮进行验证').first.click()
                time.sleep(2)
            
            page.screenshot(path=os.path.join(os.path.dirname(__file__), "cocoduck_tanz_geetest.png"))
            
            # 4. 拖拽滑块
            print("[4] 拖拽Geetest滑块...", flush=True)
            
            # Geetest滑块选择器列表
            selectors = [
                '.geetest_slider_button',
                '.geetest_btn',
                '[class*="geetest_slide"]',
                '.gt_slider_knob',
                '.gt_slider',
            ]
            
            for sel in selectors:
                slider = page.query_selector(sel)
                if slider:
                    print(f"  找到滑块: {sel}", flush=True)
                    human_like_drag(page, sel)
                    break
            
            time.sleep(2)
            page.screenshot(path=os.path.join(os.path.dirname(__file__), "cocoduck_tanz_after_drag.png"))
            
            # 5. 检查验证结果
            print("[5] 检查验证结果...", flush=True)
            body_text = page.evaluate("() => document.body.innerText")
            if "验证成功" in body_text or "请完成验证" not in body_text:
                print("  验证可能已通过!", flush=True)
                
                # 尝试注册
                print("[6] 尝试注册...", flush=True)
                reg_btn = page.locator('button:has-text("注册")').first
                reg_btn.click()
                time.sleep(3)
                page.wait_for_load_state("networkidle", timeout=10000)
                
                current_url = page.url
                print(f"  注册后URL: {current_url}", flush=True)
                
                if "/login" in current_url or "/user" in current_url:
                    print("  注册成功!", flush=True)
                    
                    # 登录
                    if "/login" in current_url or "/auth/login" in current_url:
                        page.locator('#email, input[name="email"]').first.fill(EMAIL)
                        page.locator('#passwd, input[name="passwd"]').first.fill(PASSWORD)
                        page.locator('button:has-text("登录")').first.click()
                        page.wait_for_load_state("networkidle", timeout=10000)
                        time.sleep(3)
                    
                    if "/user" in page.url:
                        # 提取订阅
                        page.screenshot(path=os.path.join(os.path.dirname(__file__), "cocoduck_tanz_dashboard.png"))
                        
                        # SSPANEL订阅提取
                        sub_url = page.evaluate("""() => {
                            let old = navigator.clipboard.writeText;
                            window.__tanz_sub = '';
                            navigator.clipboard.writeText = function(t) {
                                window.__tanz_sub = t;
                                return old.call(navigator.clipboard, t);
                            };
                            let btns = document.querySelectorAll('button');
                            for (let b of btns) {
                                if (b.textContent.includes('Clash') || b.textContent.includes('订阅')) {
                                    b.click();
                                    break;
                                }
                            }
                            return new Promise(r => setTimeout(() => r(window.__tanz_sub || ''), 500));
                        }""")
                        
                        print(f"  订阅: {sub_url}", flush=True)
                        
                        if not sub_url:
                            # SSPANEL备用方法
                            sub_url = page.evaluate("""() => {
                                let links = document.querySelectorAll('a');
                                for (let a of links) {
                                    if (a.href && a.href.includes('/link/')) {
                                        return a.href;
                                    }
                                }
                                // 找sub token
                                let text = document.body.innerText;
                                let m = text.match(/https?:\\/\\/[^\\s]+(?:subscribe|sub|link)[^\\s]+/);
                                return m ? m[0] : '';
                            }""")
                            print(f"  订阅(备用): {sub_url}", flush=True)
                    else:
                        print(f"  未跳转到Dashboard: {page.url}", flush=True)
                else:
                    print(f"  注册可能失败: {current_url}", flush=True)
            else:
                print(f"  验证未通过: {body_text[:200]}", flush=True)
            
            page.screenshot(path=os.path.join(os.path.dirname(__file__), "cocoduck_tanz_final.png"))
            
        except Exception as e:
            print(f"  异常: {e}", flush=True)
            import traceback
            traceback.print_exc()
        finally:
            time.sleep(3)
            browser.close()

if __name__ == "__main__":
    run()
