#!/usr/bin/env python3
"""
机场注册流程深度逆向分析工具
使用 Playwright + SOCKS5 代理 (127.0.0.1:7897)
逐个打开机场网站，分析注册流程
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

# Fix GBK encoding issue on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from playwright.async_api import async_playwright

# Configuration
PROXY = {
    "server": "socks5://127.0.0.1:7897",
}
OUTPUT_DIR = Path(r"E:\API获取工具\自动集成免费代理服务\01-机场VPN注册机")
SCREENSHOT_DIR = OUTPUT_DIR / "screenshots"
SUBS_FILE = OUTPUT_DIR / "订阅链接" / "new_subs_20260628.txt"
REPORT_FILE = OUTPUT_DIR / "analysis_report_20260628.json"

SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
SUBS_FILE.parent.mkdir(parents=True, exist_ok=True)

# Test email domains
TEST_DOMAIN = "outlook.com"

AIRPORTS = [
    {
        "name": "NanoCloud-360buy",
        "url": "https://edu.360buyimg.men",
        "invite_code": "nano",
    },
    {
        "name": "NanoCloud-yuque",
        "url": "https://edu.yuque.men",
        "invite_code": "nano",
    },
    {
        "name": "BoostNet",
        "url": "https://www.boostnet.top",
        "invite_code": None,
    },
    {
        "name": "一元中转",
        "url": "https://www.xn--9kqw2h015j2lg.site",
        "invite_code": None,
    },
    {
        "name": "一分机场",
        "url": "https://xn--z7xv9z0vo1e.top",
        "invite_code": None,
    },
    {
        "name": "69云-fly99",
        "url": "https://69.fly99.xyz",
        "invite_code": None,
    },
    {
        "name": "猫猴VPN",
        "url": "https://www.nekohou.com",
        "invite_code": None,
    },
    {
        "name": "白嫖机场",
        "url": "https://www.xn--fctv8v9uh5rc.com",
        "invite_code": None,
    },
    {
        "name": "FSCloud",
        "url": "https://fscloud.one",
        "invite_code": None,
    },
    {
        "name": "农夫山泉-nfsq",
        "url": "https://www.nfsq.xyz",
        "invite_code": None,
    },
]


def random_email(domain=TEST_DOMAIN):
    """Generate a random email address"""
    name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    return f"{name}@{domain}"


def random_password(length=12):
    """Generate a random password"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))


async def analyze_airport(browser, airport):
    """Analyze a single airport's registration flow"""
    result = {
        "name": airport["name"],
        "url": airport["url"],
        "status": "unknown",
        "form_elements": [],
        "has_captcha": False,
        "email_accepted": None,
        "subscription_direct": False,
        "subscription_url": None,
        "registration_possible": False,
        "notes": [],
    }
    
    context = None
    page = None
    
    try:
        print(f"\n{'='*60}")
        print(f"[{airport['name']}] Opening: {airport['url']}")
        
        context = await browser.new_context(
            proxy=PROXY,
            ignore_https_errors=True,
        )
        page = await context.new_page()
        
        # Short timeout for problematic sites
        await page.goto(airport["url"], timeout=25000, wait_until="domcontentloaded")
        
        # Wait a bit for rendering
        await asyncio.sleep(3)
        
        # Try to get page title
        try:
            title = await page.title()
            print(f"[{airport['name']}] Title: {title}")
            result["title"] = title
        except:
            result["title"] = "N/A"
        
        # Screenshot
        safe_name = airport["name"].replace("/", "_").replace(":", "_")
        screenshot_path = str(SCREENSHOT_DIR / f"{safe_name}.png")
        await page.screenshot(path=screenshot_path, full_page=True)
        print(f"[{airport['name']}] Screenshot saved: {screenshot_path}")
        
        # Check for reCAPTCHA / hCaptcha / Cloudflare Turnstile
        page_content = await page.content()
        captcha_indicators = [
            "recaptcha",
            "h-captcha",
            "hcaptcha",
            "g-recaptcha",
            "cf-turnstile",
            "cloudflare",
            "challenge",
            "captcha",
            "验证码",
            "人机验证",
            "Please verify you are human",
            "Checking your browser",
            "DDoS protection",
            "Just a moment",
            "安全检测",
            "Are you a robot",
        ]
        
        content_lower = page_content.lower()
        captcha_matches = [c for c in captcha_indicators if c.lower() in content_lower]
        if captcha_matches:
            print(f"[{airport['name']}] ⚠️ CAPTCHA detected: {captcha_matches}")
            result["has_captcha"] = True
            result["captcha_type"] = captcha_matches
            result["status"] = "blocked_captcha"
            result["notes"].append(f"CAPTCHA: {', '.join(captcha_matches)}")
            return result
        
        # Get page URL after redirect
        final_url = page.url
        print(f"[{airport['name']}] Final URL: {final_url}")
        result["final_url"] = final_url
        
        # Look for registration links
        # Common registration link patterns
        register_selectors = [
            'a:has-text("注册")',
            'a:has-text("Register")',
            'a:has-text("sign up")',
            'a:has-text("Sign Up")',
            'a:has-text("加入")',
            'a:has-text("注")',
            'button:has-text("注册")',
            'button:has-text("Register")',
            '[href*="register"]',
            '[href*="signup"]',
            '[href*="sign_up"]',
            '[href*="auth"]',
        ]
        
        register_link = None
        for sel in register_selectors:
            try:
                el = await page.query_selector(sel)
                if el:
                    href = await el.get_attribute("href")
                    text = await el.inner_text()
                    print(f"[{airport['name']}] Found register link: '{text.strip()}' -> {href}")
                    register_link = href
                    break
            except:
                pass
        
        # Check for login/register forms on main page
        form_elements = await page.query_selector_all("input, select, textarea")
        print(f"[{airport['name']}] Found {len(form_elements)} input elements on page")
        
        for i, el in enumerate(form_elements):
            try:
                tag = await el.evaluate("el => el.tagName.toLowerCase()")
                input_type = await el.get_attribute("type") or "text"
                name = await el.get_attribute("name") or ""
                placeholder = await el.get_attribute("placeholder") or ""
                required = await el.get_attribute("required")
                el_id = await el.get_attribute("id") or ""
                aria_label = await el.get_attribute("aria-label") or ""
                
                form_info = {
                    "index": i,
                    "tag": tag,
                    "type": input_type,
                    "name": name,
                    "id": el_id,
                    "placeholder": placeholder,
                    "required": required is not None,
                    "aria_label": aria_label,
                }
                result["form_elements"].append(form_info)
                print(f"  [{i}] <{tag} type={input_type}> name='{name}' placeholder='{placeholder}' id='{el_id}'")
            except Exception as e:
                print(f"  [{i}] Error reading element: {e}")
        
        # If there's a register link, navigate to registration page
        if register_link:
            # Handle relative URLs
            if register_link.startswith("/"):
                from urllib.parse import urljoin
                register_url = urljoin(airport["url"], register_link)
            elif register_link.startswith("http"):
                register_url = register_link
            else:
                register_url = urljoin(airport["url"], register_link)
            
            print(f"[{airport['name']}] Navigating to register page: {register_url}")
            try:
                await page.goto(register_url, timeout=25000, wait_until="domcontentloaded")
                await asyncio.sleep(3)
                
                # Screenshot register page
                reg_screenshot_path = str(SCREENSHOT_DIR / f"{safe_name}_register.png")
                await page.screenshot(path=reg_screenshot_path, full_page=True)
                
                # Re-check content for CAPTCHA
                reg_content = await page.content()
                reg_content_lower = reg_content.lower()
                reg_captcha = [c for c in captcha_indicators if c.lower() in reg_content_lower]
                if reg_captcha:
                    print(f"[{airport['name']}] ⚠️ CAPTCHA on register page: {reg_captcha}")
                    result["has_captcha"] = True
                    result["captcha_type"] = reg_captcha
                    result["status"] = "blocked_captcha"
                    result["notes"].append(f"Register page CAPTCHA: {', '.join(reg_captcha)}")
                    return result
                
                # List form elements on register page
                reg_forms = await page.query_selector_all("input, select, textarea")
                print(f"[{airport['name']}] Register page has {len(reg_forms)} inputs")
                
                register_form_elements = []
                for j, el in enumerate(reg_forms):
                    try:
                        tag = await el.evaluate("el => el.tagName.toLowerCase()")
                        input_type = await el.get_attribute("type") or "text"
                        name = await el.get_attribute("name") or ""
                        placeholder = await el.get_attribute("placeholder") or ""
                        el_id = await el.get_attribute("id") or ""
                        
                        register_form_elements.append({
                            "tag": tag,
                            "type": input_type,
                            "name": name,
                            "placeholder": placeholder,
                            "id": el_id,
                        })
                        
                        email_keywords = ["email", "邮箱", "mail", "e-mail", "信箱"]
                        is_email_field = any(kw in (name + placeholder + el_id).lower() for kw in email_keywords)
                        
                        if is_email_field and input_type in ("text", "email", ""):
                            print(f"  [REG-{j}] EMAIL field: name='{name}' placeholder='{placeholder}'")
                            # Test with Outlook email
                            test_addr = random_email("outlook.com")
                            try:
                                await el.fill(test_addr)
                                print(f"  [REG-{j}] ✅ Filled with Outlook email: {test_addr}")
                                result["email_accepted"] = "outlook.com"
                            except:
                                print(f"  [REG-{j}] ❌ Failed to fill email")
                        else:
                            print(f"  [REG-{j}] <{tag} type={input_type}> name='{name}' placeholder='{placeholder}'")
                    except Exception as e:
                        print(f"  [REG-{j}] Error: {e}")
                
                result["register_form_elements"] = register_form_elements
                
                # Check for invite code field
                if airport.get("invite_code"):
                    invite_field = None
                    for j, el in enumerate(reg_forms):
                        try:
                            placeholder = await el.get_attribute("placeholder") or ""
                            name = await el.get_attribute("name") or ""
                            el_id = await el.get_attribute("id") or ""
                            invite_keywords = ["invite", "邀请", "邀请码", "code", "referral", "推荐码"]
                            if any(kw in (name + placeholder + el_id).lower() for kw in invite_keywords):
                                invite_field = el
                                print(f"  [REG-{j}] Invite code field found")
                                break
                        except:
                            pass
                    
                    if invite_field:
                        try:
                            await invite_field.fill(airport["invite_code"])
                            print(f"[{airport['name']}] ✅ Filled invite code: {airport['invite_code']}")
                        except:
                            pass
                
            except Exception as e:
                print(f"[{airport['name']}] Failed to navigate to register page: {e}")
                result["notes"].append(f"Register page error: {str(e)[:100]}")
        
        # Check if site is accessible at all
        result["status"] = "reachable"
        
    except Exception as e:
        error_str = str(e)
        print(f"[{airport['name']}] ❌ Error: {error_str[:200]}")
        result["status"] = "error"
        result["notes"].append(f"Error: {error_str[:200]}")
        
        # Check for common issues
        if "ERR_PROXY_CONNECTION_FAILED" in error_str or "ERR_TUNNEL_CONNECTION_FAILED" in error_str:
            result["notes"].append("Proxy connection failed")
        elif "net::ERR_NAME_NOT_RESOLVED" in error_str:
            result["notes"].append("DNS resolution failed")
        elif "Timeout" in error_str or "timeout" in error_str.lower():
            result["notes"].append("Connection timeout")
        elif "cert" in error_str.lower():
            result["notes"].append("SSL/Certificate error")
    
    finally:
        if page:
            try:
                await page.close()
            except:
                pass
        if context:
            try:
                await context.close()
            except:
                pass
    
    print(f"\n=== [{airport['name']}] DONE ===")
    print(f"  Status: {result['status']}")
    print(f"  CAPTCHA: {result['has_captcha']}")
    print(f"  Email accepted: {result.get('email_accepted', 'Unknown')}")
    print(f"  Form elements: {len(result.get('form_elements', []))}")
    if result.get("notes"):
        for note in result["notes"]:
            print(f"  Note: {note}")
    
    return result


async def main():
    results = []
    subs_links = []
    
    print("=" * 60)
    print("机场注册流程逆向分析")
    print(f"代理: socks5://127.0.0.1:7897")
    print(f"时间: {datetime.now().isoformat()}")
    print(f"目标: {len(AIRPORTS)} 个机场")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--ignore-certificate-errors',
                '--disable-web-security',
                '--no-sandbox',
            ]
        )
        
        try:
            for airport in AIRPORTS:
                result = await analyze_airport(browser, airport)
                results.append(result)
                
                # Collect subscription links if any
                if result.get("subscription_url"):
                    subs_links.append(f"{result['name']}: {result['subscription_url']}")
        finally:
            await browser.close()
    
    # Save results
    print("\n" + "=" * 60)
    print("SAVING RESULTS")
    
    # Save JSON report
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Report saved: {REPORT_FILE}")
    
    # Save subscription links
    if subs_links:
        with open(SUBS_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n=== {datetime.now().strftime('%Y-%m-%d %H:%M')} ===\n")
            for link in subs_links:
                f.write(link + "\n")
        print(f"Subscription links saved: {SUBS_FILE}")
    else:
        print("No subscription links found (all sites had CAPTCHA or were unreachable)")
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for r in results:
        status_icon = "✅" if r["status"] == "reachable" else "❌"
        captcha_icon = "🤖" if r.get("has_captcha") else "🆗"
        email_icon = "📧" if r.get("email_accepted") else "❓"
        print(f"{status_icon} {captcha_icon} {email_icon} [{r['name']}] {r['url']}")
        print(f"     Status: {r['status']} | CAPTCHA: {r.get('has_captcha', '?')} | Email: {r.get('email_accepted', '?')}")
        if r.get("notes"):
            for note in r["notes"]:
                print(f"     └ {note}")


if __name__ == "__main__":
    asyncio.run(main())
