#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FLYBIT 验证V2 - 完整邮箱输入"""
import sys,os,io,json,time,re
os.environ['HTTP_PROXY']='http://127.0.0.1:7897'; os.environ['HTTPS_PROXY']='http://127.0.0.1:7897'
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
from playwright.sync_api import sync_playwright

EMAIL="colemanbroovp9xyduj92hubhn@outlook.com"
PASS="VpnTest2026!"

with sync_playwright() as p:
    b=p.chromium.launch(channel="msedge",headless=False,
        args=["--proxy-server=http://127.0.0.1:7897","--ignore-certificate-errors","--no-sandbox"])
    c=b.new_context(viewport={"width":1280,"height":900},ignore_https_errors=True,locale="zh-CN")
    pg=c.new_page();pg.set_default_timeout(15000)
    pg.add_init_script('Object.defineProperty(navigator,"webdriver",{get:()=>false});')
    try:
        print("=== FLYBIT V2 ===",flush=True)

        # 先探测登录页结构
        pg.goto("https://www.flybit.vip/#/login",wait_until="domcontentloaded",timeout=45000)
        time.sleep(3)
        body=pg.evaluate("()=>document.body.innerText")
        print(f"URL:{pg.url}\nBody:{body[:400]}",flush=True)

        # 填完整邮箱
        pg.fill('input[placeholder="邮箱"]',EMAIL)
        pw=pg.query_selector_all('input[type="password"]')
        if pw: pw[0].fill(PASS)
        time.sleep(0.3)
        pg.screenshot(path="flybit_vfy2_filled.png")

        # 点击登录
        pg.click('button:has-text("登入")')
        time.sleep(6)
        try: pg.wait_for_load_state("networkidle",timeout=10000)
        except: pass

        body2=pg.evaluate("()=>document.body.innerText")
        url2=pg.url
        print(f"AfterLogin URL:{url2}\nBody:{body2[:400]}",flush=True)
        pg.screenshot(path="flybit_vfy2_dash.png")

        # 提取订阅
        raw=pg.evaluate('localStorage.getItem("VUE_NAIVE_ACCESS_TOKEN")')
        print(f"TOKEN:{(raw or 'NONE')[:80]}",flush=True)

        if raw:
            resp=pg.evaluate("""(tok) => {
                let t='';
                try{ let p=JSON.parse(tok); t=p.value||p.token||p } catch(e){ t=tok }
                let x=new XMLHttpRequest();
                x.open('GET','/api/v1/user/getSubscribe',false);
                x.setRequestHeader('Authorization',t);
                try{x.send()}catch(e){}
                return x.responseText;
            }""", raw)
            print(f"getSubscribe:{resp[:300]}",flush=True)
            try:
                d=json.loads(resp)
                sub=d.get("data",{}).get("subscribe_url","") or d.get("subscribe_url","")
            except:
                urls=re.findall(r'"subscribe_url":"([^"]+)"',resp)
                sub=urls[0] if urls else ""
            if sub:
                print(f"✅ SUB:{sub}",flush=True)
                save_dir=os.path.join(os.path.dirname(os.path.dirname(__file__)),"register_results")
                os.makedirs(save_dir,exist_ok=True)
                with open(os.path.join(save_dir,f"flybit_{EMAIL.split('@')[0]}.json"),"w",encoding="utf-8") as f:
                    json.dump({"airport":"FLYBIT","email":EMAIL,"password":PASS,"subscribe_url":sub},f,ensure_ascii=False,indent=2)
                print("  saved!",flush=True)
            else:
                print("  NO SUB in response",flush=True)
        else:
            print("  NO TOKEN",flush=True)

        time.sleep(5)
    except Exception as e:
        print(f"e:{e}",flush=True)
        import traceback;traceback.print_exc()
    finally:
        b.close()
