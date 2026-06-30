#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
倚天屠龙(aiguobit) 注册脚本 V1 — SSO系统 + 完整邮箱
面板: a.aiguobit.com  |  SSO: sso.aiguobit.com  |  系统: 自定义(倚天剑shadow)
用法: python register_aiguobit_v1.py [email] [password]
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
    print(f"\n{'='*60}")
    print(f"  倚天屠龙(aiguobit) V1 注册: {email}")
    print(f"  系统: SSO自定义面板 (sso.aiguobit.com)")
    print(f"{'='*60}", flush=True)

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
            # ──────── Step 1: 打开注册页(会重定向到SSO) ────────
            print("\n[1/7] 打开注册页 (→ sso.aiguobit.com)...", flush=True)
            page.goto("https://a.aiguobit.com/users/register",
                      wait_until="networkidle", timeout=45000)
            time.sleep(3)
            print(f"  ✅ 当前URL: {page.url}", flush=True)
            print(f"  ✅ 页面标题: {page.title()}", flush=True)
            page.screenshot(path=os.path.join(
                SCREENSHOT_DIR, "aiguobit_v1_step1_sso_register.png"))

            # ──────── Step 2: 填表 ────────
            print("\n[2/7] 填邮箱+密码...", flush=True)
            # SSO注册页：完整邮箱 + 验证码 + 密码x2
            page.fill('input[type="email"]', email)
            time.sleep(0.3)

            pws = page.query_selector_all('input[type="password"]')
            pws[0].fill(password)
            time.sleep(0.2)
            if len(pws) >= 2:
                pws[1].fill(password)
            print(f"  邮箱={email} 密码x{len(pws)}已填", flush=True)
            page.screenshot(path=os.path.join(
                SCREENSHOT_DIR, "aiguobit_v1_step2_filled.png"))

            # ──────── Step 3: 发送验证码 ────────
            print("\n[3/7] 发送验证码...", flush=True)
            page.screenshot(path=os.path.join(
                SCREENSHOT_DIR, "aiguobit_v1_step3a_before_send.png"))
            page.click('button:has-text("发送验证码")')
            time.sleep(1)
            page.screenshot(path=os.path.join(
                SCREENSHOT_DIR, "aiguobit_v1_step3b_after_send.png"))

            # 检查是否发送成功
            body_after_send = page.evaluate("() => document.body.innerText")
            print(f"  发送后页面文本(前200): {body_after_send[:200]}", flush=True)

            fetcher.mark_send_time()
            print("  验证码已发送，开始精确收码...", flush=True)

            # ──────── Step 4: 收验证码 ────────
            print("\n[4/7] 等待验证码 (发件人: 倚天剑/aiguobit)...", flush=True)
            code = fetcher.fetch(
                sender_keywords=["倚天剑", "aiguobit", "shadow", "倚天屠龙",
                                  "ytj", "aiguo"],
                timeout=120, retries=3)
            if not code:
                print("  ❌ 验证码获取失败", flush=True)
                print("  尝试不限发件人...", flush=True)
                # 备用：不限发件人
                fetcher2 = OutlookCodeFetcher(email=email)
                fetcher2.mark_send_time()
                code = fetcher2.fetch(sender_keywords=[], timeout=60, retries=2)
                if not code:
                    page.screenshot(path=os.path.join(
                        SCREENSHOT_DIR, "aiguobit_v1_step4_nocode.png"))
                    browser.close()
                    return None

            # ──────── Step 5: 填码+注册 ────────
            print(f"\n[5/7] 填码 {code} + 注册...", flush=True)
            # SSO的验证码输入框是 type=text (第2个input, 在email之后)
            code_inputs = page.query_selector_all('input[type="text"]')
            if code_inputs:
                code_inputs[0].fill(code)
            else:
                # 备用：找非email非password的input
                all_inputs = page.query_selector_all('input')
                for inp in all_inputs:
                    itype = inp.get_attribute('type')
                    if itype not in ('email', 'password'):
                        inp.fill(code)
                        break
            time.sleep(0.3)
            page.screenshot(path=os.path.join(
                SCREENSHOT_DIR, "aiguobit_v1_step5a_code_filled.png"))

            # 点击注册
            page.click('button:has-text("注册")')
            time.sleep(8)

            # 等待SSO重定向回主站
            try:
                page.wait_for_load_state("networkidle", timeout=15000)
            except:
                pass

            cur_url = page.url
            body = page.evaluate("() => document.body.innerText")
            print(f"  注册后URL: {cur_url}", flush=True)
            print(f"  页面内容(前300): {body[:300]}", flush=True)
            page.screenshot(path=os.path.join(
                SCREENSHOT_DIR, "aiguobit_v1_step5b_after_register.png"))

            # ──────── Step 6: 导航到用户面板提取订阅 ────────
            print("\n[6/7] 导航到用户面板提取订阅...", flush=True)

            # 如果还在SSO页面，可能需要手动导航
            if "sso.aiguobit.com" in cur_url:
                print("  仍在SSO，尝试导航回主站...", flush=True)
                page.goto("https://a.aiguobit.com",
                          wait_until="networkidle", timeout=30000)
                time.sleep(3)
                cur_url = page.url
                body = page.evaluate("() => document.body.innerText")
                print(f"  导航后URL: {cur_url}", flush=True)
                print(f"  页面内容(前300): {body[:300]}", flush=True)
                page.screenshot(path=os.path.join(
                    SCREENSHOT_DIR, "aiguobit_v1_step6_home.png"))

            # 尝试找订阅链接 - 探索所有可能的路径
            print("\n  探索订阅入口...", flush=True)

            # 检查页面所有链接
            all_links = page.evaluate("""() => {
                let links = [];
                document.querySelectorAll('a').forEach(a => {
                    let href = a.getAttribute('href') || '';
                    let text = (a.textContent || '').trim();
                    if (href || text) links.push({href, text: text.substring(0,50)});
                });
                return links;
            }""")
            print(f"  页面链接({len(all_links)}个):")
            for link in all_links[:15]:
                print(f"    [{link['text'][:30]}] → {link['href'][:60]}", flush=True)

            # 尝试点击包含"订阅"或"节点"的链接
            sub_clicked = False
            for link_text in ["订阅", "节点", "套餐", "用户中心", "我的", "dashboard",
                               "user", "client", "服务", "product", "plan"]:
                try:
                    page.click(f'a:has-text("{link_text}")', timeout=3000)
                    time.sleep(2)
                    cur_url = page.url
                    body = page.evaluate("() => document.body.innerText")
                    print(f"  点击「{link_text}」→ {cur_url}", flush=True)
                    print(f"  内容(前200): {body[:200]}", flush=True)
                    page.screenshot(path=os.path.join(
                        SCREENSHOT_DIR, f"aiguobit_v1_step6_{link_text}.png"))

                    # 在页面文本中找订阅链接
                    m = re.search(r'https?://[^\s]+(?:sub|subscribe|token|ss$|ssr$|[?&]token=)[^\s]{10,}',
                                  body, re.I)
                    if m:
                        print(f"  🎯 找到订阅: {m.group(0)}", flush=True)
                        sub_clicked = True
                        break
                except:
                    continue

            # ──────── Step 7: 提取订阅链接 ────────
            print("\n[7/7] 提取订阅链接...", flush=True)

            # 方法1: 检查localStorage
            ls_len = page.evaluate("() => localStorage.length")
            for i in range(ls_len):
                key = page.evaluate(f"() => localStorage.key({i})")
                val = page.evaluate(f"() => localStorage.getItem('{key}')")
                print(f"  localStorage[{key}]: {val[:80] if val else 'null'}", flush=True)
                # 匹配订阅URL
                if val:
                    m = re.search(r'(https?://[^\s"]*(?:sub|subscribe|token|ss://|ssr://)[^\s"]+)',
                                  val, re.I)
                    if m:
                        sub_url = m.group(1)
                        print(f"  🎯 localStorage中找到: {sub_url}", flush=True)
                        save_result(email, password, sub_url)
                        return sub_url

            # 方法2: 尝试API请求 (V2Board风格)
            raw_token = page.evaluate("""() => {
                let r = localStorage.getItem('VUE_NAIVE_ACCESS_TOKEN');
                if (!r) r = localStorage.getItem('token');
                if (!r) r = localStorage.getItem('auth_token');
                if (!r) {
                    for (let i = 0; i < localStorage.length; i++) {
                        let k = localStorage.key(i);
                        let v = localStorage.getItem(k);
                        if (v && (v.includes('token') || v.includes('Bearer'))) {
                            r = v; break;
                        }
                    }
                }
                return r || 'NONE';
            }""")

            if raw_token and raw_token != 'NONE':
                print(f"  找到Token: {raw_token[:60]}...", flush=True)
                # 尝试 /api/v1/user/getSubscribe
                resp = page.evaluate("""
                    (function(rawToken) {
                        let t = '';
                        try { let p = JSON.parse(rawToken); t = p.value || p.token || p; }
                        catch(e) { t = rawToken; }
                        let x = new XMLHttpRequest();
                        x.open('GET', '/api/v1/user/getSubscribe', false);
                        x.setRequestHeader('Authorization', t);
                        try { x.send(); } catch(e) {}
                        return JSON.stringify({status: x.status, body: x.responseText});
                    })
                """, raw_token)

                try:
                    api_resp = json.loads(resp)
                    print(f"  getSubscribe: HTTP {api_resp.get('status')}", flush=True)
                    body_text = api_resp.get('body', '')
                    print(f"  响应(前200): {body_text[:200]}", flush=True)

                    # 解析subscribe_url
                    try:
                        d = json.loads(body_text)
                        sub_url = d.get("data", {}).get("subscribe_url", "")
                        if not sub_url:
                            sub_url = d.get("subscribe_url", "")
                    except:
                        urls = re.findall(r'subscribe_url["\s:]+(https?://[^"\s]+)', body_text)
                        sub_url = urls[0] if urls else ""

                    if sub_url:
                        print(f"  🎯 订阅链接: {sub_url}", flush=True)
                        save_result(email, password, sub_url)
                        return sub_url
                except:
                    pass

            # 方法3: 全文搜索订阅链接
            body_full = page.evaluate("() => document.body.innerText")
            for pat in [r'(https?://[^\s]*(?:sub[^\s]{3,}|subscribe[^\s]*|token=[^\s]{10,})[^\s]*)',
                         r'(ssr?://[^\s]+)',
                         r'(trojan://[^\s]+)']:
                matches = re.findall(pat, body_full, re.I)
                if matches:
                    sub_url = matches[0]
                    print(f"  🎯 页面中找到订阅: {sub_url}", flush=True)
                    save_result(email, password, sub_url)
                    return sub_url

            # 如果没有找到，保留浏览器让用户手动查看
            print("\n  ⚠️ 未自动找到订阅链接", flush=True)
            print(f"  完整页面文本(前500): {body_full[:500]}", flush=True)
            print("  浏览器保持打开，请手动检查...", flush=True)
            page.screenshot(path=os.path.join(
                SCREENSHOT_DIR, "aiguobit_v1_step7_no_sub.png"))
            time.sleep(30)

            return None

        except Exception as e:
            print(f"  ❌ 异常: {e}", flush=True)
            import traceback
            traceback.print_exc()
            try:
                page.screenshot(path=os.path.join(
                    SCREENSHOT_DIR, "aiguobit_v1_error.png"))
            except:
                pass
            return None
        finally:
            browser.close()


def save_result(email, password, sub_url):
    """保存注册结果"""
    result = {
        "airport": "aiguobit",
        "panel": "a.aiguobit.com",
        "email": email,
        "password": password,
        "subscribe_url": sub_url,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    save_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "register_results")
    os.makedirs(save_dir, exist_ok=True)
    prefix = email.split("@")[0]
    with open(os.path.join(save_dir, f"aiguobit_{prefix}.json"),
              "w", encoding="utf-8") as fp:
        json.dump(result, fp, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    EMAIL = sys.argv[1] if len(sys.argv) > 1 else "mxih36u8zfmxj42v75fid@outlook.com"
    PASS = sys.argv[2] if len(sys.argv) > 2 else "VpnTest2026!"
    result = register(EMAIL, PASS)
    if result:
        print(f"\n🎉 倚天屠龙注册成功!\n  订阅: {result}")
        sys.exit(0)
    else:
        print(f"\n❌ 注册失败")
        sys.exit(1)
