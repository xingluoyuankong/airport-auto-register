import sys,io,time
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(channel='msedge',headless=False,args=['--proxy-server=http://127.0.0.1:7897','--ignore-certificate-errors','--no-sandbox'])
    ctx=b.new_context(viewport={'width':1280,'height':800},ignore_https_errors=True,locale='zh-CN')
    page=ctx.new_page()
    page.add_init_script('Object.defineProperty(navigator,"webdriver",{get:()=>false})')
    page.goto('https://flybit.vip/#/register',wait_until='networkidle',timeout=45000)
    time.sleep(3)
    
    print('=== FLYBIT ===')
    print(f'URL: {page.url}')
    print(f'Title: {page.title()}')
    
    cf=page.query_selector('iframe[src*="challenges.cloudflare.com"]')
    print(f'Turnstile: {"YES" if cf else "NO"}')
    
    print()
    print('--- INPUTS ---')
    for i,el in enumerate(page.query_selector_all('input')):
        attrs=el.evaluate('el=>({t:el.type,n:el.name,p:el.placeholder})')
        print(f'  [{i}] type={attrs["t"]} name={attrs["n"]} placeholder={attrs["p"]}')
    
    print()
    print('--- SELECTS ---')
    for i,sel in enumerate(page.query_selector_all('select')):
        opts=sel.evaluate('el=>Array.from(el.options).map(o=>o.value)')
        print(f'  [{i}] options: {opts}')
    
    print()
    print('--- BUTTONS ---')
    for i,btn in enumerate(page.query_selector_all('button')):
        t=(btn.inner_text() or '').strip()[:100]
        if t: print(f'  [{i}] "{t}"')
    
    print()
    print('--- PAGE TEXT ---')
    print(page.evaluate('()=>document.body.innerText')[:600])
    
    page.screenshot(path='flybit_analyze.png')
    print('screenshot: flybit_analyze.png')
    b.close()
