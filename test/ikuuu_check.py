import sys, os
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(channel='msedge', headless=False, args=['--ignore-certificate-errors','--no-sandbox','--proxy-server=http://127.0.0.1:7897'])
    ctx = b.new_context(viewport={'width':1280,'height':900}, ignore_https_errors=True)
    page = ctx.new_page()
    for url in ['https://ikuu.win','https://www.ikuu.win','https://ikuu8.com','https://ikuu.lol','https://ikuuu.org']:
        try:
            page.goto(url, wait_until='domcontentloaded', timeout=12000)
            title = page.title()
            body = page.evaluate('() => document.body.innerText.substring(0, 200)')
            print(f'{url} -> OK ({page.url}) title={title}')
            print(f'body={body}')
            page.screenshot(path=f'E:/API获取工具/自动集成免费代理服务/01-机场VPN注册机/test/ikuuu_check_{hash(url)%10000}.png')
        except Exception as e:
            code = str(e)[:80]
            print(f'{url} -> FAIL: {code}')
    b.close()
