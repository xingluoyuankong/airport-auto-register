# -*- coding: utf-8 -*-
"""奈云v2ny 注册脚本 — B型完整邮箱(自定义面板)
面板: v2ny.com  免费: 2GB/1天 8US TROJAN  系统: 自定义Vue3(Naiun)
关键: 完整邮箱输入, naiun.auth.header取订阅
"""
import sys,io,os,json,time,requests,re
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
from playwright.sync_api import sync_playwright

TD=r"E:\.Outlook邮箱\批量注册邮箱\已经使用\1"
def graph_wait_code(email_addr,to=90):
    tk=None
    for f in os.listdir(TD):
        if email_addr.lower() in f.lower() and f.endswith("_combo.txt"):
            with open(os.path.join(TD,f),encoding="utf-8") as fh:
                p=fh.read().strip().split("----")
                if len(p)>=4: tk={"email":p[0],"cid":p[2],"rt":p[3]}
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

def run(email_addr,reg_pass):
    print(f"\n=== v2ny: {email_addr} ===")
    with sync_playwright() as p:
        b=p.chromium.launch(channel="msedge",headless=False,
            args=["--proxy-server=http://127.0.0.1:7897","--ignore-certificate-errors","--no-sandbox"])
        ctx=b.new_context(viewport={"width":1280,"height":800},ignore_https_errors=True,locale="zh-CN")
        pg=ctx.new_page()
        pg.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>false})")
        try:
            # 1. 打开登录页,直接导航到注册或点"创建账户"
            print("[1] open register...")
            pg.goto("https://www.v2ny.com/#/auth/login",wait_until="domcontentloaded",timeout=60000)
            time.sleep(4)
            cf=pg.query_selector('iframe[src*="challenges.cloudflare.com"]')
            if cf:
                print("[Turnstile] waiting 60s...")
                dl=time.time()+60
                while time.time()<dl:
                    if not pg.query_selector('iframe[src*="challenges.cloudflare.com"]'): break
                    time.sleep(2)
            # 点"创建账户" - 等Vue SPA切换
            try:
                pg.click('text=创建账户',timeout=5000)
                time.sleep(4)
            except:
                try: pg.click('text=Create',timeout=5000); time.sleep(4)
                except: pass
            print(f"URL:{pg.url} Title:{pg.title()}")
            
            # 2. 填完整邮箱 (B型)
            print(f"[2] fill email...")
            pg.fill('input[type="email"]',email_addr)
            
            # 3. 填密码
            print("[3] fill password...")
            pg.fill('input[type="password"]',reg_pass)
            
            # 4. 发送验证码
            print("[4] click send...")
            pg.click('button:has-text("发送")')
            time.sleep(2)
            
            # 5. 收码
            print("[5] wait graph...")
            code,err=graph_wait_code(email_addr,to=90)
            if not code: print(f"NOCODE:{err}"); b.close(); return None
            
            # 6. 填码+创建账户
            print(f"[6] code={code} fill + create...")
            pg.fill('input[placeholder*="验证码"]',code)
            time.sleep(1)
            pg.click('button:has-text("创建账户")')
            time.sleep(5)
            
            # 7. 提取订阅 (奈云注册后自动登录,SPA不换URL)
            print("[7] extract subscribe...")
            # 等SPA响应
            time.sleep(3)
            cur=pg.url
            print(f"URL after create: {cur}")
            
            # 如果还在auth页面,可能在login模式,先切到dashboard
            if "/auth" in cur:
                # 尝试登录(如果还在login模式)
                try:
                    has_login_btn=pg.query_selector('button:has-text("登录")')
                    if has_login_btn:
                        pg.fill('input[type="email"]',email_addr)
                        pg.fill('input[type="password"]',reg_pass)
                        has_login_btn.click()
                        time.sleep(5)
                except: pass
            
            # 8. 提取订阅 (naiun.auth.header)
            print("[8] extract subscribe...")
            # 奈云用naiun.auth.header
            sub_url=pg.evaluate("""
                (function(){
                    var raw=localStorage.getItem('naiun.auth.header');
                    if(!raw) raw=localStorage.getItem('VUE_NAIVE_ACCESS_TOKEN');
                    if(!raw) return 'NO_TOKEN';
                    var tok='';
                    try{var p=JSON.parse(raw);tok=(p.value||p.token||'').replace('Bearer ','')}catch(e){tok=raw}
                    var x=new XMLHttpRequest();
                    x.open('GET','/api/v1/user/getSubscribe',false);
                    x.setRequestHeader('Authorization','Bearer '+tok);
                    try{x.send()}catch(e){return x.responseText}
                    return x.responseText;
                })()
            """)
            print(f"getSubscribe: {sub_url}")
            # 解析
            subscribe_url=""
            try:
                d=json.loads(sub_url)
                subscribe_url=d.get("data",{}).get("subscribe_url","")
            except:
                urls=re.findall(r'"subscribe_url":"([^"]+)"',sub_url)
                subscribe_url=urls[0] if urls else ""
            print(f"SUB_URL: {subscribe_url}")
            
            result={"airport":"v2ny","panel":"v2ny.com","email":email_addr,
                    "password":reg_pass,"subscribe_url":subscribe_url,"system":"NaiunPanel"}
            os.makedirs("register_results",exist_ok=True)
            nm=email_addr.split("@")[0]
            with open(f"register_results/v2ny_{nm}.json","w",encoding="utf-8") as f:
                json.dump(result,f,ensure_ascii=False,indent=2)
            return subscribe_url
        except Exception as e:
            import traceback; traceback.print_exc()
            return None
        finally:
            b.close()

if __name__=="__main__":
    EMAIL=sys.argv[1] if len(sys.argv)>1 else "mx738945e98b@outlook.com"
    PASS=sys.argv[2] if len(sys.argv)>2 else "VpnTest2026!"
    r=run(EMAIL,PASS)
    print(f"\n{'SUB: '+str(r) if r else 'FAILED'}")
    sys.exit(0 if r else 1)
