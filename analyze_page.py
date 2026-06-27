#!/usr/bin/env python3
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # 导航到稳连云注册页
        await page.goto("https://wenlianyun.com/#/register", wait_until="networkidle")
        await asyncio.sleep(2)
        
        # 填充表单
        await page.fill('input[type="email"]', "test@example.com")
        await page.fill('input[type="password"]', "Test123456!")
        await page.fill('input[placeholder*="密码"]', "Test123456!")
        print("表单已填充")
        
        # 检查所有按钮
        buttons = await page.query_selector_all('button')
        print(f"\n找到 {len(buttons)} 个按钮:")
        for i, btn in enumerate(buttons):
            text = await btn.inner_text()
            visible = await btn.is_visible()
            print(f"  [{i}] '{text[:40]}' visible={visible}")
        
        # 检查是否有"发送验证码"类按钮
        send_code_btn = await page.query_selector('button:has-text("发送"), button:has-text("获取"), button:has-text("code"), button:has-text("Code")')
        if send_code_btn:
            print("\n找到发送验证码按钮!")
            text = await send_code_btn.inner_text()
            print(f"  文字: {text}")
        
        # 点击注册，看会发生什么
        print("\n点击注册按钮...")
        await page.click('button:has-text("注册")')
        await asyncio.sleep(3)
        
        # 再次检查按钮和输入框
        print("\n点击后页面检查:")
        all_inputs = await page.query_selector_all('input')
        print(f"  输入框数量: {len(all_inputs)}")
        for inp in all_inputs:
            attrs = await inp.evaluate('el => ({type: el.type, name: el.name, placeholder: el.placeholder})')
            visible = await inp.is_visible()
            print(f"    {attrs} visible={visible}")
        
        # 检查是否有验证码输入框出现
        code_input = await page.query_selector('input[placeholder*="验证码"], input[name="email_code"], input[name="code"]')
        if code_input:
            print("\n找到验证码输入框!")
            visible = await code_input.is_visible()
            print(f"  visible={visible}")
        else:
            print("\n未找到验证码输入框")
        
        # 截图
        await page.screenshot(path="analyze_page.png")
        print("\n截图保存: analyze_page.png")
        
        await browser.close()

asyncio.run(main())
