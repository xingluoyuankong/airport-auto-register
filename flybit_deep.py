import sys,io,time
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(channel="msedge",headless=False,
        args=["--proxy-server=http://127.0.0.1:7897","--ignore-certificate-errors","--no-sandbox"])
    ctx=b.new_context(viewport={"width":1280,"height":800},ignore_https_errors=True,locale="zh-CN")
    pg=ctx.new_page()
    pg.goto("https://flybit.vip/#/register",wait_until="networkidle",timeout=45000)
    time.sleep(3)
    
    # 深度DOM分析
    print("=== DEEP DOM ANALYSIS ===")
    
    # 1. 找所有email相关的输入框
    print("\n--- EMAIL INPUTS ---")
    for el in pg.query_selector_all("input"):
        html=el.evaluate("el=>el.outerHTML")
        if "email" in html.lower() or "mail" in html.lower() or "邮箱" in html:
            print(html[:200])
    
    # 2. 找包含@qq.com的元素(可能是自定义下拉框)
    print("\n--- @qq.com ELEMENTS ---")
    els_with_qq=pg.evaluate("""()=>{
        var walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
        var results=[];
        while(walker.nextNode()){
            var node=walker.currentNode;
            if(node.textContent.includes('@qq.com')||node.textContent.includes('@outlook.com')){
                var el=node.parentElement;
                results.push({tag:el.tagName,cls:el.className,html:el.outerHTML.substring(0,200),text:node.textContent.trim()});
            }
        }
        return JSON.stringify(results,null,2);
    }""")
    print(els_with_qq[:2000])
    
    # 3. 找所有下拉/选择类组件 (不限于select)
    print("\n--- DROPDOWN COMPONENTS ---")
    dropdowns=pg.evaluate("""()=>{
        var results=[];
        // select元素
        document.querySelectorAll('select').forEach(function(s){
            results.push({type:'select',html:s.outerHTML.substring(0,200),
                options:Array.from(s.options).map(function(o){return o.value})});
        });
        // 带dropdown/select类的元素
        document.querySelectorAll('[class*=dropdown],[class*=select],[class*=picker],[class*=chooser]').forEach(function(el){
            results.push({type:'class-match',tag:el.tagName,cls:el.className,html:el.outerHTML.substring(0,300)});
        });
        // 包含@符号的span/div(可能是当前选中的邮箱域)
        document.querySelectorAll('span,div,li').forEach(function(el){
            var t=el.textContent||'';
            if(/^@[a-z]/.test(t.trim()) && t.trim().length<20){
                results.push({type:'email-suffix',tag:el.tagName,cls:el.className,text:t.trim(),html:el.outerHTML.substring(0,200)});
            }
        });
        return JSON.stringify(results,null,2);
    }""")
    print(dropdowns[:3000])
    
    # 4. 全页面文字分析
    print("\n--- FULL PAGE TEXT ---")
    print(pg.evaluate("()=>document.body.innerText")[:800])
    
    # 5. 截图
    pg.screenshot(path="flybit_deep_analyze.png")
    print("\nscreenshot saved: flybit_deep_analyze.png")
    
    b.close()
