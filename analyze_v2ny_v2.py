import sys,io,time
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(channel="msedge",headless=False,
        args=["--proxy-server=http://127.0.0.1:7897","--ignore-certificate-errors","--no-sandbox"])
    ctx=b.new_context(viewport={"width":1280,"height":800},ignore_https_errors=True,locale="zh-CN")
    pg=ctx.new_page()
    pg.goto("https://www.v2ny.com/#/auth/login",wait_until="domcontentloaded",timeout=60000)
    time.sleep(5)
    
    # 点击"创建账户"
    for a in pg.query_selector_all("a,button,span"):
        t=(a.inner_text() or "").strip()
        if "创建" in t or "注册" in t or "register" in t.lower() or "sign" in t.lower():
            print(f"clicking: {t}")
            try: a.click(); time.sleep(5); break
            except: pass
    
    print(f"URL:{pg.url} Title:{pg.title()}")
    
    # 分析注册表单
    print("\n--- INPUTS ---")
    for el in pg.query_selector_all("input"):
        a=el.evaluate("el=>({t:el.type,n:el.name,p:el.placeholder,id:el.id})")
        print(f"  type={a['t']} name={a['n']} placeholder={a['p']}")
    
    print("\n--- SELECTS ---")
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
    
    print("\n--- PAGE TEXT ---")
    print(pg.evaluate("()=>document.body.innerText")[:600])
    pg.screenshot(path="v2ny_register.png")
    b.close()
