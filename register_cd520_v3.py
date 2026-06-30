#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cd520 注册脚本 V3 — 专业验证码获取 + 截图审计
面板: cd520.xyz (→ cd1314.xyz)  |  免费: 5GB/3天  |  系统: 自定义V2Board
用法: python register_cd520_v3.py [email] [password]
"""
import sys, os, io, json, time, re
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7897'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7897'
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from playwright.sync_api import sync_playwright
from outlook_verify_v2 import OutlookCodeFetcher

SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def register(email, password):
    prefix, suffix_domain = email.split("@", 1)
    suffix = "@" + suffix_domain
    print(f"\n{'='*60}\n  cd520 V3 注册: {email}\n  prefix={prefix} suffix={suffix}\n{'='*60}", flush=True)

    fetcher = OutlookCodeFetcher(email=email)
    if not fetcher.cid:
        print("❌ 无Graph API凭据", flush=True)
        return None

    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="msedge", headless=False,
            args=["--proxy-server=http://127.0.0.1:7897",
                  "--ignore-certificate-errors", "--no-sandbox"])
        ctx = browser.new_context(
            viewport={"width": 1280, "height": 900},
            ignore_https_errors=True, locale="zh-CN")
        page = ctx.new_page()
        page.set_default_timeout(30000)
        page.add_init_script("""
            Object.defineProperty(navigator,'webdriver',{get:()=>false});
        """)

        try:
            # ──────── Step 1: 打开注册页 ────────
            print("\n[1/6] 打开注册页...", flush=True)
            page.goto("https://cd520.xyz/#/register",
                      wait_until="networkidle", timeout=60000)
            time.sleep(3)
            page.screenshot(path=os.path.join(
                SCREENSHOT_DIR, "cd520_v3_step1_register.png"))
            print(f"  ✅ 页面: {page.title()} URL: {page.url}", flush=True)

            # ──────── Step 2: 填表 (原生select) ────────
            print("\n[2/6] 填邮箱+密码...", flush=True)
            page.fill('input[placeholder="邮箱"]', prefix)
            time.sleep(0.3)
            # cd520使用原生select元素
            try:
                page.select_option('select', suffix)
                print(f"  select_option('select', '{suffix}')", flush=True)
            except:
                # 备用：可能是NaiveUI
                page.click(".n-base-selection-label")
                time.sleep(0.5)
                page.click(f'text={suffix}')
                print(f"  NaiveUI click: {suffix}", flush=True)
            time.sleep(0.3)

            pws = page.query_selector_all('input[type="password"]')
            pws[0].fill(password)
            time.sleep(0.2)
            if len(pws) >= 2:
                pws[1].fill(password)
            print(f"  邮箱前缀={prefix} 后缀={suffix} 密码x{len(pws)}已填", flush=True)
            page.screenshot(path=os.path.join(
                SCREENSHOT_DIR, "cd520_v3_step2_filled.png"))

            # ──────── Step 3: 发送验证码 ────────
            print("\n[3/6] 发送验证码...", flush=True)
            page.screenshot(path=os.path.join(
                SCREENSHOT_DIR, "cd520_v3_step3a_before_send.png"))
            page.click('button:has-text("发送")')
            time.sleep(1)
            page.screenshot(path=os.path.join(
                SCREENSHOT_DIR, "cd520_v3_step3b_after_send.png"))

            fetcher.mark_send_time()
            print("  验证码已发送，开始精确收码...", flush=True)

            # ──────── Step 4: 收验证码 ────────
            print("\n[4/6] 等待验证码 (发件人: cd520/cd1314)...", flush=True)
            code = fetcher.fetch(
                sender_keywords=["cd520", "cd1314", "nivpn", "cd520.xyz"],
                timeout=90, retries=3)
            if not code:
                print("  ❌ 验证码获取失败", flush=True)
                page.screenshot(path=os.path.join(
                    SCREENSHOT_DIR, "cd520_v3_step4_nocode.png"))
                browser.close()
                return None

            # ──────── Step 5: 填码+注册 ────────
            print(f"\n[5/6] 填码 {code} + 注册...", flush=True)
            page.fill('input[placeholder="邮箱验证码"]', code)
            time.sleep(0.3)
            page.screenshot(path=os.path.join(
                SCREENSHOT_DIR, "cd520_v3_step5a_code_filled.png"))
            page.click('button:has-text("注册")')
            time.sleep(6)
            try:
                page.wait_for_load_state("networkidle", timeout=12000)
            except:
                pass

            cur_url = page.url
            body = page.evaluate("() => document.body.innerText")
            print(f"  注册后URL: {cur_url}", flush=True)
            print(f"  页面内容(前300): {body[:300]}", flush=True)
            page.screenshot(path=os.path.join(
                SCREENSHOT_DIR, "cd520_v3_step5b_after_register.png"))

            # 自动登录(如需) — cd520登录页用完整邮箱+密码
            if "/login" in cur_url or "登入" in body:
                print("  🔐 自动登录...", flush=True)
                page.fill('input[placeholder="邮箱"]', email)
                time.sleep(0.3)
                pw = page.query_selector('input[type="password"]')
                if pw:
                    pw.fill(password)
                time.sleep(0.2)
                for btn_text in ["登入", "登录", "登 录", "Login"]:
                    try:
                        page.click(f'button:has-text("{btn_text}")', timeout=3000)
                        print(f"  点击了「{btn_text}」按钮", flush=True)
                        break
                    except:
                        continue
                time.sleep(5)
                body = page.evaluate("() => document.body.innerText")
                print(f"  登录后: {body[:200]}", flush=True)
                page.screenshot(path=os.path.join(
                    SCREENSHOT_DIR, "cd520_v3_step5c_after_login.png"))

            # ──────── Step 6: 提取订阅链接 ────────
            print("\n[6/6] 提取订阅链接...", flush=True)
            raw_token = page.evaluate("""() => {
                let r = localStorage.getItem('VUE_NAIVE_ACCESS_TOKEN');
                if (!r) {
                    for (let i = 0; i < localStorage.length; i++) {
                        let v = localStorage.getItem(localStorage.key(i));
                        if (v && v.includes('token')) { r = v; break; }
                    }
                }
                return r || 'NONE';
            }""")

            if raw_token and raw_token != 'NONE':
                print(f"  Token前50: {raw_token[:50]}...", flush=True)
                resp = page.evaluate("""
                    (function(rawToken) {
                        let t = '';
                        try {
                            let p = JSON.parse(rawToken);
                            t = p.value || p.token || p;
                        } catch(e) {
                            t = rawToken;
                        }
                        let x = new XMLHttpRequest();
                        x.open('GET', '/api/v1/user/getSubscribe', false);
                        x.setRequestHeader('Authorization', t);
                        try { x.send(); } catch(e) {}
                        return x.responseText;
                    })
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
                    print(f"\n{'='*60}")
                    print(f"  ✅ cd520订阅链接: {sub_url}")
                    print(f"{'='*60}", flush=True)

                    result = {
                        "airport": "cd520",
                        "panel": "cd520.xyz",
                        "email": email,
                        "password": password,
                        "subscribe_url": sub_url,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                    save_dir = os.path.join(
                        os.path.dirname(os.path.dirname(__file__)),
                        "register_results")
                    os.makedirs(save_dir, exist_ok=True)
                    with open(os.path.join(save_dir,
                                           f"cd520_{prefix}.json"),
                              "w", encoding="utf-8") as fp:
                        json.dump(result, fp, ensure_ascii=False, indent=2)
                    print(f"  已保存: register_results/cd520_{prefix}.json",
                          flush=True)
                    return sub_url

            body_text = page.evaluate("() => document.body.innerText")
            m = re.search(r'https?://[^\s]+(?:sub|subscribe|token)[^\s]+',
                          body_text, re.I)
            if m:
                print(f"  页面中找到: {m.group(0)}", flush=True)
            else:
                print("  ⚠️ 未找到订阅链接", flush=True)
                print(f"  完整页面文本: {body_text[:500]}", flush=True)
                time.sleep(10)

            return None

        except Exception as e:
            print(f"  ❌ 异常: {e}", flush=True)
            import traceback
            traceback.print_exc()
            try:
                page.screenshot(path=os.path.join(
                    SCREENSHOT_DIR, "cd520_v3_error.png"))
            except:
                pass
            return None
        finally:
            browser.close()


if __name__ == "__main__":
    EMAIL = sys.argv[1] if len(sys.argv) > 1 else "avery845zqijmkk7bygo@outlook.com"
    PASS = sys.argv[2] if len(sys.argv) > 2 else "VpnTest2026!"
    result = register(EMAIL, PASS)
    if result:
        print(f"\n🎉 cd520注册成功!\n  订阅: {result}")
        sys.exit(0)
    else:
        print(f"\n❌ 注册失败")
        sys.exit(1)
