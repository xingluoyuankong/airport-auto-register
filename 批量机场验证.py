"""
批量机场注册页面验证工具
逐个打开机场注册页面，截图并检查：
1. 是否需要邮箱验证
2. 是否有免费试用
3. 是否有验证码(类型)
4. 是否支持 Outlook 邮箱
"""
import asyncio, json, os, re, time
from pathlib import Path
from playwright.async_api import async_playwright

OUTPUT_DIR = Path(r"E:\API获取工具\自动集成免费代理服务\01-机场VPN注册机\verify_results")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

AIRPORTS_TO_TEST = [
    # 免费试用专区 (from everett7623 + panda-vpn-pro + jichang)
    {"name": "FSCloud", "url": "https://dash.fscloud.app/#/register", "trial": "3天免费试用", "note": "terskywork/jichang主推"},
    {"name": "一元机场", "url": "https://xn--4gq62f52gdss.top/#/register?code=CYvaRQDf", "trial": "¥1/月", "note": "jichang主推"},
    {"name": "69云", "url": "https://69yun69.com/auth/register?code=oo2dOV", "trial": "签到送流量", "note": "jichang主推"},
    {"name": "奈云v2ny", "url": "https://www.v2ny.com/#/register?code=baRRZ5rx", "trial": "注册试用3天5G", "note": "RanZiXuan/dd"},
    {"name": "ikuuu", "url": "https://ikuuu.me/", "trial": "50G永久直连", "note": "RanZiXuan/dd"},
    {"name": "Free机场", "url": "https://zero.76898102.xyz/", "trial": "免费白嫖机场", "note": "RanZiXuan/dd"},
    {"name": "ssrsub", "url": "https://sub.ssrsub.com/", "trial": "0元购优惠码", "note": "RanZiXuan/dd"},
    {"name": "悠兔机场", "url": "https://clashsub.net/youtu", "trial": "注册免费试用", "note": "jichang推荐"},
    {"name": "OKANC", "url": "https://clashsub.net/okanc", "trial": "注册免费试用", "note": "jichang推荐"},
    {"name": "红葉", "url": "https://xn--qprx60h.site/", "trial": "注册送50G免费", "note": "panda-vpn-pro"},
]

async def verify_airport(browser, airport):
    """验证单个机场的注册页面"""
    name, url = airport["name"], airport["url"]
    print(f"\n{'='*60}")
    print(f"[{name}] 开始验证: {url}")
    result = {"name": name, "url": url, "trial": airport.get("trial",""), "status": "unknown", "errors": []}
    
    try:
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            locale="zh-CN"
        )
        page = await context.new_page()
        
        try:
            await page.goto(url, timeout=20000, wait_until="domcontentloaded")
            await page.wait_for_timeout(3000)
        except Exception as e:
            result["status"] = "unreachable"
            result["errors"].append(f"页面加载失败: {str(e)[:100]}")
            await context.close()
            return result
        
        final_url = page.url
        result["final_url"] = final_url
        
        # 提取页面文本
        try:
            body_text = await page.evaluate("() => document.body.innerText.substring(0, 3000)")
        except:
            body_text = ""
        
        # 检查关键元素
        checks = {
            "has_email_input": "邮箱|email|Email|邮件|账号",
            "has_password_input": "密码|password|Password",
            "has_register_btn": "注册|register|Register|创建账号|Create Account",
            "has_login_btn": "登录|login|Login|Sign In",
            "has_trial_mention": "试用|免费|free|trial|测试",
            "has_captcha": "验证码|captcha|Captcha|CAPTCHA|人机验证|验证",
            "has_outlook_block": "不支持.*outlook|outlook.*不支持|禁止.*outlook",
            "has_invite_code_req": "邀请码|invite|Invite|推荐码|aff",
        }
        
        for key, pattern in checks.items():
            if re.search(pattern, body_text, re.IGNORECASE):
                result[key] = True
            else:
                result[key] = False
        
        # 截图
        safe_name = re.sub(r'[^\w\-]', '_', name)
        screenshot_path = OUTPUT_DIR / f"{safe_name}_register.png"
        try:
            await page.screenshot(path=str(screenshot_path), full_page=False)
            result["screenshot"] = str(screenshot_path)
        except:
            pass
        
        # 判断可注册性
        if result.get("has_email_input") and result.get("has_password_input"):
            if result.get("has_invite_code_req"):
                result["can_register"] = "needs_invite_code"
            elif result.get("has_captcha"):
                result["can_register"] = "with_captcha"
            else:
                result["can_register"] = "yes_no_captcha"
        elif result.get("has_login_btn") and not result.get("has_register_btn"):
            result["can_register"] = "login_only"
        else:
            result["can_register"] = "needs_inspection"
        
        if result.get("has_trial_mention"):
            result["status"] = "trial_available"
        elif result.get("can_register", "").startswith("yes"):
            result["status"] = "registerable"
        else:
            result["status"] = "check_manually"
        
        # 打印摘要
        print(f"  URL: {final_url[:80]}")
        print(f"  状态: {result['status']}")
        print(f"  邮箱输入: {result.get('has_email_input')}")
        print(f"  密码输入: {result.get('has_password_input')}")
        print(f"  注册按钮: {result.get('has_register_btn')}")
        print(f"  验证码: {result.get('has_captcha')}")
        print(f"  试用提及: {result.get('has_trial_mention')}")
        print(f"  邀请码: {result.get('has_invite_code_req')}")
        print(f"  综合判断: {result['can_register']}")
        
        await context.close()
        
    except Exception as e:
        result["status"] = "error"
        result["errors"].append(str(e)[:200])
        print(f"  ❌ 异常: {e}")
    
    return result


async def main():
    results = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            channel="msedge",
            headless=False,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
        )
        
        for airport in AIRPORTS_TO_TEST:
            r = await verify_airport(browser, airport)
            results.append(r)
            # 短暂间隔避免触发限速
            await asyncio.sleep(2)
        
        # 保持浏览器打开30秒供手动查看
        print("\n\n✅ 全部验证完成！浏览器保持打开30秒...")
        await asyncio.sleep(30)
        await browser.close()
    
    # 保存结果
    summary_path = OUTPUT_DIR / f"verify_summary_{time.strftime('%Y%m%d_%H%M%S')}.json"
    summary = {
        "test_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total": len(results),
        "success": sum(1 for r in results if r["status"] in ("trial_available","registerable")),
        "results": results
    }
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\n📊 结果已保存: {summary_path}")
    
    # 打印汇总表
    print("\n" + "="*80)
    print("验证结果汇总:")
    print(f"{'机场':<12} {'状态':<18} {'可注册':<20} {'试用':<10} {'验证码':<8}")
    print("-"*80)
    for r in results:
        status = r.get("status","?")
        can_reg = r.get("can_register","?")
        trial = "✅" if r.get("has_trial_mention") else "❌"
        captcha = "✅" if r.get("has_captcha") else "❌"
        print(f"{r['name']:<12} {status:<18} {can_reg:<20} {trial:<10} {captcha:<8}")

asyncio.run(main())
