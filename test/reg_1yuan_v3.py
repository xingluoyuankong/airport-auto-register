"""一元机场注册 v3 - 设referrer直连扬帆云"""
from playwright.sync_api import sync_playwright

EMAIL = "mx9433499602@outlook.com"
PASSWORD = "VpnTest2026!"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, channel="msedge")
    context = browser.new_context()
    page = context.new_page()
    
    # 先访问1rmb.org获取referrer上下文
    print("[1] 先访问1rmb.org获取上下文...")
    page.goto("https://1rmb.org", wait_until="networkidle")
    print(f"    URL: {page.url}")
    
    # 然后用同一个页面直接导航到注册页面
    print("[2] 导航到扬帆云注册页（带code）...")
    page.goto("https://a04.yfyn01.net/register?code=0WEO6ulk", 
              wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(5000)
    print(f"    跳转后URL: {page.url}")
    print(f"    标题: {page.title()}")
    
    inner = page.evaluate("document.body.innerText")[:500]
    print(f"    内容: {inner[:300]}")
    
    if "login" in page.url.lower():
        print("[!] 被踢回登录。尝试另类方法：用add_init_script设置referrer")
        # 尝试新标签页方案
        page2 = context.new_page()
        page2.goto("https://a04.yfyn01.net/register?code=0WEO6ulk", 
                   wait_until="networkidle", timeout=15000)
        page2.wait_for_timeout(5000)
        print(f"    新标签URL: {page2.url}")
        inner2 = page2.evaluate("document.body.innerText")[:500]
        print(f"    新标签内容: {inner2[:300]}")
        
        if "创建账号" in inner2 or "注册" in inner2:
            page = page2
            inner = inner2
    
    if "创建账号" in inner or "注册" in inner:
        print("[3] 填表...")
        try:
            page.get_by_placeholder("请输入完整邮箱").fill(EMAIL, timeout=5000)
            print(f"    邮箱已填")
        except:
            print("    !找不到邮箱输入框")
        
        try:
            pw_boxes = page.get_by_placeholder("*****")
            pw_boxes.first.fill(PASSWORD, timeout=5000)
            pw_boxes.last.fill(PASSWORD, timeout=5000)
            print(f"    密码已填")
        except:
            print("    !找不到密码输入框")
        
        print("[4] 点创建账号...")
        try:
            page.get_by_role("button", name="创建账号").click(timeout=5000)
            page.wait_for_timeout(8000)
            print(f"    跳转后URL: {page.url}")
            result = page.evaluate("document.body.innerText")
            print(f"    结果: {result[:500]}")
        except Exception as e:
            print(f"    !点击失败: {e}")
    
    # 提取localStorage
    ls = page.evaluate("""() => {
        var r = {};
        for (var i = 0; i < localStorage.length; i++) {
            var k = localStorage.key(i);
            r[k] = localStorage.getItem(k);
        }
        return r;
    }""")
    print(f"\n[Info] localStorage: {ls}")
    
    sub = ls.get("subscribe_url", "")
    token = ls.get("token", "")
    if sub:
        print(f"\n✓ 订阅链接: {sub}")
    if token:
        print(f"Token: {token}")
    
    page.wait_for_timeout(2000)
    browser.close()
    print("完成")
