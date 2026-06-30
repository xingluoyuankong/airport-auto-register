#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v2ny/奈云 批量注册+提取 — 验证模式版"""
import sys,os,io,json,time,re
os.environ['HTTP_PROXY']='http://127.0.0.1:7897'
os.environ['HTTPS_PROXY']='http://127.0.0.1:7897'
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')

TOKEN_DIR=r"E:\.Outlook邮箱\批量注册邮箱\已经使用\1"
from playwright.sync_api import sync_playwright
import requests as req

def graph_wait_code(email_addr, to=90):
    """Microsoft Graph API 收验证码"""
    tk=None
    for f in os.listdir(TOKEN_DIR):
        fname=f.replace("tokens_","")
        if email_addr.lower() in fname.lower() and f.endswith("_combo.txt"):
            with open(os.path.join(TOKEN_DIR,f),encoding="utf-8") as fh:
                p=fh.read().strip().split("----")
                if len(p)>=4: tk={"email":p[0],"cid":p[2],"rt":p[3]}
    if not tk: return None,"no token file"
    dl=time.time()+to; at=None; la=0; seen=set()
    while time.time()<dl:
        if time.time()-la>1200 or not at:
            r=req.post("https://login.microsoftonline.com/consumers/oauth2/v2.0/token",
                data={"client_id":tk["cid"],"grant_type":"refresh_token","refresh_token":tk["rt"],
                "scope":"offline_access https://graph.microsoft.com/Mail.Read"},timeout=15)
            at=r.json().get("access_token") if r.status_code==200 else None; la=time.time()
        if not at: time.sleep(3); continue
        try:
            r=req.get("https://graph.microsoft.com/v1.0/me/messages?$top=10&$select=id,subject,bodyPreview,receivedDateTime&$orderby=receivedDateTime desc",
                headers={"Authorization":f"Bearer {at}"},timeout=10)
            if r.status_code==401: at=None; continue
            if r.status_code!=200: time.sleep(3); continue
            for msg in r.json().get("value",[]):
                mid=msg.get("id")
                if mid in seen: continue
                seen.add(mid)
                subj=msg.get("subject","")
                prev=msg.get("bodyPreview","")
                txt=f"{subj} {prev}"
                for pat in [r"(?:验证码|激活码|注册码)\D{0,20}?(\d{4,8})",r"code\s*(?:is|:)\s*(\d{4,8})",r"\b(\d{6})\b"]:
                    m=re.search(pat,txt,re.I)
                    if m and len(m.group(1))>=4:
                        code=m.group(1)
                        if code=="000000": continue
                        print(f"  [Graph] code={code} subj={subj[:40]}",flush=True)
                        return code,None
            time.sleep(3)
        except: time.sleep(3)
    return None,"timeout"

def register_v2ny(email_addr, password):
    print(f"\n=== v2ny: {email_addr} ===",flush=True)
    with sync_playwright() as p:
        b=p.chromium.launch(channel="msedge",headless=False,
            args=["--proxy-server=http://127.0.0.1:7897","--ignore-certificate-errors","--no-sandbox"])
        c=b.new_context(viewport={"width":1280,"height":900},ignore_https_errors=True,locale="zh-CN")
        pg=c.new_page();pg.set_default_timeout(15000)
        pg.add_init_script('Object.defineProperty(navigator,"webdriver",{get:()=>false});')
        try:
            # 注册页
            pg.goto("https://www.v2ny.com/#/auth/register",wait_until="domcontentloaded",timeout=45000)
            time.sleep(3)
            pg.fill("#reg-email",email_addr)
            pg.fill("#reg-password",password)
            time.sleep(0.3)
            pg.screenshot(path="v2ny_reg_filled.png")
            # 发码
            pg.click('button:has-text("发送")')
            time.sleep(2)
            # Record timestamp BEFORE sending, only accept code after
            before_ts=time.time()
            # 收码 (with time filter)
            code,err=graph_wait_code_after(email_addr,to=90,after_ts=before_ts)
            if not code: print(f"  NO CODE: {err}",flush=True); return None
            # 填码+注册
            pg.fill("#reg-code",code)
            time.sleep(0.5)
            pg.click('button:has-text("创建")')
            time.sleep(6)
            try: pg.wait_for_load_state("networkidle",timeout=10000)
            except: pass
            url=pg.url;body=pg.evaluate("()=>document.body.innerText")
            print(f"  URL:{url}\n  Body:{body[:300]}",flush=True)
            pg.screenshot(path="v2ny_reg_dash.png")
            # 如果跳到login则登录
            if "/auth/login" in url:
                print("  Need login...",flush=True)
                pg.fill("#login-email",email_addr)
                pg.fill("#login-password",password)
                pg.click('button:has-text("登录")')
                time.sleep(6)
                body=pg.evaluate("()=>document.body.innerText")
            # 提取订阅
            m=re.search(r'https?://[^\s]+/sleep/\w+',body)
            if m:
                sub=m.group(0)
                print(f"  ✅ SUB:{sub}",flush=True)
                return sub
            print("  NO SUB in body",flush=True)
            return None
        except Exception as e:
            print(f"  e:{e}",flush=True)
            return None
        finally: b.close()

if __name__=="__main__":
    EMAIL="mx738945e98b@outlook.com"
    PASS="VpnTest2026!"
    sub=register_v2ny(EMAIL,PASS)
    if sub:
        os.makedirs("../register_results",exist_ok=True)
        with open(f"../register_results/v2ny_{EMAIL.split('@')[0]}.json","w",encoding="utf-8") as f:
            json.dump({"airport":"v2ny","email":EMAIL,"password":PASS,"subscribe_url":sub},f,ensure_ascii=False,indent=2)
        print(f"\n✅ DONE: {sub}",flush=True)
    else:
        print("\n❌ FAILED",flush=True)
