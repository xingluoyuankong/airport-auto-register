"""批量机场注册引擎 v4 - 最终修复版
- besnow等拒收Outlook：自动检测跳过
- 等待DOM加载后再检测表单
- disabled按钮用JS强制点击
- 只跑确认能注册的机场
"""
import os, sys, json, time, re, io
from datetime import datetime
from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(__file__))
from outlook_code_reader import load_all_tokens, wait_for_code

PASSWORD = "VpnTest2026!"
ALL_TOKENS = load_all_tokens()
TOKEN_KEYS = list(ALL_TOKENS.keys())
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "register_results")
os.makedirs(OUTPUT_DIR, exist_ok=True)

LOG_FILE = os.path.join(OUTPUT_DIR, f"batch_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
RESULT_FILE = os.path.join(OUTPUT_DIR, "batch_register_results.jsonl")
_email_idx = 0

def log(msg):
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
    try: print(line, flush=True)
    except: pass
    with open(LOG_FILE, "a", encoding="utf-8") as f: f.write(line + "\n")

def get_next_email():
    global _email_idx
    if not TOKEN_KEYS: return None, None
    email = TOKEN_KEYS[_email_idx % len(TOKEN_KEYS)]
    _email_idx += 1
    return email, ALL_TOKENS.get(email.lower(), list(ALL_TOKENS.values())[0])

def save_result(r):
    with open(RESULT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

AIRPORTS = [
    # ---- 第1批：已确认在线+接受Outlook的 ----
    {"name": "极光加速", "url": "https://jgjs02.com/#/register", "free": "2天10G"},
    {"name": "FSCloud", "url": "https://dash.fscloud.cc/#/register", "free": "3天10G"},
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
    {"name": "Speedy", "url": "https://cloud.speedypro.xyz/#/register", "free": "7天10G"},
    {"name": "闪狐云", "url": "https://shanhuyun.com", "free": "待确认"},
    {"name": "尔湾云", "url": "https://erwangyun.com", "free": "签到送"},
    {"name": "疾风云", "url": "https://jifengyun.com", "free": "签到送"},
]

# 已知拒收Outlook的机场
MS_REJECT = {
    "besnow": "only gmail/qq/163/126/foxmail/icloud",
    "雨燕云": "rejects Microsoft",
    "GLaDOS": "rejects Microsoft",
    "ikuuu": "needs custom handling",
}

NON_MS_EMAILS = ["@gmail.com", "@qq.com", "@163.com", "@126.com", "@proton.me"]

def detect_email_restriction(body):
    """从页面文本检测邮箱限制"""
    non_ms = ["@gmail.com", "@qq.com", "@163.com", "@126.com", "@foxmail.com", "@icloud.com", "@proton.me"]
    restrict = [e for e in non_ms if e.lower() in body.lower()]
    if restrict:
        # 也检查是否允许outlook/hotmail
        for allow in ["outlook", "hotmail", "@live"]:
            if allow.lower() in body.lower():
                return None  # Outlook allowed
        return restrict
    return None

def force_click(page, sel):
    """强制点击按钮（处理disabled情况）"""
    el = page.locator(sel).first
    if el.count() == 0:
        return False
    try:
        el.click(timeout=5000)
        return True
    except:
        try:
            # JS强制点击
            el.evaluate("el => el.click()")
            return True
        except:
            try:
                el.dispatch_event("click")
                return True
            except:
                return False

def register_one(browser, airport, email, token_info):
    name = airport["name"]
    url = airport["url"]
    free = airport.get("free", "?")
    r = {"name": name, "url": url, "free": free, "email": email, "success": False, "ts": datetime.now().isoformat()}
    
    page = browser.new_page()
    try:
        log(f"[{name}] START | {free} | {email}")
        
        # 1. 导航
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=15000)
            page.wait_for_timeout(2000)
        except Exception as e:
            log(f"[{name}] NAV: {str(e)[:80]}")
            page.wait_for_timeout(2000)
        
        # 等待DOM里有input
        try:
            page.wait_for_selector("input", timeout=5000)
        except:
            pass
        
        cur_url = page.url
        try:
            body = page.evaluate("document.body ? document.body.innerText.substring(0,500) : 'NO'")
        except:
            body = ""
        
        log(f"[{name}] URL={cur_url}")
        
        # 检测邮箱限制
        ms_rej = detect_email_restriction(body)
        if ms_rej:
            log(f"[{name}] SKIP: MS email rejected, needs {ms_rej}")
            r["error"] = f"ms_rejected:{ms_rej}"
            page.close()
            return r
        
        # DNS劫持检测
        if any(w in body.lower() for w in ["quickresultsonline", "domain for sale"]):
            log(f"[{name}] SKIP: DNS hijacked")
            r["error"] = "dns_hijack"
            page.close()
            return r
        
        # CF挑战
        if "checking" in body.lower() and "cloudflare" in body.lower():
            log(f"[{name}] CF wait...")
            page.wait_for_timeout(10000)
        
        # 2. 填邮箱 - 多种选择器尝试
        email_sel = "input[type='email'], input[placeholder*='邮箱'], input[placeholder*='Email'], input[name*='email'], input[name*='username'], input[id*='email']"
        email_el = page.locator(email_sel).first
        if email_el.count() == 0:
            # fallback: 第一个text输入框
            for inp in page.locator("input:visible").all():
                tp = inp.get_attribute("type") or ""
                if tp in ("text", "email", ""):
                    email_el = inp
                    break
        
        if email_el.count() == 0:
            log(f"[{name}] FAIL: no email input")
            r["error"] = "no_email_input"
            page.close()
            return r
        
        email_el.fill(email)
        page.wait_for_timeout(300)
        log(f"[{name}] Filled email")
        
        # 3. 填密码
        pw_count = 0
        for pw in page.locator("input[type='password']").all()[:2]:
            try:
                pw.fill(PASSWORD)
                pw_count += 1
                page.wait_for_timeout(200)
            except:
                pass
        log(f"[{name}] PW: {pw_count}")
        
        # 4. 发送验证码
        needs_code = False
        send_btn = page.locator("button:has-text('发送验证码'), button:has-text('获取验证码'), a:has-text('发送验证码'), button:has-text('Send Code')").first
        if send_btn.count() > 0:
            try:
                send_btn.click()
                page.wait_for_timeout(2000)
                needs_code = True
                log(f"[{name}] Sent code")
            except:
                pass
        
        # 也检查验证码输入框
        code_sel = "input[placeholder*='验证码'], input[placeholder*='code'], input[name*='code'], input[placeholder*='Code']"
        code_el = page.locator(code_sel).first
        if code_el.count() > 0:
            needs_code = True
        
        # 5. 等待验证码
        if needs_code:
            log(f"[{name}] Waiting code (90s)...")
            code, err = wait_for_code(email, token_info, timeout=90, interval=3)
            if code:
                code_el = page.locator(code_sel).first
                if code_el.count() > 0:
                    code_el.fill(code)
                    page.wait_for_timeout(500)
                    log(f"[{name}] Code: {code}")
                else:
                    # 找number输入框或短输入框
                    for inp in page.locator("input:visible").all():
                        tp = inp.get_attribute("type") or "text"
                        maxl = inp.get_attribute("maxlength") or ""
                        val = inp.get_attribute("value") or ""
                        if (tp == "number" or (maxl and int(maxl) <= 8)) and "@" not in val:
                            inp.fill(code)
                            page.wait_for_timeout(500)
                            log(f"[{name}] Code(fallback): {code}")
                            break
            else:
                log(f"[{name}] No code ({err})")
        
        # 6. 提交
        submit_sel = "button:has-text('注册'), button:has-text('确定'), button:has-text('提交'), button:has-text('Register'), button[type='submit']"
        submit_btn = page.locator(submit_sel).first
        if submit_btn.count() > 0:
            clicked = force_click(page, submit_sel)
            if not clicked:
                log(f"[{name}] Submit btn not clickable")
            else:
                log(f"[{name}] Clicked submit")
                page.wait_for_timeout(5000)
        else:
            # 直接回车
            log(f"[{name}] No submit, pressing Enter")
            page.keyboard.press("Enter")
            page.wait_for_timeout(4000)
        
        # 7. 检查结果
        final_url = page.url
        try:
            final_body = page.evaluate("document.body ? document.body.innerText.substring(0,300) : ''")
        except:
            final_body = ""
        
        fail_words = ["验证码错误", "邮箱已注册", "已被注册", "已存在", "格式不正确", "请重试", "注册失败"]
        still_register = any(w in final_url.lower() for w in ["/register", "/auth/register", "/signup"])
        on_login = any(w in final_url.lower() for w in ["/login", "/auth/login"])
        
        if not still_register and not on_login and not any(w in final_body.lower() for w in fail_words):
            r["success"] = True
            log(f"[{name}] SUCCESS! {final_url}")
            
            # 提取订阅
            try:
                sub = page.evaluate("localStorage.getItem('subscribe_url')")
                if sub: r["subscribe_url"] = sub
                token = page.evaluate("localStorage.getItem('VUE_NAIVE_ACCESS_TOKEN')")
                if token: r["api_token"] = token[:80]
            except: pass
            
            try:
                page.screenshot(path=os.path.join(OUTPUT_DIR, f"screenshot_{name}.png"))
            except: pass
        else:
            r["error"] = final_body[:200]
            log(f"[{name}] FAIL: {final_body[:80]}")
            try:
                page.screenshot(path=os.path.join(OUTPUT_DIR, f"screenshot_{name}_fail.png"))
            except: pass
        
    except Exception as e:
        r["error"] = str(e)[:300]
        log(f"[{name}] EXC: {str(e)[:120]}")
    finally:
        try: page.close()
        except: pass
    
    save_result(r)
    return r

def main():
    log("=" * 50)
    log(f"BATCH v4 START - {len(ALL_TOKENS)} tokens, {len(AIRPORTS)} targets")
    
    success = 0; total = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, channel="msedge",
            args=["--disable-blink-features=AutomationControlled"])
        
        for i, ap in enumerate(AIRPORTS):
            email, token_info = get_next_email()
            if not email: break
            
            log(f"[{i+1}/{len(AIRPORTS)}] {ap['name']} <- {email}")
            result = register_one(browser, ap, email, token_info)
            total += 1
            if result["success"]: success += 1
            time.sleep(1)
        
        browser.close()
    
    log(f"\nDONE: {success}/{total} success")
    log(f"Results: {RESULT_FILE}")

if __name__ == "__main__":
    main()
