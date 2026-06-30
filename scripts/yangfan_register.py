"""扬帆云注册 - 滑块验证+注册"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'turnstile-bypass'))
from turnstile_patch import TURNSTILE_PATCH_SCRIPT

from playwright.sync_api import sync_playwright

EMAIL = "yangfan_test_2026@gmail.com"
PASSWORD = "YangFan2026"

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,
        channel="msedge",
        args=["--disable-blink-features=AutomationControlled"]
    )
    page = browser.new_page()
    page.set_viewport_size({"width": 1280, "height": 800})
    
    # Open yangfan
    print("Opening Yangfan Cloud...")
    page.goto("https://yangfanhome.com/", wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(3000)
    
    # Handle slider
    print("Handling slider verification...")
    for i in range(5):
        body_text = page.evaluate("document.body.innerText.substring(0,200)")
        if '验证成功' in body_text or '验证通过' in body_text:
            print(f"  Verification passed on attempt {i+1}")
            break
        
        # Move slider
        page.evaluate("""
            (function() {
                var thumb = document.getElementById('sliderThumb');
                if (thumb) {
                    thumb.style.left = '260px';
                    var down = new MouseEvent('mousedown', {bubbles: true, button: 0});
                    thumb.dispatchEvent(down);
                    var move = new MouseEvent('mousemove', {bubbles: true});
                    thumb.dispatchEvent(move);
                    var up = new MouseEvent('mouseup', {bubbles: true});
                    thumb.dispatchEvent(up);
                    return 'moved';
                }
                return 'not_found';
            })()
        """)
        page.wait_for_timeout(2000)
        print(f"  Attempt {i+1}: moved slider")
    
    page.wait_for_timeout(3000)
    
    # Check where we are
    current_url = page.url
    print(f"\nCurrent URL: {current_url}")
    
    body = page.evaluate("document.body.innerText.substring(0,800)")
    print(f"\nPage content:\n{body}")
    
    # If we're on login/register page
    if 'login' in current_url or 'register' in current_url or 'auth' in current_url:
        # Fill registration form
        email_input = page.query_selector("input[type='email'], input[placeholder*='邮箱']")
        pw_input = page.query_selector("input[type='password']")
        
        if email_input:
            email_input.fill(EMAIL)
            print(f"\nFilled email: {EMAIL}")
        if pw_input:
            pw_input.fill(PASSWORD)
            print("Filled password")
        
        # Click register button
        register_btn = page.query_selector("button:has-text('注册'), input[type='submit'][value*='注册']")
        if register_btn:
            print("Clicking register button...")
            register_btn.click()
            page.wait_for_timeout(5000)
            
            print(f"\nAfter register URL: {page.url}")
            body = page.evaluate("document.body.innerText.substring(0,800)")
            print(f"Body: {body}")
    
    browser.close()
    print("\nDone!")
