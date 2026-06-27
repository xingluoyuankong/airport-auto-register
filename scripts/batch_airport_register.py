"""批量机场注册引擎 - 2026-06-28 大规模版本
支持50+机场自动注册，V2Board/SSPANEL/hidexx三大系统全覆盖
Outlook Graph API自动验证码，Playwright+Edge穿GFW
"""
import os, sys, json, time, re, traceback
from datetime import datetime
from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(__file__))
from outlook_code_reader import load_all_tokens, wait_for_code

PASSWORD = "VpnTest2026!"
ALL_TOKENS = load_all_tokens()
TOKEN_KEYS = list(ALL_TOKENS.keys())
TOKEN_IDX = [0]  # 全局token索引
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "register_results")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_next_email():
    """轮转获取下一个未用邮箱"""
    if not TOKEN_KEYS:
        return None, None
    email = TOKEN_KEYS[TOKEN_IDX[0] % len(TOKEN_KEYS)]
    token_info = ALL_TOKENS.get(email.lower(), list(ALL_TOKENS.values())[0])
    TOKEN_IDX[0] += 1
    return email, token_info

# ============ 全部待注册机场列表 ============
AIRPORTS = [
    # --- 高优先级：免费额度明确 ---
    {"name": "ikuuu", "url": "https://ikuuu.me/", "free": "50G永久", "panel": "auto"},
    {"name": "qlgq", "url": "https://www.qlgq.top/auth/register", "free": "7天888G", "panel": "auto"},
    {"name": "Speedy", "url": "https://cloud.speedypro.xyz/#/register", "free": "7天10G", "panel": "v2board"},
    {"name": "速云", "url": "https://zhu.suyun.bio/auth/register", "free": "3天10G", "panel": "auto"},
    {"name": "闪电狗", "url": "https://shandiandog.com/#/register", "free": "3天50G", "panel": "v2board"},
    {"name": "翱翔云", "url": "https://www.aoxiangyun.top/auth/register", "free": "7天20G+签到", "panel": "auto"},
    {"name": "奈云", "url": "https://www.v2ny.com/#/register", "free": "3天5G", "panel": "v2board"},
    {"name": "Bochidev", "url": "https://b0chi.r-yu.me/#/register", "free": "50G不限时", "panel": "v2board"},
    {"name": "快乐星球", "url": "https://klxq.djgskc.top/#/register", "free": "7天10G", "panel": "v2board"},
    {"name": "FSCloud", "url": "https://dash.fscloud.cc/#/register", "free": "3天10G", "panel": "v2board"},
    {"name": "极光加速", "url": "https://jgjs02.com/#/register", "free": "2天10G", "panel": "v2board"},
    {"name": "盛丰", "url": "https://xn--iiq540h.com/auth/register", "free": "5天1G", "panel": "auto"},
    {"name": "besnow", "url": "https://besnow.me/index.php#/register", "free": "3天9G", "panel": "sspanel"},
    {"name": "TaiShan Net", "url": "https://www.taishan.pro/#/register", "free": "7天10G", "panel": "v2board"},
    {"name": "逗猫", "url": "https://doucat.top/index.php#/register", "free": "1天3G", "panel": "sspanel"},
    {"name": "BT3rd-Speed", "url": "https://px.bt3.one/#/register", "free": "6天10G", "panel": "v2board"},
    {"name": "彩虹云", "url": "https://chy.fit/#/register", "free": "10G/天", "panel": "v2board"},
    {"name": "宝贝云", "url": "https://v3ssy.xyz/#/register", "free": "1天2G", "panel": "v2board"},
    {"name": "大迅云", "url": "https://daxun.club/#/register", "free": "10G/2天", "panel": "v2board"},
    {"name": "BCast", "url": "https://bcast.ink/#/register", "free": "6天10G", "panel": "v2board"},
    {"name": "cd520", "url": "https://cd520.xyz/#/register", "free": "3天5G", "panel": "v2board"},
    {"name": "Mickey", "url": "https://www.mickey.business/#/register", "free": "3天2G", "panel": "v2board"},
    {"name": "农夫山泉", "url": "https://sp.nfsq.me/#/register", "free": "2天1G", "panel": "v2board"},
    {"name": "cocolink", "url": "https://cocolink.org/#/register", "free": "7天64G", "panel": "v2board"},
    {"name": "alori", "url": "https://oukasou.xyz/index.php#/register", "free": "6天50G", "panel": "sspanel"},
    {"name": "aimacloud", "url": "https://www.aimacloud.info/#/register", "free": "6天20G", "panel": "v2board"},
    {"name": "Synapse", "url": "https://user.xinna.co/#/register", "free": "3天5G", "panel": "v2board"},
    {"name": "难民机场", "url": "https://nanmin.xyz/#/register", "free": "2天5G", "panel": "v2board"},
    {"name": "BBQ烧烤店", "url": "https://qiaoxbbq.com/#/register", "free": "7天10G", "panel": "v2board"},
    {"name": "猫熊网络", "url": "https://mxwljsq.xyz/auth/register", "free": "3天5G", "panel": "auto"},
    {"name": "纵横加速", "url": "https://www.okvpn.cc/#/register", "free": "7天2G", "panel": "v2board"},
    {"name": "JetFast", "url": "https://my.jetfast.dev/#/register", "free": "1月5G", "panel": "v2board"},
    {"name": "sockboom", "url": "https://sockboom.love/auth/register", "free": "1天1G", "panel": "auto"},
    {"name": "KELECLOUD", "url": "https://panel.keleofficial.com/#/register", "free": "1天1G", "panel": "v2board"},
    {"name": "大牛机场", "url": "https://daniu.e300daniu.top/#/register", "free": "1小时1G", "panel": "v2board"},
    {"name": "proxyvip", "url": "https://www.proxyvip.xyz/#/register", "free": "1G/天", "panel": "v2board"},
    {"name": "青森云", "url": "https://sub.cccc.gg/auth/register", "free": "6小时", "panel": "auto"},
    {"name": "大哥云", "url": "https://ab12y.com/#/register", "free": "1天10G", "panel": "v2board"},
    {"name": "Arisaka", "url": "https://reurl.cc/XG68o7", "free": "10G", "panel": "auto"},
    {"name": "极客加速器", "url": "https://board.jike99.xyz/#/register", "free": "3天5G", "panel": "v2board"},
    {"name": "Free机场", "url": "https://zero.76898102.xyz", "free": "白嫖", "panel": "auto"},
    {"name": "雨燕云", "url": "https://yuyan.online/#/register", "free": "8h 1G", "panel": "v2board"},
    {"name": "狗头加速", "url": "https://lksi.xyz/#/register", "free": "5天5G", "panel": "v2board"},
    {"name": "一元机场", "url": "https://xn--4gq62f52gdss.com/#/register", "free": "11元/年50G", "panel": "v2board"},
    {"name": "ssrsub", "url": "https://sub.ssrsub.com/", "free": "0元购", "panel": "auto"},
    {"name": "xqc.best", "url": "https://xqc.best/#/register", "free": "待确认", "panel": "v2board"},
    {"name": "tly", "url": "https://tly.sh/", "free": "3天2G+签到", "panel": "auto"},
    {"name": "GLaDOS", "url": "https://glados.rocks", "free": "4天10G+签到续", "panel": "custom"},
    {"name": "快连", "url": "https://8m5tnb.onelink.me/0Iq2/72awzjy7", "free": "3天", "panel": "custom"},
]

# ============ 核心注册逻辑 ============
def register_one(browser, airport, email, token_info):
    """注册单个机场"""
    name = airport["name"]
    url = airport["url"]
    free = airport.get("free", "未知")
    result = {"name": name, "url": url, "free": free, "email": email, "success": False, "error": ""}
    
    page = browser.new_page()
    try:
        print(f"\n{'='*60}")
        print(f"[{name}] 开始注册 | {free} | {url}")
        
        # 1. 导航到注册页
        page.goto(url, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(4000)
        
        # 快照页面内容用于诊断
        body = page.evaluate("document.body.innerText.substring(0,800)")
        current_url = page.url
        print(f"[{name}] 当前URL: {current_url}")
        print(f"[{name}] 页面内容: {body[:300]}")
        
        # 2. 自动检测面板类型
        is_v2board = "#/register" in current_url or "register" in current_url.lower()
        is_sspanel = "/auth/register" in current_url or "index.php" in current_url
        has_cf = "checking" in body.lower() or "cloudflare" in body.lower()
        
        if has_cf:
            print(f"[{name}] 检测到Cloudflare挑战，等待...")
            page.wait_for_timeout(8000)
        
        # 3. 找邮箱输入框
        inputs = page.query_selector_all("input")
        email_input = None
        pw_inputs = []
        code_input = None
        
        for inp in inputs:
            ph = (inp.get_attribute("placeholder") or "").lower()
            nm = (inp.get_attribute("name") or "").lower()
            tp = (inp.get_attribute("type") or "")
            auto = (inp.get_attribute("autocomplete") or "").lower()
            
            if any(k in ph or k in nm or k in auto for k in ["邮箱", "email", "e-mail", "username"]):
                if not email_input:
                    email_input = inp
            elif "password" in ph or "密码" in ph or tp == "password":
                pw_inputs.append(inp)
            elif any(k in ph for k in ["验证码", "code", "verification"]):
                code_input = inp
        
        if not email_input:
            # 尝试通过type找
            for inp in inputs:
                tp = inp.get_attribute("type") or ""
                if tp == "email" or tp == "text":
                    email_input = inp
                    break
        
        if not email_input:
            result["error"] = "找不到邮箱输入框"
            print(f"[{name}] [FAIL] {result['error']}")
            page.close()
            return result
        
        # 4. 填邮箱
        email_input.click()
        page.wait_for_timeout(500)
        email_input.fill(email)
        page.wait_for_timeout(500)
        print(f"[{name}] [v] 填入邮箱: {email}")
        
        # 5. 填密码
        for pw in pw_inputs[:2]:
            try:
                pw.fill(PASSWORD)
                page.wait_for_timeout(300)
            except:
                pass
        if pw_inputs:
            print(f"[{name}] [v] 填入密码")
        
        # 6. 判断是否需要验证码 - 找发送验证码按钮
        send_btn = page.query_selector(
            "button:has-text('发送验证码'),button:has-text('获取验证码'),"
            "button:has-text('Send'),button:has-text('send'),"
            "span:has-text('发送'),span:has-text('获取'),"
            "a:has-text('发送验证码'),a:has-text('获取验证码')"
        )
        
        needs_code = False
        if send_btn:
            try:
                send_btn.click()
                page.wait_for_timeout(2000)
                needs_code = True
                print(f"[{name}] [v] 点击发送验证码")
            except:
                pass
        
        # 也检查页面是否直接有验证码输入框
        if code_input and not needs_code:
            needs_code = True
        
        # 7. 等待并填入验证码
        if needs_code:
            print(f"[{name}] 等待Outlook验证码(最长90秒)...")
            code, err = wait_for_code(email, token_info, timeout=90, interval=4)
            if code:
                if not code_input:
                    # 重新找验证码输入框
                    inputs2 = page.query_selector_all("input")
                    for inp in inputs2:
                        ph = (inp.get_attribute("placeholder") or "").lower()
                        if any(k in ph for k in ["验证码", "code"]):
                            code_input = inp
                            break
                    if not code_input:
                        for inp in inputs2:
                            tp = inp.get_attribute("type") or ""
                            if tp == "text" or tp == "number":
                                # 跳过邮箱输入框
                                val = inp.get_attribute("value") or ""
                                if "@" not in val:
                                    code_input = inp
                                    break
                
                if code_input:
                    code_input.click()
                    page.wait_for_timeout(300)
                    code_input.fill(code)
                    page.wait_for_timeout(500)
                    print(f"[{name}] [v] 填入验证码: {code}")
                else:
                    print(f"[{name}] [WARN] 收到验证码{code}但找不到输入框")
                    result["error"] = f"有验证码{code}无输入框"
                    page.close()
                    return result
            else:
                print(f"[{name}] [WARN] 未收到验证码: {err}")
                # 尝试不填验证码直接提交（有些机场不需要）
        
        # 8. 找注册/提交按钮并点击
        reg_btn = page.query_selector(
            "button:has-text('注册'),button:has-text('注 册'),"
            "button:has-text('确定'),button:has-text('提交'),"
            "button:has-text('Register'),button:has-text('Sign Up'),"
            "button[type='submit'],input[type='submit']"
        )
        
        if not reg_btn:
            # 尝试任意button
            btns = page.query_selector_all("button")
            for b in btns:
                txt = (b.inner_text() or "").strip()
                if txt and len(txt) <= 6:
                    reg_btn = b
                    break
        
        if reg_btn:
            try:
                reg_btn.click()
                page.wait_for_timeout(5000)
                print(f"[{name}] [v] 点击注册按钮")
            except Exception as e:
                print(f"[{name}] 点击注册按钮失败: {e}")
        
        # 9. 检查结果
        page.wait_for_timeout(3000)
        final_url = page.url
        final_body = page.evaluate("document.body.innerText.substring(0,800)")
        
        success_keywords = ["dashboard", "user", "ucenter", "home", "main", "shop", "购买", "套餐", "流量", "节点"]
        fail_keywords = ["验证码错误", "邮箱已注册", "邮箱已存在", "已被注册", "已注册", "邮箱格式不正确", "error", "失败"]
        
        is_success = any(kw in final_url.lower() for kw in ["dashboard", "user", "ucenter", "home"])
        is_fail = any(kw in final_body.lower() for kw in fail_keywords)
        
        if is_success or (not is_fail and "register" not in final_url.lower()):
            result["success"] = True
            print(f"[{name}] [OK] 注册成功!")
            
            # 提取订阅链接
            try:
                sub_url = page.evaluate("localStorage.getItem('subscribe_url')")
                if not sub_url:
                    token = page.evaluate("localStorage.getItem('VUE_NAIVE_ACCESS_TOKEN')")
                    if token:
                        result["api_token"] = token[:80]
                        # 尝试fetch user/info
                        try:
                            page.evaluate(f"""
                                (function() {{
                                    var t = '{token}';
                                    fetch('/api/v1/user/info', {{headers:{{'Authorization':'Bearer '+t}}}})
                                    .then(function(r){{return r.text()}})
                                    .then(function(d){{window.__user_info = d}})
                                }})()
                            """)
                            page.wait_for_timeout(3000)
                            info = page.evaluate("window.__user_info || ''")
                            if info:
                                result["user_info"] = info[:200]
                        except:
                            pass
                if sub_url:
                    result["subscribe_url"] = sub_url
            except Exception as e:
                print(f"[{name}] 提取订阅链接失败: {e}")
            
            # 截图保存
            try:
                ss_path = os.path.join(OUTPUT_DIR, f"{name}_success.png")
                page.screenshot(path=ss_path)
            except:
                pass
        else:
            print(f"[{name}] [FAIL] 注册未成功")
            err_line = final_body[:200]
            result["error"] = err_line
            try:
                ss_path = os.path.join(OUTPUT_DIR, f"{name}_fail.png")
                page.screenshot(path=ss_path)
            except:
                pass
        
    except Exception as e:
        result["error"] = str(e)[:300]
        print(f"[{name}] [FAIL] 异常: {e}")
        try:
            ss_path = os.path.join(OUTPUT_DIR, f"{name}_error.png")
            page.screenshot(path=ss_path)
        except:
            pass
    finally:
        page.close()
    
    return result

def main():
    if not ALL_TOKENS:
        print("[FAIL] 没有可用的Outlook Token!")
        return
    
    print(f"[START] Batch airport register engine")
    print(f"Available tokens: {len(ALL_TOKENS)}")
    print(f"Target airports: {len(AIRPORTS)}")
    print(f"Password: {PASSWORD}")
    
    results = []
    success_count = 0
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            channel="msedge",
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        for i, airport in enumerate(AIRPORTS):
            email, token_info = get_next_email()
            if not email:
                print("[FAIL] 没有可用的邮箱了!")
                break
            
            print(f"\n[{i+1}/{len(AIRPORTS)}] {airport['name']} ← {email}")
            
            result = register_one(browser, airport, email, token_info)
            results.append(result)
            
            if result["success"]:
                success_count += 1
            
            # 保存中间结果
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            with open(os.path.join(OUTPUT_DIR, f"batch_results_{ts}.json"), "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            time.sleep(2)
        
        browser.close()
    
    # 最终汇总
    print(f"\n{'='*60}")
    print(f"[SUM] 注册汇总: 成功{success_count}/{len(AIRPORTS)}")
    
    success_list = [r for r in results if r["success"]]
    print(f"\n[OK] 成功列表:")
    for r in success_list:
        print(f"  {r['name']} | {r['email']} | {r.get('subscribe_url', '无订阅')}")
    
    fail_list = [r for r in results if not r["success"]]
    print(f"\n[FAIL] 失败列表:")
    for r in fail_list:
        print(f"  {r['name']} | {r.get('error', '未知')}")
    
    # 保存最终结果
    final_path = os.path.join(OUTPUT_DIR, "batch_register_final.json")
    with open(final_path, "w", encoding="utf-8") as f:
        json.dump({"success_count": success_count, "total": len(results), "results": results}, f, ensure_ascii=False, indent=2)
    
    print(f"\n结果已保存到: {final_path}")

if __name__ == "__main__":
    main()
