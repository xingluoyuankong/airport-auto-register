#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""99ba 终极精准版 — 用已验证token+秒收发码"""
import sys, os, io, json, time, re, threading
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

def quick_poll(email, timeout=25):
    cid,rt=find_t(email)
    if not cid: return None
    dl=time.time()+timeout; at=None; at_t=0; seen=set()
    while time.time()<dl:
        try:
            now=time.time()
            if not at or now-at_t>600:
                r=req.post("https://login.microsoftonline.com/consumers/oauth2/v2.0/token",
                    data={"client_id":cid,"grant_type":"refresh_token","refresh_token":rt,
                          "scope":"offline_access https://graph.microsoft.com/Mail.Read"},timeout=8)
                if r.status_code==200: at=r.json().get("access_token",""); at_t=now
                else: time.sleep(1.5); continue
            if not at: time.sleep(1.5); continue
            resp=req.get("https://graph.microsoft.com/v1.0/me/messages?$top=10&$orderby=receivedDateTime desc&$select=id,subject,bodyPreview",
                headers={"Authorization":f"Bearer {at}"},timeout=8)
            if resp.status_code!=200: time.sleep(1.5); continue
            for msg in resp.json().get("value",[]):
                mid=msg.get("id","");
                if mid in seen: continue
                seen.add(mid)
                combined=f"{msg.get('subject','')} {msg.get('bodyPreview','')}"
                m=re.search(r"\b(\d{6})\b",combined)
                if m and m.group(1) not in ("000000","111111","222222","999999","123456"):
                    elapsed=int(time.time()+timeout-dl)
                    print(f"  code={m.group(1)} [{elapsed}s] subj={msg.get('subject','')[:50]}",flush=True)
                    return m.group(1)
            time.sleep(1.5)
        except: time.sleep(2)
    return None

# 用有token的邮件
EMAILS=["mx40f8e7ef94@outlook.com","landsanchehrqvrw49590ycpji@outlook.com","bushuozaijian2026@outlook.com"]
PASS="VpnTest2026!"

def run_one(email):
    prefix,suffix=email.split("@",1); suffix="@"+suffix
    # 先启动轮询
    res=[None]; stop=threading.Event()
    def poll():
        c=quick_poll(email, 25)
        if c: res[0]=c
        stop.set()
    t=threading.Thread(target=poll); t.start()
    time.sleep(1)
    
    with sync_playwright() as p:
        b=p.chromium.launch(channel="msedge",headless=False,
            args=["--proxy-server=http://127.0.0.1:7897","--ignore-certificate-errors","--no-sandbox"])
        ctx=b.new_context(viewport={"width":1280,"height":900},ignore_https_errors=True,locale="zh-CN")
        pg=ctx.new_page();pg.set_default_timeout(15000)
        pg.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>false});")
        
        try:
            pg.goto("https://a.99ba2026.fyi/#/register",wait_until="networkidle",timeout=45000)
            time.sleep(2)
            
            # 填前缀→n-base-selection-label→text=@outlook.com
            pg.fill('input[placeholder="邮箱"]',prefix)
            time.sleep(0.2)
            pg.click(".n-base-selection-label")
            time.sleep(0.5)
            pg.click(f'text={suffix}')
            time.sleep(0.2)
            
            # 密码
            pws=pg.query_selector_all('input[type="password"]')
            pws[0].fill(PASS); pws[1].fill(PASS)
            
            # 发码
            pg.click('button:has-text("发送")')
            print(f"  发码",flush=True)
            
            # 等码(最多20s)
            t.join(20)
            code=res[0]
            if not code: 
                print(f"  ❌ nocode",flush=True); b.close(); return None
            
            pg.fill('input[placeholder="邮箱验证码"]',code)
            time.sleep(0.1)
            pg.click('button:has-text("注册")')
            time.sleep(4)
            
            body=pg.evaluate("()=>document.body.innerText")
            url=pg.url
            print(f"  url={url}\n  body={body[:250]}",flush=True)
            
            if "/login" in url or "登入" in body:
                print("  login...",flush=True)
                pg.fill('input[placeholder="邮箱"]',prefix)
                time.sleep(0.2)
                pg.click(".n-base-selection-label"); time.sleep(0.5)
                pg.click(f'text={suffix}'); time.sleep(0.2)
                pw=pg.query_selector('input[type="password"]')
                if pw: pw.fill(PASS)
                for t in ["登录","登入"]:
                    try: pg.click(f'button:has-text("{t}")',timeout=2000); time.sleep(4); break
                    except: continue
                body=pg.evaluate("()=>document.body.innerText")
                print(f"  after login:{body[:300]}",flush=True)
            
            raw=pg.evaluate("localStorage.getItem('VUE_NAIVE_ACCESS_TOKEN')")
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
                if sub:
                    print(f"  ✅ {sub}",flush=True)
                    with open(os.path.join(os.path.dirname(__file__),f"99ba_{email.split('@')[0]}.json"),"w",encoding="utf-8") as f:
                        json.dump({"airport":"99ba","email":email,"password":PASS,"subscribe_url":sub},f,ensure_ascii=False,indent=2)
                    b.close(); return sub
            # already registered case - try direct login
            if "已经注册" in body or "已被注册" in body or "邮箱已" in body or "该邮箱" in body:
                print("  已注册→直接登录",flush=True)
                pg.goto("https://a.99ba2026.fyi/#/login",wait_until="networkidle",timeout=15000)
                time.sleep(2)
                pg.fill('input[placeholder="邮箱"]',prefix)
                time.sleep(0.2)
                pg.click(".n-base-selection-label"); time.sleep(0.5)
                pg.click(f'text={suffix}'); time.sleep(0.2)
                pg.fill('input[type="password"]',PASS)
                pg.click('button:has-text("登录")',timeout=3000)
                time.sleep(5)
                raw=pg.evaluate("localStorage.getItem('VUE_NAIVE_ACCESS_TOKEN')")
                if raw:
                    resp=pg.evaluate("""(()=>{let r=arguments[0];let t='';try{let p=JSON.parse(r);t=p.value||p.token||p}catch(e){t=r}
                        let x=new XMLHttpRequest();x.open('GET','/api/v1/user/getSubscribe',false);
                        x.setRequestHeader('Authorization',t);try{x.send()}catch(e){}return x.responseText})()""",raw)
                    try:
                        d=json.loads(resp)
                        sub=d.get("data",{}).get("subscribe_url","") or d.get("subscribe_url","")
                    except: sub=""
                    if sub:
                        print(f"  ✅ login {sub}",flush=True)
                        with open(os.path.join(os.path.dirname(__file__),f"99ba_{email.split('@')[0]}.json"),"w",encoding="utf-8") as f:
                            json.dump({"airport":"99ba","email":email,"password":PASS,"subscribe_url":sub},f,ensure_ascii=False,indent=2)
                        b.close(); return sub
            
            bt=pg.evaluate("()=>document.body.innerText")
            m=re.search(r'https?://[^\s]+(?:sub|subscribe|token)[^\s]+',bt,re.I)
            print(f"  text_url={m.group(0) if m else 'NONE'}",flush=True)
            b.close(); return None
        except Exception as e:
            print(f"  e:{e}",flush=True)
            b.close(); return None
        finally:
            stop.set()

for em in EMAILS:
    print(f"\n99ba: {em}",flush=True)
    sub=run_one(em)
    if sub:
        print(f"  🎉 {sub}",flush=True)
        break
    print(f"  -- next --",flush=True)

print("Done")
