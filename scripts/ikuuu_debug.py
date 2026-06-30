"""iKuuu Login - Debug Geetest captcha"""
import os, sys, time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'turnstile-bypass'))
from turnstile_patch import launch_with_turnstile_bypass, TURNSTILE_PATCH_SCRIPT

from playwright.sync_api import sync_playwright

EMAIL = "kebukeyi2026@outlook.com"
PASSWORD = "VpnTest2026!"

with sync_playwright() as p:
    browser = launch_with_turnstile_bypass(p, channel="msedge", headless=False)
    page = browser.new_page()
    page.set_viewport_size({"width": 1280, "height": 800})
    
    print("Opening iKuuu login page...")
    page.goto("https://ikuuu.win/auth/login", wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(3000)
    
    # Fill form
    email_input = page.query_selector("input[type='email']")
    pw_input = page.query_selector("input[type='password']")
    if email_input:
        email_input.fill(EMAIL)
    if pw_input:
        pw_input.fill(PASSWORD)
    page.wait_for_timeout(1000)
    
    # Take screenshot before clicking
    page.screenshot(path="C:/tmp/ikuuu_before_click.png")
    print("Screenshot saved: C:/tmp/ikuuu_before_click.png")
    
    # Check Geetest elements
    geetest_info = page.evaluate("""
        (function() {
            var info = {};
            info.hasGeetestBtn = !!document.querySelector('.geetest_btn_click');
            info.hasGeetestPanel = !!document.querySelector('.geetest_panel, .geetest_wind');
            info.hasVerifyInput = !!document.querySelector('[name="geetest_challenge"], [name="geetest_validate"], [name="geetest_seccode]');
            info.iframeCount = document.querySelectorAll('iframe').length;
            info.allBtns = [];
            var btns = document.querySelectorAll('button, [role="button"]');
            for (var i = 0; i < btns.length; i++) {
                info.allBtns.push({
                    tag: btns[i].tagName,
                    text: (btns[i].innerText || '').substring(0, 30),
                    class: (btns[i].className || '').substring(0, 50)
                });
            }
            return JSON.stringify(info);
        })()
    """)
    print(f"Geetest info: {geetest_info}")
    
    # Try to click Geetest button
    print("Clicking Geetest button...")
    page.evaluate("""
        (function() {
            var btn = document.querySelector('.geetest_btn_click');
            if (btn) {
                btn.click();
                return 'clicked';
            }
            return 'not_found';
        })()
    """)
    page.wait_for_timeout(5000)
    
    # Take screenshot after clicking
    page.screenshot(path="C:/tmp/ikuuu_after_click.png")
    print("Screenshot saved: C:/tmp/ikuuu_after_click.png")
    
    # Check state
    state = page.evaluate("""
        (function() {
            var text = document.body.innerText;
            if (text.indexOf('验证通过') > -1) return 'passed';
            if (text.indexOf('验证失败') > -1) return 'failed';
            return 'waiting';
        })()
    """)
    print(f"State after click: {state}")
    
    browser.close()
    print("Done!")
