"""iKuuu Login - Geetest bypass + Extract Subscribe URL"""
import os, sys, time, json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'turnstile-bypass'))
from turnstile_patch import TURNSTILE_PATCH_SCRIPT

from playwright.sync_api import sync_playwright

EMAIL = "kebukeyi2026@outlook.com"
PASSWORD = "VpnTest2026!"

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False, 
        channel="msedge",
        args=["--disable-blink-features=AutomationControlled"]
    )
    page = browser.new_page()
    page.set_viewport_size({"width": 1280, "height": 800})
    
    # Open login page
    print("Opening iKuuu login page...")
    page.goto("https://ikuuu.win/auth/login", wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(2000)
    
    # Inject Turnstile/Geetest bypass
    page.evaluate(TURNSTILE_PATCH_SCRIPT)
    print("Geetest bypass injected")
    
    # Fill form
    email_input = page.query_selector("input[type='email']")
    pw_input = page.query_selector("input[type='password']")
    
    if email_input:
        email_input.fill(EMAIL)
        print(f"Filled email: {EMAIL}")
    if pw_input:
        pw_input.fill(PASSWORD)
        print("Filled password")
    
    page.wait_for_timeout(1000)
    
    # Click verification button
    print("Clicking verification...")
    verify_clicked = page.evaluate("""
        (function() {
            var btn = document.querySelector('.geetest_btn_click');
            if (btn) { btn.click(); return 'clicked'; }
            // fallback: find by aria-label
            var btns = document.querySelectorAll('[aria-label*="验证"]');
            for (var i = 0; i < btns.length; i++) {
                btns[i].click();
                return 'clicked_fallback:' + btns[i].getAttribute('aria-label');
            }
            return 'not_found';
        })()
    """)
    print(f"Verify button: {verify_clicked}")
    
    # Wait for verification to complete
    print("Waiting for verification...")
    page.wait_for_timeout(5000)
    
    # Check verification state
    verify_state = page.evaluate("""
        (function() {
            var text = document.body.innerText;
            if (text.indexOf('验证通过') > -1) return 'passed';
            if (text.indexOf('验证失败') > -1) return 'failed';
            return 'waiting';
        })()
    """)
    print(f"Verification state: {verify_state}")
    
    # If verification passed, click login
    if verify_state == 'passed':
        print("Verification passed! Clicking login...")
        page.evaluate("""
            (function() {
                var btns = document.querySelectorAll('button');
                for (var i = 0; i < btns.length; i++) {
                    var txt = btns[i].innerText || '';
                    if (txt.trim() === '登录') {
                        btns[i].click();
                        return 'clicked_login';
                    }
                }
                return 'login_not_found';
            })()
        """)
        page.wait_for_timeout(5000)
    else:
        # Try clicking login anyway (maybe verification auto-passed)
        print("Trying login anyway...")
        page.evaluate("""
            (function() {
                var btns = document.querySelectorAll('button');
                for (var i = 0; i < btns.length; i++) {
                    var txt = btns[i].innerText || '';
                    if (txt.trim() === '登录') {
                        btns[i].click();
                        return 'clicked_login';
                    }
                }
                return 'login_not_found';
            })()
        """)
        page.wait_for_timeout(5000)
    
    # Check current URL
    current_url = page.url
    print(f"\nCurrent URL: {current_url}")
    print(f"Title: {page.title()}")
    
    # If we're on the dashboard, extract subscription link
    if '/user' in current_url or '/dashboard' in current_url:
        print("\n=== LOGIN SUCCESSFUL! ===")
        
        # Try to find subscription link
        page.wait_for_timeout(2000)
        
        # Method 1: Look for subscribe links in page
        sub_link = page.evaluate("""
            (function() {
                // Check localStorage
                var keys = Object.keys(localStorage);
                for (var i = 0; i < keys.length; i++) {
                    var val = localStorage.getItem(keys[i]);
                    if (val && (val.indexOf('subscribe') > -1 || val.indexOf('token') > -1)) {
                        return 'LS:' + keys[i] + '=' + val;
                    }
                }
                // Check sessionStorage
                var skeys = Object.keys(sessionStorage);
                for (var i = 0; i < skeys.length; i++) {
                    var val = sessionStorage.getItem(skeys[i]);
                    if (val && (val.indexOf('subscribe') > -1 || val.indexOf('token') > -1)) {
                        return 'SS:' + skeys[i] + '=' + val;
                    }
                }
                // Check for subscribe links in DOM
                var links = document.querySelectorAll('a');
                for (var i = 0; i < links.length; i++) {
                    if (links[i].href && links[i].href.indexOf('subscribe') > -1) {
                        return 'LINK:' + links[i].href;
                    }
                }
                return 'NOT_FOUND';
            })()
        """)
        print(f"Subscribe link: {sub_link}")
        
        # Method 2: Navigate to subscription page
        page.goto("https://ikuuu.win/user/subscribe", wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(3000)
        
        sub_url = page.evaluate("""
            (function() {
                var text = document.body.innerText;
                // Look for subscription URL pattern
                var match = text.match(/https?:\/\/[^\s]+subscribe[^\s]*/);
                if (match) return match[0];
                // Look for any URL in the page
                var links = document.querySelectorAll('a');
                for (var i = 0; i < links.length; i++) {
                    if (links[i].innerText && links[i].innerText.indexOf('订阅') > -1) {
                        return links[i].href;
                    }
                }
                return 'NOT_FOUND';
            })()
        """)
        print(f"Subscribe page link: {sub_url}")
        
        # Get full page text
        body = page.evaluate("document.body.innerText.substring(0,1000)")
        print(f"\nSubscribe page content:\n{body}")
    
    browser.close()
    print("\nDone!")
