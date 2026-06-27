"""直接连接已打开的Playwright浏览器，获取宝可梦订阅链接"""
import asyncio
from playwright.async_api import async_playwright
import json

async def main():
    async with async_playwright() as p:
        # 连接到已运行的浏览器 (playwright-cli打开的)
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        pages = browser.contexts[0].pages
        print(f"Found {len(pages)} pages")
        
        for page in pages:
            print(f"Page: {page.url}")
            if "52pokemon" in page.url:
                # Get token
                token = await page.evaluate("localStorage.getItem('token')")
                print(f"Token: {token}")
                
                # Get user info via fetch
                info = await page.evaluate("""
                    async () => {
                        const resp = await fetch('/api/v1/user/info', {
                            headers: {'Authorization': localStorage.getItem('token')}
                        });
                        return await resp.text();
                    }
                """)
                print(f"User Info: {info[:2000]}")
                
                # Try getting subscribe URL
                sub = await page.evaluate("""
                    async () => {
                        const resp = await fetch('/api/v1/user/getSubscribe', {
                            headers: {'Authorization': localStorage.getItem('token')}
                        });
                        return await resp.text();
                    }
                """)
                print(f"Subscribe: {sub[:2000]}")
                
                # Also try to get it from page elements
                html = await page.content()
                # Look for subscribe URLs in HTML
                import re
                urls = re.findall(r'(https?://[^"\'\\s<>]+)', html)
                sub_urls = [u for u in urls if 'subscribe' in u.lower() or 'sub?' in u.lower()]
                print(f"\nFound subscription URLs in HTML: {sub_urls}")
                
                # Try the page's vue app data
                app_data = await page.evaluate("""
                    () => {
                        const root = document.querySelector('#app');
                        if (root && root.__vue_app__) {
                            return JSON.stringify(Object.keys(root.__vue_app__));
                        }
                        const pinia = document.querySelector('[data-v-app]');
                        return 'no vue app found';
                    }
                """)
                print(f"Vue App: {app_data}")

asyncio.run(main())
