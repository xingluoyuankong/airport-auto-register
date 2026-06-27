"""通用Playwright浏览器注册引擎 - 三大系统全覆盖"""
import os, sys, json, time
from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(__file__))
from outlook_code_reader import load_all_tokens, wait_for_code

PASSWORD = "VpnTest2026!"
ALL_TOKENS = load_all_tokens()
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "register_results")

# ============ SSPANEL系统 (稳连云/大象网络/三毛) ============
def register_sspanel(name, login_url, register_url, email_domain="@outlook.com", use_prefix=True, invite_code=""):
    """SSPANEL/V2Board通用注册 - 自动判断是否需要验证码"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, channel="msedge")
        page = browser.new_page()
        result = {"name": name, "success": False}
        
        try:
            page.goto(register_url, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(3000)
            
            # 选择注册邮箱
            email_full = ALL_TOKENS.get(list(ALL_TOKENS.keys())[0], {}).get("email", "")
            if not email_full:
                print(f"[{name}] No email available")
                browser.close()
                return result
            
            # 找输入框
            inputs = page.query_selector_all("input")
            email_input = None
            pw_inputs = []
            for inp in inputs:
                ph = (inp.get_attribute("placeholder") or "").lower()
                nm = (inp.get_attribute("name") or "").lower()
                tp = (inp.get_attribute("type") or "")
                if any(k in ph for k in ["邮箱", "email", "e-mail"]):
                    email_input = inp
                elif tp == "password" or "密码" in ph or "password" in ph:
                    pw_inputs.append(inp)
            
            if not email_input:
                print(f"[{name}] Email input not found")
                browser.close()
                return result
            
            # 填表
            if use_prefix and "@" not in email_full.split("@")[0]:
                email_input.fill(f"{email_full.split('@')[0]}{email_domain}")
            else:
                email_input.fill(email_full)
            
            for pw in pw_inputs[:2]:
                pw.fill(PASSWORD)
            
            # 找注册按钮
            reg_btn = page.query_selector("button:has-text('注册'),button:has-text('创建'),button:has-text('Register')")
            if not reg_btn:
                print(f"[{name}] Register button not found")
                browser.close()
                return result
            
            reg_btn.click()
            page.wait_for_timeout(5000)
            
            # 检查是否需要验证码
            inner = page.evaluate("document.body.innerText")
            if "验证码" in inner or "verification" in inner or "code" in inner.lower():
                print(f"[{name}] Needs verification code, waiting...")
                code, err = wait_for_code(email_full, ALL_TOKENS.get(email_full.lower(), list(ALL_TOKENS.values())[0]), timeout=60)
                if code:
                    # 找验证码输入框
                    code_inputs = page.query_selector_all("input[placeholder*='验证'],input[placeholder*='code'],input[name*='code']")
                    if code_inputs:
                        code_inputs[0].fill(code)
                        reg_btn.click()
                        page.wait_for_timeout(5000)
            
            # 检查是否跳转成功
            if "dashboard" in page.url.lower() or "ucenter" in page.url.lower() or "user" in page.url.lower():
                result["success"] = True
                result["email"] = email_full
                
                # 提取订阅链接
                sub_url = page.evaluate("localStorage.getItem('subscribe_url')")
                if sub_url:
                    result["subscribe_url"] = sub_url
                else:
                    token = page.evaluate("localStorage.getItem('VUE_NAIVE_ACCESS_TOKEN')")
                    if token:
                        result["api_token"] = token[:80]
            
            page.wait_for_timeout(2000)
            browser.close()
            
        except Exception as e:
            print(f"[{name}] Error: {e}")
            browser.close()
        
        return result

# ============ hidexx系统 (aiguobit) ============
def register_hidexx(name, base_url):
    """hidexx/倚天剑系统注册"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, channel="msedge")
        page = browser.new_page()
        result = {"name": name, "success": False}
        
        try:
            page.goto(f"{base_url}/users/register", wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(3000)
            
            email_full = list(ALL_TOKENS.keys())[0] if ALL_TOKENS else ""
            if not email_full:
                browser.close()
                return result
            
            token_info = ALL_TOKENS.get(email_full.lower(), list(ALL_TOKENS.values())[0])
            
            # 填邮箱
            email_input = page.query_selector("input[placeholder*='email'],input[placeholder*='邮箱']")
            if email_input:
                email_input.fill(email_full)
            
            # 点发送验证码
            send_btn = page.query_selector("button:has-text('发送验证码'),button:has-text('Send')")
            if send_btn:
                send_btn.click()
                page.wait_for_timeout(1000)
            
            # 等验证码
            code, _ = wait_for_code(email_full, token_info, timeout=60)
            if not code:
                print(f"[{name}] No code received")
                browser.close()
                return result
            
            # 填验证码和密码
            code_input = page.query_selector("input[placeholder*='验证码'],input[type='text']:not([placeholder*='email'])")
            if code_input:
                code_input.fill(code)
            
            pw_inputs = page.query_selector_all("input[type='password']")
            for pw in pw_inputs[:2]:
                pw.fill(PASSWORD)
            
            # 注册
            reg_btn = page.query_selector("button:has-text('注册'),button:has-text('Register')")
            if reg_btn:
                reg_btn.click()
                page.wait_for_timeout(5000)
            
            if "ucenter" in page.url.lower() or "login" not in page.url.lower():
                result["success"] = True
                result["email"] = email_full
            
            browser.close()
        except Exception as e:
            print(f"[{name}] Error: {e}")
            browser.close()
        
        return result

if __name__ == "__main__":
    # 测试
    res = register_sspanel("稳连云", "https://wenlianyun.com/#/login",
                           "https://wenlianyun.com/#/register")
    print(json.dumps(res, ensure_ascii=False, indent=2))
