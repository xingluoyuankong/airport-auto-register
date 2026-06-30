"""大哥云订阅提取 - 全层拦截"""
from playwright.sync_api import sync_playwright
import base64, time, json

def solve_captcha(page):
    svg = page.evaluate("() => document.querySelector('img').getAttribute('src')")
    raw = base64.b64decode(svg.split(',')[1])
    text = raw.decode('utf-8')
    code = ''
    for line in text.split('>'):
        if line.endswith('</text'):
            for c in reversed(line):
                if c == '<': break
                if c.isdigit(): code = c + code
    print(f"  Captcha: {code}")
    return code

with sync_playwright() as p:
    browser = p.chromium.launch(channel='msedge', headless=False)
    page = browser.new_page()
    page.goto('https://a03.dgy02.com/#/login', wait_until='domcontentloaded')
    time.sleep(4)
    
    if not page.evaluate("() => document.querySelector('input')"):
        page.evaluate("() => location.href='https://a03.dgy02.com/#/login'")
        time.sleep(4)
    
    code = solve_captcha(page)
    page.fill('[placeholder*="邮箱"]', 'dageyun_test_2026@outlook.com')
    page.fill('[placeholder*="密码"]', 'VpnTest2026')
    page.fill('[placeholder*="验证码"]', code)
    page.click('button:has-text("登入")')
    time.sleep(4)
    print(f"  Login => {page.url}")
    
    # 关弹窗
    try: page.click('button:has-text("Close")', timeout=3000)
    except: pass
    time.sleep(1)
    
    # 一键订阅
    page.click('text=一键订阅')
    time.sleep(1)
    
    # === 全层拦截 ===
    page.evaluate("""
    window.CAPTURED = [];
    window.SUB_URL = null;
    
    // Hook clipboard
    navigator.clipboard.writeText = function(t) {
        window.SUB_URL = t;
        window.CAPTURED.push('CLIP:' + t);
        return Promise.resolve();
    };
    
    // Hook execCommand
    var _exec = document.execCommand;
    document.execCommand = function(cmd) {
        window.CAPTURED.push('EXEC:' + cmd);
        if(cmd === 'copy') {
            var sel = window.getSelection();
            if(sel && sel.toString()) {
                window.SUB_URL = sel.toString();
                window.CAPTURED.push('SEL:' + sel.toString());
            }
        }
        return _exec.apply(document, arguments);
    };
    
    // Hook fetch
    var _fetch = window.fetch;
    window.fetch = function(url, opts) {
        var u = typeof url === 'string' ? url : url.url;
        window.CAPTURED.push('FETCH:' + u);
        return _fetch.apply(this, arguments).then(function(r) {
            var c = r.clone();
            c.text().then(function(t) {
                if(t.indexOf('subscribe') >= 0 || t.indexOf('token') >= 0 || t.indexOf('sub_url') >= 0)
                    window.CAPTURED.push('FETCH-RESP:' + u + '=' + t.substring(0,500));
            }).catch(function(){});
            return r;
        });
    };
    
    // Hook XHR
    var _open = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function(m, u) {
        this.__u = u;
        window.CAPTURED.push('XHR:' + m + ' ' + u);
        var x = this;
        x.addEventListener('load', function() {
            window.CAPTURED.push('XHR-RESP:' + x.__u + '=' + x.responseText.substring(0,500));
        });
        return _open.apply(this, arguments);
    };
    
    // Watch DOM for textarea/hidden inputs
    new MutationObserver(function(ms) {
        ms.forEach(function(m) {
            m.addedNodes.forEach(function(n) {
                if(n.nodeType === 1) {
                    var v = n.value || n.getAttribute('data-clipboard-text') || '';
                    if(v && v.length > 5 && v.indexOf('http') >= 0) {
                        window.CAPTURED.push('DOM:' + v);
                        window.SUB_URL = v;
                    }
                }
            });
        });
    }).observe(document.body, {childList: true, subtree: true, attributes: true, attributeFilter: ['data-clipboard-text']});
    """)
    
    time.sleep(1)
    
    # 点击复制订阅地址
    page.evaluate("""
    var el = document.querySelector('.subsrcibe-for-link');
    if(el) el.click();
    else {
        var all = document.querySelectorAll('*');
        for(var i=0;i<all.length;i++){
            if(all[i].textContent.trim() === '复制订阅地址'){
                all[i].click();
                break;
            }
        }
    }
    """)
    
    time.sleep(3)
    
    # 收网
    captured = page.evaluate("() => window.CAPTURED || []")
    sub_url = page.evaluate("() => window.SUB_URL")
    
    print(f"\n  SUB URL: {sub_url}")
    print(f"\n  All captured ({len(captured)} items):")
    for c in captured[:30]:
        print(f"    {str(c)[:200]}")
    
    # 额外：扫描DOM中所有data-clipboard-text
    clips = page.evaluate("""
    () => {
        var r = [];
        document.querySelectorAll('[data-clipboard-text]').forEach(function(el){
            r.push(el.tagName + ': ' + el.getAttribute('data-clipboard-text'));
        });
        return r;
    }
    """)
    print(f"\n  data-clipboard-text elements: {clips}")
    
    # 查找所有input/textarea
    hidden = page.evaluate("""
    () => {
        var r = [];
        document.querySelectorAll('input,textarea').forEach(function(el){
            var v = el.value || '';
            if(v.indexOf('http') >= 0 || v.indexOf('token') >= 0 || v.indexOf('sub') >= 0)
                r.push(el.tagName + '[' + (el.name||el.id||'') + ']=' + v.substring(0,200));
        });
        return r;
    }
    """)
    print(f"\n  Input/textarea values: {hidden}")
    
    with open('dageyun_final.json', 'w', encoding='utf-8') as f:
        json.dump({'url': sub_url, 'captured': [str(c) for c in captured], 'clips': clips, 'hidden': hidden}, f, ensure_ascii=False, indent=2)
    
    print("\n  Saved to dageyun_final.json")
    time.sleep(5)
    browser.close()
