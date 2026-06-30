#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""喵喵网络 注册+提取 完整脚本 V1
https://www.miaonetwork.com — 72小时免费试用
完整邮箱输入，需人机验证
"""
import sys, os, time, io, re, json, random, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from playwright.sync_api import sync_playwright

EMAIL = f"miaogoog{random.randint(100,999)}@outlook.com"
PASSWORD = "VpnTest2026!"
BASE = "https://www.miaonetwork.com"
REGISTER_URL = f"{BASE}/#/register?code=v3fkHXqC"

def human_slide(page, slider_sel, max_dist=300):
    """拟人拖动滑块"""
    slider = page.query_selector(slider_sel)
    if not slider:
        try: slider = page.locator('.slider-btn, .verification-slider-btn, [class*="slider"]').first
        except: slider = None
    if not slider: return False
    
    box = slider.bounding_box()
    if not box: return False
    sx, sy = box['x'] + box['width']/2, box['y'] + box['height']/2
    page.mouse.move(sx, sy)
    time.sleep(random.uniform(0.05, 0.2))
    page.mouse.down()
    time.sleep(random.uniform(0.02, 0.08))
    
    steps = random.randint(30, 50)
    for i in range(steps):
        p = (i+1)/steps
        eased = 1 - (1-p)**3
        nx = sx + max_dist * eased + random.uniform(-2, 2)
        ny = sy + random.uniform(-3, 3)
        page.mouse.move(nx, ny)
        time.sleep(random.uniform(0.002, 0.010))
    
    time.sleep(random.uniform(0.05, 0.15))
    page.mouse.up()
    time.sleep(1.5)
    return True

print("="*60)
print("  喵喵网络 注册+提取")
print(f"  邮箱: {EMAIL}")
print("="*60)

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=False,
        args=["--ignore-certificate-errors","--no-sandbox",
              "--proxy-server=http://127.0.0.1:7897"])
    ctx = browser.new_context(viewport={"width":1280,"height":900},
        ignore_https_errors=True, locale="zh-CN")
    page = ctx.new_page()
    page.set_default_timeout(15000)
    
    page.add_init_script("""
        Object.defineProperty(navigator,'webdriver',{get:()=>false});
        if(window.MouseEvent&&MouseEvent.prototype){
            Object.defineProperty(MouseEvent.prototype,'screenX',{
                get:function(){return(this.clientX||0)+Math.floor(Math.random()*400)+80;}
            });
            Object.defineProperty(MouseEvent.prototype,'screenY',{
                get:function(){return(this.clientY||0)+Math.floor(Math.random()*200)+60;}
            });
        }
    """)
    
    try:
        # ===== STEP 1: 注册页 =====
        print("\n[STEP 1] 打开注册页...", flush=True)
        page.goto(REGISTER_URL, wait_until="networkidle", timeout=25000)
        time.sleep(4)
        
        body = page.evaluate("() => document.body.innerText")
        print(f"   URL: {page.url}", flush=True)
        print(f"   页面(500):\n{body[:500]}", flush=True)
        
        # ===== STEP 2: 处理7秒弹窗 =====
        print("\n[STEP 2] 处理规则弹窗...", flush=True)
        time.sleep(8)  # 等7秒倒计时
        
        btn = page.query_selector('.popup-action-btn')
        if btn and btn.is_visible():
            btn.click()
            print("   ✅ 弹窗已关闭", flush=True)
            time.sleep(1)
        
        # ===== STEP 3: 填表 =====
        print("\n[STEP 3] 填表...", flush=True)
        
        em = page.locator('#email')
        pw = page.locator('#password')
        cpw = page.locator('#confirmPassword')
        
        em.click(); time.sleep(0.1); em.fill(EMAIL); time.sleep(0.3)
        pw.click(); time.sleep(0.1); pw.fill(PASSWORD); time.sleep(0.3)
        cpw.click(); time.sleep(0.1); cpw.fill(PASSWORD); time.sleep(0.3)
        
        # checkbox
        cb = page.locator('input[type="checkbox"]').first
        if cb.count() > 0 and cb.is_visible():
            cb.check(force=True)
            time.sleep(0.3)
        
        page.screenshot(path=os.path.join(os.path.dirname(__file__), "miaowang_v2_filled.png"))
        print("   ✅ 表单填写完成", flush=True)
        
        # ===== STEP 4: 处理人机验证 =====
        print("\n[STEP 4] 人机验证...", flush=True)
        
        # 等 Turnstile/Geetest 出现
        time.sleep(3)
        
        # Turnstile 检测
        ts = page.query_selector('iframe[src*="turnstile"], iframe[src*="challenges.cloudflare"]')
        if ts:
            print("   检测到 Turnstile", flush=True)
        else:
            body = page.evaluate("() => document.body.innerText")
            geetest = '极验' in body or '滑块' in body or '验证' in body
            print(f"   Turnstile: {ts is not None}, 文本含验证: {geetest}", flush=True)
            if geetest:
                # 尝试滑块
                for i in range(3):
                    if human_slide(page, '.geetest_slider_button, .gt_slider_knob, [class*="slider"]', random.randint(200, 280)):
                        print(f"   滑块第{i+1}次...", flush=True)
                        time.sleep(2)
        
        # Turnstile自动点击
        if ts:
            try:
                frame = ts.content_frame()
                cb2 = frame.query_selector('.cb-lb, .checkbox')
                if cb2: cb2.click()
                time.sleep(5)
            except:
                pass
        
        page.screenshot(path=os.path.join(os.path.dirname(__file__), "miaowang_v2_verify.png"))
        
        # ===== STEP 5: 提交 =====
        print("\n[STEP 5] 提交注册...", flush=True)
        reg_btn = page.locator('button:has-text("创建账户")').first
        if reg_btn.count() > 0 and reg_btn.is_visible():
            reg_btn.click()
            print("   ✅ 已点击创建账户", flush=True)
        
        time.sleep(6)
        try: page.wait_for_load_state("networkidle", timeout=15000)
        except: pass
        
        print(f"   注册后URL: {page.url}", flush=True)
        body = page.evaluate("() => document.body.innerText")
        print(f"   页面(500):\n{body[:500]}", flush=True)
        page.screenshot(path=os.path.join(os.path.dirname(__file__), "miaowang_v2_after_register.png"))
        
        # 检测注册成功
        if "dashboard" in page.url.lower() or "user" in page.url.lower() or "仪表" in body:
            print("   ✅ 注册成功!", flush=True)
        elif "邮箱" in body or "email" in body.lower() or "错误" in body:
            print("   ❌ 可能失败", flush=True)
        
        # ===== STEP 6: 提取订阅 =====
        print("\n[STEP 6] 提取订阅...", flush=True)
        
        # 劫持剪贴板
        sub = page.evaluate("""async () => {
            window.__sub='';
            let old = navigator.clipboard.writeText;
            navigator.clipboard.writeText = function(t) {window.__sub=t; return Promise.resolve();};
            let bs = document.querySelectorAll('button');
            for(let b of bs) {
                let t = b.textContent || '';
                if(t.includes('订阅') || t.includes('Clash') || t.includes('一键')) {b.click(); break;}
            }
            await new Promise(r=>setTimeout(r, 800));
            navigator.clipboard.writeText = old;
            return window.__sub || '';
        }""")
        
        if not sub:
            # 从页面文字提取
            sub = page.evaluate("""() => {
                let t = document.body.innerText;
                let m = t.match(/https?:\\/\\/[^\\s]+(?:subscribe|sub|token|link)[^\\s]+/i);
                return m ? m[0] : '';
            }""")
        
        if not sub:
            # 遍历链接
            sub = page.evaluate("""() => {
                let links = document.querySelectorAll('a[href]');
                for(let a of links) {
                    if(a.href && (a.href.includes('/sub/') || a.href.includes('/link/') || a.href.includes('subscribe'))) {
                        return a.href;
                    }
                }
                return '';
            }""")
        
        print(f"   订阅: {sub or '未找到'}", flush=True)
        
        # 保存结果
        result = {"airport":"喵喵网络","panel":"miaonetwork.com","email":EMAIL,"password":PASSWORD,"subscribe_url":sub}
        with open(os.path.join(os.path.dirname(__file__), f"miaowang_{EMAIL.split('@')[0]}.json"), "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 结果已保存", flush=True)
        time.sleep(30)
        
    except Exception as e:
        print(f"异常: {e}", flush=True)
        import traceback; traceback.print_exc()
        try: page.screenshot(path=os.path.join(os.path.dirname(__file__),"miaowang_v2_error.png"))
        except: pass
    finally:
        browser.close()
