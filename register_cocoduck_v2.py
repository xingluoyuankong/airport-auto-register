#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COCODUCK 注册机 v2 — 基于深度逆向分析重写
面板: dash.cocoduck.co (SSPanel-UIM)
官网: cocoduck.cc
注册: https://dash.cocoduck.co/auth/register?code=8c1073605d
表单: B型（完整邮箱输入，无域名下拉框）
邀请码: 8c1073605d（URL参数自动填充）
免费: 新用户1天2GB试用
订阅域名: sub.cocoduck.cc

用法: python register_cocoduck_v2.py [email] [password]
"""
import sys, os, json, time, io, random
try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from playwright.sync_api import sync_playwright
from graph_mail import wait_for_code

# === 配置 ===
INVITE_CODE = "8c1073605d"
REGISTER_URL = f"https://dash.cocoduck.co/auth/register?code={INVITE_CODE}"
LOGIN_URL = "https://dash.cocoduck.co/auth/login"
DASHBOARD_URL = "https://dash.cocoduck.co/user"

NICKNAMES = ["疾风剑豪", "暗影刺客", "狂暴战车", "幽灵特工", "风暴猎手", 
             "极光之翼", "烈焰凤凰", "深海巨兽", "雷霆之怒", "星辰大海"]

def random_nickname():
    return random.choice(NICKNAMES) + str(random.randint(100, 999))

def run(email_addr, reg_password):
    print(f"\n{'='*60}", flush=True)
    print(f"  COCODUCK v2 注册机")
    print(f"  邮箱: {email_addr}")
    print(f"{'='*60}", flush=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=False,
            args=["--ignore-certificate-errors",
                  "--disable-blink-features=AutomationControlled",
                  "--no-sandbox"])
        ctx = browser.new_context(viewport={"width": 1280, "height": 900},
            ignore_https_errors=True, locale="zh-CN")
        page = ctx.new_page()
        
        # 注入反检测
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => false});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh', 'en']});
            window.chrome = {runtime: {}};
        """)
        
        result = {"airport": "COCODUCK", "panel": "dash.cocoduck.co",
                  "email": email_addr, "password": reg_password, "subscribe_url": ""}
        
        try:
            # ===== STEP 1: 打开注册页 =====
            print("[1/8] 加载注册页...", flush=True)
            page.goto(REGISTER_URL, wait_until="domcontentloaded", timeout=25000)
            time.sleep(2)
            
            # 检查是否成功加载
            title = page.title()
            print(f"  页面标题: {title}", flush=True)
            
            # 如果有CF验证，等待
            cf_attempts = 0
            while cf_attempts < 30:
                cf = page.query_selector('iframe[src*="challenges.cloudflare.com"], #cf-turnstile, .cf-turnstile')
                if not cf:
                    break
                print(f"  [CF验证] 等待中 ({cf_attempts+1}/30)...", flush=True)
                time.sleep(3)
                cf_attempts += 1
            
            if cf_attempts >= 30:
                print("  [CF验证] 超时!", flush=True)
            
            page.screenshot(path=os.path.join(
                os.path.dirname(__file__), "screenshots", "cocoduck_v2_step1_register.png"))
            
            # ===== STEP 2: 填表单 =====
            print("[2/8] 填写注册表单...", flush=True)
            
            # 填充昵称（已有预填，覆盖）
            nick_input = page.locator('input[placeholder="昵称"], input[name="nickname"], #nickname').first
            if nick_input.is_visible():
                nick_input.click()
                nick_input.fill("")
                nick = random_nickname()
                nick_input.fill(nick)
                print(f"  昵称: {nick}", flush=True)
            
            # 填充邮箱
            email_input = page.locator('input[placeholder*="邮箱"], input[name="email"], #email').first
            if email_input.is_visible():
                email_input.fill(email_addr)
                print(f"  邮箱: {email_addr}", flush=True)
            else:
                print("  [错误] 找不到邮箱输入框!", flush=True)
                page.screenshot(path=os.path.join(
                    os.path.dirname(__file__), "screenshots", "cocoduck_v2_error_no_email.png"))
            
            # 填充密码
            pass_inputs = page.locator('input[type="password"]')
            count = pass_inputs.count()
            print(f"  密码框数量: {count}", flush=True)
            if count >= 1:
                pass_inputs.nth(0).fill(reg_password)
            if count >= 2:
                pass_inputs.nth(1).fill(reg_password)
            print(f"  密码已填写", flush=True)
            
            page.screenshot(path=os.path.join(
                os.path.dirname(__file__), "screenshots", "cocoduck_v2_step2_filled.png"))
            
            # ===== STEP 3: 发送验证码 =====
            print("[3/8] 发送验证码...", flush=True)
            
            # 点击"获取"按钮
            get_code_btn = page.locator('button:has-text("获取")').first
            if get_code_btn.is_visible():
                get_code_btn.click()
                print("  已点击【获取】按钮", flush=True)
            else:
                print("  [错误] 找不到获取验证码按钮!", flush=True)
                page.screenshot(path=os.path.join(
                    os.path.dirname(__file__), "screenshots", "cocoduck_v2_error_no_get_btn.png"))
                browser.close()
                return None
            
            time.sleep(2)
            page.screenshot(path=os.path.join(
                os.path.dirname(__file__), "screenshots", "cocoduck_v2_step3_sent.png"))
            
            # ===== STEP 4: 收验证码 =====
            print("[4/8] Graph API收验证码 (等90秒)...", flush=True)
            code, err = wait_for_code(email_addr, timeout=90)
            
            if not code:
                print(f"  [失败] 未收到验证码: {err}", flush=True)
                page.screenshot(path=os.path.join(
                    os.path.dirname(__file__), "screenshots", "cocoduck_v2_error_no_code.png"))
                browser.close()
                return None
            
            print(f"  验证码: {code}", flush=True)
            
            # ===== STEP 5: 填验证码 =====
            print("[5/8] 填写验证码...", flush=True)
            
            # COCODUCK的验证码输入框特征是placeholder含"收不到邮件请查看垃圾箱"
            code_input = page.locator('input[placeholder*="收不到"], input[placeholder*="垃圾箱"], '
                                      'input[name="email_code"], input[name="code"]').first
            if code_input.is_visible():
                code_input.fill(code)
                print(f"  验证码已填写", flush=True)
            else:
                print("  [警告] 未找到验证码输入框，尝试通用方法", flush=True)
                # 尝试找最后一个textbox
                all_inputs = page.locator('input[type="text"], input:not([type])')
                if all_inputs.count() > 0:
                    last_input = all_inputs.nth(all_inputs.count() - 1)
                    last_input.fill(code)
            
            # ===== STEP 6: 清除弹窗遮罩 + 勾选协议 =====
            print("[6/8] 清除弹窗+勾选协议...", flush=True)
            
            # 先移除所有modal遮罩（验证码发送成功弹窗会挡住checkbox）
            page.evaluate("""() => {
                // 移除modal背景遮罩
                document.querySelectorAll('.modal-backdrop').forEach(function(e) { e.remove(); });
                // 隐藏所有modal
                document.querySelectorAll('.modal.show').forEach(function(e) {
                    e.classList.remove('show');
                    e.style.display = 'none';
                });
            }""")
            time.sleep(0.5)
            
            # 用JS直接勾选协议
            page.evaluate("""() => {
                let cb = document.getElementById('tos') || document.querySelector('input[type=checkbox]');
                if (cb) {
                    cb.checked = true;
                    cb.dispatchEvent(new Event('change', {bubbles: true}));
                }
            }""")
            print("  协议已勾选(Javascript)", flush=True)
            
            # ===== STEP 7: 提交注册 =====
            print("[7/8] 提交注册...", flush=True)
            
            register_btn = page.locator('button:has-text("注册新账户")').first
            if register_btn.is_visible():
                register_btn.click()
                print("  已点击【注册新账户】", flush=True)
            else:
                # 备用：找提交按钮
                submit_btn = page.locator('button[type="submit"]').first
                if submit_btn.is_visible():
                    submit_btn.click()
                    print("  已点击submit按钮", flush=True)
                else:
                    print("  [错误] 找不到注册按钮!", flush=True)
                    browser.close()
                    return None
            
            # 等待注册结果
            time.sleep(5)
            page.wait_for_load_state("networkidle", timeout=15000)
            
            current_url = page.url
            print(f"  注册后URL: {current_url}", flush=True)
            
            page.screenshot(path=os.path.join(
                os.path.dirname(__file__), "screenshots", "cocoduck_v2_step7_after_register.png"))
            
            # ===== STEP 8: 登录并提取订阅 =====
            print("[8/8] 确保登录+提取订阅...", flush=True)
            
            # 如果注册成功直接跳转到了/user，跳过登录
            if "/user" not in current_url and "/login" not in current_url:
                # 可能需要手动导航到登录页
                page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=15000)
                time.sleep(2)
            
            # 如果当前在登录页，执行登录
            if "/auth/login" in page.url or "/login" in page.url:
                print("  在登录页，执行登录...", flush=True)
                email_field = page.locator('#email, input[name="email"]').first
                if email_field.is_visible():
                    email_field.fill(email_addr)
                pass_field = page.locator('#passwd, input[name="passwd"]').first
                if pass_field.is_visible():
                    pass_field.fill(reg_password)
                
                login_btn = page.locator('button:has-text("登录")').first
                if login_btn.is_visible():
                    login_btn.click()
                    page.wait_for_load_state("networkidle", timeout=15000)
                    time.sleep(3)
                    print(f"  登录后URL: {page.url}", flush=True)
            
            # 确保在Dashboard
            if "/user" not in page.url:
                page.goto(DASHBOARD_URL, wait_until="networkidle", timeout=15000)
                time.sleep(2)
            
            # 关闭公告弹窗
            try:
                got_it_btn = page.locator('button:has-text("我知道了")')
                if got_it_btn.is_visible():
                    got_it_btn.click()
                    time.sleep(1)
                    print("  公告弹窗已关闭", flush=True)
            except:
                pass
            
            page.screenshot(path=os.path.join(
                os.path.dirname(__file__), "screenshots", "cocoduck_v2_step8_dashboard.png"))
            
            # 提取订阅链接 — SSPanel方法: 点击Clash按钮劫持clipboard
            print("  提取订阅链接...", flush=True)
            
            # 方法1: 劫持clipboard API
            sub_url = page.evaluate("""() => {
                let oldWrite = navigator.clipboard.writeText;
                window.__cocoduck_sub = '';
                navigator.clipboard.writeText = function(text) {
                    window.__cocoduck_sub = text;
                    return oldWrite.call(navigator.clipboard, text);
                };
                
                // 找到Clash订阅按钮并点击
                let btns = document.querySelectorAll('button');
                for (let i = 0; i < btns.length; i++) {
                    if (btns[i].textContent.includes('Clash')) {
                        btns[i].click();
                        break;
                    }
                }
                
                // 等待一下让clipboard被填充
                return new Promise(resolve => {
                    setTimeout(() => resolve(window.__cocoduck_sub || ''), 500);
                });
            }""")
            
            if sub_url:
                print(f"  订阅链接: {sub_url}", flush=True)
                result["subscribe_url"] = sub_url
            else:
                # 方法2: 查找data-clipboard-text
                sub_url = page.evaluate("""() => {
                    let els = document.querySelectorAll('[data-clipboard-text]');
                    for (let e of els) {
                        let t = e.getAttribute('data-clipboard-text');
                        if (t && t.includes('://')) return t;
                    }
                    return '';
                }""")
                if sub_url:
                    print(f"  订阅链接(data): {sub_url}", flush=True)
                    result["subscribe_url"] = sub_url
                else:
                    print("  [警告] 未能自动提取订阅链接，需手动", flush=True)
                    result["subscribe_url"] = ""
            
            # 保存结果
            os.makedirs(os.path.join(os.path.dirname(__file__), "register_results"), exist_ok=True)
            result_file = os.path.join(os.path.dirname(__file__), "register_results",
                                       f"cocoduck_v2_{email_addr.split('@')[0]}.json")
            with open(result_file, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"  结果已保存: {result_file}", flush=True)
            
            return result
            
        except Exception as e:
            print(f"  [异常] {e}", flush=True)
            import traceback
            traceback.print_exc()
            try:
                page.screenshot(path=os.path.join(
                    os.path.dirname(__file__), "screenshots", "cocoduck_v2_error.png"))
            except:
                pass
            return None
        finally:
            time.sleep(2)
            browser.close()

if __name__ == "__main__":
    EMAIL = sys.argv[1] if len(sys.argv) > 1 else "mxih36u8zfmxj42v75fid@outlook.com"
    PWD = sys.argv[2] if len(sys.argv) > 2 else "VpnTest2026!"
    
    # 确保截图目录存在
    os.makedirs(os.path.join(os.path.dirname(__file__), "screenshots"), exist_ok=True)
    
    result = run(EMAIL, PWD)
    
    if result and result.get("subscribe_url"):
        print(f"\n{'='*60}")
        print(f"  注册成功!")
        print(f"  订阅: {result['subscribe_url']}")
        print(f"{'='*60}")
        sys.exit(0)
    else:
        print(f"\n  注册失败!")
        sys.exit(1)
