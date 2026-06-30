import sys,io,time
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(channel="msedge",headless=False,
        args=["--proxy-server=http://127.0.0.1:7897","--ignore-certificate-errors","--no-sandbox"])
    ctx=b.new_context(viewport={"width":1280,"height":800},ignore_https_errors=True,locale="zh-CN")
    pg=ctx.new_page()
    pg.goto("https://a.99ba2026.fyi/#/register",wait_until="networkidle",timeout=45000)
    time.sleep(3)
    print("=== 99ba DEEP ANALYSIS ===")
    print(f"URL:{pg.url} Title:{pg.title()}")
    # 找所有input/select/带select类的元素/含@的文本
    print("\n--- INPUTS ---")
    for el in pg.query_selector_all("input"):
        a=el.evaluate("el=>({t:el.type,n:el.name,p:el.placeholder,cls:el.className})")
        print(f"  type={a['t']} name={a['n']} placeholder={a['p']} cls={a['cls'][:60]}")
    print("\n--- NATIVE SELECTS ---")
    for s in pg.query_selector_all("select"):
        opts=s.evaluate("el=>Array.from(el.options).map(o=>o.value)")
        print(f"  options:{opts}")
    print("\n--- CUSTOM DROPDOWNS ---")
    dd=pg.evaluate("""()=>{
        var r=[];
        document.querySelectorAll('[class*=select],[class*=dropdown],[class*=picker]').forEach(function(el){
            r.push({tag:el.tagName,cls:el.className,text:(el.textContent||'').trim().substring(0,60)});
        });
        return JSON.stringify(r,null,2);
    }""")
    print(dd[:3000])
    print("\n--- @xxx SUFFIX ELEMENTS ---")
    at=pg.evaluate("""()=>{
        var r=[];
        var w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
        while(w.nextNode()){
            var t=w.currentNode.textContent;
            if(/@(?:qq|163|gmail|outlook|yahoo|hotmail|126|sina|foxmail|yeah|icloud)/i.test(t)){
                var p=w.currentNode.parentElement;
                r.push({tag:p.tagName,cls:p.className,text:t.trim().substring(0,40),html:p.outerHTML.substring(0,200)});
            }
        }
        return JSON.stringify(r,null,2);
    }""")
    print(at[:3000])
    print("\n--- PAGE TEXT ---")
    print(pg.evaluate("()=>document.body.innerText")[:600])
    pg.screenshot(path="99ba_deep.png")
    print("screenshot: 99ba_deep.png")
    b.close()
