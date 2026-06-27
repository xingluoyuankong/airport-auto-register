#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Playwright浏览器驱动注册器
============================
用于需要真实浏览器的机场（有Turnstile/验证码/复杂表单的站点）

功能:
  - 自动打开浏览器注册
  - 处理Turnstile验证码
  - 自动填写表单
  - 从Outlook提取验证码
  - 提取订阅链接

用法: python browser_register.py --airport FSCloud --email parker738403dcp34kfdl6j@outlook.com --password "oo^5v=Q%&RU$pdDrax"

依赖: playwright, playwright-stealth, ddddocr, outlook_skill
"""

import asyncio
import json
import os
import re
import sys
import time
import argparse
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from outlook_skill import OutlookVerifier, BUILTIN_EMAILS

# ============ 机场注册配置 ============
AIRPORT_CONFIGS = {
    "FSCloud": {
        "url": "https://dash.fscloud.app",
        "register_url": "https://dash.fscloud.app/#/register",
        "has_turnstile": True,
        "email_selector": 'input[type="email"], input[name="email"], input[placeholder*="邮箱"], input[placeholder*="email"]',
        "password_selector": 'input[type="password"], input[name="password"]',
        "submit_selector": 'button[type="submit"], button:has-text("注册"), button:has-text("Register"), button:has-text("Sign up")',
        "verify_code_selector": 'input[name="email_code"], input[placeholder*="验证码"], input[placeholder*="code"]',
    },
    "奈云v2ny": {
        "url": "https://www.v2ny.com",
        "register_url": "https://www.v2ny.com/#/register",
        "has_turnstile": True,
        "email_selector": 'input[type="email"], input[placeholder*="邮箱"]',
        "password_selector": 'input[type="password"]',
        "submit_selector": 'button:has-text("注册"), button:has-text("Register")',
        "verify_code_selector": 'input[placeholder*="验证码"], input[name="email_code"]',
    },
    "Speedy": {
        "url": "https://cloud.speedypro.xyz",
        "register_url": "https://cloud.speedypro.xyz/#/register",
        "has_turnstile": True,
        "email_selector": 'input[type="email"], input[placeholder*="邮箱"]',
        "password_selector": 'input[type="password"]',
        "submit_selector": 'button:has-text("注册")',
        "verify_code_selector": 'input[name="email_code"]',
    },
    # 通用V2Board配置
    "v2board_default": {
        "has_turnstile": True,
        "email_selector": 'input[type="email"], input[placeholder*="邮箱"], input[placeholder*="email"], input[name="email"]',
        "password_selector": 'input[type="password"], input[name="password"], input[name="passwd"]',
        "submit_selector": 'button[type="submit"], button:has-text("注册"), button:has-text("Register"), button:has-text("Sign up"), button:has-text("注 册")',
        "verify_code_selector": 'input[name="email_code"], input[placeholder*="验证码"], input[placeholder*="code"], input[name="code"]',
    },
}


class BrowserRegistrar:
    """浏览器驱动机场注册器"""
    
    def __init__(self, headless=False):
        self.headless = headless
        self.ov = OutlookVerifier()
        self.results = []
    
    async def init_browser(self):
        """初始化浏览器"""
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            print("❌ 请先安装: pip install playwright && playwright install chromium")
            sys.exit(1)
        
        self.playwright = await async_playwright().start()
        
        # 使用Chromium，添加反检测参数
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
            ]
        )
        
        self.context = await self.browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            locale="zh-CN",
        )
        
        # 注入stealth脚本
        try:
            from playwright_stealth import stealth_async
            self.page = await self.context.new_page()
            await stealth_async(self.page)
        except ImportError:
            self.page = await self.context.new_page()
            # 手动注入反检测
            await self.page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => false});
                Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN','zh','en']});
            """)
        
        print("✅ 浏览器已启动")
    
    async def try_solve_turnstile(self, timeout=30):
        """尝试解决Turnstile验证码"""
        print("  [Turnstile] 检测验证码...")
        
        # 等待Turnstile iframe出现
        try:
            frame = await self.page.wait_for_selector(
                'iframe[src*="challenges.cloudflare.com"], iframe[src*="turnstile"], div.cf-turnstile',
                timeout=5000
            )
            if frame:
                print("  [Turnstile] 发现Cloudflare Turnstile")
        except:
            # 没有Turnstile
            return True
        
        # 策略1: 等待用户手动点击（headed模式）
        if not self.headless:
            print("  [Turnstile] 请手动完成验证码...")
            deadline = time.time() + timeout
            while time.time() < deadline:
                # 检查是否还在页面上
                has_turnstile = await self.page.query_selector('iframe[src*="challenges.cloudflare.com"]')
                if not has_turnstile:
                    print("  [Turnstile] ✅ 验证码已通过")
                    return True
                await asyncio.sleep(1)
            print("  [Turnstile] ⚠️ 超时")
            return False
        
        # 策略2: 无头模式 - 尝试用playwright点击
        try:
            # 尝试找到并点击Turnstile复选框
            checkbox = await self.page.query_selector('.cb-lb input[type="checkbox"]')
            if checkbox:
                await checkbox.click()
                await asyncio.sleep(3)
                
                # 检查是否通过
                has_turnstile = await self.page.query_selector('iframe[src*="challenges.cloudflare.com"]')
                if not has_turnstile:
                    print("  [Turnstile] ✅ 验证码已通过")
                    return True
        except:
            pass
        
        return False
    
    async def register(self, airport_name: str, email: str, password: str, 
                       custom_url: str = None) -> dict:
        """浏览器自动注册机场"""
        print(f"\n{'='*50}")
        print(f"  注册: {airport_name}")
        print(f"  邮箱: {email[:25]}...")
        print(f"{'='*50}")
        
        # 获取配置
        config = AIRPORT_CONFIGS.get(airport_name, AIRPORT_CONFIGS["v2board_default"])
        
        # 确定URL
        if custom_url:
            base_url = custom_url.rstrip("/")
            register_url = custom_url.rstrip("/") + "/#/register"
        elif "register_url" in config:
            register_url = config["register_url"]
            base_url = config.get("url", "/".join(register_url.split("/")[:3]))
        else:
            return {"success": False, "error": "未配置URL"}
        
        try:
            # 导航到注册页
            print(f"  导航: {register_url}")
            await self.page.goto(register_url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(2)
            
            # 处理Turnstile
            if config.get("has_turnstile"):
                solved = await self.try_solve_turnstile(timeout=60)
                if not solved and not self.headless:
                    print("  ⚠️ Turnstile未自动解决，请手动完成")
                    solved = await self.try_solve_turnstile(timeout=120)
            
            # 填写邮箱
            email_input = await self.page.wait_for_selector(config["email_selector"], timeout=10000)
            if email_input:
                await email_input.click()
                await email_input.fill(email)
                print(f"  ✅ 邮箱已填写")
            else:
                return {"success": False, "error": "找不到邮箱输入框"}
            
            # 填写密码
            try:
                password_inputs = await self.page.query_selector_all(config["password_selector"])
                if len(password_inputs) >= 1:
                    await password_inputs[0].click()
                    await password_inputs[0].fill(password)
                    print(f"  ✅ 密码已填写")
                if len(password_inputs) >= 2:
                    await password_inputs[1].click()
                    await password_inputs[1].fill(password)
                    print(f"  ✅ 确认密码已填写")
            except Exception as e:
                return {"success": False, "error": f"填写密码失败: {e}"}
            
            # 点击提交
            submit_btn = await self.page.query_selector(config["submit_selector"])
            if not submit_btn:
                # 尝试其他选择器
                submit_btn = await self.page.query_selector('button:has-text("注"), button:has-text("Reg"), button:has-text("Sign"), button[type="submit"]')
            
            if submit_btn:
                await submit_btn.click()
                print(f"  ✅ 已提交注册")
                await asyncio.sleep(2)
            else:
                return {"success": False, "error": "找不到提交按钮"}
            
            # 等待验证码输入页出现
            await asyncio.sleep(2)
            
            # 检查是否需要验证码
            verify_input = await self.page.query_selector(config["verify_code_selector"])
            if verify_input:
                print(f"  需要邮箱验证码，等待中...")
                
                # 从Outlook获取验证码
                code_result = self.ov.get_code_imap(email, password, timeout=90)
                
                if code_result.get("success") and code_result.get("code"):
                    code = code_result["code"]
                    print(f"  ✅ 获取到验证码: {code}")
                    
                    await verify_input.click()
                    await verify_input.fill(code)
                    await asyncio.sleep(1)
                    
                    # 再次提交
                    submit_btn2 = await self.page.query_selector(config["submit_selector"])
                    if submit_btn2:
                        await submit_btn2.click()
                        await asyncio.sleep(3)
                else:
                    print(f"  ❌ 未收到验证码")
            
            # 检查是否注册成功（跳转到用户面板）
            current_url = self.page.url
            print(f"  当前URL: {current_url}")
            
            if any(kw in current_url.lower() for kw in ["dashboard", "user", "home", "panel"]):
                print(f"  ✅ 注册成功!")
                
                # 提取订阅链接
                sub_url = await self.extract_subscribe_link(base_url)
                
                return {
                    "success": True,
                    "airport": airport_name,
                    "email": email,
                    "password": password,
                    "url": current_url,
                    "subscribe_url": sub_url,
                }
            else:
                # 截图保存调试信息
                screenshot_path = os.path.join(
                    os.path.dirname(__file__), 
                    f"debug_{airport_name}_{datetime.now().strftime('%H%M%S')}.png"
                )
                await self.page.screenshot(path=screenshot_path)
                print(f"  调试截图: {screenshot_path}")
                
                return {
                    "success": False,
                    "error": f"注册后未进入面板，当前URL: {current_url}",
                    "screenshot": screenshot_path,
                }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def extract_subscribe_link(self, base_url: str) -> str:
        """从面板提取订阅链接"""
        try:
            # 尝试导航到用户中心
            user_url = base_url.rstrip("/") + "/#/user"
            await self.page.goto(user_url, wait_until="networkidle", timeout=15000)
            await asyncio.sleep(2)
            
            # 尝试点击"复制订阅"按钮
            copy_btns = await self.page.query_selector_all(
                'button:has-text("订阅"), button:has-text("Subscribe"), button:has-text("复制"), '
                'span:has-text("订阅"), div:has-text("订阅")'
            )
            
            for btn in copy_btns:
                try:
                    await btn.click()
                    await asyncio.sleep(1)
                    # 读取剪贴板
                    clipboard_text = await self.page.evaluate("navigator.clipboard.readText()")
                    if "/api/v1/client/subscribe" in clipboard_text or "sub" in clipboard_text.lower():
                        return clipboard_text
                except:
                    pass
            
            # 直接在页面上找订阅链接
            page_text = await self.page.content()
            sub_patterns = [
                r'(https?://[^\s"\'<>]+/api/v1/client/subscribe\?token=[^\s"\'<>]+)',
                r'(https?://[^\s"\'<>]+sub[^\s"\'<>]+token=[^\s"\'<>]+)',
            ]
            
            for pattern in sub_patterns:
                match = re.search(pattern, page_text, re.I)
                if match:
                    return match.group(1)
            
            # 通过API获取
            await self.page.evaluate("""
                fetch('/api/v1/user/getSubscribe', {
                    headers: { 'Authorization': localStorage.getItem('auth_data') || '' }
                }).then(r => r.json()).then(d => window.__subscribe_url = d?.data?.subscribe_url)
            """)
            await asyncio.sleep(1)
            sub_url = await self.page.evaluate("window.__subscribe_url || ''")
            if sub_url:
                return sub_url
            
        except Exception as e:
            print(f"  提取订阅链接失败: {e}")
        
        return ""
    
    async def close(self):
        """关闭浏览器"""
        if hasattr(self, 'browser') and self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright') and self.playwright:
            await self.playwright.stop()
        print("浏览器已关闭")


async def main():
    parser = argparse.ArgumentParser(description="浏览器驱动机场注册器")
    parser.add_argument("--airport", required=True, help="机场名称")
    parser.add_argument("--email", help="邮箱地址（可选，默认用内置邮箱）")
    parser.add_argument("--password", help="邮箱密码（可选）")
    parser.add_argument("--url", help="自定义注册URL")
    parser.add_argument("--headless", action="store_true", help="无头模式")
    parser.add_argument("--list", action="store_true", help="列出支持的机场")
    
    args = parser.parse_args()
    
    if args.list:
        print("支持的机场配置:")
        for name, config in AIRPORT_CONFIGS.items():
            print(f"  - {name}: {config.get('url', '自定义URL')}")
        return
    
    # 获取邮箱
    if args.email and args.password:
        email = args.email
        password = args.password
    else:
        email_info = BUILTIN_EMAILS[0]
        email = email_info["email"]
        password = email_info["password"]
        print(f"使用内置邮箱: {email[:20]}...")
    
    registrar = BrowserRegistrar(headless=args.headless)
    
    try:
        await registrar.init_browser()
        result = await registrar.register(args.airport, email, password, args.url)
        
        print(f"\n{'='*50}")
        print(f"  注册结果: {'✅ 成功' if result.get('success') else '❌ 失败'}")
        if result.get("success"):
            print(f"  机场: {result['airport']}")
            print(f"  邮箱: {result['email']}")
            print(f"  密码: {result['password']}")
            print(f"  订阅: {result.get('subscribe_url', '无')}")
        else:
            print(f"  错误: {result.get('error', '未知')}")
        print(f"{'='*50}")
        
        # 保存结果
        results_dir = os.path.join(os.path.dirname(__file__), "register_results")
        os.makedirs(results_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(os.path.join(results_dir, f"browser_{args.airport}_{ts}.json"), "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
    finally:
        await registrar.close()

if __name__ == "__main__":
    asyncio.run(main())
