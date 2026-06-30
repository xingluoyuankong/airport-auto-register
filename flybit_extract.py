import sys,io,os,json,time
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
from playwright.sync_api import sync_playwright
email_addr=sys.argv[1] if len(sys.argv)>1 else "landsanchehrqvrw49590ycpji@outlook.com"
reg_pass=sys.argv[2] if len(sys.argv)>2 else "VpnTest2026!"
with sync_playwright() as p:
    b=p.chromium.launch(channel="msedge",headless=False,args=["--proxy-server=http://127.0.0.1:7897","--ignore-certificate-errors","--no-sandbox"])
    ctx=b.new_context(viewport={"width":1280,"height":800},ignore_https_errors=True,locale="zh-CN")
    page=ctx.new_page()
    # login
    print("login...")
    page.goto("https://flybit.vip/#/login",wait_until="domcontentloaded",timeout=30000)
    time.sleep(2)
    page.fill("input[type=email]",email_addr)
    pw=page.query_selector("input[type=password]")
    if pw: pw.fill(reg_pass)
    btns=[b for b in page.query_selector_all("button") if b.is_visible()]
    for btn in btns:
        t=(btn.inner_text() or "").lower()
        if "login" in t or "\u767b" in t:
            btn.click(); time.sleep(5); break
    else:
        if btns: btns[0].click(); time.sleep(5)
    print("URL:",page.url)
    # extract via evaluate
    result=page.evaluate("""
        (function(){
            var raw=localStorage.getItem('VUE_NAIVE_ACCESS_TOKEN');
            if(!raw) return 'NO_TOKEN_IN_LS';
            var tok='';
            try{var p=JSON.parse(raw);tok=p.value||p.token||''}catch(e){tok=raw}
            return tok;
        })()
    """)
    print("TOKEN:",result[:80] if result else "NONE")
    if result and len(result)>10:
        print("calling getSubscribe...")
        sub=page.evaluate("""
            (function(){
                var raw=localStorage.getItem('VUE_NAIVE_ACCESS_TOKEN');
                var tok='';
                try{var p=JSON.parse(raw);tok=p.value||p.token||''}catch(e){tok=raw}
                var xhr=new XMLHttpRequest();
                xhr.open('GET','/api/v1/user/getSubscribe',false);
                xhr.setRequestHeader('Authorization',tok);
                xhr.send();
                return xhr.responseText;
            })()
        """)
        print("getSubscribe response:",sub)
        import re
        for u in re.findall(r'https?://[^\s"\'\\]+',sub):
            if 'subscribe' in u.lower() or 'sub' in u.lower() or 'token' in u.lower():
                print("SUB_URL:",u)
    page.screenshot(path="flybit_dashboard.png")
    print("screenshot saved")
    b.close()
