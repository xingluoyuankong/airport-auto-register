#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""iKuuu v1 — 深度逆向分析登录+Geetest绕过+订阅提取"""
import sys, os, time, io, re, random, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from playwright.sync_api import sync_playwright

EMAIL = "kebukeyi2026@outlook.com"
PASSWORD = "VpnTest2026!"
BASE = "https://ikuu.win"

def human_drag(page, slider, target_distance=260):
    """真人轨迹Geetest拖拽"""
    box = slider.bounding_box()
    if not box: return False
    sx = box['x'] + box['width']/2
    sy = box['y'] + box['height']/2
    page.mouse.move(sx, sy)
    time.sleep(random.uniform(0.05, 0.15))
    page.mouse.down()
    time.sleep(random.uniform(0.03, 0.08))
    tx = sx + target_distance + random.randint(-15, 15)
    steps = random.randint(30, 50)
    for i in range(steps):
        progress = (i+1)/steps
        eased = 1 - math.pow(1-progress, 3)
        nx = sx + (tx-sx)*eased + random.uniform(-2, 2)
        ny = sy + random.uniform(-3, 3)
        page.mouse.move(nx, ny)
        time.sleep(random.uniform(0.005, 0.02))
    for _ in range(3):
        page.mouse.move(tx+random.uniform(-1,1), sy+random.uniform(-2,2))
        time.sleep(0.03)
    page.mouse.up()
    time.sleep(1)
    return True

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=False,
        args=["--ignore-certificate-errors", "--no-sandbox",
              "--disable-blink-features=AutomationControlled",
              "--proxy-server=http://127.0.0.1:7897"])
    ctx = browser.new_context(viewport={"width": 1280, "height": 900},
        ignore_https_errors=True, locale="zh-CN")
    page = ctx.new_page()
    page.set_default_timeout(15000)
    
    # 反检测注入
    page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {get: () => false});
        Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
        Object.defineProperty(MouseEvent.prototype, 'screenX', {
            get: function() { return (this.clientX || 0) + Math.floor(Math.random()*400) + 80; }
        });
        Object.defineProperty(MouseEvent.prototype, 'screenY', {
            get: function() { return (this.clientY || 0) + Math.floor(Math.random()*200) + 60; }
        });
    """)

    # ===== STEP 1: 深度分析登录页 =====
    print("[STEP 1] 分析首页", flush=True)
    page.goto(BASE, wait_until="networkidle", timeout=30000)
    time.sleep(5)
    page.screenshot(path=os.path.join(os.path.dirname(__file__), "ikuuu_v1_home.png"))
    
    body = page.evaluate("() => document.body?.innerText?.substring(0, 1000) || 'NONE'")
    print(f"   首页:\n{body[:800]}", flush=True)
    
    # 找所有链接和导航
    nav = page.evaluate("""() => {
        let links = Array.from(document.querySelectorAll('a[href]')).filter(a => {
            let t = (a.textContent||'').trim();
            return t && t.length < 50;
        }).map(a => ({t: (a.textContent||'').trim().substring(0,30), h: (a.href||'').substring(0,150)}));
        return links;
    }""")
    print(f"   导航({len(nav)}):")
    for l in nav[:20]:
        print(f"      [{l['t'][:25]:25s}] {l['h']}")

    # 找登录入口
    login_url = None
    for l in nav:
        if any(k in l['t'].lower() for k in ['登录','login','sign in']):
            login_url = l['h']
            break
    if not login_url:
        login_url = f"{BASE}/auth/login"
    
    print(f"\n[STEP 2] 进入登录页: {login_url}", flush=True)
    page.goto(login_url, wait_until="networkidle", timeout=20000)
    time.sleep(4)
    page.screenshot(path=os.path.join(os.path.dirname(__file__), "ikuuu_v1_login.png"))

    # 深度分析登录表单
    form = page.evaluate("""() => {
        let inputs = Array.from(document.querySelectorAll('input, select, button, textarea')).map(e => ({
            tag: e.tagName,
            name: e.name||'',
            type: e.type||'',
            placeholder: e.placeholder||'',
            id: e.id||'',
            options: e.tagName==='SELECT' ? Array.from(e.options||[]).map(o => ({t:o.text||'',v:o.value||''})) : [],
            textContent: (e.textContent||'').trim().substring(0,40)
        }));
        // Check for captcha
        let captchas = {
            turnstile: !!document.querySelector('[class*="turnstile"], iframe[src*="turnstile"], iframe[src*="cloudflare"]'),
            recaptcha: !!document.querySelector('[class*="g-recaptcha"], iframe[src*="recaptcha"], iframe[src*="google.com/recaptcha"]'),
            geetest: !!document.querySelector('[class*="geetest"], iframe[src*="geetest"]'),
            hcaptcha: !!document.querySelector('[class*="h-captcha"], iframe[src*="hcaptcha"]'),
            iframes: Array.from(document.querySelectorAll('iframe')).map(f => (f.src||'').substring(0,100))
        };
        return {inputs, captchas};
    }""")
    
    print(f"   表单字段:")
    for f in form['inputs']:
        print(f"      [{f['tag']}] name={f['name']:12s} type={f['type']:10s} placeholder={f['placeholder']:15s} id={f['id']} text={f['textContent'][:20]}")
        if f['options']:
            print(f"        options={f['options']}")
    
    print(f"   验证码检测: {form['captchas']}", flush=True)

    login_body = page.evaluate("() => document.body?.innerText?.substring(0, 800) || ''")
    print(f"   登录页文本:\n{login_body[:600]}", flush=True)
    
    # ===== STEP 3: 登录 =====
    print(f"\n[STEP 3] 登录", flush=True)
    
    # 填邮箱 - 检查是否有后缀选择
    email_inputs = [i for i in form['inputs'] if i['type'] in ('email','text') and ('邮箱' in i.get('placeholder','') or 'email' in (i['name'] or '').lower() or i['type']=='email')]
    pwd_inputs = [i for i in form['inputs'] if i['type']=='password']
    
    if email_inputs:
        for ei in email_inputs:
            try:
                if ei['name']:
                    sel = f'input[name="{ei["name"]}"]'
                elif ei['placeholder']:
                    sel = f'input[placeholder="{ei["placeholder"]}"]'
                else:
                    sel = 'input[type="email"], input[type="text"]'
                el = page.locator(sel).first
                if el.is_visible():
                    el.click(); time.sleep(0.2)
                    el.type(EMAIL, delay=70)
                    print(f"   填邮箱 ✓", flush=True)
                    break
            except: pass
    
    if pwd_inputs:
        for pi in pwd_inputs:
            try:
                if pi['name']:
                    sel = f'input[name="{pi["name"]}"]'
                else:
                    sel = 'input[type="password"]'
                el = page.locator(sel).first
                if el.is_visible():
                    el.click(); time.sleep(0.2)
                    el.type(PASSWORD, delay=70)
                    print(f"   填密码 ✓", flush=True)
                    break
            except: pass
    
    page.screenshot(path=os.path.join(os.path.dirname(__file__), "ikuuu_v1_filled.png"))
    
    # ===== STEP 4: Geetest绕过 =====
    print(f"\n[STEP 4] Geetest检测", flush=True)
    
    geetest_iframes = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('iframe')).filter(f => {
            let s = (f.src||'').toLowerCase();
            return s.includes('geetest') || s.includes('captcha') || s.includes('verify');
        }).map(f => ({src: f.src, visible: f.offsetParent !== null, width: f.offsetWidth, height: f.offsetHeight}));
    }""")
    print(f"   Geetest iframes: {geetest_iframes}", flush=True)
    
    # 找Geetest滑块/按钮区域
    geetest_elements = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('[class*="geetest"], [class*="captcha"], [class*="gt_"], [class*="slider"]')).slice(0,10).map(e => ({
            tag: e.tagName,
            className: (e.className||'').substring(0,60),
            id: e.id||'',
            visible: e.offsetParent !== null,
            text: (e.textContent||'').trim().substring(0,30),
            rect: (()=>{let r=e.getBoundingClientRect(); return {x:r.x,y:r.y,w:r.width,h:r.height};})()
        }));
    }""")
    print(f"   Geetest元素: {json.dumps(geetest_elements, ensure_ascii=False)}", flush=True)
    
    # 先尝试直接点登录（如果无Geetest）
    print(f"\n[STEP 5] 尝试登录", flush=True)
    try:
        page.locator('button[type="submit"], button:has-text("登录"), button:has-text("登入")').first.click()
        time.sleep(5)
        try: page.wait_for_load_state("networkidle", timeout=15000)
        except: pass
        
        print(f"   点击后URL: {page.url}", flush=True)
        after_text = page.evaluate("() => document.body?.innerText?.substring(0, 500) || ''")
        print(f"   响应: {after_text[:300]}", flush=True)
        page.screenshot(path=os.path.join(os.path.dirname(__file__), "ikuuu_v1_after_submit.png"))
        
        if "/user" in page.url or "/dashboard" in page.url.lower() or "仪表" in after_text:
            print(f"   ✅ 登录成功!", flush=True)
        elif "错误" in after_text or "error" in after_text.lower() or "失败" in after_text:
            print(f"   ❌ 失败", flush=True)
        elif "验证" in after_text or "captcha" in after_text.lower() or "滑块" in after_text:
            print(f"   ⚠️ 需要验证码!", flush=True)
            
            # Geetest绕过
            print(f"   尝试绕过Geetest...", flush=True)
            
            # 找iframe切换到Geetest上下文
            for frame in page.frames:
                url = frame.url
                if 'geetest' in url.lower() or 'captcha' in url.lower():
                    print(f"   进入Geetest frame: {url}", flush=True)
                    try:
                        # 在frame内找滑块
                        frame_body = frame.evaluate("() => document.body.innerHTML.substring(0, 500)")
                        print(f"   Frame内容: {frame_body[:200]}", flush=True)
                        
                        slider = frame.query_selector('.geetest_slider_button, .geetest_btn, .gt_slider_knob, [class*="slide"]')
                        if slider:
                            human_drag(frame.page, slider)
                            time.sleep(2)
                            body2 = page.evaluate("() => document.body?.innerText?.substring(0,300) || ''")
                            print(f"   拖拽后: {body2[:200]}", flush=True)
                    except Exception as e:
                        print(f"   Frame操作失败: {e}", flush=True)
            
            # 主页面找滑块
            slider_selectors = [
                '.geetest_slider_button', '.geetest_btn', '.gt_slider_knob',
                '[class*="geetest_slide"]', '.gt_slider', '[class*="slider"]'
            ]
            for sel in slider_selectors:
                slider = page.query_selector(sel)
                if slider and slider.is_visible():
                    print(f"   找到滑块: {sel}", flush=True)
                    human_drag(page, slider)
                    time.sleep(2)
                    break
    except Exception as e:
        print(f"   异常: {e}", flush=True)

    # ===== FINAL =====
    final_url = page.url
    final_text = page.evaluate("() => document.body?.innerText?.substring(0, 1000) || ''")
    print(f"\n   最终URL: {final_url}", flush=True)
    print(f"   最终文本:\n{final_text[:800]}", flush=True)
    page.screenshot(path=os.path.join(os.path.dirname(__file__), "ikuuu_v1_final.png"))

    print(f"\n✅ 完成!", flush=True)
    time.sleep(15)
    browser.close()
