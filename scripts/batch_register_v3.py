"""批量机场注册引擎 v3 - 修复全部Bug
- 只写文件日志，print用try/catch防GBK崩溃
- 用Playwright内置选择器而非JS返回假名字
- 邮箱正确轮转
- FSCloud/奈云已注册成功的先跳过
"""
import os, sys, json, time, re, traceback, io
from datetime import datetime
from playwright.sync_api import sync_playwright

# 强制UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(__file__))
from outlook_code_reader import load_all_tokens, wait_for_code

PASSWORD = "VpnTest2026!"
ALL_TOKENS = load_all_tokens()
TOKEN_KEYS = list(ALL_TOKENS.keys())
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "register_results")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 日志文件
LOG_FILE = os.path.join(OUTPUT_DIR, f"batch_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
RESULT_FILE = os.path.join(OUTPUT_DIR, "batch_register_results.jsonl")

_email_idx = 0  # 邮箱轮转计数器
_success_emails = set()  # 已成功注册的邮箱

def log(msg):
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
    try:
        print(line, flush=True)
    except:
        pass
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def get_next_email():
    global _email_idx
    if not TOKEN_KEYS:
        return None, None
    email = TOKEN_KEYS[_email_idx % len(TOKEN_KEYS)]
    _email_idx += 1
    token_info = ALL_TOKENS.get(email.lower(), list(ALL_TOKENS.values())[0])
    return email, token_info

def save_result(result):
    with open(RESULT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(result, ensure_ascii=False) + "\n")

# ============ 待注册机场（跳过高价值已注册的） ============
# 奈云v2ny.com - 成功
# FSCloud - 可能成功
SKIP = {"奈云", "ikuuu"}  # ikuuu特殊需要登录后才能注册

AIRPORTS = [
    {"name": "极光加速", "url": "https://jgjs02.com/#/register", "free": "2天10G"},
    {"name": "besnow", "url": "https://besnow.me/index.php#/register", "free": "3天9G"},
    {"name": "TaiShan Net", "url": "https://www.taishan.pro/#/register", "free": "7天10G"},
    {"name": "cd520", "url": "https://cd520.xyz/#/register", "free": "3天5G"},
    {"name": "Mickey", "url": "https://www.mickey.business/#/register", "free": "3天2G"},
    {"name": "农夫山泉", "url": "https://sp.nfsq.me/#/register", "free": "2天1G"},
    {"name": "cocolink", "url": "https://cocolink.org/#/register", "free": "7天64G"},
    {"name": "alori", "url": "https://oukasou.xyz/index.php#/register", "free": "6天50G"},
    {"name": "aimacloud", "url": "https://www.aimacloud.info/#/register", "free": "6天20G"},
    {"name": "Synapse", "url": "https://user.xinna.co/#/register", "free": "3天5G"},
    {"name": "难民机场", "url": "https://nanmin.xyz/#/register", "free": "2天5G"},
    {"name": "BBQ烧烤店", "url": "https://qiaoxbbq.com/#/register", "free": "7天10G"},
    {"name": "猫熊网络", "url": "https://mxwljsq.xyz/auth/register", "free": "3天5G"},
    {"name": "纵横加速", "url": "https://www.okvpn.cc/#/register", "free": "7天2G"},
    {"name": "JetFast", "url": "https://my.jetfast.dev/#/register", "free": "1月5G"},
    {"name": "sockboom", "url": "https://sockboom.love/auth/register", "free": "1天1G"},
    {"name": "KELECLOUD", "url": "https://panel.keleofficial.com/#/register", "free": "1天1G"},
    {"name": "大牛机场", "url": "https://daniu.e300daniu.top/#/register", "free": "1h1G"},
    {"name": "proxyvip", "url": "https://www.proxyvip.xyz/#/register", "free": "1G/天"},
    {"name": "青森云", "url": "https://sub.cccc.gg/auth/register", "free": "6小时"},
    {"name": "大哥云", "url": "https://ab12y.com/#/register", "free": "1天10G"},
    {"name": "极客加速器", "url": "https://board.jike99.xyz/#/register", "free": "3天5G"},
    {"name": "Free机场", "url": "https://zero.76898102.xyz", "free": "白嫖"},
    {"name": "宝贝云", "url": "https://v3ssy.xyz/#/register", "free": "1天2G"},
    {"name": "逗猫", "url": "https://doucat.top/index.php#/register", "free": "1天3G"},
    {"name": "一元机场", "url": "https://xn--4gq62f52gdss.com/#/register", "free": "11元/年50G"},
    {"name": "盛丰", "url": "https://xn--iiq540h.com/auth/register", "free": "5天1G"},
    {"name": "Arisaka", "url": "https://reurl.cc/XG68o7", "free": "10G"},
    {"name": "狗头加速", "url": "https://lksi.xyz/#/register", "free": "5天5G"},
    {"name": "xqc.best", "url": "https://xqc.best/#/register", "free": "待确认"},
    {"name": "tly", "url": "https://tly.sh/", "free": "3天2G+签到"},
    # GFW无法直连的（用特殊方式）
    {"name": "Speedy", "url": "https://cloud.speedypro.xyz/#/register", "free": "7天10G"},
    {"name": "闪电狗", "url": "https://shandiandog.com/#/register", "free": "3天50G"},
    {"name": "qlgq", "url": "https://www.qlgq.top/auth/register", "free": "7天888G"},
    {"name": "速云", "url": "https://zhu.suyun.bio/auth/register", "free": "3天10G"},
    {"name": "雨燕云", "url": "https://yuyan.online/#/register", "free": "8h1G"},
    {"name": "翱翔云", "url": "https://www.aoxiangyun.top/auth/register", "free": "7天20G+签到"},
    {"name": "Bochidev", "url": "https://b0chi.r-yu.me/#/register", "free": "50G不限时"},
]

def find_email_input(page):
    """用Playwright选择器找邮箱输入框 - 返回locator或None"""
    selectors = [
        "input[type='email']",
        "input[placeholder*='邮箱']", "input[placeholder*='Email']", "input[placeholder*='email']",
        "input[name*='email']", "input[name*='username']", "input[name*='account']",
        "input[id*='email']", "input[id*='username']",
    ]
    for sel in selectors:
        el = page.locator(sel).first
        if el.count() > 0:
            return el
    # 最后的兜底：第一个可见的text输入框
    for inp in page.locator("input:visible").all():
        tp = inp.get_attribute("type") or ""
        if tp in ("text", "email", ""):
            return inp
    return None

def find_pw_inputs(page):
    """找所有密码输入框"""
    pws = []
    for sel in ["input[type='password']", "input[placeholder*='密码']", "input[placeholder*='password']", "input[placeholder*='Password']"]:
        for el in page.locator(sel).all():
            if el not in pws:
                pws.append(el)
    return pws[:2]

def find_code_input(page):
    """找验证码输入框"""
    for sel in [
        "input[placeholder*='验证码']", "input[placeholder*='code']", "input[placeholder*='Code']",
        "input[name*='code']", "input[name*='verify']", "input[id*='code']",
    ]:
        el = page.locator(sel).first
        if el.count() > 0:
            return el
    # 兜底：找短输入框（验证码通常4-6位）
    for inp in page.locator("input:visible").all():
        tp = inp.get_attribute("type") or ""
        sz = inp.get_attribute("size") or ""
        maxl = inp.get_attribute("maxlength") or ""
        ph = (inp.get_attribute("placeholder") or "").lower()
        if tp == "number":
            return inp
        if maxl and int(maxl) <= 8 and "password" not in tp:
            # 确认不是邮箱
            val = inp.get_attribute("value") or ""
            if "@" not in val:
                return inp
    return None

def find_send_btn(page):
    """找发送验证码按钮"""
    for sel in [
        "button:has-text('发送验证码')", "button:has-text('获取验证码')",
        "a:has-text('发送验证码')", "span:has-text('获取验证码')",
        "button:has-text('Send Code')", "button:has-text('send')",
        "button:has-text('Send')", "a:has-text('Send Code')",
    ]:
        el = page.locator(sel).first
        if el.count() > 0:
            return el
    return None

def find_submit_btn(page):
    """找提交/注册按钮"""
    for sel in [
        "button:has-text('注册')", "button:has-text('注 册')",
        "button:has-text('确定')", "button:has-text('提交')",
        "button:has-text('Register')", "button:has-text('Sign Up')",
        "button[type='submit']", "input[type='submit']",
        "a:has-text('注册')", "button:has-text('创 建')",
        "button:has-text('Sign')", "button[type='button']:has-text('注册')",
    ]:
        el = page.locator(sel).first
        if el.count() > 0:
            return el
    return None

def register_one(browser, airport, email, token_info):
    name = airport["name"]
    url = airport["url"]
    free = airport.get("free", "?")
    result = {"name": name, "url": url, "free": free, "email": email, "success": False, "ts": datetime.now().isoformat()}
    
    page = browser.new_page()
    try:
        log(f"[{name}] START | {free} | {email} | {url}")
        
        # 1. 导航 - 用load而非networkidle避免超时
        try:
            page.goto(url, wait_until="load", timeout=20000)
            page.wait_for_timeout(3000)
        except Exception as e:
            log(f"[{name}] NAV ERR: {str(e)[:100]}")
            # 即使导航失败也继续尝试
            try:
                page.wait_for_timeout(3000)
            except:
                pass
        
        cur_url = page.url
        log(f"[{name}] URL={cur_url}")
        
        # 检查页面是否加载成功
        try:
            body = page.evaluate("document.body ? document.body.innerText.substring(0,300) : 'NO_BODY'")
        except:
            body = "EVAL_FAILED"
        
        # 快速判断：CF拦截
        if "checking your browser" in body.lower() or "cf-browser-verification" in body.lower():
            log(f"[{name}] Cloudflare waiting...")
            page.wait_for_timeout(12000)
            try:
                body = page.evaluate("document.body.innerText.substring(0,300)")
            except:
                pass
        
        # 检查是否被重定向或DNS劫持
        skip_words = ["quickresultsonline", "parking", "domain for sale", "buy this domain"]
        if any(w in body.lower() for w in skip_words):
            log(f"[{name}] SKIP: DNS hijacked/domain parked")
            result["error"] = "dns_hijack"
            page.close()
            return result
        
        # 2. 填邮箱
        email_el = find_email_input(page)
        if not email_el:
            log(f"[{name}] FAIL: no email input")
            result["error"] = "no_email_input"
            page.close()
            return result
        
        try:
            email_el.click()
        except:
            pass
        page.wait_for_timeout(300)
        email_el.fill(email)
        page.wait_for_timeout(300)
        log(f"[{name}] Filled email")
        
        # 3. 填密码
        pw_els = find_pw_inputs(page)
        pw_count = 0
        for pw_el in pw_els:
            try:
                pw_el.fill(PASSWORD)
                pw_count += 1
                page.wait_for_timeout(200)
            except:
                pass
        log(f"[{name}] Filled {pw_count} pw")
        
        # 4. 判断是否需要验证码
        needs_code = False
        send_btn = find_send_btn(page)
        if send_btn:
            try:
                send_btn.click()
                page.wait_for_timeout(2000)
                needs_code = True
                log(f"[{name}] Clicked send code")
            except:
                pass
        
        # 也检查验证码输入框
        code_el = find_code_input(page)
        if code_el and not needs_code:
            needs_code = True
            log(f"[{name}] Code input detected")
        
        # 5. 等待验证码
        if needs_code:
            log(f"[{name}] Waiting code (90s)...")
            code, err = wait_for_code(email, token_info, timeout=90, interval=4)
            if code:
                # 重新找验证码输入框
                code_el = find_code_input(page)
                if code_el:
                    try:
                        code_el.fill(code)
                        page.wait_for_timeout(500)
                        log(f"[{name}] Filled code: {code}")
                    except Exception as e:
                        log(f"[{name}] Code fill err: {e}")
                else:
                    log(f"[{name}] WARN: code {code} but no input")
                    result["error"] = f"code_no_input:{code}"
                    page.close()
                    return result
            else:
                log(f"[{name}] WARN: no code ({err})")
        
        # 6. 提交
        submit_btn = find_submit_btn(page)
        if submit_btn:
            try:
                submit_btn.click()
                page.wait_for_timeout(5000)
                log(f"[{name}] Clicked submit")
            except Exception as e:
                log(f"[{name}] Submit err: {e}")
        else:
            log(f"[{name}] No submit btn, trying Enter")
            try:
                page.keyboard.press("Enter")
                page.wait_for_timeout(4000)
            except:
                pass
        
        # 7. 检查结果
        final_url = page.url
        try:
            final_body = page.evaluate("document.body ? document.body.innerText.substring(0,300) : ''")
        except:
            final_body = ""
        
        fail_terms = ["验证码错误", "邮箱已注册", "已被注册", "已存在", "格式不正确", "请重试", "注册失败"]
        
        # 成功的标志：跳转到非注册/登录页
        still_on_register = any(w in final_url.lower() for w in ["/register", "/auth/register", "/signup"])
        on_login = any(w in final_url.lower() for w in ["/login", "/auth/login"])
        has_fail = any(w in final_body.lower() for w in fail_terms)
        
        if not still_on_register and not on_login and not has_fail:
            result["success"] = True
            log(f"[{name}] SUCCESS! url={final_url}")
            
            # 提取订阅
            try:
                sub = page.evaluate("localStorage.getItem('subscribe_url')")
                if sub:
                    result["subscribe_url"] = sub
                    log(f"[{name}] Sub URL found: {sub[:60]}")
                else:
                    token = page.evaluate("localStorage.getItem('VUE_NAIVE_ACCESS_TOKEN')")
                    if token:
                        result["api_token"] = token[:80]
                        log(f"[{name}] Token extracted")
            except Exception as e:
                log(f"[{name}] Extract err: {e}")
            
            try:
                ss = os.path.join(OUTPUT_DIR, f"screenshot_{name}.png")
                page.screenshot(path=ss)
            except:
                pass
        else:
            err = final_body[:150]
            result["error"] = err
            log(f"[{name}] FAIL: {err}")
            try:
                ss = os.path.join(OUTPUT_DIR, f"screenshot_{name}_fail.png")
                page.screenshot(path=ss)
            except:
                pass
        
    except Exception as e:
        result["error"] = str(e)[:300]
        log(f"[{name}] EXC: {str(e)[:150]}")
        try:
            ss = os.path.join(OUTPUT_DIR, f"screenshot_{name}_err.png")
            page.screenshot(path=ss)
        except:
            pass
    finally:
        page.close()
    
    save_result(result)
    return result

def main():
    log("=" * 50)
    log(f"BATCH REGISTER v3 START - Tokens:{len(ALL_TOKENS)} Targets:{len(AIRPORTS)}")
    
    success = 0
    total = 0
    _email_idx = 0
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            channel="msedge",
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        for i, airport in enumerate(AIRPORTS):
            email, token_info = get_next_email()
            if not email:
                log("NO MORE EMAILS!")
                break
            
            log(f"[{i+1}/{len(AIRPORTS)}] {airport['name']} <- {email}")
            result = register_one(browser, airport, email, token_info)
            total += 1
            if result["success"]:
                success += 1
                _success_emails.add(email)
            
            time.sleep(2)
        
        browser.close()
    
    log(f"\n=== FINAL: {success}/{total} success ===")
    log(f"Results: {RESULT_FILE}")
    log(f"Log: {LOG_FILE}")

if __name__ == "__main__":
    main()
