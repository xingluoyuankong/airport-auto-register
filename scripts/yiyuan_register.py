"""一元机场注册 - Cloudflare绕过"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'turnstile-bypass'))
from turnstile_patch import TURNSTILE_PATCH_SCRIPT

from playwright.sync_api import sync_playwright

EMAIL_PREFIX = "yiyuan_test_2026"
PASSWORD = "Yiyuan2026"

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,
        channel="msedge",
        args=["--disable-blink-features=AutomationControlled"]
    )
    page = browser.new_page()
    page.set_viewport_size({"width": 1280, "height": 800})
    
    # Open yiyuan
    print("Opening Yiyuan Airport...")
    page.goto("https://yiyuan.co/", wait_until="commit", timeout=30000)
    page.wait_for_timeout(10000)  # Wait for CF challenge
    
    # Inject Turnstile patch
    page.evaluate(TURNSTILE_PATCH_SCRIPT)
    print("Turnstile patch injected")
    
    # Check if CF passed
    body = page.evaluate("document.body.innerText.substring(0,500)")
    print(f"\nPage state:\n{body}")
    
    # If still on CF page, wait more
    if '安全验证' in body or '请稍候' in body:
        print("Waiting for Cloudflare challenge...")
        page.wait_for_timeout(15000)
        body = page.evaluate("document.body.innerText.substring(0,500)")
        print(f"After wait:\n{body}")
    
    # Check current URL
    current_url = page.url
    print(f"\nCurrent URL: {current_url}")
    
    # If we're past CF, look for register button
    if 'register' in current_url or 'login' in current_url:
        print("Found register/login page!")
    else:
        # Try to find register link
        register_link = page.evaluate("""
            (function() {
                var links = document.querySelectorAll('a');
                for (var i = 0; i < links.length; i++) {
                    if (links[i].innerText.indexOf('注册') > -1 || links[i].innerText.indexOf('Register') > -1) {
                        return links[i].href;
                    }
                }
                return 'not_found';
            })()
        """)
        print(f"Register link: {register_link}")
        if register_link != 'not_found':
            page.goto(register_link, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(3000)
    
    browser.close()
    print("\nDone!")
