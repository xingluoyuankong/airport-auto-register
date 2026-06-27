"""一元机场注册 v2 - 从1rmb.org跟随c.jichangs.com重定向"""
import asyncio
from playwright.sync_api import sync_playwright

EMAIL = "mx9433499602@outlook.com"
PASSWORD = "VpnTest2026!"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, channel="msedge")
    context = browser.new_context()
    page = context.new_page()
    
    print("[1] 打开1rmb.org...")
    page.goto("https://1rmb.org", wait_until="networkidle")
    
    print("[2] 找注册链接...")
    reg_link = page.locator('a[href*="c.jichangs.com/1yuan"]').first
    if reg_link.count() > 0:
        print(f"    找到: {reg_link.text_content()}")
        href = reg_link.get_attribute("href")
        print(f"    href: {href}")
        
        # 直接navigate到href（让浏览器处理重定向）
        print("[3] 导航到注册面板...")
        page.goto(href, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(5000)
        print(f"    URL: {page.url}")
        print(f"    Title: {page.title()}")
    else:
        print("    未找到注册链接！")
        browser.close()
        exit()
    
    # 检查当前页面
    inner = page.evaluate("document.body.innerText")[:500]
    print(f"    页面内容: {inner[:300]}")
    
    if "login" in page.url.lower():
        print("[4] 被踢到登录页！尝试点击注册链接...")
        reg_links = page.locator('a[href*="register"]')
        if reg_links.count() > 0:
            print(f"    找到{reg_links.count()}个注册链接")
            # 用完整的注册URL（含code）
            page.goto("https://a04.yfyn01.net/register?code=0WEO6ulk", wait_until="domcontentloaded")
            page.wait_for_timeout(3000)
            print(f"    跳转后URL: {page.url}")
    
    inner = page.evaluate("document.body.innerText")[:500]
    print(f"    当前页面: {inner[:300]}")
    
    # 如果还在注册页
    if "创建账号" in inner:
        print("[5] 填表注册...")
        page.get_by_placeholder("请输入完整邮箱").fill(EMAIL)
        pw_boxes = page.get_by_placeholder("*****")
        pw_boxes.first.fill(PASSWORD)
        pw_boxes.last.fill(PASSWORD)
        
        print("[6] 点创建账号...")
        page.get_by_role("button", name="创建账号").click()
        page.wait_for_timeout(5000)
        
        print(f"    URL: {page.url}")
        inner2 = page.evaluate("document.body.innerText")
        print(f"    结果: {inner2[:500]}")
        
        # 提取订阅
        sub = page.evaluate("localStorage.getItem('subscribe_url')")
        if sub:
            print(f"\n    ✓ 订阅链接: {sub}")
        
        # 提取token  
        token = page.evaluate("localStorage.getItem('token')")
        if token:
            print(f"    Token: {token}")
    elif "注册" in inner and "邮箱" in inner:
        print("[5] 已在注册页，直接填表...")
        page.get_by_placeholder("请输入完整邮箱").fill(EMAIL)
        pw_boxes = page.get_by_placeholder("*****")
        pw_boxes.first.fill(PASSWORD)
        pw_boxes.last.fill(PASSWORD)
        page.get_by_role("button", name="创建账号").click()
        page.wait_for_timeout(5000)
        print(f"    URL: {page.url}")
    else:
        print("    未知页面状态")
    
    page.wait_for_timeout(3000)
    browser.close()
    print("完成")
