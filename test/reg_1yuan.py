"""一元机场(扬帆云)注册脚本"""
import asyncio
from playwright.sync_api import sync_playwright

REG_URL = "https://a04.yfyn01.net/register?code=0WEO6ulk"
EMAIL = "mx9433499602@outlook.com"
PASSWORD = "VpnTest2026!"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, channel="msedge")
    context = browser.new_context()
    page = context.new_page()
    
    print("[1] 打开注册页...")
    page.goto(REG_URL, wait_until="networkidle")
    page.wait_for_timeout(3000)
    print(f"    URL: {page.url}")
    print(f"    Title: {page.title()}")
    
    print("[2] 填邮箱...")
    email_input = page.get_by_placeholder("请输入完整邮箱")
    email_input.fill(EMAIL)
    
    print("[3] 填密码...")
    pw_inputs = page.get_by_placeholder("*****")
    pw_inputs.first.fill(PASSWORD)
    pw_inputs.last.fill(PASSWORD)
    
    print("[4] 点创建账号...")
    page.get_by_role("button", name="创建账号").click()
    
    # 等待导航
    page.wait_for_timeout(5000)
    print(f"    跳转后URL: {page.url}")
    print(f"    跳转后标题: {page.title()}")
    
    # 检查是否需要验证码
    print("[5] 检查页面状态...")
    inner = page.evaluate("document.body.innerText")
    
    if "邮箱验证码" in inner or "验证码" in inner or "verification" in inner.lower():
        print("    需要验证码！")
        print(f"    页面内容: {inner[:500]}")
    elif "dashboard" in page.url.lower() or "登录" in inner:
        print("    ✓ 注册成功！进入仪表盘")
    else:
        print(f"    未知状态，页面内容: {inner[:300]}")
    
    # 保存localStorage
    print("[6] 提取账户信息...")
    data = page.evaluate("""() => {
        var result = {};
        for (var i = 0; i < localStorage.length; i++) {
            var k = localStorage.key(i);
            result[k] = localStorage.getItem(k);
        }
        return result;
    }""")
    print(f"    localStorage: {data}")
    
    # 检查subscribe_url
    sub_url = data.get("subscribe_url", "")
    if sub_url:
        print(f"\n    ✓ 订阅链接: {sub_url}")
    
    page.wait_for_timeout(2000)
    browser.close()
    print("完成")
