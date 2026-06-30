#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COCODUCK 注册机 — Graph API版
面板: cocoduck.cc  免费: 有试用  系统: 待逆向
订阅域名: sub.cocoduck.cc
用法: python register_cocoduck.py [email] [password]
"""
import sys, os, json, time, io
try: sys.stdout.reconfigure(encoding='utf-8')
except: sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8') if hasattr(sys.stdout,'buffer') else open('CONOUT$','w',encoding='utf-8')
from playwright.sync_api import sync_playwright
from graph_mail import wait_for_code

def run(email_addr, reg_password):
    print(f"\n{'='*60}\n  COCODUCK 注册  邮箱: {email_addr}\n{'='*60}", flush=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=False,
            args=["--proxy-server=http://127.0.0.1:7897","--ignore-certificate-errors",
                  "--disable-blink-features=AutomationControlled","--no-sandbox"])
        ctx = browser.new_context(viewport={"width":1280,"height":800},
            ignore_https_errors=True, locale="zh-CN")
        page = ctx.new_page()
        page.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>false})")
        
        try:
            # 1. 探测注册页
            print("[1/7] 探测COCODUCK注册页...", flush=True)
            for url in ["https://cocoduck.cc/#/register","https://www.cocoduck.cc/#/register"]:
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=20000)
                    time.sleep(2)
                    break
                except: continue
            page.screenshot(path=os.path.join(os.path.dirname(__file__),"screenshot_cocoduck_landing.png"))
            txt = page.evaluate("()=>document.body.innerText")[:500]
            print(f"  页面: {txt[:200]}", flush=True)
            
            # Cloudflare处理
            cf = page.query_selector('iframe[src*="challenges.cloudflare.com"]')
            if cf:
                print("[Turnstile] 等待(60s)...", flush=True)
                dl = time.time()+60
                while time.time()<dl:
                    if not page.query_selector('iframe[src*="challenges.cloudflare.com"]'): break
                    time.sleep(2)
            
            # 2. 填表
            print("[2/7] 填表...", flush=True)
            has_email = page.query_selector('input[type="email"], input[name="email"], input[placeholder*="邮箱"]')
            if not has_email:
                print("  无注册表单, 可能自动跳转登录页", flush=True)
                # 尝试点"注册"链接
                for a in page.query_selector_all('a'):
                    t = (a.inner_text() or '').strip()
                    if '注册' in t or 'Register' in t:
                        try: a.click(); time.sleep(3); break
                        except: pass
            
            page.fill('input[type="email"], input[name="email"], input[placeholder*="邮箱"]', email_addr)
            pws = page.query_selector_all('input[type="password"]')
            if pws:
                pws[0].fill(reg_password)
                if len(pws)>=2: pws[1].fill(reg_password)
            
            # 3. 发验证码
            print("[3/7] 发送验证码...", flush=True)
            send = page.query_selector('button:has-text("发送")')
            if send: send.click(); time.sleep(2)
            else:
                reg = page.query_selector('button:has-text("注册")')
                if reg: reg.click(); time.sleep(2)
            
            # 4. 收码
            print("[4/7] Graph API收码...", flush=True)
            code, err = wait_for_code(email_addr, timeout=90)
            if not code:
                page.screenshot(path=os.path.join(os.path.dirname(__file__),"debug_cocoduck_no_code.png"))
                print(f"  失败: {err}", flush=True)
                browser.close(); return None
            print(f"  验证码: {code}", flush=True)
            
            # 5. 提交
            print("[5/7] 提交...", flush=True)
            ci = page.query_selector('input[name="email_code"], input[placeholder*="验证码"]')
            if ci:
                ci.fill(code); time.sleep(1)
                sub = page.query_selector('button:has-text("注册"), button[type="submit"]')
                if sub: sub.click(); time.sleep(4)
            
            # 6. 登录
            print("[6/7] 确保登录...", flush=True)
            page.wait_for_load_state("networkidle", timeout=15000)
            if "/#/register" in page.url or "/login" in page.url:
                base = "/".join(page.url.split("/")[:3])
                page.goto(f"{base}/#/login", wait_until="networkidle", timeout=15000)
                time.sleep(2)
                ei = page.query_selector_all('input[type="email"], input[name="email"]')
                if ei: ei[0].fill(email_addr)
                pi = page.query_selector_all('input[type="password"]')
                if pi: pi[0].fill(reg_password)
                lb = page.query_selector('button:has-text("登录"), button[type="submit"]')
                if lb: lb.click(); time.sleep(4)
            
            # 7. 提取订阅 — 多方法
            print("[7/7] 多方法提取订阅...", flush=True)
            sub_url = ""
            
            # 方法1: V2Board
            sub_url = page.evaluate("""
                (async()=>{let r=localStorage.getItem('VUE_NAIVE_ACCESS_TOKEN');if(!r)return'';
                let t='';try{let p=JSON.parse(r);t=p.value||p.token||''}catch(e){t=r}
                if(!t||t.length<10)return'';
                let resp=await fetch('/api/v1/user/getSubscribe',{headers:{'Authorization':t}});
                let d=await resp.json();
                return(d&&d.data&&d.data.subscribe_url)||(d&&d.subscribe_url)||'';})()
            """)
            
            # 方法2: 遍历localStorage
            if not sub_url:
                sub_url = page.evaluate("""
                    (()=>{for(let i=0;i<localStorage.length;i++){
                        let v=localStorage.getItem(localStorage.key(i));
                        if(!v)continue;
                        if(v.includes&&v.includes('/api/v1/client/subscribe'))return v;
                        try{let p=JSON.parse(v);if(p.subscribe_url)return p.subscribe_url}catch(e){}
                    }return''})()
                """)
            
            # 方法3: 打开用户中心找
            if not sub_url:
                base = "/".join(page.url.split("/")[:3])
                page.goto(f"{base}/#/user", wait_until="networkidle", timeout=10000)
                time.sleep(2)
                page.screenshot(path=os.path.join(os.path.dirname(__file__),"screenshot_cocoduck_user.png"))
                sub_url = page.evaluate("""
                    (()=>{let m=document.body.innerText.match(/https?:\\/\\/[^\\s]+(?:subscribe|sub)[^\\s]+/i);return m?m[0]:''})()
                """)
            
            print(f"\n  订阅: {sub_url or '(未找到，需手动提取)'}", flush=True)
            result = {"airport":"COCODUCK","panel":"cocoduck.cc","email":email_addr,
                      "password":reg_password,"subscribe_url":sub_url,"system":"待确认"}
            os.makedirs(os.path.join(os.path.dirname(__file__),"register_results"), exist_ok=True)
            with open(os.path.join(os.path.dirname(__file__),"register_results",
                      f"cocoduck_{email_addr.split('@')[0]}.json"),"w",encoding="utf-8") as f:
                json.dump(result,f,ensure_ascii=False,indent=2)
            return sub_url
        except Exception as e:
            print(f"  异常: {e}", flush=True)
            return None
        finally:
            browser.close()

if __name__ == "__main__":
    EMAIL = sys.argv[1] if len(sys.argv)>1 else "mxih36u8zfmxj42v75fid@outlook.com"
    REG = sys.argv[2] if len(sys.argv)>2 else "VpnTest2026!"
    sub = run(EMAIL, REG)
    print(f"\n{'[SUB] '+sub if sub else 'FAIL 失败'}")
    sys.exit(0 if sub else 1)
