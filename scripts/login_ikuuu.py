"""iKuuu登录 - Turnstile绕过+获取订阅"""
import os,sys,json,time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'turnstile-bypass'))
from playwright.sync_api import sync_playwright
from turnstile_patch import TURNSTILE_PATCH_SCRIPT

EMAIL = "kebukeyi2026@outlook.com"
PASSWORD = "VpnTest2026!"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, channel="msedge",
        args=["--disable-blink-features=AutomationControlled"])
    page = browser.new_page()
    page.set_viewport_size({"width": 1280, "height": 800})
    
    # 打开登录页
    print("Opening login page...")
    page.goto("https://ikuuu.win/auth/login", wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(3000)
    
    # 注入Turnstile bypass
    page.evaluate(TURNSTILE_PATCH_SCRIPT)
    print("Turnstile patch injected")
    
    # 关Telegram弹窗
    try:
        close_btn = page.query_selector("button:has-text('Close'), button:has-text('×')")
        if close_btn:
            close_btn.click()
            page.wait_for_timeout(500)
    except:
        pass
    
    page.wait_for_timeout(1000)
    
    # 填表
    email_input = page.query_selector("input[type='email']")
    pw_input = page.query_selector("input[type='password']")
    
    if email_input:
        email_input.fill(EMAIL)
        print(f"Filled email: {EMAIL}")
    else:
        print("No email input found!")
        browser.close()
        exit()
    
    if pw_input:
        pw_input.fill(PASSWORD)
        print("Filled password")
    
    page.wait_for_timeout(2000)
    
    # 等待Turnstile自动完成（managed类型，补丁注入后会自动过）
    print("Waiting for Turnstile...")
    for i in range(15):
        ts_state = page.evaluate("""
            (function() {
                try {
                    if (typeof turnstile !== 'undefined') {
                        var token = turnstile.getResponse();
                        if (token) return 'ready';
                    }
                } catch(e) {}
                var input = document.querySelector('input[name="cf-turnstile-response"]');
                if (input && input.value) return 'ready';
                return 'waiting';
            })()
        """)
        print(f"  Turnstile [{i+1}/15]: {ts_state}")
        if ts_state == 'ready':
            print("Turnstile passed!")
            break
        page.wait_for_timeout(2000)
    
    # 点击登录按钮
    page.wait_for_timeout(1000)
    clicked = page.evaluate("""
        (function() {
            var btns = document.querySelectorAll('button, input[type="submit"]');
            for (var i = 0; i < btns.length; i++) {
                var txt = btns[i].innerText || btns[i].value || '';
                if (txt.indexOf('登录') > -1 || txt.indexOf('登 录') > -1 
                    || btns[i].getAttribute('type') === 'submit') {
                    btns[i].click();
                    return 'clicked:' + txt.substring(0, 10);
                }
            }
            return 'not_found';
        })()
    """)
    print(f"Login button: {clicked}")
    page.wait_for_timeout(5000)
    
    print(f"\nURL: {page.url}")
    print(f"Title: {page.title()}")
    body = page.evaluate("document.body ? document.body.innerText.substring(0,400) : ''")
    print(f"Body: {body}")
    
    # 如果还在登录页，试试注册看账号是否已存在
    if '/login' in page.url or '/auth/login' in page.url:
        print("\nStill on login page. Account may not exist. Trying registration...")
        
        page.goto("https://ikuuu.win/auth/register", wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(2000)
        page.evaluate(TURNSTILE_PATCH_SCRIPT)
        page.wait_for_timeout(1000)
        
        # 换一个邮箱
        page.fill("input[type='email']", "bushuozaijian2026@outlook.com")
        try:
            page.fill("input#username, input[name='username'], input[placeholder*='昵称']", "bushuo")
        except: pass
        page.fill("input[type='password']:first-of-type", PASSWORD)
        try:
            page.fill("input[type='password']:nth-of-type(2)", PASSWORD)
        except: pass
        
        page.wait_for_timeout(1000)
        # 点击发送验证码
        send_btn = page.query_selector("button:has-text('发送')")
        if send_btn:
            send_btn.click()
            print("Sent verification code")
            page.wait_for_timeout(3000)
            
            # 轮询Outlook
            sys.path.insert(0, os.path.dirname(__file__))
            from outlook_code_reader import load_all_tokens, wait_for_code
            tokens = load_all_tokens()
            ti = tokens.get("bushuozaijian2026@outlook.com")
            if ti:
                code, err = wait_for_code("bushuozaijian2026@outlook.com", ti, timeout=60, interval=2)
                if code:
                    print(f"Code: {code}")
                    code_inp = page.query_selector("input#email_code, input[name='email_code']")
                    if code_inp:
                        code_inp.fill(code)
                    # 点击注册
                    page.evaluate("""
                        (function() {
                            var btns = document.querySelectorAll('button');
                            for (var i = 0; i < btns.length; i++) {
                                if (btns[i].innerText.indexOf('注册') > -1) { btns[i].click(); break; }
                            }
                        })()
                    """)
                    page.wait_for_timeout(5000)
                    print(f"After register URL: {page.url}")
                    print(f"Body: {page.evaluate('document.body ? document.body.innerText.substring(0,300) : \"\"')}")
    
    browser.close()
