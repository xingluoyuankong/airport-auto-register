#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量浏览器注册机场 - 自动识别已注册→登录→取订阅"""
import asyncio, json, os, sys, re, time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "register_results")
os.makedirs(RESULTS_DIR, exist_ok=True)

AIRPORTS = [
    {"name": "稳连云", "url": "https://wenlianyun.com", "register_url": "https://wenlianyun.com/#/register", "login_url": "https://wenlianyun.com/#/login", "user_url": "https://wenlianyun.com/#/user"},
    {"name": "Speedy",  "url": "https://cloud.speedypro.xyz", "register_url": "https://cloud.speedypro.xyz/#/register", "login_url": "https://cloud.speedypro.xyz/#/login", "user_url": "https://cloud.speedypro.xyz/#/user"},
    {"name": "大象网络", "url": "https://www.elephant223.com", "register_url": "https://www.elephant223.com/#/register", "login_url": "https://www.elephant223.com/#/login", "user_url": "https://www.elephant223.com/#/user"},
]

def load_token_accounts():
    token_dir = r"E:\.Outlook邮箱\批量注册邮箱\已经使用\1"
    accounts = []
    for fname in os.listdir(token_dir):
        if not fname.endswith("_combo.txt"): continue
        fpath = os.path.join(token_dir, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            parts = f.read().strip().split("----")
        if len(parts) >= 4:
            accounts.append({"email": parts[0], "password": parts[1], "client_id": parts[2], "refresh_token": parts[3]})
    return accounts

TOKEN_ACCOUNTS = load_token_accounts()
EMAIL_INDEX = [0]

def get_next_email():
    idx = EMAIL_INDEX[0] % len(TOKEN_ACCOUNTS)
    EMAIL_INDEX[0] += 1
    return TOKEN_ACCOUNTS[idx]

# 记录每个邮箱在哪些机场已注册过（格式: "email|airport_url"）
REGISTERED_MAP = {}

def get_code_graph(email, client_id, refresh_token, timeout=90, sent_after=None):
    import requests as req
    deadline = time.time() + timeout
    token_url = "https://login.microsoftonline.com/consumers/oauth2/v2.0/token"
    scope = "offline_access https://graph.microsoft.com/Mail.Read"
    seen_codes = set()
    while time.time() < deadline:
        try:
            r = req.post(token_url, data={"client_id": client_id, "grant_type": "refresh_token", "refresh_token": refresh_token, "scope": scope}, timeout=15)
            at_data = r.json()
            if not at_data.get("access_token"): time.sleep(3); continue
            at = at_data["access_token"]
            resp = req.get("https://graph.microsoft.com/v1.0/me/messages?$top=10&$select=subject,from,body,receivedDateTime,bodyPreview",
                headers={"Authorization": f"Bearer {at}"}, timeout=10)
            for msg in resp.json().get("value", []):
                received = msg.get("receivedDateTime", "")
                if sent_after and received < sent_after: continue
                body = (msg.get("body", {}).get("content", "") or "") + " " + (msg.get("bodyPreview", "") or "")
                combined = msg.get("subject", "") + " " + body
                m = re.search(r'(?:verification|security|确认|验证|code|激活|注册|login).*?(\d{6})', combined, re.I)
                if not m: m = re.search(r'(\d{6})', combined)
                if m and not re.search(r'\d{7}', m.group(0)):
                    code = m.group(1)
                    if code not in seen_codes:
                        return {"success": True, "code": code, "subject": msg.get("subject", "")}
                    seen_codes.add(code)
            time.sleep(5)
        except: time.sleep(3)
    return {"success": False, "error": "超时"}

async def extract_subscribe(page, base_url):
    """从用户面板提取订阅链接"""
    try:
        user_url = base_url.rstrip("/") + "/#/user"
        await page.goto(user_url, wait_until="domcontentloaded", timeout=15000)
        await asyncio.sleep(2)
        # 尝试点复制订阅按钮
        btns = await page.query_selector_all('button:has-text("复制"), button:has-text("订阅"), span:has-text("复制")')
        for btn in btns:
            try:
                await btn.click(); await asyncio.sleep(1)
                clip = await page.evaluate("navigator.clipboard.readText()")
                if clip and ("sub" in clip.lower() or "token" in clip.lower()):
                    return clip
            except: pass
        # 从页面文本提取
        page_text = await page.evaluate("document.body.innerText")
        m = re.search(r'(https?://[^\s]+/api/v1/client/subscribe\?token=[^\s]+)', page_text)
        if m: return m.group(1)
    except: pass
    return ""

async def register_one(airport, email_info, browser_context):
    name = airport["name"]
    email = email_info["email"]
    reg_pwd = f"Aa{int(time.time()) % 1000000}!"
    key = f"{email}|{airport['url']}"
    
    print(f"\n{'='*60}")
    print(f"  [{name}] 邮箱: {email[:30]}...  pwd: {reg_pwd}")
    
    page = await browser_context.new_page()
    result = {"airport": name, "email": email, "reg_password": reg_pwd, "success": False}
    
    try:
        # === 如果之前已注册过，直接登录 ===
        if key in REGISTERED_MAP:
            print(f"  [SKIP] 已知已注册，切登录...")
            await page.goto(airport["login_url"], wait_until="domcontentloaded", timeout=15000)
            await asyncio.sleep(2)
            saved_pwd = REGISTERED_MAP[key]
            try:
                await page.fill('input[type="email"], input[placeholder*="邮箱"]', email)
                await page.fill('input[type="password"]', saved_pwd)
                await page.click('button:has-text("登录"), button:has-text("Login"), button:has-text("登 录")', force=True)
                await asyncio.sleep(4)
                page_text = await page.evaluate("document.body.innerText")
                login_url = page.url
                if "dashboard" in login_url or "user" in login_url or "仪表盘" in page_text:
                    result["success"] = True; result["already_registered"] = True
                    print(f"  [OK] 登录成功")
            except Exception as e:
                print(f"  登录异常: {e}")
            sub = await extract_subscribe(page, airport["url"])
            if sub: result["subscribe_url"] = sub; print(f"  订阅: {sub[:80]}")
            await page.close()
            return result
        
        # === 正常注册流程 ===
        await page.goto(airport["register_url"], wait_until="domcontentloaded", timeout=20000)
        await asyncio.sleep(3)
        await page.screenshot(path=os.path.join(RESULTS_DIR, f"{name}_step1.png"))
        
        # 填邮箱
        await page.fill('input[type="email"], input[placeholder*="邮箱"]', email)
        await asyncio.sleep(0.3)
        
        # 填密码
        pw_inputs = await page.query_selector_all('input[type="password"]')
        for i, pw in enumerate(pw_inputs[:2]):
            await pw.fill(reg_pwd, force=True, timeout=3000)
        print(f"  已填写表单")
        
        # 点发送验证码（如果有的话）
        send_btn = await page.query_selector('button:has-text("发送"), span:has-text("发送")')
        if send_btn:
            await send_btn.click(force=True, timeout=3000)
            print(f"  已点发送验证码")
            await asyncio.sleep(3)
        
        # 记录提交时间戳
        submit_time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # 点注册
        submit_btn = await page.query_selector('button:has-text("注册"), button:has-text("Register"), button[type="submit"]')
        if submit_btn:
            await submit_btn.click(force=True, timeout=5000)
            print(f"  已点注册 (submit_time={submit_time})")
        else:
            result["error"] = "找不到注册按钮"
            await page.close()
            return result
        
        await asyncio.sleep(3)
        await page.screenshot(path=os.path.join(RESULTS_DIR, f"{name}_step2.png"))
        
        # === 检查"已注册"提示 ===
        page_text = await page.evaluate("document.body.innerText")
        current_url = page.url
        
        if any(kw in page_text for kw in ["已注册", "already registered", "账号已存在", "邮箱已注册", "该邮箱已"]):
            print(f"  [INFO] 检测到'已注册'，切登录!")
            REGISTERED_MAP[key] = reg_pwd  # 记录这个邮箱在这个机场的密码
            await page.goto(airport["login_url"], wait_until="domcontentloaded", timeout=15000)
            await asyncio.sleep(2)
            await page.fill('input[type="email"], input[placeholder*="邮箱"]', email)
            await page.fill('input[type="password"]', reg_pwd)
            await page.click('button:has-text("登录"), button:has-text("Login"), button:has-text("登 录")', force=True)
            await asyncio.sleep(4)
            page_text2 = await page.evaluate("document.body.innerText")
            if "仪表盘" in page_text2 or "Dashboard" in page_text2 or "user" in page.url:
                result["success"] = True; result["already_registered"] = True
                print(f"  [OK] 登录成功（之前已注册）")
            sub = await extract_subscribe(page, airport["url"])
            if sub: result["subscribe_url"] = sub; print(f"  订阅: {sub[:80]}")
            await page.close()
            return result
        
        # === 检查验证码输入 ===
        code_input = await page.query_selector('input[placeholder*="验证码"], input[name="email_code"], input[name="code"]')
        if code_input:
            print(f"  等待验证码...")
            client_id = email_info.get("client_id", "")
            refresh_token = email_info.get("refresh_token", "")
            code_result = get_code_graph(email, client_id, refresh_token, timeout=90, sent_after=submit_time)
            
            if code_result.get("success") and code_result.get("code"):
                code = code_result["code"]
                print(f"  验证码: {code}")
                
                # JS直接设值（NaiveUI组件常隐藏）
                filled = await page.evaluate("""
                    (code) => {
                        const inputs = document.querySelectorAll('input');
                        for (const inp of inputs) {
                            const ph = inp.placeholder || '';
                            if (ph.includes('验证码') || ph.includes('Code') || inp.name === 'email_code' || inp.name === 'code') {
                                const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                                setter.call(inp, code);
                                inp.dispatchEvent(new Event('input', {bubbles: true}));
                                inp.dispatchEvent(new Event('change', {bubbles: true}));
                                return true;
                            }
                        }
                        return false;
                    }
                """, code)
                
                if filled:
                    print(f"  验证码已填入")
                else:
                    # fallback
                    try:
                        loc = page.locator('input[placeholder*="验证码"]').first
                        await loc.fill(code, force=True, timeout=3000)
                        print(f"  验证码已force填入")
                    except:
                        print(f"  无法填入验证码")
                
                await asyncio.sleep(1)
                # 再点提交
                submit2 = await page.query_selector('button:has-text("注册"), button:has-text("Register"), button[type="submit"]')
                if submit2:
                    await submit2.click(force=True, timeout=5000)
                    await asyncio.sleep(4)
        
        # === 最终检查是否注册成功 ===
        final_url = page.url
        final_text = await page.evaluate("document.body.innerText")
        
        if any(kw in final_url for kw in ["dashboard", "user", "home", "panel"]):
            result["success"] = True
            REGISTERED_MAP[key] = reg_pwd
        elif "仪表盘" in final_text or "Dashboard" in final_text or "用户中心" in final_text:
            result["success"] = True
            REGISTERED_MAP[key] = reg_pwd
        
        if result["success"]:
            print(f"  [OK] 注册成功!")
            sub = await extract_subscribe(page, airport["url"])
            if sub: result["subscribe_url"] = sub; print(f"  订阅: {sub[:80]}")
        else:
            # 检查错误信息
            errs = re.findall(r'(?:error|错误|失败|message)[^\\n]{0,100}', final_text, re.I)
            result["error"] = "; ".join(errs[:2]) if errs else "未知"
            print(f"  [FAIL] {result['error'][:100]}")
        
        await page.screenshot(path=os.path.join(RESULTS_DIR, f"{name}_final.png"))
    
    except Exception as e:
        result["error"] = str(e)[:200]
        print(f"  [ERR] {e}")
    finally:
        await page.close()
    
    return result

async def main():
    print(f"\n航班注册系统 - {len(AIRPORTS)}机场 | {len(TOKEN_ACCOUNTS)}邮箱")
    
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("pip install playwright && playwright install chromium"); return
    
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled", "--no-sandbox"])
        context = await browser.new_context(viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36")
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => false});")
        
        for airport in AIRPORTS:
            email_info = get_next_email()
            result = await register_one(airport, email_info, context)
            results.append(result)
            status = "[OK]" if result.get("success") else "[FAIL]"
            tag = "(已注册登录)" if result.get("already_registered") else ""
            print(f"  >> {status} {airport['name']} {tag}")
            await asyncio.sleep(2)
        
        await browser.close()
    
    # 保存
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(os.path.join(RESULTS_DIR, f"register_{ts}.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    with open(os.path.join(os.path.dirname(__file__), "订阅链接", f"subs_{ts}.txt"), "w", encoding="utf-8") as f:
        f.write(f"# 订阅链接 {datetime.now()}\n")
        for r in results:
            if r.get("success") and r.get("subscribe_url"):
                f.write(f"# {r['airport']} - {r['email'][:25]}...\n{r['subscribe_url']}\n\n")
    
    success = [r for r in results if r.get("success")]
    print(f"\n[结果] 成功 {len(success)}/{len(results)}")
    for r in success:
        sub = r.get("subscribe_url", "无")
        tag = "(登录)" if r.get("already_registered") else "(新注册)"
        print(f"  {r['airport']} {tag}: {r['email'][:25]}... | {sub[:60] if sub else '无订阅'}")

if __name__ == "__main__":
    asyncio.run(main())
