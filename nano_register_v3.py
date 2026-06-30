#!/usr/bin/env python3
"""
NanoCloud 注册 - DOM遍历版
处理 var-input 自定义组件
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

async def register_nano(browser, site):
    name = site["name"]
    safe = name.replace("/", "_")
    result = {"name": name, "registered": False, "sub_url": None, "notes": []}
    
    ctx = await browser.new_context(proxy=PROXY, ignore_https_errors=True)
    page = await ctx.new_page()
    
    try:
        print(f"\n{'='*60}")
        print(f"[{name}] Starting on {site['url']}")
        
        # Go to register page directly
        await page.goto(f"{site['url']}/auth/register", timeout=30000)
        await asyncio.sleep(3)
        try:
            await page.wait_for_load_state("networkidle", timeout=10000)
        except:
            pass
        
        print(f"[{name}] URL: {page.url}, Title: {await page.title()}")
        
        # Screenshot
        await page.screenshot(path=str(SCREEN_DIR / f"{safe}_reg.png"), full_page=True)
        
        # Deep DOM analysis: find var-input components and their labels
        dom_info = await page.evaluate("""
        () => {
            const result = [];
            // Find all var-input custom elements
            const varInputs = document.querySelectorAll('.var-input, var-input, [class*="var-input"]');
            varInputs.forEach((el, i) => {
                const info = { index: i, tag: el.tagName, class: el.className.substring(0, 100) };
                
                // Get the label text from parent or sibling
                const parent = el.parentElement;
                if (parent) {
                    const parentLabel = parent.querySelector('label, .var-input__label, [class*="label"]');
                    if (parentLabel) {
                        info.parentLabel = parentLabel.innerText.trim().substring(0, 50);
                    }
                    // Check parent text
                    const parentText = parent.innerText.trim().substring(0, 100);
                    info.parentText = parentText;
                    
                    // Check parent HTML snippet
                    info.parentHTML = parent.outerHTML.substring(0, 300);
                }
                
                // Find the actual input inside
                const input = el.querySelector('input');
                if (input) {
                    info.inputType = input.type || 'text';
                    info.inputId = input.id || '';
                    info.inputName = input.name || '';
                    info.inputPlaceholder = input.placeholder || '';
                    info.inputAria = input.getAttribute('aria-label') || '';
                }
                
                result.push(info);
            });
            
            // Also check for any labels on the page
            const labels = document.querySelectorAll('label');
            const labelTexts = Array.from(labels).map(l => ({
                text: l.innerText.trim().substring(0, 50),
                htmlFor: l.getAttribute('for') || ''
            }));
            
            // And any element with text "邮箱", "密码" etc nearby inputs
            const allText = document.body ? document.body.innerText : '';
            
            return { varInputs: result, labelTexts, bodyLength: allText.length };
        }
        """)
        
        print(f"[{name}] DOM Analysis:")
        print(f"  var-input components: {len(dom_info.get('varInputs', []))}")
        for vi in dom_info.get('varInputs', []):
            print(f"    [{vi['index']}] {vi['tag']}.{vi['class']} inputType={vi.get('inputType','?')} id={vi.get('inputId','?')} placeholder={vi.get('inputPlaceholder','?')}")
            if vi.get('parentLabel'):
                print(f"         label='{vi['parentLabel']}'")
            if vi.get('parentText'):
                print(f"         parentText='{vi['parentText']}'")
        
        print(f"  Labels: {dom_info.get('labelTexts', [])}")
        
        # Now walk the ACTUAL DOM to find inputs by their surrounding text
        # Strategy: find elements containing "邮箱" text, then find nearby input
        input_map = await page.evaluate("""
        () => {
            const map = {};
            
            // Find all labels, spans, divs that contain key words
            const allElements = document.querySelectorAll('*');
            const keywords = ['邮箱', '密码', '确认密码', '邀请码', '邀请', '确认'];
            
            allElements.forEach(el => {
                const text = (el.childNodes.length === 1 && el.childNodes[0].nodeType === 3) 
                    ? el.textContent.trim() : '';
                if (!text || text.length > 20) return;
                
                for (const kw of keywords) {
                    if (text.includes(kw)) {
                        // Find nearest input
                        let parent = el.parentElement;
                        for (let i = 0; i < 5 && parent; i++) {
                            const input = parent.querySelector('input');
                            if (input) {
                                map[kw] = {
                                    labelText: text,
                                    inputId: input.id,
                                    inputType: input.type,
                                    inputPlaceholder: input.placeholder,
                                    selector: input.id ? `#${input.id}` : 
                                              input.name ? `[name="${input.name}"]` : null
                                };
                                break;
                            }
                            parent = parent.parentElement;
                        }
                        break;
                    }
                }
            });
            
            return map;
        }
        """)
        
        print(f"[{name}] Input map from text labels: {input_map}")
        
        # Now try to fill using found selectors
        test_email = f"{rand_str(10)}@outlook.com"
        test_pass = f"Test{rand_str(8)}!1"
        invite_code = site.get("invite", "")
        
        # Try to fill email - the email field is split into username + domain selector on NanoCloud
        # Strategy: try multiple approaches
        
        filled = False
        
        # Approach 1: use placeholder-based selectors
        for sel in [
            'input[placeholder*="邮箱"]',
            'input[placeholder*="email"]', 
            'input[placeholder*="Email"]',
            'input[placeholder*="请输入"]',
        ]:
            try:
                el = page.locator(sel).first
                if await el.count() > 0:
                    await el.fill(test_email)
                    print(f"[{name}] Filled email via selector: {sel}")
                    filled = True
                    break
            except:
                pass
        
        # Approach 2: navigate by label text
        if not filled:
            try:
                # Find the label/span with "邮箱" text and click on the next input
                email_input = page.locator('text=邮箱').locator('..').locator('input').first
                if await email_input.count() > 0:
                    await email_input.fill(test_email)
                    print(f"[{name}] Filled email via '..' of '邮箱' text")
                    filled = True
            except:
                pass
        
        # Approach 3: Click the label then type
        if not filled:
            try:
                # The NanoCloud form has: label "邮箱" then input
                # Click on "邮箱" text, then type
                el = page.get_by_text("邮箱", exact=True).first
                await el.click()
                await asyncio.sleep(0.5)
                # Tab might focus the input
                await page.keyboard.press("Tab")
                await asyncio.sleep(0.3)
                await page.keyboard.type(test_email, delay=50)
                print(f"[{name}] Typed email via keyboard after clicking label")
                filled = True
            except Exception as e:
                print(f"[{name}] Keyboard approach failed: {e}")
        
        # Approach 4: Fill by input index
        if not filled:
            try:
                # The register page has 5 inputs: email-username, email-domain, password, invite-code, confirm-password
                # Input 0 is the email username part
                all_inputs = page.locator('input:visible')
                count = await all_inputs.count()
                print(f"[{name}] Visible inputs: {count}")
                for i in range(min(count, 10)):
                    inp = all_inputs.nth(i)
                    tp = await inp.get_attribute("type")
                    ph = await inp.get_attribute("placeholder") or ""
                    print(f"  input[{i}]: type={tp} placeholder='{ph}'")
                
                # Fill username part of email
                email_username = test_email.split('@')[0]
                await all_inputs.nth(0).fill(email_username)
                print(f"[{name}] Filled email username part: {email_username}")
                filled = True
            except Exception as e:
                print(f"[{name}] Index approach failed: {e}")
        
        # Fill password - input index 2 or find by type=password
        await asyncio.sleep(0.5)
        try:
            pass_inputs = page.locator('input[type="password"]:visible')
            pc = await pass_inputs.count()
            print(f"[{name}] Password inputs: {pc}")
            if pc >= 1:
                await pass_inputs.nth(0).fill(test_pass)
                print(f"[{name}] ✅ Filled password (index 0)")
            if pc >= 2:
                await pass_inputs.nth(1).fill(test_pass)
                print(f"[{name}] ✅ Filled confirm password (index 1)")
        except Exception as e:
            print(f"[{name}] Password fill error: {e}")
        
        # Fill invite code - could be the non-password visible text input
        await asyncio.sleep(0.5)
        if invite_code:
            try:
                text_inputs = page.locator('input[type="text"]:visible')
                tc = await text_inputs.count()
                for i in range(tc):
                    inp = text_inputs.nth(i)
                    val = await inp.input_value()
                    ph = await inp.get_attribute("placeholder") or ""
                    # The invite field is the one that's a plain text input, not the email domain picker
                    if not val and ('@' not in ph) and ('邀请' in (await inp.evaluate("el => el.closest('[class*=\"var\"]')?.textContent || ''")) or True):
                        pass
                    print(f"  text_input[{i}]: value='{val}' placeholder='{ph}'")
                
                # Try the 4th visible input (index 3) for invite
                all_vis = page.locator('input:visible')
                if await all_vis.count() > 3:
                    await all_vis.nth(3).fill(invite_code)
                    print(f"[{name}] ✅ Filled invite code at index 3")
            except Exception as e:
                print(f"[{name}] Invite fill error: {e}")
        
        # Screenshot filled form
        await asyncio.sleep(0.5)
        await page.screenshot(path=str(SCREEN_DIR / f"{safe}_filled.png"), full_page=True)
        
        # Submit
        try:
            submit_btn = page.locator('button:has-text("下一步")').first
            if await submit_btn.count() > 0:
                await submit_btn.click()
                print(f"[{name}] ✅ Clicked '下一步'")
            else:
                # Try pressing Enter
                await page.keyboard.press("Enter")
                print(f"[{name}] Pressed Enter to submit")
        except Exception as e:
            print(f"[{name}] Submit error: {e}")
        
        # Wait for response
        await asyncio.sleep(4)
        try:
            await page.wait_for_load_state("networkidle", timeout=10000)
        except:
            pass
        
        after_url = page.url
        after_title = await page.title()
        body_text = await page.evaluate("() => document.body ? document.body.innerText.substring(0, 2000) : ''")
        print(f"[{name}] After submit: URL={after_url}, Title={after_title}")
        print(f"[{name}] Body: {body_text[:300]}")
        
        await page.screenshot(path=str(SCREEN_DIR / f"{safe}_after.png"), full_page=True)
        
        # Check for error messages
        errors = await page.evaluate("""
        () => {
            const errs = [];
            document.querySelectorAll('[class*="error"], [class*="err"], [class*="message"], .var-input__error-message').forEach(el => {
                errs.push(el.innerText.trim());
            });
            return errs;
        }
        """)
        if errors:
            print(f"[{name}] Errors: {errors}")
            result["notes"].append(f"Errors: {errors}")
        
        # Check for success
        if '/user' in after_url or '/dashboard' in after_url:
            result["registered"] = True
            result["notes"].append("Successfully registered and redirected to user panel")
        elif 'login' in after_url.lower() and 'register' not in after_url.lower():
            result["registered"] = True
            result["notes"].append("Redirected to login - registration likely successful, needs login")
        elif after_url == f"{site['url']}/auth/register":
            result["notes"].append("Still on register page - check validation errors")
        
        # Try to find sub link
        if result["registered"]:
            sub_links = await page.evaluate("""
            () => {
                return Array.from(document.querySelectorAll('a')).filter(a => {
                    const h = a.href || '';
                    const t = (a.innerText || '').toLowerCase();
                    return h.includes('sub') || t.includes('订阅') || t.includes('subscribe');
                }).map(a => ({href: a.href, text: a.innerText.trim()}));
            }
            """)
            if sub_links:
                result["sub_url"] = sub_links[0]["href"]
                result["notes"].append(f"Found subscription link")
                print(f"[{name}] 📡 Sub link: {sub_links[0]}")
        
    except Exception as e:
        print(f"[{name}] ❌ Error: {e}")
        result["notes"].append(f"Error: {str(e)[:200]}")
    finally:
        await page.close()
        await ctx.close()
    
    print(f"\n=== [{name}] DONE === registered={result['registered']} sub={result['sub_url']}")
    return result


async def main():
    print("=" * 60)
    print(f"NanoCloud 注册 v3 - DOM遍历 {datetime.now().isoformat()}")
    print("=" * 60)
    
    sites = [
        {"name": "NanoCloud-360buy", "url": "https://edu.360buyimg.men", "invite": "nano"},
        {"name": "NanoCloud-yuque", "url": "https://edu.yuque.men", "invite": "nano"},
    ]
    
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
        try:
            for s in sites:
                results.append(await register_nano(browser, s))
        finally:
            await browser.close()
    
    # Save
    with open(SUBS_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n=== NanoCloud {datetime.now().strftime('%Y-%m-%d %H:%M')} ===\n")
        for r in results:
            if r["sub_url"]:
                f.write(f"{r['name']}: {r['sub_url']}\n")
            else:
                f.write(f"# {r['name']}: reg={r['registered']} {r['notes']}\n")


if __name__ == "__main__":
    asyncio.run(main())
