#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TANZCLOUD 登录+提取 — 精准版，修正input name"""
import sys, os, time, io, re, json, random, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from playwright.sync_api import sync_playwright

EMAIL = "hendricktamm95v80awzaxli@outlook.com"
PASSWORDS = ["VpnTest2026!", "@^NdxP5KN#s9G2Hqu0!"]
BASE = "https://www.tanz.website"

# ===== 核心：真人轨迹拖滑块 =====
def human_drag(page, slider_el, distance=260):
    box = slider_el.bounding_box()
    if not box:
        return False
    sx = box['x'] + box['width']/2
    sy = box['y'] + box['height']/2
    page.mouse.move(sx, sy)
    time.sleep(random.uniform(0.05, 0.15))
    page.mouse.down()
    time.sleep(random.uniform(0.03, 0.08))
    tx = sx + distance + random.randint(-10, 10)
    steps = random.randint(30, 50)
    for i in range(steps):
        p = (i+1)/steps
        eased = 1 - (1-p)**3
        nx = sx + (tx-sx)*eased + random.uniform(-2,2)
        ny = sy + random.uniform(-3,3)
        page.mouse.move(nx, ny)
        time.sleep(random.uniform(0.003, 0.015))
    page.mouse.move(tx + random.uniform(-1,1), sy + random.uniform(-2,2))
    time.sleep(random.uniform(0.05, 0.15))
    page.mouse.up()
    time.sleep(0.5)
    return True

# ===== 核心：提取订阅 =====
def extract_sub(page):
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
            if (t.includes('Clash') || t.includes('订阅链接') || t.includes('复制订阅')) {
                b.click();
                break;
            }
        }
        await new Promise(r => setTimeout(r, 800));
        return window.__tanz_sub || '';
    }""")
    if sub:
        return sub
    
    # 备用：从页面文本找
    sub = page.evaluate("""() => {
        let links = document.querySelectorAll('a');
        for (let a of links) {
            if (a.href && (a.href.includes('/link/') || a.href.includes('subscribe') || a.href.includes('/sub/'))) {
                return a.href;
            }
        }
        let t = document.body.innerText;
        let m = t.match(/https?:\\/\\/[^\\s]+(?:subscribe|sub|link|token)[^\\s]*/i);
        if (m) return m[0];
        let html = document.documentElement.outerHTML;
        let m2 = html.match(/https?:\\/\\/[^\\s"']+token[^\\s"']*/i);
        return m2 ? m2[0] : '';
    }""")
    return sub

# ===== 主流程 =====
print("="*60)
print("  TANZCLOUD 登录+提取 V6 (SSPanel精准版)")
print(f"  邮箱: {EMAIL}")
print("="*60)

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=False,
        args=["--ignore-certificate-errors",
              "--disable-blink-features=AutomationControlled",
              "--no-sandbox",
              "--proxy-server=http://127.0.0.1:7897"])
    ctx = browser.new_context(viewport={"width": 1280, "height": 900},
        ignore_https_errors=True, locale="zh-CN")
    page = ctx.new_page()
    
    # 反检测patch
    page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {get: () => false});
        Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
        Object.defineProperty(MouseEvent.prototype, 'screenX', {
            get: function() { return (this.clientX || 0) + Math.floor(Math.random() * 400) + 80; }
        });
        Object.defineProperty(MouseEvent.prototype, 'screenY', {
            get: function() { return (this.clientY || 0) + Math.floor(Math.random() * 200) + 60; }
        });
    """)
    
    try:
        # ===== STEP 1: 登录 =====
        print("\n[1] 打开登录页...", flush=True)
        page.goto(f"{BASE}/auth/login", wait_until="domcontentloaded", timeout=25000)
        page.wait_for_load_state("networkidle", timeout=15000)
        time.sleep(2)
        
        # 截图看实际HTML结构
        html = page.evaluate("() => document.body.innerHTML.substring(0, 2000)")
        print(f"   HTML(2000):\n{html[:1500]}", flush=True)
        
        # 找所有input
        inputs = page.evaluate("""() => {
            return Array.from(document.querySelectorAll('input')).map(i => ({
                type: i.type, name: i.name, id: i.id,
                placeholder: i.placeholder, className: i.className
            }));
        }""")
        print(f"   Inputs: {inputs}", flush=True)
        
        # 精准填邮箱 - 用name属性找
        email_inputs = page.locator('input[name="email"]')
        pw_inputs = page.locator('input[name="password"]')
        
        print(f"   email inputs: {email_inputs.count()}", flush=True)
        print(f"   password inputs: {pw_inputs.count()}", flush=True)
        
        if email_inputs.count() == 0:
            # 尝试其他可能的选择器
            for sel in ['#email', 'input[placeholder*="邮箱"]', 'input[type="email"]']:
                if page.locator(sel).count() > 0:
                    email_inputs = page.locator(sel).first
                    break
        
        if pw_inputs.count() == 0:
            for sel in ['#passwd', '#password', 'input[placeholder*="密码"]']:
                if page.locator(sel).count() > 0:
                    pw_inputs = page.locator(sel).first
                    break
        
        email_inputs_first = email_inputs if hasattr(email_inputs, 'count') else email_inputs
        if isinstance(email_inputs_first, int) and email_inputs_first == 0:
            email_inputs = page.locator('input[type="email"]').first
        
        # 快速试每个密码
        logged_in = False
        for pwd in PASSWORDS:
            if logged_in:
                break
            
            print(f"\n[2] 试密码: {pwd[:4]}...", flush=True)
            
            # 刷新登录页
            page.goto(f"{BASE}/auth/login", wait_until="networkidle", timeout=20000)
            time.sleep(1.5)
            
            # 用pressSequentially模拟真实输入
            em = page.locator('input[name="email"]').first
            if em.count() == 0:
                em = page.locator('#email').first
            em.click()
            time.sleep(0.2)
            em.fill("")
            time.sleep(0.1)
            em.type(EMAIL, delay=random.randint(30, 80))
            time.sleep(0.3)
            
            pw = page.locator('input[name="password"]').first
            if pw.count() == 0:
                pw = page.locator('#password').first
            if pw.count() == 0:
                pw = page.locator('#passwd').first
            pw.click()
            time.sleep(0.2)
            pw.type(pwd, delay=random.randint(30, 80))
            time.sleep(0.5)
            
            page.screenshot(path=os.path.join(os.path.dirname(__file__), f"tanz_v6_filled_{pwd[:4]}.png"))
            
            # 点login
            login_btn = page.locator('button:has-text("登录")').first
            if login_btn.count() == 0:
                login_btn = page.locator('button[type="submit"]').first
            login_btn.click()
            time.sleep(4)
            
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except:
                pass
            time.sleep(1)
            
            print(f"   URL: {page.url}", flush=True)
            
            # 检查是否有弹窗（Geetest/错误提示）
            body = page.evaluate("() => document.body.innerText")
            print(f"   页面文本(250): {body[:250]}", flush=True)
            
            page.screenshot(path=os.path.join(os.path.dirname(__file__), f"tanz_v6_after_{pwd[:4]}.png"))
            
            if "/user" in page.url or "/dashboard" in page.url:
                logged_in = True
                print(f"   ✅ 登录成功! 使用密码: {pwd[:4]}...", flush=True)
                break
            elif "密码" in body and ("错误" in body or "不正确" in body):
                print(f"   ❌ 密码错误: {pwd[:4]}...", flush=True)
            elif "验证" in body or "geetest" in body.lower():
                print(f"   ⚠️ 需要Geetest验证!", flush=True)
                # 尝试绕过
                slider_selectors = [
                    '.geetest_slider_button', '.geetest_btn',
                    '.gt_slider_knob', '[class*="geetest_slide"]',
                    '.gt_slider', '.geetest_slide_button'
                ]
                for ss in slider_selectors:
                    s_el = page.query_selector(ss)
                    if s_el and s_el.is_visible():
                        print(f"   找到滑块: {ss}", flush=True)
                        human_drag(page, s_el)
                        time.sleep(2)
                        # 验证后重新点登录
                        login_btn = page.locator('button:has-text("登录")').first
                        if login_btn.count() > 0:
                            login_btn.click()
                            time.sleep(4)
                            try:
                                page.wait_for_load_state("networkidle", timeout=10000)
                            except:
                                pass
                            print(f"   验证后URL: {page.url}", flush=True)
                            if "/user" in page.url:
                                logged_in = True
                                print(f"   ✅ Geetest突破成功! 密码: {pwd[:4]}...", flush=True)
                                break
                        break
            else:
                print(f"   未知状态，可能已登录", flush=True)
        
        if not logged_in:
            print("\n❌ 所有密码都登录失败! 可能是账号不存在或被封", flush=True)
            page.screenshot(path=os.path.join(os.path.dirname(__file__), "tanz_v6_fail_final.png"))
            browser.close()
            exit(1)
        
        # ===== STEP 2: 提取订阅 =====
        print("\n[3] 提取订阅...", flush=True)
        
        # 导航到user页
        if "/user" not in page.url:
            page.goto(f"{BASE}/user", wait_until="networkidle", timeout=20000)
            time.sleep(3)
        
        page.screenshot(path=os.path.join(os.path.dirname(__file__), "tanz_v6_dashboard.png"))
        
        # 扫描所有页面元素
        full_text = page.evaluate("() => document.body.innerText")
        print(f"   Dashboard文本(500):\n{full_text[:500]}", flush=True)
        
        # 尝试劫持剪贴板点订阅按钮
        sub = extract_sub(page)
        print(f"   劫持剪贴板: {sub}", flush=True)
        
        if not sub:
            # 找所有链接
            all_links = page.evaluate("""() => {
                return Array.from(document.querySelectorAll('a[href]'))
                    .filter(a => a.href && a.href.includes('http'))
                    .slice(0, 30)
                    .map(a => ({text: (a.textContent||'').trim().slice(0,40), href: a.href.slice(0,200)}));
            }""")
            print(f"   Links: {all_links}", flush=True)
        
        if not sub:
            # 去订阅页面
            for sp in ["/user/subscribe", "/user#subscribe", "/user/sub"]:
                print(f"   尝试: {BASE}{sp}", flush=True)
                try:
                    page.goto(f"{BASE}{sp}", wait_until="networkidle", timeout=10000)
                    time.sleep(2)
                    st = page.evaluate("() => document.body.innerText")
                    print(f"   文本(400): {st[:400]}", flush=True)
                    
                    urls = re.findall(r'https?://[^\s]+(?:subscribe|sub|token|link)[^\s]*', st)
                    if urls:
                        sub = urls[0]
                        print(f"   ✅ 找到: {sub}", flush=True)
                        break
                except:
                    pass
        
        if sub:
            # 保存结果
            result = {
                "airport": "TANZCLOUD",
                "panel": "tanz.website",
                "email": EMAIL,
                "password": pwd,
                "subscribe_url": sub
            }
            out_dir = os.path.join(os.path.dirname(__file__), "../register_results")
            os.makedirs(out_dir, exist_ok=True)
            with open(os.path.join(out_dir, "tanzcloud_sub.json"), "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print(f"\n{'='*60}")
            print(f"  🎉 TANZCLOUD 订阅提取成功!")
            print(f"  订阅链接: {sub}")
            print(f"  结果已保存到 register_results/tanzcloud_sub.json")
            print(f"{'='*60}")
        else:
            print(f"\n⚠️ 登录成功但未能提取订阅链接，请手动查看浏览器")
            page.screenshot(path=os.path.join(os.path.dirname(__file__), "tanz_v6_no_sub.png"))
            # 保存完整HTML
            html_full = page.evaluate("() => document.documentElement.outerHTML")
            with open(os.path.join(os.path.dirname(__file__), "tanz_v6_full_html.txt"), "w", encoding="utf-8") as f:
                f.write(html_full)
            print(f"   完整HTML已保存到 tanz_v6_full_html.txt")
        
        time.sleep(20)
        
    except Exception as e:
        print(f"\n异常: {e}", flush=True)
        import traceback
        traceback.print_exc()
        page.screenshot(path=os.path.join(os.path.dirname(__file__), "tanz_v6_crash.png"))
    finally:
        browser.close()
