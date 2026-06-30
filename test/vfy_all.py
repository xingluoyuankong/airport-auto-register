#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量验证v2ny/COCODUCK/cd520 — 已注册账户直接登录提取"""
import sys,os,io,json,time,re
os.environ['HTTP_PROXY']='http://127.0.0.1:7897'; os.environ['HTTPS_PROXY']='http://127.0.0.1:7897'
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
from playwright.sync_api import sync_playwright

TASKS=[
    {"airport":"v2ny","login_url":"https://www.v2ny.com/#/auth/login",
     "email":"averymorga4g0jfbs6q2up@outlook.com","pass":"VpnTest2026!",
     "email_id":"reg-email","pass_id":"reg-password","btn_text":"登录",
     "token_key":"VUE_NAIVE_ACCESS_TOKEN","sub_api":"/api/v1/user/getSubscribe",
     "sub_parser":"api"},
    {"airport":"COCODUCK","login_url":"https://cocoduck.cc/#/login",
     "email":"floraide3rb1508k2xlbbi@hotmail.com","pass":"VpnTest2026!",
     "email_ph":"邮箱","pass_ph":"密码","btn_text":"登录",
     "token_key":"VUE_NAIVE_ACCESS_TOKEN","sub_api":"/api/v1/user/getSubscribe",
     "sub_parser":"api"},
    {"airport":"cd520","login_url":"https://cd1314.xyz/#/login",
     "email":"hendricktamm95v80awzaxli@outlook.com","pass":"VpnTest2026!",
     "email_ph":"邮箱","pass_ph":"密码","btn_text":"登录",
     "token_key":"VUE_NAIVE_ACCESS_TOKEN","sub_api":"/api/v1/user/getSubscribe",
     "sub_parser":"api"},
]

for t in TASKS:
    print(f"\n{'='*50}\n  {t['airport']}: {t['email']}\n{'='*50}",flush=True)
    try:
        with sync_playwright() as p:
            b=p.chromium.launch(channel="msedge",headless=False,
                args=["--proxy-server=http://127.0.0.1:7897","--ignore-certificate-errors","--no-sandbox"])
            c=b.new_context(viewport={"width":1280,"height":900},ignore_https_errors=True,locale="zh-CN")
            pg=c.new_page();pg.set_default_timeout(15000)

            # Login
            pg.goto(t["login_url"],wait_until="domcontentloaded",timeout=45000)
            time.sleep(3)

            # Fill email (try by id first, then placeholder)
            eid=t.get("email_id","")
            if eid:
                el=pg.query_selector(f"#{eid}")
                if el: el.fill(t["email"])
                else: pg.fill(f'input[placeholder="{t.get("email_ph","邮箱")}"]',t["email"])
            else:
                pg.fill(f'input[placeholder="{t.get("email_ph","邮箱")}"]',t["email"])

            # Fill password
            pid=t.get("pass_id","")
            if pid:
                el=pg.query_selector(f"#{pid}")
                if el: el.fill(t["pass"])
                else:
                    pws=pg.query_selector_all('input[type="password"]')
                    pws[0].fill(t["pass"])
            else:
                pws=pg.query_selector_all('input[type="password"]')
                pws[0].fill(t["pass"])

            time.sleep(0.3)
            pg.screenshot(path=f"vfy_{t['airport']}_filled.png")

            # Click login btn
            pg.click(f'button:has-text("{t["btn_text"]}")')
            time.sleep(6)
            try: pg.wait_for_load_state("networkidle",timeout=10000)
            except: pass

            body=pg.evaluate("()=>document.body.innerText")
            url=pg.url
            print(f"  URL:{url}\n  Body:{body[:300]}",flush=True)
            pg.screenshot(path=f"vfy_{t['airport']}_dash.png")

            # Extract
            raw=pg.evaluate(f'localStorage.getItem("{t["token_key"]}")')
            if raw:
                resp=pg.evaluate("""(tok) => {
                    let t='';
                    try{ let p=JSON.parse(tok); t=p.value||p.token||p } catch(e){ t=tok }
                    let x=new XMLHttpRequest();
                    x.open('GET',arguments[1],false);
                    x.setRequestHeader('Authorization',t);
                    try{x.send()}catch(e){}
                    return x.responseText;
                }""", raw, t["sub_api"])
                print(f"  getSubscribe:{resp[:300]}",flush=True)
                try:
                    d=json.loads(resp)
                    sub=d.get("data",{}).get("subscribe_url","") or d.get("subscribe_url","")
                except:
                    urls=re.findall(r'subscribe_url["\s:]+(https?://[^"\s]+)',resp)
                    sub=urls[0] if urls else ""
                if sub:
                    print(f"  ✅ {t['airport']} SUB:{sub}",flush=True)
                else:
                    # Fallback: search body text
                    m=re.search(r'https?://[^\s]+(?:sub|subscribe|token|link)[^\s]+',body,re.I)
                    if m:
                        sub=m.group(0)
                        print(f"  ✅ {t['airport']} SUB(from body):{sub}",flush=True)
                    else:
                        print(f"  ❌ NO SUB for {t['airport']}",flush=True)
            else:
                print(f"  ❌ NO TOKEN for {t['airport']}",flush=True)

            time.sleep(2)
            b.close()
    except Exception as e:
        print(f"  e:{e}",flush=True)
        try: b.close()
        except: pass
