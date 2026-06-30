#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""iKuuu 登录+提取 — Geetest人机验证"""
import sys, os, time, io, re, json, random, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from playwright.sync_api import sync_playwright

EMAIL = "kebukeyi2026@outlook.com"
PASSWORD = "VpnTest2026!"
BASE = "https://ikuu.win"

def human_drag(page, slider, dist=260):
    box = slider.bounding_box()
    if not box: return False
    sx,sy = box['x']+box['width']/2, box['y']+box['height']/2
    page.mouse.move(sx,sy)
    time.sleep(random.uniform(0.05,0.15))
    page.mouse.down()
    time.sleep(random.uniform(0.03,0.08))
    steps=40
    for i in range(steps):
        p = (i+1)/steps
        eased = 1-(1-p)**3
        nx = sx + dist*eased + random.uniform(-2,2)
        ny = sy + random.uniform(-3,3)
        page.mouse.move(nx,ny)
        time.sleep(random.uniform(0.003,0.012))
    page.mouse.up()
    time.sleep(0.5)
    return True

print("="*60)
print("  iKuuu 登录+提取")
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
        if(window.MouseEvent && MouseEvent.prototype) {
            Object.defineProperty(MouseEvent.prototype,'screenX',{
                get:function(){return (this.clientX||0)+Math.floor(Math.random()*400)+80;}
            });
            Object.defineProperty(MouseEvent.prototype,'screenY',{
                get:function(){return (this.clientY||0)+Math.floor(Math.random()*200)+60;}
            });
        }
    """)
    
    try:
        print("\n[1] 打开首页...", flush=True)
        page.goto(f"{BASE}/", wait_until="networkidle", timeout=25000)
        time.sleep(3)
        body = page.evaluate("() => document.body.innerText")
        print(f"   URL: {page.url}", flush=True)
        print(f"   标题: {page.title()}", flush=True)
        print(f"   文本(600): {body[:600]}", flush=True)
        page.screenshot(path=os.path.join(os.path.dirname(__file__),"ikuuu_v2_home.png"))
        
        # 找登录链接
        links = page.evaluate("""() => Array.from(document.querySelectorAll('a[href]'))
            .filter(a => a.href && a.href.includes('http'))
            .slice(0,30)
            .map(a => ({t:(a.textContent||'').trim().slice(0,40), h:a.href.slice(0,200)}))""")
        print(f"   链接: {links}", flush=True)
        
        inputs = page.evaluate("""() => Array.from(document.querySelectorAll('input'))
            .map(i => ({type:i.type, name:i.name, id:i.id, pl:i.placeholder}))""")
        print(f"   Inputs: {inputs}", flush=True)
        
        # 导航登录页
        print("\n[2] 登录...", flush=True)
        for lp in ["/auth/login","/login","/user"]:
            try:
                page.goto(f"{BASE}{lp}", wait_until="networkidle", timeout=15000)
                time.sleep(3)
                body = page.evaluate("() => document.body.innerText")
                print(f"   {lp}(300): {body[:300]}", flush=True)
                if "邮箱" in body or "密码" in body or "email" in body.lower():
                    print(f"   ✅ 登录页: {page.url}", flush=True)
                    break
            except:
                print(f"   {lp}: fail", flush=True)
        
        inputs2 = page.evaluate("""() => Array.from(document.querySelectorAll('input'))
            .map(i => ({type:i.type, name:i.name, id:i.id, pl:i.placeholder}))""")
        print(f"   登录页Inputs: {inputs2}", flush=True)
        
        # 填表
        em = page.locator('input[name="email"], input[type="email"], #email').first
        pw = page.locator('input[name="passwd"], input[name="password"], #passwd, #password, input[type="password"]').first
        
        if em.count() > 0:
            em.click(); time.sleep(0.1); em.fill(EMAIL); time.sleep(0.3)
        if pw.count() > 0:
            pw.click(); time.sleep(0.1); pw.fill(PASSWORD); time.sleep(0.5)
        
        page.screenshot(path=os.path.join(os.path.dirname(__file__),"ikuuu_v2_filled.png"))
        
        # 检查Geetest
        geetest_btn = page.query_selector('.geetest_btn_click, [class*="geetest_btn"]')
        if geetest_btn:
            print("   需要Geetest验证", flush=True)
            geetest_btn.click()
            time.sleep(2)
            slider = page.query_selector('.geetest_slider_button, .gt_slider_knob')
            if slider and slider.is_visible():
                for attempt in range(3):
                    print(f"   滑第{attempt+1}次...", flush=True)
                    human_drag(page, slider, random.randint(200,240))
                    time.sleep(2)
                    ok = page.evaluate("() => document.querySelector('.geetest_success,.gt_success,.geetest_validate') != null")
                    if ok:
                        print("   ✅ Geetest通过!", flush=True)
                        break
        
        # 提交
        btn = page.locator('button:has-text("登录"), button[type="submit"]').first
        if btn.count() > 0:
            btn.click()
            time.sleep(5)
            try: page.wait_for_load_state("networkidle", timeout=15000)
            except: pass
        
        print(f"   登录后URL: {page.url}", flush=True)
        body = page.evaluate("() => document.body.innerText")
        print(f"   页面(500): {body[:500]}", flush=True)
        page.screenshot(path=os.path.join(os.path.dirname(__file__),"ikuuu_v2_after_login.png"))
        
        # 提取订阅
        print("\n[3] 提取...", flush=True)
        for sp in ["/user","/user/subscribe"]:
            try:
                page.goto(f"{BASE}{sp}", wait_until="networkidle", timeout=15000)
                time.sleep(3)
                body = page.evaluate("() => document.body.innerText")
                urls = re.findall(r'https?://[^\s]+(?:subscribe|sub|token|link)[^\s]*', body)
                if urls:
                    print(f"   ✅ {sp}: {urls[0]}", flush=True)
                    break
                print(f"   {sp}(300): {body[:300]}", flush=True)
            except:
                pass
        
        # 剪贴板劫持
        page.goto(f"{BASE}/user", wait_until="networkidle", timeout=15000)
        time.sleep(3)
        sub = page.evaluate("""async () => {
            window.__sub=''; 
            navigator.clipboard.writeText=function(t){window.__sub=t;return Promise.resolve();}; 
            let bs=document.querySelectorAll('button'); 
            for(let b of bs){if((b.textContent||'').includes('订阅')||(b.textContent||'').includes('Clash')){b.click();break;}} 
            await new Promise(r=>setTimeout(r,800)); 
            return window.__sub||'';
        }""")
        print(f"   剪贴板: {sub}", flush=True)
        
        time.sleep(30)
        
    except Exception as e:
        print(f"异常: {e}", flush=True)
        import traceback; traceback.print_exc()
    finally:
        browser.close()
