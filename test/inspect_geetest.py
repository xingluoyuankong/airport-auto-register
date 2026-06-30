"""快速检查Geetest实际DOM结构"""
import sys, os, time, io
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=False,
        args=["--ignore-certificate-errors", "--no-sandbox"])
    page = browser.new_page()
    
    print("加载注册页...", flush=True)
    page.goto("https://www.tanz.website/auth/register?code=ssfJ", wait_until="domcontentloaded", timeout=20000)
    time.sleep(3)
    
    # 填表
    page.locator('#name').first.fill("测试")
    page.locator('#email').first.fill("test")
    page.locator('#email_postfix').first.select_option('@qq.com')
    
    # 触发Geetest
    print("触发Geetest...", flush=True)
    try:
        page.locator('[class*="geetest_btn"]').first.click()
    except:
        page.locator('text=点击按钮进行验证').first.click()
    
    time.sleep(4)
    
    # 检查
    info = page.evaluate("""() => {
        let r = {};
        
        // Canvas
        let cans = document.querySelectorAll('canvas');
        r.canvasCount = cans.length;
        r.canvases = [];
        cans.forEach(function(c, i) {
            r.canvases.push({w: c.width, h: c.height, cls: c.className.toString().substring(0, 80)});
        });
        
        // Geetest元素
        let gels = document.querySelectorAll('[class*=geetest]');
        let classes = [];
        gels.forEach(function(e) {
            let c = e.className.toString().substring(0, 100);
            if (classes.indexOf(c) === -1 && classes.length < 30) classes.push(c);
        });
        r.classes = classes;
        
        // Img标签
        let imgs = document.querySelectorAll('img');
        r.imgCount = imgs.length;
        
        // Body文本截取(去掉非ASCII)
        r.bodyText = document.body.innerText.substring(0, 500).replace(/[^\\x00-\\x7F\\u4e00-\\u9fff]/g, '[?]');
        
        return r;
    }""")
    
    import json
    with open(os.path.join(os.path.dirname(__file__), "geetest_info.json"), "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=2)
    print("信息已保存到 geetest_info.json", flush=True)
    
    page.screenshot(path=os.path.join(os.path.dirname(__file__), "geetest_inspect.png"))
    print("截图保存", flush=True)
    
    time.sleep(5)
    browser.close()
