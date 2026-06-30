#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FLYBIT 正式注册脚本 V1.0
面板: s.fb.22na.cn  |  免费: 2GB测试体验  |  系统: V2Board
模板: 前缀input + select下拉后缀 + 密码x1 + 验证码
用法: python register_flybit_v2.py [email] [password]
"""
import sys, os, io, json, time, re
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7897'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7897'
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests as req
from playwright.sync_api import sync_playwright

TK = r"E:\.Outlook邮箱\批量注册邮箱\已经使用\1"


def find_token(email):
    for f in os.listdir(TK):
        if email.lower() in f.lower() and f.endswith("_combo.txt"):
            with open(os.path.join(TK, f), encoding="utf-8") as fh:
                p = fh.read().strip().split("----")
                if len(p) >= 4:
                    return p[2], p[3]
    return None, None


def wait_code(email, timeout=45):
    """持续轮询Graph API收验证码"""
    cid, rt = find_token(email)
    if not cid:
        return None

    deadline = time.time() + timeout
    at = None
    at_time = 0
    seen = set()
    start = time.time()

    while time.time() < deadline:
        try:
            now = time.time()
            if not at or now - at_time > 600:
                r = req.post(
                    "https://login.microsoftonline.com/consumers/oauth2/v2.0/token",
                    data={
                        "client_id": cid,
                        "grant_type": "refresh_token",
                        "refresh_token": rt,
                        "scope": "offline_access https://graph.microsoft.com/Mail.Read"
                    },
                    timeout=10)
                if r.status_code == 200:
                    at = r.json().get("access_token", "")
                    at_time = now
                else:
                    time.sleep(1.5)
                    continue

            if not at:
                time.sleep(1.5)
                continue

            resp = req.get(
                "https://graph.microsoft.com/v1.0/me/messages?$top=10&$orderby=receivedDateTime desc&$select=id,subject,bodyPreview",
                headers={"Authorization": f"Bearer {at}"},
                timeout=10)
            if resp.status_code != 200:
                time.sleep(1.5)
                continue

            for msg in resp.json().get("value", []):
                mid = msg.get("id", "")
                if mid in seen:
                    continue
                seen.add(mid)

                combined = f"{msg.get('subject', '')} {msg.get('bodyPreview', '')}"
                m = re.search(r"\b(\d{6})\b", combined)
                if m:
                    code = m.group(1)
                    if code in ("000000", "111111", "222222", "999999", "123456"):
                        continue
                    elapsed = time.time() - start
                    subject = msg.get('subject', '')[:60]
                    print(f"  ✅ [{elapsed:.1f}s] 验证码={code} 主题={subject}", flush=True)
                    return code

            time.sleep(1.5)

        except Exception as e:
            print(f"  [Graph] 异常: {e}", flush=True)
            time.sleep(2)

    return None


def register(email, password):
    """完整注册流程"""
    prefix, suffix_domain = email.split("@", 1)
    suffix = "@" + suffix_domain
    print(f"\n{'='*60}\n  FLYBIT注册: {email}\n  prefix={prefix} suffix={suffix}\n{'='*60}", flush=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="msedge",
            headless=False,
            args=["--proxy-server=http://127.0.0.1:7897",
                  "--ignore-certificate-errors",
                  "--no-sandbox"])
        ctx = browser.new_context(
            viewport={"width": 1280, "height": 900},
            ignore_https_errors=True,
            locale="zh-CN")
        page = ctx.new_page()
        page.set_default_timeout(15000)
        page.add_init_script("""
            Object.defineProperty(navigator,'webdriver',{get:()=>false});
        """)

        try:
            # Step 1: 打开注册页
            print("[1/5] 打开注册页...", flush=True)
            page.goto("https://flybit.vip/#/register",
                      wait_until="networkidle", timeout=45000)
            time.sleep(2)

            # Step 2: 填表 - NaiveUI下拉框
            print("[2/5] 填邮箱前缀+NaiveUI选后缀...", flush=True)
            page.fill('input[placeholder="邮箱"]', prefix)
            time.sleep(0.3)
            # NaiveUI下拉框：点击展开，选@outlook.com
            page.click(".n-base-selection-label")
            time.sleep(0.5)
            page.click(f'text={suffix}')
            time.sleep(0.3)

            # 密码
            pws = page.query_selector_all('input[type="password"]')
            pws[0].fill(password)
            time.sleep(0.2)
            if len(pws) >= 2:
                pws[1].fill(password)
            print(f"  密码x{len(pws)}已填", flush=True)

            page.screenshot(path=os.path.join(os.path.dirname(__file__),
                                              "flybit_v2_filled.png"))

            # Step 3: 发码+收码
            print("[3/5] 发送验证码...", flush=True)
            page.click('button:has-text("发送")')

            print("  等待Graph API收码...", flush=True)
            code = wait_code(email, timeout=45)
            if not code:
                print("  ❌ 超时", flush=True)
                browser.close()
                return None

            # Step 4: 填码+注册
            print(f"[4/5] 填码 {code} + 注册...", flush=True)
            page.fill('input[placeholder="邮箱验证码"]', code)
            time.sleep(0.15)
            page.click('button:has-text("注册")')

            time.sleep(5)
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except:
                pass

            body = page.evaluate("() => document.body.innerText")
            cur_url = page.url
            print(f"  注册后URL: {cur_url}", flush=True)
            page.screenshot(path=os.path.join(os.path.dirname(__file__),
                                              "flybit_v2_after.png"))

            # 自动登录(如需要) — 登录页用完整邮箱
            if "/login" in cur_url or "登入" in body:
                print("  自动登录...", flush=True)
                page.fill('input[placeholder="邮箱"]', email)
                time.sleep(0.3)
                pw = page.query_selector('input[type="password"]')
                if pw:
                    pw.fill(password)
                time.sleep(0.2)
                for btn_text in ["登入", "登录", "Login"]:
                    try:
                        page.click(f'button:has-text("{btn_text}")', timeout=3000)
                        break
                    except:
                        continue
                time.sleep(5)
                body = page.evaluate("() => document.body.innerText")
                print(f"  登录后: {body[:200]}", flush=True)

            # Step 5: 提取订阅链接
            print("[5/5] 提取订阅链接...", flush=True)
            raw_token = page.evaluate(
                "localStorage.getItem('VUE_NAIVE_ACCESS_TOKEN')")

            if raw_token:
                resp = page.evaluate("""
                    (() => {
                        let r = arguments[0];
                        let t = '';
                        try {
                            let p = JSON.parse(r);
                            t = p.value || p.token || p;
                        } catch(e) {
                            t = r;
                        }
                        let x = new XMLHttpRequest();
                        x.open('GET', '/api/v1/user/getSubscribe', false);
                        x.setRequestHeader('Authorization', t);
                        try { x.send(); } catch(e) {}
                        return x.responseText;
                    })()
                """, raw_token)

                sub_url = ""
                try:
                    d = json.loads(resp)
                    sub_url = d.get("data", {}).get("subscribe_url", "")
                    if not sub_url:
                        sub_url = d.get("subscribe_url", "")
                except:
                    urls = re.findall(
                        r'subscribe_url["\s:]+(https?://[^"\s]+)', resp)
                    sub_url = urls[0] if urls else ""

                if sub_url:
                    print(f"  ✅ 订阅链接: {sub_url}", flush=True)

                    result = {
                        "airport": "FLYBIT",
                        "panel": "flybit.vip",
                        "email": email,
                        "password": password,
                        "subscribe_url": sub_url
                    }
                    save_dir = os.path.join(
                        os.path.dirname(os.path.dirname(__file__)),
                        "register_results")
                    os.makedirs(save_dir, exist_ok=True)
                    with open(os.path.join(save_dir,
                                           f"flybit_{prefix}.json"),
                              "w", encoding="utf-8") as fp:
                        json.dump(result, fp, ensure_ascii=False, indent=2)
                    print(f"  已保存: register_results/flybit_{prefix}.json",
                          flush=True)
                    return sub_url

            # 备用
            body_text = page.evaluate("() => document.body.innerText")
            m = re.search(r'https?://[^\s]+(?:sub|subscribe|token)[^\s]+',
                          body_text, re.I)
            if m:
                print(f"  页面中找到: {m.group(0)}", flush=True)
            else:
                print("  ⚠️ 未找到", flush=True)
                time.sleep(15)

            return None

        except Exception as e:
            print(f"  ❌ 异常: {e}", flush=True)
            import traceback
            traceback.print_exc()
            return None
        finally:
            browser.close()


if __name__ == "__main__":
    EMAIL = sys.argv[1] if len(sys.argv) > 1 else "mx40f8e7ef94@outlook.com"
    PASS = sys.argv[2] if len(sys.argv) > 2 else "VpnTest2026!"
    result = register(EMAIL, PASS)
    if result:
        print(f"\n🎉 FLYBIT注册成功!\n  订阅: {result}")
        sys.exit(0)
    else:
        print(f"\n❌ 注册失败")
        sys.exit(1)
