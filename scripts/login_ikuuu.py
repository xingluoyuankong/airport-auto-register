"""iKuuu登录 - 用Turnstile绕过补丁"""
import os,sys,json
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'turnstile-bypass'))

from playwright.sync_api import sync_playwright
from turnstile_patch import TURNSTILE_PATCH_SCRIPT

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, channel="msedge",
        args=["--disable-blink-features=AutomationControlled"])
    page = browser.new_page()
    
    # 打开登录页
    page.goto("https://ikuuu.win/auth/login", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3000)
    
    # 注入Turnstile bypass
    result = page.evaluate(TURNSTILE_PATCH_SCRIPT)
    print(f"Patch: {result}")
    page.wait_for_timeout(1000)
    
    # 填表
    page.fill("input[type='email']", "kebukeyi2026@outlook.com")
    page.fill("input[type='password']", "VpnTest2026!")
    page.wait_for_timeout(500)
    
    # 点击Turnstile验证框
    try:
        page.evaluate("""
            (function() {
                var iframe = document.querySelector('iframe[src*="challenges.cloudflare"]');
                if (iframe && iframe.contentDocument) {
                    var body = iframe.contentDocument.body;
                    if (body && body.shadowRoot) {
                        var cb = body.shadowRoot.querySelector('input[type="checkbox"]');
                        if (cb) cb.click();
                    }
                }
                var labels = document.querySelectorAll('.cf-turnstile label, [class*="turnstile"] label');
                if (labels.length > 0) labels[0].click();
            })();
        """)
    except:
        pass
    
    # 点击登录（iKuuu的按钮可能不在正常DOM中，用JS点击）
    page.wait_for_timeout(2000)
    page.evaluate("""(function() {
        var btns = document.querySelectorAll('button');
        for (var i = 0; i < btns.length; i++) {
            if (btns[i].innerText.indexOf('登录') > -1 || btns[i].innerText.indexOf('登 录') > -1) {
                btns[i].click();
                break;
            }
        }
    })()""")
    page.wait_for_timeout(5000)
    
    print(f"URL: {page.url}")
    print(f"Title: {page.title()}")
    body = page.evaluate("document.body ? document.body.innerText.substring(0,300) : ''")
    print(f"Body: {body}")
    
    browser.close()
