"""批量机场注册引擎 v2 - 全自动无人值守版
- 所有日志写入文件，避免控制台编码问题
- Edge浏览器逐站注册，自动Outlook验证码
- 支持V2Board/SSPANEL/hidexx/custom面板
"""
import os, sys, json, time, re, traceback, io
from datetime import datetime
from playwright.sync_api import sync_playwright

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

def log(msg):
    """同时写入日志文件和控制台"""
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def get_next_email():
    """轮转获取邮箱"""
    if not TOKEN_KEYS:
        return None, None
    idx = len([l for l in open(LOG_FILE, encoding="utf-8") if "Using email" in l]) % len(TOKEN_KEYS)
    email = TOKEN_KEYS[idx]
    token_info = ALL_TOKENS.get(email.lower(), list(ALL_TOKENS.values())[0])
    return email, token_info

# ============ 全部50+待注册机场 ============
AIRPORTS = [
    # == 最高优先级：超大免费额度 ==
    {"name": "ikuuu", "url": "https://ikuuu.me/", "free": "50G永久"},
    {"name": "qlgq", "url": "https://www.qlgq.top/auth/register", "free": "7天888G"},
    {"name": "闪电狗", "url": "https://shandiandog.com/#/register", "free": "3天50G"},
    {"name": "翱翔云", "url": "https://www.aoxiangyun.top/auth/register", "free": "7天20G+签到"},
    {"name": "Bochidev", "url": "https://b0chi.r-yu.me/#/register", "free": "50G不限时"},
    {"name": "Speedy", "url": "https://cloud.speedypro.xyz/#/register", "free": "7天10G"},
    {"name": "速云", "url": "https://zhu.suyun.bio/auth/register", "free": "3天10G"},
    # == 高优先级 ==
    {"name": "奈云", "url": "https://www.v2ny.com/#/register", "free": "3天5G"},
    {"name": "快乐星球", "url": "https://klxq.djgskc.top/#/register", "free": "7天10G"},
    {"name": "FSCloud", "url": "https://dash.fscloud.cc/#/register", "free": "3天10G"},
    {"name": "极光加速", "url": "https://jgjs02.com/#/register", "free": "2天10G"},
    {"name": "besnow", "url": "https://besnow.me/index.php#/register", "free": "3天9G"},
    {"name": "TaiShan Net", "url": "https://www.taishan.pro/#/register", "free": "7天10G"},
    {"name": "BT3rd-Speed", "url": "https://px.bt3.one/#/register", "free": "6天10G"},
    {"name": "彩虹云", "url": "https://chy.fit/#/register", "free": "10G/天"},
    {"name": "大迅云", "url": "https://daxun.club/#/register", "free": "10G/2天"},
    {"name": "BCast", "url": "https://bcast.ink/#/register", "free": "6天10G"},
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
    {"name": "雨燕云", "url": "https://yuyan.online/#/register", "free": "8h1G"},
    {"name": "宝贝云", "url": "https://v3ssy.xyz/#/register", "free": "1天2G"},
    {"name": "逗猫", "url": "https://doucat.top/index.php#/register", "free": "1天3G"},
    {"name": "一元机场", "url": "https://xn--4gq62f52gdss.com/#/register", "free": "11元/年50G"},
    {"name": "盛丰", "url": "https://xn--iiq540h.com/auth/register", "free": "5天1G"},
    {"name": "ssrsub", "url": "https://sub.ssrsub.com/", "free": "0元购"},
    {"name": "Arisaka", "url": "https://reurl.cc/XG68o7", "free": "10G"},
    {"name": "狗头加速", "url": "https://lksi.xyz/#/register", "free": "5天5G"},
    {"name": "xqc.best", "url": "https://xqc.best/#/register", "free": "待确认"},
    {"name": "tly", "url": "https://tly.sh/", "free": "3天2G+签到"},
    {"name": "GLaDOS", "url": "https://glados.rocks", "free": "4天10G+签到续"},
]

def save_result(result):
    """保存单个结果到JSONL"""
    with open(RESULT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(result, ensure_ascii=False) + "\n")

def register_one(browser, airport, email, token_info):
    """注册单个机场 - 返回结果dict"""
    name = airport["name"]
    url = airport["url"]
    free = airport.get("free", "?")
    result = {"name": name, "url": url, "free": free, "email": email, "success": False, "ts": datetime.now().isoformat()}
    
    page = browser.new_page()
    try:
        log(f"[{name}] START | {free} | {email}")
        
        # 1. 导航
        page.goto(url, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(4000)
        
        body = page.evaluate("document.body.innerText.substring(0,500)")
        cur_url = page.url
        log(f"[{name}] URL={cur_url}")
        
        # 检查CF挑战
        if "checking" in body.lower() or "cloudflare" in body.lower():
            log(f"[{name}] Cloudflare detected, waiting...")
            page.wait_for_timeout(10000)
            body = page.evaluate("document.body.innerText.substring(0,500)")
        
        # 2. 找输入框 - 用JS更可靠
        fields = page.evaluate("""() => {
            let inputs = document.querySelectorAll('input');
            let result = {email: null, pw: [], code: null};
            for (let inp of inputs) {
                let ph = (inp.placeholder || '').toLowerCase();
                let nm = (inp.name || '').toLowerCase();
                let tp = inp.type || '';
                let id = (inp.id || '').toLowerCase();
                let label = (inp.getAttribute('aria-label') || '').toLowerCase();
                let combined = ph + nm + id + label;
                if (combined.includes('email') || combined.includes('e-mail') || combined.includes('username') || combined.includes('account') || tp === 'email') {
                    if (!result.email) result.email = inp.name || inp.id || 'email_input';
                }
                if (tp === 'password' || ph.includes('password') || ph.includes('密码')) {
                    result.pw.push(inp.name || inp.id || 'pw_' + result.pw.length);
                }
                if (ph.includes('code') || ph.includes('验证码') || ph.includes('verification') || nm.includes('code')) {
                    if (!result.code) result.code = inp.name || inp.id || 'code_input';
                }
            }
            return result;
        }""")
        
        if not fields.get("email"):
            # fallback: 第一个text/email输入框
            email_el = page.query_selector("input[type='email'], input[type='text']:first-of-type")
            if email_el:
                fields["email"] = "first_text"
        
        email_sel = None
        if fields.get("email"):
            if fields["email"] == "first_text":
                email_sel = "input[type='email'], input[type='text']:first-of-type"
            else:
                email_sel = f"input[name='{fields['email']}'], #{fields['email']}"
        
        if not email_sel:
            result["error"] = "no_email_input"
            log(f"[{name}] FAIL: no email input found")
            page.close()
            return result
        
        # 3. 填邮箱
        page.fill(email_sel, email)
        page.wait_for_timeout(300)
        log(f"[{name}] Filled email")
        
        # 4. 填密码
        pw_filled = 0
        for pw_name in fields.get("pw", [])[:2]:
            try:
                sel = f"input[name='{pw_name}'], #{pw_name}"
                page.fill(sel, PASSWORD)
                pw_filled += 1
                page.wait_for_timeout(200)
            except:
                pass
        
        if pw_filled == 0:
            # fallback
            pw_inputs = page.query_selector_all("input[type='password']")
            for pw in pw_inputs[:2]:
                try:
                    pw.fill(PASSWORD)
                    pw_filled += 1
                    page.wait_for_timeout(200)
                except:
                    pass
        
        log(f"[{name}] Filled {pw_filled} password fields")
        
        # 5. 发送验证码
        send_btn = page.query_selector("button:has-text('发送验证码'),button:has-text('获取验证码'),button:has-text('Send Code'),a:has-text('发送验证码'),span:has-text('获取验证码')")
        needs_code = False
        if send_btn:
            try:
                send_btn.click()
                page.wait_for_timeout(2000)
                needs_code = True
                log(f"[{name}] Clicked send code button")
            except:
                pass
        
        if not needs_code:
            # 检查是否有验证码输入框
            code_field = fields.get("code")
            if code_field:
                needs_code = True
                log(f"[{name}] Code field detected, needs verification")
        
        # 6. 等待验证码
        if needs_code:
            log(f"[{name}] Waiting for email code (max 90s)...")
            code, err = wait_for_code(email, token_info, timeout=90, interval=4)
            if code:
                # 填入验证码
                code_sel = None
                if fields.get("code"):
                    code_sel = f"input[name='{fields['code']}'], #{fields['code']}"
                if not code_sel:
                    code_inputs = page.query_selector_all("input[type='text']:not([type='email']), input[type='number']")
                    for ci in code_inputs:
                        val = ci.get_attribute("value") or ""
                        ph = (ci.get_attribute("placeholder") or "").lower()
                        if "@" not in val and ("code" in ph or "验证" in ph or len(ph) < 6):
                            code_sel = ci
                            break
                        elif "@" not in val and not ci.get_attribute("name"):
                            code_sel = ci
                            break
                
                if code_sel:
                    if isinstance(code_sel, str):
                        page.fill(code_sel, code)
                    else:
                        code_sel.fill(code)
                    page.wait_for_timeout(500)
                    log(f"[{name}] Filled code: {code}")
                else:
                    log(f"[{name}] WARN: code received but cant find input")
                    result["error"] = "code_no_input"
                    page.close()
                    return result
            else:
                log(f"[{name}] WARN: no code received ({err}), trying submit anyway")
        
        # 7. 提交注册
        reg_btn = page.query_selector(
            "button:has-text('注册'),button:has-text('确定'),"
            "button:has-text('提交'),button:has-text('Register'),"
            "button:has-text('Sign Up'),button[type='submit'],"
            "input[type='submit'],a:has-text('注册'),button:has-text('创 建')"
        )
        
        if reg_btn:
            try:
                reg_btn.click()
                page.wait_for_timeout(6000)
                log(f"[{name}] Clicked register button")
            except Exception as e:
                log(f"[{name}] Click error: {e}")
        else:
            log(f"[{name}] No register button found, trying Enter")
            page.keyboard.press("Enter")
            page.wait_for_timeout(5000)
        
        # 8. 检查结果
        final_url = page.url
        final_body = page.evaluate("document.body.innerText.substring(0,500)")
        
        fail_words = ["验证码错误", "邮箱已注册", "已被注册", "已存在", "格式不正确", "error", "失败", "请重试"]
        success_urls = ["dashboard", "user", "ucenter", "home", "shop", "商店", "购买"]
        
        is_fail = any(w in final_body.lower() for w in fail_words)
        is_success = any(w in final_url.lower() for w in success_urls) or ("register" not in final_url.lower() and not is_fail)
        
        if is_success:
            result["success"] = True
            log(f"[{name}] SUCCESS!")
            
            # 提取订阅链接
            try:
                sub = page.evaluate("localStorage.getItem('subscribe_url')")
                if sub:
                    result["subscribe_url"] = sub
                    log(f"[{name}] Sub URL found!")
                else:
                    token = page.evaluate("localStorage.getItem('VUE_NAIVE_ACCESS_TOKEN')")
                    if token:
                        result["api_token"] = token[:80]
                        log(f"[{name}] API token extracted")
            except Exception as e:
                log(f"[{name}] Extract sub error: {e}")
            
            # 截图
            try:
                ss = os.path.join(OUTPUT_DIR, f"screenshot_{name}.png")
                page.screenshot(path=ss)
            except:
                pass
        else:
            result["error"] = final_body[:200]
            log(f"[{name}] FAIL: {final_body[:100]}")
            try:
                ss = os.path.join(OUTPUT_DIR, f"screenshot_{name}_fail.png")
                page.screenshot(path=ss)
            except:
                pass
        
    except Exception as e:
        result["error"] = str(e)[:300]
        log(f"[{name}] EXCEPTION: {e}")
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
    log(f"BATCH REGISTER ENGINE v2 START")
    log(f"Tokens: {len(ALL_TOKENS)}, Targets: {len(AIRPORTS)}")
    
    success = 0
    total = 0
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            channel="msedge",
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        for i, airport in enumerate(AIRPORTS):
            email, token_info = get_next_email()
            if not email:
                log("No more emails!")
                break
            
            log(f"[{i+1}/{len(AIRPORTS)}] {airport['name']} <- {email}")
            result = register_one(browser, airport, email, token_info)
            total += 1
            if result["success"]:
                success += 1
            
            time.sleep(2)
        
        browser.close()
    
    log(f"\nFINAL: {success}/{total} success")
    log(f"Results: {RESULT_FILE}")
    log(f"Log: {LOG_FILE}")

if __name__ == "__main__":
    main()
