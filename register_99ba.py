# -*- coding: utf-8 -*-
"""99吧 注册脚本 — A型表单(Naive UI下拉框)
面板: a.99ba2026.fyi  免费: 1GB/24h  系统: V2Board+NaiveUI
关键: 邮箱前缀+Naive UI n-select下拉选后缀
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
    parts=email_addr.split("@",1)
    prefix=parts[0]
    suffix="@"+parts[1]
    print(f"\n=== 99ba: {email_addr} ===")
    print(f"prefix={prefix} suffix={suffix}")
    with sync_playwright() as p:
        b=p.chromium.launch(channel="msedge",headless=False,
            args=["--proxy-server=http://127.0.0.1:7897","--ignore-certificate-errors","--no-sandbox"])
        ctx=b.new_context(viewport={"width":1280,"height":800},ignore_https_errors=True,locale="zh-CN")
        pg=ctx.new_page()
        pg.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>false})")
        try:
            print("[1] open register...")
            pg.goto("https://a.99ba2026.fyi/#/register",wait_until="networkidle",timeout=45000)
            time.sleep(2)
            # A型: 邮箱prefix (type=text, NOT email!)
            print(f"[2] fill prefix: {prefix}")
            pg.fill('input[placeholder*="邮箱"]',prefix)  # 99ba用的是 n-input__input-el, 无type=email
            # Naive UI下拉选后缀
            print(f"[3] select suffix: {suffix}")
            pg.click(".n-base-selection-label")
            time.sleep(1)
            pg.click(f"text={suffix}")
            time.sleep(1)
            # 密码
            print("[4] fill passwords...")
            pws=pg.query_selector_all('input[type="password"]')
            pws[0].fill(reg_pass)
            if len(pws)>=2: pws[1].fill(reg_pass)
            # 发送验证码
            print("[5] click send...")
            pg.click('button:has-text("发送")')
            time.sleep(2)
            # 收码
            print("[6] wait graph...")
            code,err=graph_wait_code(email_addr,to=90)
            if not code: print(f"NOCODE:{err}"); b.close(); return None
            # 填码+注册
            print(f"[7] code={code} fill + register...")
            pg.fill('input[placeholder*="验证码"]',code)
            time.sleep(1)
            pg.click('button:has-text("注册")')
            time.sleep(5)
            # 检查状态
            cur=pg.url
            print(f"[8] URL after reg: {cur}")
            if "/login" in cur:
                print("need login...")
                pg.fill('input[placeholder*="邮箱"]',prefix)
                pg.click(".n-base-selection-label"); time.sleep(1)
                pg.click(f"text={suffix}"); time.sleep(1)
                pw2=pg.query_selector('input[type="password"]')
                if pw2: pw2.fill(reg_pass)
                for btn in pg.query_selector_all("button"):
                    if "登" in (btn.inner_text() or ""):
                        btn.click(); time.sleep(4); break
                print(f"after login: {pg.url}")
            # 提取订阅
            print("[9] extract subscribe...")
            raw=pg.evaluate("localStorage.getItem('VUE_NAIVE_ACCESS_TOKEN')")
            print(f"TOKEN: {(raw or 'NONE')[:80]}")
            if raw:
                resp=pg.evaluate("""
                    (function(){
                        var raw=localStorage.getItem('VUE_NAIVE_ACCESS_TOKEN');
                        var tok='';
                        try{var p=JSON.parse(raw);tok=p.value||''}catch(e){}
                        var x=new XMLHttpRequest();
                        x.open('GET','/api/v1/user/getSubscribe',false);
                        x.setRequestHeader('Authorization',tok);
                        try{x.send()}catch(e){return x.responseText}
                        return x.responseText;
                    })()
                """)
                print(f"getSubscribe: {resp}")
                # 解析subscribe_url
                try:
                    d=json.loads(resp)
                    sub_url=d.get("data",{}).get("subscribe_url","")
                except:
                    urls=re.findall(r'"subscribe_url":"([^"]+)"',resp)
                    sub_url=urls[0] if urls else ""
                print(f"SUB_URL: {sub_url}")
                result={"airport":"99ba","panel":"a.99ba2026.fyi","system":"V2Board+NaiveUI",
                        "email":email_addr,"password":reg_pass,"subscribe_url":sub_url}
                os.makedirs("register_results",exist_ok=True)
                with open(f"register_results/99ba_{prefix}.json","w",encoding="utf-8") as f:
                    json.dump(result,f,ensure_ascii=False,indent=2)
                print(f"saved register_results/99ba_{prefix}.json")
                return sub_url
            else:
                print("NO TOKEN - reg failed")
                pg.screenshot(path="99ba_fail.png")
                return None
        except Exception as e:
            import traceback; traceback.print_exc()
            return None
        finally:
            b.close()

if __name__=="__main__":
    EMAIL=sys.argv[1] if len(sys.argv)>1 else "mx9433499602@outlook.com"
    PASS=sys.argv[2] if len(sys.argv)>2 else "VpnTest2026!"
    r=run(EMAIL,PASS)
    print(f"\n{'SUB: '+str(r) if r else 'FAILED'}")
    sys.exit(0 if r else 1)
