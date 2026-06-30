import sys,io,time
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(channel="msedge",headless=False,
        args=["--proxy-server=http://127.0.0.1:7897","--ignore-certificate-errors","--no-sandbox"])
    ctx=b.new_context(viewport={"width":1280,"height":800},ignore_https_errors=True,locale="zh-CN")
    pg=ctx.new_page()
    pg.goto("https://flybit.vip/#/register",wait_until="networkidle",timeout=45000)
    time.sleep(2)
    
    # 点开Naive UI下拉框
    print("clicking n-base-selection-label...")
    pg.click(".n-base-selection-label")
    time.sleep(2)
    
    # 查看弹出的选项
    print("--- DROPDOWN OPTIONS ---")
    opts=pg.evaluate("""()=>{
        var results=[];
        // Naive UI popup通常在body末尾
        document.querySelectorAll('[class*=n-base-select-option], [class*=n-option]').forEach(function(el){
            results.push({text:el.textContent.trim(),cls:el.className});
        });
        // 也可能在n-base-select-menu里
        document.querySelectorAll('[class*=n-base-select-menu] [class*=option]').forEach(function(el){
            results.push({text:el.textContent.trim(),cls:el.className});
        });
        // 查找所有新出现的@元素
        document.querySelectorAll('body > div:last-child [class*=option]').forEach(function(el){
            results.push({text:el.textContent.trim(),cls:el.className});
        });
        return JSON.stringify(results,null,2);
    }""")
    print(opts[:3000])
    
    # 如果没有，查找body最后面的动态弹出元素
    if not opts or len(opts)<3:
        print("\n--- BODY LAST CHILD ---")
        last=pg.evaluate("""()=>{
            var body=document.body;
            var lastChildren=[];
            for(var i=Math.max(0,body.children.length-5);i<body.children.length;i++){
                var el=body.children[i];
                lastChildren.push({tag:el.tagName,cls:el.className,html:el.outerHTML.substring(0,500)});
            }
            return JSON.stringify(lastChildren,null,2);
        }""")
        print(last[:3000])
    
    pg.screenshot(path="flybit_dropdown_open.png")
    b.close()
