#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证 99ba 注册脚本是否完好"""
import sys,os,io,json,time,re
os.environ['HTTP_PROXY']='http://127.0.0.1:7897'; os.environ['HTTPS_PROXY']='http://127.0.0.1:7897'
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
import requests as req
from playwright.sync_api import sync_playwright

TK=r"E:\.Outlook邮箱\批量注册邮箱\已经使用\1"

def find_t(email):
    for f in os.listdir(TK):
        if email.lower() in f.lower() and f.endswith("_combo.txt"):
            with open(os.path.join(TK,f),encoding="utf-8") as fh:
                p=fh.read().strip().split("----")
                if len(p)>=4: return p[2],p[3]
    return None,None

def wait_code(email,timeout=45):
    cid,rt=find_t(email)
    if not cid: return None
    dl=time.time()+timeout; at=None; at_t=0; seen=set(); start=time.time()
    while time.time()<dl:
        try:
            now=time.time()
            if not at or now-at_t>600:
                r=req.post("https://login.microsoftonline.com/consumers/oauth2/v2.0/token",
                    data={"client_id":cid,"grant_type":"refresh_token","refresh_token":rt,
                          "scope":"offline_access https://graph.microsoft.com/Mail.Read"},timeout=10)
                if r.status_code==200: at=r.json().get("access_token",""); at_t=now
                else: time.sleep(1.5); continue
            if not at: time.sleep(1.5); continue
            resp=req.get("https://graph.microsoft.com/v1.0/me/messages?$top=10&$orderby=receivedDateTime desc&$select=id,subject,bodyPreview",
                headers={"Authorization":f"Bearer {at}"},timeout=10)
            if resp.status_code!=200: time.sleep(1.5); continue
            for msg in resp.json().get("value",[]):
                mid=msg.get("id","")
                if mid in seen: continue
                seen.add(mid)
                combined=f'{msg.get("subject","")} {msg.get("bodyPreview","")}'
                m=re.search(r"\b(\d{6})\b",combined)
                if m and m.group(1) not in ("000000","111111","222222","999999","123456"):
                    elapsed=time.time()-start
                    print(f"  code={m.group(1)} [{elapsed:.1f}s] subj={msg.get('subject','')[:50]}",flush=True)
                    return m.group(1)
            time.sleep(1.5)
        except: time.sleep(2)
    return None

EMAIL="mx40f8e7ef94@outlook.com"
PASS="VpnTest2026!"
prefix,suffix=EMAIL.split("@",1); suffix="@"+suffix

with sync_playwright() as p:
    b=p.chromium.launch(channel="msedge",headless=False,
        args=["--proxy-server=http://127.0.0.1:7897","--ignore-certificate-errors","--no-sandbox"])
    c=b.new_context(viewport={"width":1280,"height":900},ignore_https_errors=True,locale="zh-CN")
    pg=c.new_page();pg.set_default_timeout(15000)
    pg.add_init_script('Object.defineProperty(navigator,"webdriver",{get:()=>false});')
    try:
        print("=== 99ba VERIFY ===",flush=True)
        pg.goto("https://a.99ba2026.fyi/#/register",wait_until="networkidle",timeout=45000)
        time.sleep(2)
        body=pg.evaluate("()=>document.body.innerText")
        print(f"Page:{body[:300]}",flush=True)

        pg.fill('input[placeholder="邮箱"]',prefix)
        time.sleep(0.3)
        pg.click(".n-base-selection-label"); time.sleep(0.5)
        pg.click(f"text={suffix}"); time.sleep(0.3)
        pws=pg.query_selector_all('input[type="password"]')
        pws[0].fill(PASS); pws[1].fill(PASS)
        pg.screenshot(path="99ba_vfy_filled.png")

        pg.click('button:has-text("发送")')
        print("sent",flush=True)
        code=wait_code(EMAIL,45)
        if not code: print("NOCODE"); exit(1)

        pg.fill('input[placeholder="邮箱验证码"]',code)
        time.sleep(0.15)
        pg.click('button:has-text("注册")')
        time.sleep(5)
        body2=pg.evaluate("()=>document.body.innerText")
        url=pg.url
        print(f"URL:{url}\nBody:{body2[:400]}",flush=True)
        pg.screenshot(path="99ba_vfy_after.png")

        if "/login" in url or "登入" in body2:
            print("login...",flush=True)
            pg.fill('input[placeholder="邮箱"]',prefix)
            time.sleep(0.2)
            pg.click(".n-base-selection-label"); time.sleep(0.5)
            pg.click(f"text={suffix}"); time.sleep(0.2)
            pw=pg.query_selector('input[type="password"]')
            if pw: pw.fill(PASS)
            pg.click('button:has-text("登录")'); time.sleep(5)

        raw=pg.evaluate('localStorage.getItem("VUE_NAIVE_ACCESS_TOKEN")')
        if raw:
            resp=pg.evaluate("""(()=>{let r=arguments[0];let t='';try{let p=JSON.parse(r);t=p.value||p.token||p}catch(e){t=r}
                let x=new XMLHttpRequest();x.open('GET','/api/v1/user/getSubscribe',false);
                x.setRequestHeader('Authorization',t);try{x.send()}catch(e){}return x.responseText})()""",raw)
            try:
                d=json.loads(resp)
                sub=d.get("data",{}).get("subscribe_url","") or d.get("subscribe_url","")
            except:
                urls=re.findall(r'subscribe_url["\s:]+(https?://[^"\s]+)',resp)
                sub=urls[0] if urls else ""
            if sub: print(f"SUB:{sub}",flush=True)
        time.sleep(5)
    except Exception as e:
        print(f"e:{e}",flush=True)
    finally:
        b.close()
