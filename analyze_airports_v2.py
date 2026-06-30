#!/usr/bin/env python3
"""
机场注册流程深度逆向分析 v2
修复：正确区分真实CAPTCHA和HTML中的captcha字样
添加：实际注册尝试
"""

import os
import sys
import json
import time
import random
import string
import asyncio
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from playwright.async_api import async_playwright

PROXY = {"server": "socks5://127.0.0.1:7897"}
OUTPUT_DIR = Path(r"E:\API获取工具\自动集成免费代理服务\01-机场VPN注册机")
SCREENSHOT_DIR = OUTPUT_DIR / "screenshots"
SUBS_FILE = OUTPUT_DIR / "订阅链接" / "new_subs_20260628.txt"
REPORT_FILE = OUTPUT_DIR / "analysis_report_v2_20260628.json"

SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
SUBS_FILE.parent.mkdir(parents=True, exist_ok=True)

def random_email(domain):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=10)) + '@' + domain

def random_pass():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=14))

# Real CAPTCHA detection - check for iframes (reCAPTCHA/hCaptcha), turnstile divs, challenge pages
REAL_CAPTCHA_JS = """
() => {
    // Check for reCAPTCHA iframe
    const recaptchaFrames = document.querySelectorAll('iframe[src*="recaptcha"], iframe[src*="hcaptcha"], iframe[src*="captcha"]');
    if (recaptchaFrames.length > 0) return 'iframe_captcha';
    
    // Check for Turnstile
    if (document.querySelector('.cf-turnstile, #cf-turnstile, [data-sitekey]')) return 'turnstile';
    
    // Check for Cloudflare challenge page
    const title = document.title.toLowerCase();
    const body = document.body ? document.body.innerText.substring(0, 500).toLowerCase() : '';
    if (title.includes('just a moment') || title.includes('attention required') || 
        body.includes('checking your browser') || body.includes('ddos protection') ||
        title.includes('please wait')) return 'cloudflare_challenge';
    
    // Check for image/text captcha input fields
    const captchaInputs = document.querySelectorAll('input[name*="captcha"], input[name*="verif"], input[placeholder*="验证码"], input[placeholder*="captcha"], input[id*="captcha"]');
    if (captchaInputs.length > 0) return 'captcha_input';
    
    // Check for captcha images
    const captchaImgs = document.querySelectorAll('img[src*="captcha"], img[src*="Captcha"], img[id*="captcha"]');
    if (captchaImgs.length > 0) return 'captcha_image';
    
    return null;
}
"""

AIRPORTS = [
    {"name": "NanoCloud-360buy", "url": "https://edu.360buyimg.men", "invite_code": "nano"},
    {"name": "NanoCloud-yuque", "url": "https://edu.yuque.men", "invite_code": "nano"},
    {"name": "BoostNet", "url": "https://www.boostnet.top", "invite_code": None},
    {"name": "一元中转", "url": "https://www.xn--9kqw2h015j2lg.site", "invite_code": None},
    {"name": "一分机场", "url": "https://xn--z7xv9z0vo1e.top", "invite_code": None},
    {"name": "69云-fly99", "url": "https://69.fly99.xyz", "invite_code": None},
    {"name": "猫猴VPN", "url": "https://www.nekohou.com", "invite_code": None},
    {"name": "白嫖机场", "url": "https://www.xn--fctv8v9uh5rc.com", "invite_code": None},
    {"name": "FSCloud", "url": "https://fscloud.one", "invite_code": None},
    {"name": "农夫山泉-nfsq", "url": "https://www.nfsq.xyz", "invite_code": None},
]

SUBS_COLLECTED = []

async def snapshot_forms(page):
    """Get all form-like elements"""
    forms_info = []
    inputs = await page.query_selector_all("input, select, textarea, button[type='submit']")
    for i, el in enumerate(inputs):
        try:
            tag = await el.evaluate("el => el.tagName.toLowerCase()")
            itype = await el.get_attribute("type") or "text"
            name = await el.get_attribute("name") or ""
            pid = await el.get_attribute("placeholder") or ""
            elid = await el.get_attribute("id") or ""
            val = await el.input_value() if tag == 'input' else ''
            text = await el.inner_text() if tag == 'button' else ''
            label = await el.get_attribute("aria-label") or ""
            forms_info.append({
                "tag": tag, "type": itype, "name": name,
                "placeholder": pid, "id": elid, "value": val[:50],
                "text": text.strip()[:50], "label": label
            })
        except:
            pass
    return forms_info


async def find_and_click(page, texts):
    """Find and click a link/button by text"""
    for t in texts:
        try:
            el = await page.query_selector(f'a:has-text("{t}"), button:has-text("{t}")')
            if el:
                await el.click()
                return el
        except:
            pass
    return None


async def analyze_and_register(browser, airport):
    result = {
        "name": airport["name"], "url": airport["url"],
        "status": "unknown", "form_elements": [],
        "has_captcha": False, "captcha_reason": None,
        "email_accepted": None, "subscription_direct": False,
        "subscription_url": None, "registered": False, "notes": []
    }
    
    ctx = None
    page = None
    safe_name = airport["name"].replace("/", "_").replace(":", "_")
    
    try:
        print(f"\n{'='*60}")
        print(f"[{airport['name']}] Opening: {airport['url']}")
        
        ctx = await browser.new_context(proxy=PROXY, ignore_https_errors=True)
        page = await ctx.new_page()
        
        resp = await page.goto(airport["url"], timeout=30000, wait_until="domcontentloaded")
        await asyncio.sleep(3)
        
        final_url = page.url
        title = await page.title()
        print(f"[{airport['name']}] URL: {final_url}, Title: {title}")
        result["final_url"] = final_url
        result["title"] = title
        
        # Screenshot
        ss = str(SCREENSHOT_DIR / f"{safe_name}_home.png")
        await page.screenshot(path=ss, full_page=True)
        print(f"  Screenshot: {ss}")
        
        # Check for domain for sale
        if 'godaddy.com' in final_url or 'forsale' in final_url or 'parked' in final_url.lower():
            result["status"] = "domain_for_sale"
            result["notes"].append("Domain is parked/for sale")
            return result
        
        # Check for Cloudflare challenge / access denied
        if 'access denied' in title.lower() or 'blocked' in title.lower() or 'just a moment' in title.lower():
            result["status"] = "access_blocked"
            result["notes"].append(f"Access blocked: {title}")
            return result
        
        # Smart CAPTCHA detection
        cap_check = await page.evaluate(REAL_CAPTCHA_JS)
        if cap_check:
            print(f"  REAL CAPTCHA: {cap_check}")
            result["has_captcha"] = True
            result["captcha_reason"] = cap_check
            result["status"] = "blocked_captcha"
            result["notes"].append(f"Real CAPTCHA: {cap_check}")
            if cap_check in ("iframe_captcha", "cloudflare_challenge", "turnstile"):
                return result
            # captcha_input or captcha_image - proceed to analyze form anyway
        
        # List forms
        forms = await snapshot_forms(page)
        result["form_elements"] = forms
        print(f"  Form elements: {len(forms)}")
        for f in forms:
            print(f"    <{f['tag']} type={f['type']}> name='{f['name']}' placeholder='{f['placeholder']}' label='{f['label']}' text='{f['text']}'")
        
        # Find register link
        reg_clicked = await find_and_click(page, ["注册", "Register", "sign up", "Sign Up", "加入"])
        
        if not reg_clicked:
            # Try href-based
            try:
                reg_el = await page.query_selector('[href*="register"], [href*="signup"], [href*="reg"]')
                if reg_el:
                    href = await reg_el.get_attribute("href")
                    print(f"  Register link: {href}")
                    await page.goto(urljoin(airport["url"], href), timeout=30000)
                    reg_clicked = True
            except:
                pass
        
        if reg_clicked:
            await asyncio.sleep(2)
            # Wait for navigation
            try:
                await page.wait_for_load_state("networkidle", timeout=10000)
            except:
                pass
            
            reg_url = page.url
            print(f"  Register page: {reg_url}")
            
            # Screenshot register page
            ss = str(SCREENSHOT_DIR / f"{safe_name}_register.png")
            await page.screenshot(path=ss, full_page=True)
            
            # Check CAPTCHA on register page
            cap_check2 = await page.evaluate(REAL_CAPTCHA_JS)
            if cap_check2:
                print(f"  Register page CAPTCHA: {cap_check2}")
                result["has_captcha"] = True
                result["captcha_reason"] = cap_check2
                if cap_check2 in ("iframe_captcha", "cloudflare_challenge", "turnstile"):
                    result["status"] = "blocked_captcha"
                    return result
            
            # Get register page forms
            reg_forms = await snapshot_forms(page)
            result["register_form_elements"] = reg_forms
            print(f"  Register form elements: {len(reg_forms)}")
            
            # Find email, password, confirm fields
            email_fields = []
            pass_fields = []
            confirm_fields = []
            invite_fields = []
            other_fields = []
            
            for f in reg_forms:
                combined = (f['name'] + f['placeholder'] + f['label'] + f['id'] + f['text']).lower()
                if any(kw in combined for kw in ['email', '邮箱', 'mail', 'e-mail', '信箱', '邮件']):
                    email_fields.append(f)
                elif any(kw in combined for kw in ['password', '密码', 'pass', 'pwd']):
                    if any(kw in combined for kw in ['confirm', '确认', 'repeat', '再次']):
                        confirm_fields.append(f)
                    else:
                        pass_fields.append(f)
                elif any(kw in combined for kw in ['invite', '邀请', '推荐', 'referral', 'code', '码']):
                    invite_fields.append(f)
                else:
                    other_fields.append(f)
            
            print(f"  Email fields: {len(email_fields)}, Pass: {len(pass_fields)}, Confirm: {len(confirm_fields)}, Invite: {len(invite_fields)}")
            
            # Try to register
            if email_fields and pass_fields:
                # Check email domain restrictions
                email_domains = []
                for f in reg_forms:
                    if f['tag'] == 'option' or 'qq.com' in f['text'] or 'gmail' in f['text'] or '163.com' in f['text'] or 'outlook' in f['text']:
                        email_domains.append(f['text'])
                    if f['tag'] == 'select':
                        try:
                            opts = await page.query_selector_all(f'#{f["id"]} option, [name="{f["name"]}"] option')
                            for o in opts:
                                txt = await o.inner_text()
                                email_domains.append(txt.strip())
                        except:
                            pass
                
                print(f"  Email domains: {email_domains}")
                
                # Determine if Outlook email is accepted
                all_domains_text = ' '.join(email_domains).lower()
                outlook_ok = 'outlook' in all_domains_text or len(email_domains) == 0
                
                # Check if there's a free-form email input (not just domain picker)
                freeform_email = any(f['type'] in ('email', 'text') and (f['placeholder'].lower() in ('email', '邮箱', '') or f['label'].lower() in ('email', '邮箱')) for f in email_fields)
                
                if outlook_ok:
                    test_email = random_email("outlook.com")
                    result["email_accepted"] = "outlook.com"
                else:
                    # Use first available domain
                    if email_domains:
                        domain = email_domains[0].replace('@', '')
                        test_email = random_email(domain)
                        result["email_accepted"] = domain
                    else:
                        test_email = random_email("gmail.com")
                        result["email_accepted"] = "gmail.com"
                
                test_pass = random_pass()
                print(f"  Test email: {test_email}, password: {test_pass}")
                
                # Fill email - try free-form input first
                email_filled = False
                for f in email_fields:
                    if f['type'] in ('email', 'text') and not f.get('disabled'):
                        # Find the actual input element
                        sel = None
                        if f['id']:
                            sel = f'#{f["id"]}'
                        elif f['name']:
                            sel = f'[name="{f["name"]}"]'
                        
                        if sel:
                            try:
                                el = await page.query_selector(sel)
                                if el:
                                    await el.fill(test_email)
                                    email_filled = True
                                    print(f"  Filled email: {test_email}")
                                    break
                            except:
                                pass
                
                if not email_filled:
                    # Try filling the first text/email input
                    for f in reg_forms:
                        if f['type'] in ('email', 'text') and f['tag'] == 'input':
                            sel = f'#{f["id"]}' if f['id'] else f'[name="{f["name"]}"]'
                            try:
                                el = await page.query_selector(sel)
                                if el:
                                    await el.fill(test_email)
                                    email_filled = True
                                    print(f"  Filled email via generic input: {test_email}")
                                    break
                            except:
                                pass
                
                # Fill password
                for f in pass_fields:
                    sel = f'#{f["id"]}' if f['id'] else f'[name="{f["name"]}"]'
                    try:
                        el = await page.query_selector(sel)
                        if el:
                            await el.fill(test_pass)
                            print(f"  Filled password")
                            break
                    except:
                        pass
                
                # Fill confirm password
                for f in confirm_fields:
                    sel = f'#{f["id"]}' if f['id'] else f'[name="{f["name"]}"]'
                    try:
                        el = await page.query_selector(sel)
                        if el:
                            await el.fill(test_pass)
                            print(f"  Filled confirm password")
                            break
                    except:
                        pass
                
                # Fill invite code
                if airport.get("invite_code"):
                    for f in invite_fields:
                        sel = f'#{f["id"]}' if f['id'] else f'[name="{f["name"]}"]'
                        try:
                            el = await page.query_selector(sel)
                            if el:
                                await el.fill(airport["invite_code"])
                                print(f"  Filled invite code: {airport['invite_code']}")
                                break
                        except:
                            pass
                
                # Screenshot filled form
                ss = str(SCREENSHOT_DIR / f"{safe_name}_filled.png")
                await page.screenshot(path=ss, full_page=True)
                
                # Click submit/register button
                submit_clicked = await find_and_click(page, ["注册", "下一步", "Register", "Sign Up", "提交", "Submit", "Create Account"])
                
                if submit_clicked:
                    await asyncio.sleep(4)
                    try:
                        await page.wait_for_load_state("networkidle", timeout=10000)
                    except:
                        pass
                    
                    # Screenshot after submit
                    ss = str(SCREENSHOT_DIR / f"{safe_name}_after_submit.png")
                    await page.screenshot(path=ss, full_page=True)
                    
                    after_url = page.url
                    after_title = await page.title()
                    print(f"  After submit: URL={after_url}, Title={after_title}")
                    
                    # Check result
                    page_text = await page.evaluate("() => document.body ? document.body.innerText.substring(0, 1000) : ''")
                    
                    success_indicators = ['success', '成功', 'registered', 'dashboard', 'user', 'panel', '仪表盘', '控制面板', '订阅', '套餐']
                    fail_indicators = ['error', '错误', 'fail', 'invalid', '无效', '已存在', 'exists', 'exist']
                    
                    is_success = any(s in page_text.lower() for s in success_indicators)
                    is_fail = any(s in page_text.lower() for s in fail_indicators)
                    
                    if is_success and not is_fail:
                        result["registered"] = True
                        result["status"] = "registered"
                        result["notes"].append("Registration appears successful!")
                        
                        # Try to find subscription link
                        sub_links = await page.evaluate("""
                        () => {
                            const links = [];
                            document.querySelectorAll('a').forEach(a => {
                                const href = a.href;
                                const text = (a.innerText || '').trim();
                                if (href && (href.includes('subscribe') || href.includes('sub') || 
                                    text.includes('订阅') || text.includes('subscribe') ||
                                    text.includes('节点') || text.includes('node') ||
                                    href.includes('clash') || href.includes('v2ray') ||
                                    href.includes('ssr') || href.includes('trojan'))) {
                                    links.push({href, text});
                                }
                            });
                            return links;
                        }
                        """)
                        print(f"  Subscription links: {sub_links}")
                        if sub_links:
                            result["subscription_url"] = sub_links[0]["href"]
                            result["subscription_direct"] = True
                            SUBS_COLLECTED.append(f"{result['name']}: {sub_links[0]['href']}")
                    elif is_fail:
                        result["notes"].append(f"Registration failed: {page_text[:200]}")
                        result["status"] = "register_failed"
                    else:
                        result["notes"].append(f"Unknown result. Page text: {page_text[:200]}")
                        result["status"] = "register_unknown"
        else:
            result["status"] = "no_register_link"
            result["notes"].append("Could not find registration link/button")
        
        if not result["status"].startswith("blocked") and not result["status"].startswith("registered"):
            result["status"] = "reachable"
    
    except Exception as e:
        error_str = str(e)
        print(f"  ERROR: {error_str[:200]}")
        result["status"] = "error"
        result["notes"].append(f"Error: {error_str[:200]}")
        
        if "ERR_CONNECTION_CLOSED" in error_str or "ERR_TUNNEL" in error_str:
            result["notes"].append("Connection refused/closed")
        elif "Timeout" in error_str or "timeout" in error_str.lower():
            result["notes"].append("Connection timeout")
    
    finally:
        if page:
            try: await page.close()
            except: pass
        if ctx:
            try: await ctx.close()
            except: pass
    
    print(f"\n=== [{airport['name']}] DONE ===")
    print(f"  Status: {result['status']}, CAPTCHA: {result['has_captcha']}, Registered: {result.get('registered', False)}")
    if result.get('notes'):
        for n in result['notes']:
            print(f"  Note: {n}")
    
    return result


async def main():
    print("=" * 60)
    print("机场注册流程逆向分析 v2")
    print(f"代理: socks5://127.0.0.1:7897")
    print(f"时间: {datetime.now().isoformat()}")
    print(f"目标: {len(AIRPORTS)} 个机场")
    print("=" * 60)
    
    results = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--ignore-certificate-errors', '--disable-web-security', '--no-sandbox']
        )
        try:
            for airport in AIRPORTS:
                r = await analyze_and_register(browser, airport)
                results.append(r)
        finally:
            await browser.close()
    
    # Save report
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nReport: {REPORT_FILE}")
    
    # Save subscription links
    with open(SUBS_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n=== {datetime.now().strftime('%Y-%m-%d %H:%M')} ===\n")
        for link in SUBS_COLLECTED:
            f.write(link + "\n")
        if not SUBS_COLLECTED:
            f.write("# No subscriptions collected in this run\n")
    print(f"Subs saved: {SUBS_FILE}")
    
    # Summary
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    for r in results:
        icon = "✅" if r.get("registered") else ("🟡" if r["status"] == "reachable" else ("🤖" if r["has_captcha"] else "❌"))
        print(f"  {icon} [{r['name']}] status={r['status']} captcha={r['has_captcha']} email={r.get('email_accepted','?')} registered={r.get('registered',False)}")
        if r.get('subscription_url'):
            print(f"    SUB: {r['subscription_url']}")

if __name__ == "__main__":
    asyncio.run(main())
