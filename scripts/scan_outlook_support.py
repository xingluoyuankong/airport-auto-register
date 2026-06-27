"""快速扫描机场是否支持@outlook.com"""
import os,sys,json
from playwright.sync_api import sync_playwright

AIRPORTS = [
    {"name":"逗猫","url":"https://doucat.top/index.php#/register","free":"1天3G"},
    {"name":"一元机场","url":"https://xn--4gq62f52gdss.com/#/register","free":"11元/年50G"},
    {"name":"盛丰","url":"https://xn--iiq540h.com/auth/register","free":"5天1G"},
    {"name":"Arisaka","url":"https://reurl.cc/XG68o7","free":"10G"},
    {"name":"极客加速器","url":"https://board.jike99.xyz/#/register","free":"3天5G"},
    {"name":"宝贝云","url":"https://v3ssy.xyz/#/register","free":"1天2G"},
    {"name":"xqc.best","url":"https://xqc.best/#/register","free":"待确认"},
    {"name":"大牛机场","url":"https://daniu.e300daniu.top/#/register","free":"1h1G"},
    {"name":"青森云","url":"https://sub.cccc.gg/auth/register","free":"6小时"},
    {"name":"难民机场","url":"https://nanmin.xyz/#/register","free":"2天5G"},
    {"name":"BBQ烧烤店","url":"https://qiaoxbbq.com/#/register","free":"7天10G"},
    {"name":"猫熊网络","url":"https://mxwljsq.xyz/auth/register","free":"3天5G"},
    {"name":"纵横加速","url":"https://www.okvpn.cc/#/register","free":"7天2G"},
    {"name":"JetFast","url":"https://my.jetfast.dev/#/register","free":"1月5G"},
    {"name":"KELECLOUD","url":"https://panel.keleofficial.com/#/register","free":"1天1G"},
]

results = []
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, channel="msedge")
    page = browser.new_page()
    
    for ap in AIRPORTS:
        name = ap["name"]
        url = ap["url"]
        r = {"name": name, "url": url, "free": ap["free"], "outlook_support": False, "has_full_email": False, "reachable": False, "error": ""}
        
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=15000)
            page.wait_for_timeout(2000)
            body = page.evaluate("document.body.innerText")
            cur_url = page.url
            
            r["reachable"] = True
            
            # Check for @outlook.com mention
            if "@outlook.com" in body.lower() or "outlook.com" in body.lower():
                r["outlook_support"] = True
            
            # Check for full email input (single textbox with email type or @placeholder)
            has_full = page.evaluate("""() => {
                let inputs = document.querySelectorAll('input');
                for (let inp of inputs) {
                    let ph = (inp.placeholder || '').toLowerCase();
                    let tp = inp.type || '';
                    if ((ph.includes('@') || ph.includes('email') || tp === 'email') && 
                        !ph.includes('code') && !ph.includes('验证码')) {
                        return true;
                    }
                }
                return false;
            }""")
            r["has_full_email"] = has_full
            
            status = "OK" if r["outlook_support"] else "NO"
            email_type = "FULL" if has_full else "SPLIT"
            print(f"[{status}] {name} | {email_type} | {r['free']}")
            
        except Exception as e:
            r["error"] = str(e)[:100]
            print(f"[ERR] {name} | {r['error'][:80]}")
        
        results.append(r)
    
    browser.close()

# Summary
outlook_ok = [r for r in results if r["outlook_support"]]
full_email = [r for r in results if r["has_full_email"]]
print(f"\n=== SCAN RESULTS ===")
print(f"Total scanned: {len(results)}")
print(f"@outlook.com support: {len(outlook_ok)}")
print(f"Full email input: {len(full_email)}")
print(f"\n@outlook.com list:")
for r in outlook_ok:
    print(f"  {r['name']}: {r['url']}")
print(f"\nFull email list:")
for r in full_email:
    print(f"  {r['name']}: {r['url']}")
