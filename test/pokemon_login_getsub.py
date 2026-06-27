"""宝可梦机场登录+获取订阅链接 - Playwright版"""
from playwright.sync_api import sync_playwright
import re, json

EMAIL = "mallenbb9qdjidg9y5tw1yqd@outlook.com"
PASSWORD = "VpnTest2026!"
LOGIN_URL = "https://web4.52pokemon.cc/login"
DASHBOARD_URL = "https://web4.52pokemon.cc/dashboard"

with sync_playwright() as p:
    # 用Edge浏览器（和playwright-cli一样）
    browser = p.chromium.launch(headless=False, channel="msedge")
    page = browser.new_page()
    
    print("[1] 打开登录页...")
    page.goto(LOGIN_URL)
    page.wait_for_load_state("networkidle")
    print(f"    当前URL: {page.url}")
    print(f"    标题: {page.title()}")
    
    # 拦截剪贴板（页面加载后）
    clipboard_data = []
    page.evaluate("""
        var origDescriptor = Object.getOwnPropertyDescriptor(Navigator.prototype, 'clipboard');
        if (!navigator.clipboard) {
            Object.defineProperty(navigator, 'clipboard', {value: {}, configurable: true});
        }
        navigator.clipboard.writeText = function(text) {
            window.__captured_clipboard = text;
            console.log('CLIPBOARD_CAPTURED:', text);
            return Promise.resolve();
        };
    """)
    print("    剪贴板拦截已就绪")
    
    # 填邮箱
    print("[2] 填写邮箱...")
    email_input = page.locator('input[type="email"], input[placeholder*="邮箱"], input[placeholder*="电子邮件"], input').first
    email_input.fill(EMAIL)
    
    # 填密码
    print("[3] 填写密码...")
    password_input = page.locator('input[type="password"]').first
    password_input.fill(PASSWORD)
    
    # 点登录
    print("[4] 点击登录...")
    login_btn = page.get_by_role("button", name="登录")
    login_btn.click()
    
    # 等跳转
    page.wait_for_url("**/dashboard**", timeout=15000)
    print(f"    登录成功! 当前URL: {page.url}")
    
    # 找"复制通用订阅链接"按钮
    print("[5] 查找订阅链接按钮...")
    page.wait_for_selector('button:has-text("复制通用订阅链接")', timeout=10000)
    
    # 点按钮（剪贴板已被拦截）
    sub_btn = page.get_by_role("button", name="复制通用订阅链接")
    sub_btn.click()
    print("    已点击复制订阅链接按钮")
    
    # 读拦截的数据
    page.wait_for_timeout(1000)
    captured = page.evaluate("window.__captured_clipboard")
    print(f"\n    截获数据: {captured}")
    
    # 如果直接没截获，从network请求里找
    if not captured:
        print("[6] 从页面HTML搜索订阅链接...")
        html = page.content()
        urls = re.findall(r'(https?://[^"\'\\s<>]+)', html)
        for u in urls:
            if 'subscribe' in u.lower() or 'token=' in u.lower():
                print(f"    SUB URL: {u}")
    
    # 也尝试用API
    token = page.evaluate("localStorage.getItem('token')")
    print(f"\n    Token: {token}")
    
    # 用fetch获取订阅地址
    result = page.evaluate("""
        async () => {
            try {
                const resp = await fetch('/api/v1/user/getSubscribe', {
                    headers: {'Authorization': localStorage.getItem('token')}
                });
                const text = await resp.text();
                return text;
            } catch(e) {
                return 'Error: ' + e.message;
            }
        }
    """)
    print(f"    API getSubscribe: {result[:500]}")
    
    print("\n[DONE]")
    page.wait_for_timeout(2000)
    browser.close()
