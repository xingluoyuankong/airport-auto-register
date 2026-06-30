"""大哥云极简提取"""
from playwright.sync_api import sync_playwright
import base64 as b64
from io import BytesIO
import time, json, re

def captcha(page):
    svg = page.evaluate("() => document.querySelector('img').getAttribute('src')")
    data = b64.b64decode(svg.split(',')[1]).decode()
    return ''.join(re.findall(r'>(\d+)<', data))

with sync_playwright() as p:
    b = p.chromium.launch(channel='msedge', headless=False)
    pg = b.new_page()
    pg.goto('https://a03.dgy02.com/#/login', wait_until='domcontentloaded', timeout=15000)
    time.sleep(5)
    # Ensure SPA loaded
    pg.evaluate("() => location.href = 'https://a03.dgy02.com/#/login'")
    time.sleep(3)
    
    # Login
    code = captcha(pg)
    print(f"Captcha: {code}")
    pg.fill('[placeholder*="邮箱"]', 'dageyun_test_2026@outlook.com')
    pg.fill('[placeholder*="密码"]', 'VpnTest2026')
    pg.fill('[placeholder*="验证码"]', code)
    pg.click('button:has-text("登入")')
    time.sleep(4)
    print(f"Login: {pg.url}")
    
    # Close dialog
    try: pg.click('button:has-text("Close")', timeout=3000)
    except: pass
    time.sleep(1)
    
    # Hook + click
    pg.evaluate("""
        window._url = null;
        var origExec = document.execCommand;
        document.execCommand = function(cmd) {
            if(cmd === 'copy') {
                var t = document.querySelector('textarea');
                if(t) window._url = t.value;
                if(!window._url) {
                    var sel = window.getSelection();
                    if(sel) window._url = sel.toString();
                }
            }
            return origExec.apply(document, arguments);
        };
        
        var origWrite = navigator.clipboard.writeText;
        if(origWrite) navigator.clipboard.writeText = function(t) {
            window._url = t;
            return Promise.resolve();
        };
        
        var origWrite2 = navigator.clipboard.write;
        if(origWrite2) navigator.clipboard.write = function(t) {
            window._url = new TextDecoder().decode(t[0]);
            return Promise.resolve();
        };
        
        document.addEventListener('copy', function(e) {
            if(e.clipboardData) window._url = e.clipboardData.getData('text');
        }, true);
        
        // Also observe textarea additions
        new MutationObserver(function(ms) {
            ms.forEach(function(m) {
                m.addedNodes.forEach(function(n) {
                    if(n.tagName === 'TEXTAREA' || n.tagName === 'INPUT') {
                        window._url = n.value;
                    }
                    if(n.nodeType === 1) {
                        var h = n.innerHTML || '';
                        var m2 = h.match(/https?:\\/\\/[^"\\s]{20,}/);
                        if(m2) window._url = m2[0];
                    }
                });
            });
        }).observe(document.body, {childList: true, subtree: true});
    """)
    
    # Click 一键订阅
    pg.click('text=一键订阅')
    time.sleep(2)
    
    # Click 复制订阅地址
    el = pg.evaluate("""() => {
        var el = document.querySelector('.subsrcibe-for-link');
        if(el) { el.click(); return 'clicked via class'; }
        var all = document.querySelectorAll('*');
        for(var i=0;i<all.length;i++) {
            if(all[i].textContent.trim() === '复制订阅地址') {
                all[i].click();
                return 'clicked via text';
            }
        }
        return 'not found';
    }""")
    print(f"Click: {el}")
    time.sleep(3)
    
    url = pg.evaluate("() => window._url")
    print(f"URL: {url}")
    
    # Try scanning DOM
    dom = pg.evaluate("""() => {
        var r = [];
        document.querySelectorAll('*').forEach(function(e) {
            var dc = e.getAttribute ? e.getAttribute('data-clipboard-text') : null;
            if(dc && dc.indexOf('http') >= 0) r.push('dc:' + dc);
            if(e.tagName === 'INPUT' || e.tagName === 'TEXTAREA') {
                if(e.value && e.value.indexOf('http') >= 0) r.push('input:' + e.value);
            }
        });
        return r;
    }""")
    print(f"DOM: {dom}")
    
    # Visit subscribe page  
    pg.goto('https://a03.dgy02.com/#/subscribe')
    time.sleep(3)
    text = pg.evaluate("() => document.body.innerText.substring(0,1000)")
    print(f"Subscribe page: {text[:500]}")
    
    with open('dg_result.json', 'w') as f:
        json.dump({'url': url, 'dom': dom, 'page': text}, f)
    
    print("Done")
    time.sleep(5)
    b.close()
