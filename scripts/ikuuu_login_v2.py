"""iKuuu Login - Using Chrome Extension for Geetest bypass"""
import os, sys, time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'turnstile-bypass'))
from turnstile_patch import launch_with_turnstile_bypass, click_turnstile_sync, TURNSTILE_PATCH_SCRIPT

from playwright.sync_api import sync_playwright

EMAIL = "kebukeyi2026@outlook.com"
PASSWORD = "VpnTest2026!"

with sync_playwright() as p:
    # Launch with Chrome extension
    print("Launching browser with Turnstile bypass extension...")
    browser = launch_with_turnstile_bypass(p, channel="msedge", headless=False)
    page = browser.new_page()
    page.set_viewport_size({"width": 1280, "height": 800})
    
    # Open login page
    print("Opening iKuuu login page...")
    page.goto("https://ikuuu.win/auth/login", wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(3000)
    
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
    
    # Try to click Geetest button using JavaScript
    print("Clicking Geetest verification...")
    for attempt in range(3):
        result = page.evaluate("""
            (function() {
                // Try to find and click Geetest button
                var btns = document.querySelectorAll('[class*="geetest"]');
                for (var i = 0; i < btns.length; i++) {
                    if (btns[i].classList.contains('geetest_btn_click')) {
                        btns[i].click();
                        return 'clicked_geetest';
                    }
                }
                // Try by aria-label
                var allBtns = document.querySelectorAll('[aria-label*="验证"]');
                for (var i = 0; i < allBtns.length; i++) {
                    allBtns[i].click();
                    return 'clicked_aria';
                }
                return 'not_found';
            })()
        """)
        print(f"  Attempt {attempt+1}: {result}")
        page.wait_for_timeout(3000)
        
        # Check if verification passed
        state = page.evaluate("""
            (function() {
                var text = document.body.innerText;
                if (text.indexOf('验证通过') > -1) return 'passed';
                if (text.indexOf('验证失败') > -1) return 'failed';
                return 'waiting';
            })()
        """)
        print(f"  State: {state}")
        if state == 'passed':
            break
    
    # Click login button
    print("\nClicking login button...")
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
        page.wait_for_timeout(3000)
        
        # Get page content
        body = page.evaluate("document.body.innerText.substring(0,2000)")
        print(f"\nDashboard content:\n{body}")
        
        # Look for subscription link
        sub_link = page.evaluate("""
            (function() {
                var links = document.querySelectorAll('a');
                for (var i = 0; i < links.length; i++) {
                    var href = links[i].href || '';
                    var text = links[i].innerText || '';
                    if (href.indexOf('subscribe') > -1 || text.indexOf('订阅') > -1) {
                        return 'LINK:' + href + ' | ' + text;
                    }
                }
                return 'NOT_FOUND';
            })()
        """)
        print(f"\nSubscribe link: {sub_link}")
        
        # Try to navigate to user/subscribe page
        page.goto("https://ikuuu.win/user/subscribe", wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(3000)
        
        sub_body = page.evaluate("document.body.innerText.substring(0,2000)")
        print(f"\nSubscribe page content:\n{sub_body}")
    
    browser.close()
    print("\nDone!")
