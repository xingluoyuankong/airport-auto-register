#!/usr/bin/env python3
"""
NanoCloud 专属注册脚本
使用 Playwright 处理自定义 Web Component 表单
"""

import asyncio
import sys
import io
import random
import string
from datetime import datetime
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from playwright.async_api import async_playwright

PROXY = {"server": "socks5://127.0.0.1:7897"}
SUBS_FILE = Path(r"E:\API获取工具\自动集成免费代理服务\01-机场VPN注册机\订阅链接\new_subs_20260628.txt")
SCREEN_DIR = Path(r"E:\API获取工具\自动集成免费代理服务\01-机场VPN注册机\screenshots")

def rand_str(k=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=k))

SITES = [
    {"name": "NanoCloud-360buy", "url": "https://edu.360buyimg.men", "invite": "nano"},
    {"name": "NanoCloud-yuque", "url": "https://edu.yuque.men", "invite": "nano"},
]

async def register_nano(browser, site):
    name = site["name"]
    safe = name.replace("/", "_")
    result = {"name": name, "registered": False, "sub_url": None, "notes": []}
    
    ctx = await browser.new_context(proxy=PROXY, ignore_https_errors=True)
    page = await ctx.new_page()
    
    try:
        print(f"\n{'='*60}")
        print(f"[{name}] Starting registration on {site['url']}")
        
        # Go to main page
        await page.goto(site["url"], timeout=30000)
        await page.wait_for_load_state("networkidle", timeout=15000)
        print(f"[{name}] Home page: {page.url}, title: {await page.title()}")
        
        # Screenshot home
        await page.screenshot(path=str(SCREEN_DIR / f"{safe}_home.png"), full_page=True)
        
        # Navigate to register page
        await page.goto(f"{site['url']}/auth/register", timeout=30000)
        await asyncio.sleep(2)
        await page.wait_for_load_state("networkidle", timeout=15000)
        print(f"[{name}] Register page: {page.url}")
        
        # Get all interactive elements for debugging
        all_inputs = await page.evaluate("""
        () => {
            const els = document.querySelectorAll('input, textarea, select, [role="textbox"]');
            return Array.from(els).map((el, i) => ({
                i,
                tag: el.tagName,
                type: el.type || el.getAttribute('type') || '',
                placeholder: el.placeholder || el.getAttribute('placeholder') || '',
                name: el.name || el.getAttribute('name') || '',
                id: el.id || '',
                ariaLabel: el.getAttribute('aria-label') || el.getAttribute('aria-labelledby') || '',
                role: el.getAttribute('role') || '',
                value: (el.value || '').substring(0, 30),
                textContent: (el.textContent || '').substring(0, 50),
                className: (el.className || '').substring(0, 80),
                parentHTML: (el.parentElement ? el.parentElement.outerHTML.substring(0, 200) : ''),
            }));
        }
        """)
        print(f"[{name}] Found {len(all_inputs)} interactive elements:")
        for inp in all_inputs:
            print(f"  [{inp['i']}] {inp['tag']}#{inp['id']} type={inp['type']} role={inp['role']} placeholder='{inp['placeholder']}' aria='{inp['ariaLabel']}' name='{inp['name']}' class='{inp['className']}'")
        
        # Screenshot register page
        await page.screenshot(path=str(SCREEN_DIR / f"{safe}_register.png"), full_page=True)
        
        # Find email input - use aria-label or placeholder
        email_input = None
        pass_input = None
        confirm_input = None
        invite_input = None
        
        # Strategy: find by aria-label attribute
        for inp in all_inputs:
            combined = f"{inp['ariaLabel']} {inp['placeholder']} {inp['name']} {inp['id']}".lower()
            if any(kw in combined for kw in ['邮箱', 'email', 'mail']):
                if not email_input:
                    email_input = inp
            elif any(kw in combined for kw in ['密码', 'password', 'pass']):
                if any(kw in combined for kw in ['确认', 'confirm', '重复', 'repeat', '再次']):
                    if not confirm_input:
                        confirm_input = inp
                else:
                    if not pass_input:
                        pass_input = inp
            elif any(kw in combined for kw in ['邀请', 'invite', '推荐', 'referral', 'code', '码']):
                if not invite_input:
                    invite_input = inp
        
        # Fallback: find by role + label
        if not email_input:
            for inp in all_inputs:
                if inp['tag'] == 'INPUT' and inp['type'] in ('email', 'text'):
                    if '邮箱' in (inp.get('placeholder', '') + inp.get('ariaLabel', '')):
                        email_input = inp
                        break
        
        # Fallback: use xpath
        if not email_input:
            try:
                el = await page.query_selector('//input[@placeholder="邮箱" or @aria-label="邮箱"]')
                if el:
                    email_input = {"selector": '//input[@placeholder="邮箱" or @aria-label="邮箱"]', "use_xpath": True}
            except:
                pass
        
        print(f"  Email input: {email_input}")
        print(f"  Pass input: {pass_input}")
        print(f"  Confirm input: {confirm_input}")
        print(f"  Invite input: {invite_input}")
        
        # Fill the form
        test_email = f"{rand_str(10)}@outlook.com"
        test_pass = f"Test{rand_str(8)}!1"
        
        # Fill email - NanoCloud has a two-part email input: username + domain selector
        # First try aria-label based
        email_selector = 'input[aria-label="邮箱"], input[placeholder="邮箱"], [role="textbox"][aria-label="邮箱"]'
        try:
            email_el = await page.query_selector(email_selector)
            if email_el:
                await email_el.click()
                await asyncio.sleep(0.5)
                await email_el.fill(test_email)
                print(f"  ✅ Filled email: {test_email}")
            else:
                # Try grabbing all textboxes
                textboxes = await page.query_selector_all('[role="textbox"]')
                print(f"  Found {len(textboxes)} textboxes via role")
                for i, tb in enumerate(textboxes):
                    try:
                        lbl = await tb.get_attribute("aria-label") or ""
                        ph = await tb.get_attribute("placeholder") or ""
                        print(f"    textbox[{i}]: aria='{lbl}' placeholder='{ph}'")
                    except:
                        pass
        except Exception as e:
            print(f"  Email fill error: {e}")
        
        # Fill password
        try:
            pass_el = await page.query_selector('input[aria-label="密码"], input[placeholder="密码"], [role="textbox"][aria-label="密码"]')
            if pass_el:
                await pass_el.click()
                await asyncio.sleep(0.3)
                await pass_el.fill(test_pass)
                print(f"  ✅ Filled password")
        except Exception as e:
            print(f"  Password fill error: {e}")
        
        # Fill confirm password
        try:
            conf_el = await page.query_selector('input[aria-label="确认密码"], input[placeholder="确认密码"], [role="textbox"][aria-label="确认密码"]')
            if conf_el:
                await conf_el.click()
                await asyncio.sleep(0.3)
                await conf_el.fill(test_pass)
                print(f"  ✅ Filled confirm password")
        except Exception as e:
            print(f"  Confirm password fill error: {e}")
        
        # Fill invite code
        try:
            invite_el = await page.query_selector('input[aria-label*="邀请"], input[placeholder*="邀请"], [role="textbox"][aria-label*="邀请"]')
            if not invite_el:
                # Try all textboxes, the invite field might be one without label
                all_tb = await page.query_selector_all('[role="textbox"]')
                for tb in all_tb:
                    lbl = await tb.get_attribute("aria-label") or ""
                    ph = await tb.get_attribute("placeholder") or ""
                    if '邀请' in lbl or '邀请' in ph or 'invite' in lbl or 'invite' in ph:
                        invite_el = tb
                        break
            if invite_el:
                await invite_el.click()
                await asyncio.sleep(0.3)
                await invite_el.fill(site["invite"])
                print(f"  ✅ Filled invite: {site['invite']}")
        except Exception as e:
            print(f"  Invite fill error: {e}")
        
        # Screenshot filled
        await page.screenshot(path=str(SCREEN_DIR / f"{safe}_filled.png"), full_page=True)
        
        # Click submit - "下一步" button
        try:
            submit_btn = await page.query_selector('button:has-text("下一步"), button:has-text("注册"), button:has-text("Register"), button:has-text("Sign")')
            if submit_btn:
                await submit_btn.click()
                print(f"  ✅ Clicked submit")
            else:
                # Try text-based click
                await page.click('text=下一步')
                print(f"  ✅ Clicked '下一步' by text")
        except Exception as e:
            print(f"  Submit error: {e}")
        
        # Wait for response
        await asyncio.sleep(5)
        try:
            await page.wait_for_load_state("networkidle", timeout=10000)
        except:
            pass
        
        after_url = page.url
        after_title = await page.title()
        print(f"  After submit: {after_url}, title: {after_title}")
        
        await page.screenshot(path=str(SCREEN_DIR / f"{safe}_after_submit.png"), full_page=True)
        
        # Check if logged in (dashboard page)
        body_text = await page.evaluate("() => document.body ? document.body.innerText.substring(0, 2000) : ''")
        print(f"  Page text: {body_text[:500]}")
        
        # Try to find subscription link
        sub_links = await page.evaluate("""
        () => {
            const links = [];
            document.querySelectorAll('a').forEach(a => {
                const href = a.href || '';
                const text = (a.innerText || '').trim();
                if (href.includes('subscribe') || href.includes('sub?') || 
                    text.includes('订阅') || text.includes('Subscribe') ||
                    href.includes('clash') || href.includes('v2ray')) {
                    links.push({href, text});
                }
            });
            return links;
        }
        """)
        print(f"  Sub links: {sub_links}")
        
        # Check URL for /user or /dashboard patterns
        if '/user' in after_url or '/dashboard' in after_url or '/panel' in after_url:
            result["registered"] = True
            result["notes"].append("Redirected to dashboard")
        elif 'login' in after_url.lower():
            # Might need login after registration
            result["notes"].append("Redirected to login page after registration")
        
        # Try to find subscription in user panel
        if result["registered"] or '/user' in after_url:
            # Look for "订阅" link in sidebar
            sub_btn = await page.query_selector('a:has-text("订阅"), a:has-text("Subscribe")')
            if sub_btn:
                await sub_btn.click()
                await asyncio.sleep(3)
                sub_url = page.url
                result["sub_url"] = sub_url
                result["notes"].append(f"Subscription link: {sub_url}")
                print(f"  📡 Subscription page: {sub_url}")
        
        # If we're on a page that shows subscription info
        if '订阅' in body_text or 'subscribe' in body_text.lower():
            # Find "一键订阅" or import links
            copy_btns = await page.query_selector_all('button:has-text("复制"), button:has-text("Copy"), button:has-text("导入")')
            if copy_btns:
                result["notes"].append("Found copy/import buttons for subscription")
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        result["notes"].append(f"Error: {str(e)[:200]}")
    finally:
        await page.close()
        await ctx.close()
    
    print(f"\n=== [{name}] DONE ===")
    print(f"  Registered: {result['registered']}, Sub URL: {result['sub_url']}")
    for n in result["notes"]:
        print(f"  {n}")
    return result


async def main():
    print("=" * 60)
    print("NanoCloud 专属注册脚本")
    print(f"时间: {datetime.now().isoformat()}")
    print("=" * 60)
    
    results = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--ignore-certificate-errors', '--disable-web-security', '--no-sandbox']
        )
        try:
            for site in SITES:
                r = await register_nano(browser, site)
                results.append(r)
        finally:
            await browser.close()
    
    # Save results
    with open(SUBS_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n=== NanoCloud {datetime.now().strftime('%Y-%m-%d %H:%M')} ===\n")
        for r in results:
            if r["sub_url"]:
                f.write(f"{r['name']}: {r['sub_url']}\n")
            else:
                f.write(f"# {r['name']}: registered={r['registered']} notes={'; '.join(r['notes'])}\n")
    
    print(f"\nFinal results:")
    for r in results:
        print(f"  [{r['name']}] registered={r['registered']} sub={r['sub_url']}")


if __name__ == "__main__":
    asyncio.run(main())
