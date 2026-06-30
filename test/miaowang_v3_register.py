#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""喵喵网络 注册+提取 V3 — 深度分析+Turnstile处理"""
import sys, os, time, io, re, json, random
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from playwright.sync_api import sync_playwright

EMAIL = f"miaogoog{random.randint(100,999)}@outlook.com"
PASSWORD = "VpnTest2026!"
REGISTER_URL = "https://www.miaonetwork.com/#/register?code=v3fkHXqC"

print("="*60)
print(f"  喵喵网络 V3: {EMAIL}")
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
        }
    """)
    
    try:
        print("\n[1] 打开注册页...", flush=True)
        page.goto(REGISTER_URL, wait_until="networkidle", timeout=25000)
        time.sleep(5)
        
        # 关闭弹窗
        print("[2] 处理弹窗...", flush=True)
        time.sleep(8)
        for _ in range(3):
            try:
                btn = page.locator('.popup-action-btn').first
                if btn.count() > 0 and btn.is_visible(timeout=2000):
                    btn.click()
                    print("   ✅ 弹窗关闭", flush=True)
                    time.sleep(1)
            except: pass
        
        # 深析所有iframe
        print("[3] 分析验证码...", flush=True)
        iframes = page.evaluate("""() => Array.from(document.querySelectorAll('iframe'))
            .map(f => ({src:f.src?.slice(0,100), id:f.id, className:f.className?.slice(0,50)}))""")
        print(f"   Iframes: {json.dumps(iframes, ensure_ascii=False)}", flush=True)
        
        # 检查Turnstile
        ts = page.query_selector('iframe[src*="turnstile"], iframe[src*="challenges.cloudflare"]')
        print(f"   Turnstile iframe: {ts is not None}", flush=True)
        
        # 截图
        page.screenshot(path=os.path.join(os.path.dirname(__file__), "miaowang_v3_prefill.png"))
        
        # 填表
        print("[4] 填表...", flush=True)
        page.locator('#email').first.fill(EMAIL); time.sleep(0.2)
        page.locator('#password').first.fill(PASSWORD); time.sleep(0.2)
        page.locator('#confirmPassword').first.fill(PASSWORD); time.sleep(0.3)
        
        # checkbox
        cb = page.locator('input[type="checkbox"]').first
        if cb.count() > 0: 
            try: cb.check(force=True)
            except: pass
            time.sleep(0.3)
        
        time.sleep(2)
        page.screenshot(path=os.path.join(os.path.dirname(__file__), "miaowang_v3_filled.png"))
        
        # 再检查iframe
        iframes2 = page.evaluate("""() => Array.from(document.querySelectorAll('iframe'))
            .map(f => ({src:f.src?.slice(0,100), id:f.id}))""")
        print(f"   Iframes after fill: {json.dumps(iframes2, ensure_ascii=False)}", flush=True)
        
        # 处理Turnstile
        ts2 = page.query_selector('iframe[src*="turnstile"], iframe[src*="challenges.cloudflare"]')
        if ts2:
            print("[5] Turnstile检测到, 尝试处理...", flush=True)
            try:
                frame = ts2.content_frame()
                if frame:
                    cb2 = frame.locator('[role="checkbox"], .cb-lb, label').first
                    if cb2.count() > 0:
                        cb2.click()
                        print("   ✅ Turnstile clicked", flush=True)
                        time.sleep(5)
            except Exception as e:
                print(f"   Turnstile click fail: {e}", flush=True)
        else:
            print("[5] 无Turnstile iframe — 可能DNS问题", flush=True)
        
        # 尝试提交
        print("[6] 尝试提交...", flush=True)
        reg_btn = page.locator('button:has-text("创建账户")').first
        if reg_btn.count() > 0 and reg_btn.is_visible():
            reg_btn.click()
            print("   ✅ 已点击", flush=True)
        
        time.sleep(8)
        try: page.wait_for_load_state("networkidle", timeout=15000)
        except: pass
        
        print(f"   结果URL: {page.url}", flush=True)
        body = page.evaluate("() => document.body.innerText")
        print(f"   结果(600):\n{body[:600]}", flush=True)
        page.screenshot(path=os.path.join(os.path.dirname(__file__), "miaowang_v3_result.png"))
        
        # 提取
        print("[7] 提取订阅...", flush=True)
        sub = page.evaluate("""async () => {
            window.__sub='';
            navigator.clipboard.writeText=function(t){window.__sub=t;return Promise.resolve();};
            let bs=document.querySelectorAll('button');
            for(let b of bs){if((b.textContent||'').includes('订阅')||(b.textContent||'').includes('Clash')){b.click();break;}}
            await new Promise(r=>setTimeout(r,800));
            let t=document.body.innerText;
            let m=t.match(/https?:\\/\\/[^\\s]+(?:subscribe|sub|token|link)[^\\s]+/i);
            return window.__sub||(m?m[0]:'');
        }""")
        print(f"   订阅: {sub or '未找到'}", flush=True)
        
        result = {"airport":"喵喵网络","panel":"miaonetwork.com","email":EMAIL,"password":PASSWORD,"sub":sub}
        with open(os.path.join(os.path.dirname(__file__), f"miaowang_{EMAIL.split('@')[0]}.json"), "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        time.sleep(20)
        
    except Exception as e:
        print(f"异常: {e}", flush=True)
        import traceback; traceback.print_exc()
        try: page.screenshot(path=os.path.join(os.path.dirname(__file__),"miaowang_v3_error.png"))
        except: pass
    finally:
        browser.close()
