import sys,io,os,json,time,requests,re
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
from playwright.sync_api import sync_playwright
# ===== CONFIG =====
EMAIL=sys.argv[1] if len(sys.argv)>1 else "mx40f8e7ef94@outlook.com"
PASS=sys.argv[2] if len(sys.argv)>2 else "VpnTest2026!"
# ===== Graph API =====
TD=r"E:\.Outlook邮箱\批量注册邮箱\已经使用\1"
def graph_wait_code(email_addr,to=90):
    tk=None
    for f in os.listdir(TD):
        if email_addr.lower() in f.lower() and f.endswith("_combo.txt"):
            with open(os.path.join(TD,f),encoding="utf-8") as fh:
                p=fh.read().strip().split("----")
                if len(p)>=4: tk={"email":p[0],"cid":p[2],"rt":p[3]}
            break
    if not tk: return None,"no token"
    dl=time.time()+to; at=None; la=0; seen=set()
    print("[Graph] waiting...")
    while time.time()<dl:
        if time.time()-la>1200 or not at:
            r=requests.post("https://login.microsoftonline.com/consumers/oauth2/v2.0/token",
                data={"client_id":tk["cid"],"grant_type":"refresh_token","refresh_token":tk["rt"],
                "scope":"offline_access https://graph.microsoft.com/Mail.Read"},timeout=15)
            at=r.json().get("access_token") if r.status_code==200 else None; la=time.time()
        if not at: time.sleep(3); continue
        try:
            r=requests.get("https://graph.microsoft.com/v1.0/me/messages?$top=10&$select=id,subject,bodyPreview,body&$orderby=receivedDateTime desc",
                headers={"Authorization":f"Bearer {at}"},timeout=10)
            if r.status_code==401: at=None; continue
            if r.status_code!=200: time.sleep(3); continue
            for msg in r.json().get("value",[]):
                mid=msg.get("id")
                if mid in seen: continue
                seen.add(mid)
                txt=f"{msg.get('subject','')} {msg.get('bodyPreview','')} {msg.get('body',{}).get('content','')}"
                for pat in [r"(?:验证码|激活码|注册码)\D{0,20}?(\d{4,8})",r"code\s*(?:is|:)\s*(\d{4,8})",r"\b(\d{6})\b"]:
                    m=re.search(pat,txt,re.I)
                    if m and 4<=len(m.group(1))<=8:
                        print(f"[Graph] code={m.group(1)}")
                        return m.group(1),None
            time.sleep(3)
        except: time.sleep(3)
    return None,"timeout"
# ===== MAIN =====
print(f"=== FLYBIT: {EMAIL} ===")
with sync_playwright() as p:
    b=p.chromium.launch(channel="msedge",headless=False,
        args=["--proxy-server=http://127.0.0.1:7897","--ignore-certificate-errors","--no-sandbox"])
    ctx=b.new_context(viewport={"width":1280,"height":800},ignore_https_errors=True,locale="zh-CN")
    pg=ctx.new_page()
    pg.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>false})")
    try:
        # 1. open
        print("[1] open register...")
        pg.goto("https://flybit.vip/#/register",wait_until="networkidle",timeout=45000)
        time.sleep(2)
        # 2. fill email
        print("[2] fill email...")
        pg.fill("input[type=email]",EMAIL)
        # 3. fill password x2
        print("[3] fill passwords...")
        pws=pg.query_selector_all("input[type=password]")
        pws[0].fill(PASS)
        if len(pws)>=2: pws[1].fill(PASS)
        # 4. click send code
        print("[4] click send...")
        pg.click("button:has-text(\"\u53d1\u9001\")")
        time.sleep(2)
        # 5. wait code
        print("[5] wait graph...")
        code,err=graph_wait_code(EMAIL,to=90)
        if not code: print(f"NOCODE:{err}"); b.close(); sys.exit(1)
        # 6. fill code + register
        print(f"[6] code={code} filling...")
        pg.fill("input[placeholder*=\"\u9a8c\u8bc1\u7801\"]",code)
        time.sleep(1)
        # click register button (not send)
        for btn in pg.query_selector_all("button"):
            t=(btn.inner_text() or "").strip()
            if t=="\u6ce8\u518c":
                btn.click(); time.sleep(5); break
        else:
            pg.click("button:has-text(\"\u6ce8\u518c\")"); time.sleep(5)
        # 7. check login
        print(f"[7] URL after reg: {pg.url}")
        if "/login" in pg.url:
            print("need login...")
            pg.fill("input[type=email]",EMAIL)
            pw2=pg.query_selector("input[type=password]")
            if pw2: pw2.fill(PASS)
            for btn in pg.query_selector_all("button"):
                if "\u767b" in (btn.inner_text() or ""):
                    btn.click(); time.sleep(4); break
            print(f"after login: {pg.url}")
        # 8. extract subscribe
        print("[8] extract...")
        raw=pg.evaluate("localStorage.getItem('VUE_NAIVE_ACCESS_TOKEN')")
        if raw:
            parts=json.loads(raw)
            tok=parts.get("value","")
            # use sync XHR in page context
            resp=pg.evaluate("""
                (function(){
                    var raw=localStorage.getItem('VUE_NAIVE_ACCESS_TOKEN');
                    var tok='';
                    try{var p=JSON.parse(raw);tok=p.value||''}catch(e){}
                    var x=new XMLHttpRequest();
                    x.open('GET','/api/v1/user/getSubscribe',false);
                    x.setRequestHeader('Authorization',tok);
                    try{x.send()}catch(e){return'XHR_ERR:'+e.message}
                    return x.responseText;
                })()
            """)
            print(f"getSubscribe: {resp}")
            # extract URLs
            urls=re.findall(r'(https?://[^\s"\'\\}]+)',resp)
            for u in urls:
                print(f"SUB_URL: {u}")
            # save
            result={"airport":"FLYBIT","panel":"flybit.vip","email":EMAIL,
                    "password":PASS,"subscribe_url":resp,"system":"V2Board"}
            os.makedirs("register_results",exist_ok=True)
            nm=EMAIL.split("@")[0]
            with open(f"register_results/flybit_{nm}.json","w",encoding="utf-8") as f:
                json.dump(result,f,ensure_ascii=False,indent=2)
            print(f"saved to register_results/flybit_{nm}.json")
        else:
            print("NO TOKEN - registration may have failed")
            pg.screenshot(path="flybit_no_token.png")
    except Exception as e:
        import traceback; traceback.print_exc()
    finally:
        b.close()
