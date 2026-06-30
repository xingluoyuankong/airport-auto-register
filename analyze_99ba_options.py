import sys,io,time
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(channel="msedge",headless=False,
        args=["--proxy-server=http://127.0.0.1:7897","--ignore-certificate-errors","--no-sandbox"])
    ctx=b.new_context(viewport={"width":1280,"height":800},ignore_https_errors=True,locale="zh-CN")
    pg=ctx.new_page()
    pg.goto("https://a.99ba2026.fyi/#/register",wait_until="networkidle",timeout=45000)
    time.sleep(2)
    # 点开下拉框
    pg.click(".n-base-selection-label")
    time.sleep(1)
    # 找选项
    opts=pg.evaluate("""()=>{
        var r=[];
        document.querySelectorAll('[class*=n-base-select-option]').forEach(function(el){
            var t=el.textContent.trim();
            if(t && t.length<30) r.push(t);
        });
        return JSON.stringify(r,null,2);
    }""")
    print("OPTIONS:",opts)
    pg.screenshot(path="99ba_dropdown.png")
    b.close()
