"""Wait for Cloudflare challenge and complete registration"""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    # Connect to existing browser
    browser = p.chromium.connect_over_cdp("http://localhost:3000")
    page = browser.pages[0]
    
    print("Waiting for Cloudflare challenge to complete...")
    for i in range(20):
        body = page.evaluate("document.body.innerText.substring(0,500)")
        if '安全验证' not in body and '请稍候' not in body:
            print(f"CF challenge passed after {i*5}s")
            break
        print(f"  Waiting... ({i*5}s)")
        page.wait_for_timeout(5000)
    
    # Check current state
    current_url = page.url
    print(f"\nCurrent URL: {current_url}")
    body = page.evaluate("document.body.innerText.substring(0,800)")
    print(f"\nPage content:\n{body}")
    
    browser.close()
