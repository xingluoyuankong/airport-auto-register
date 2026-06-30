"""疾风云订阅提取 - Python playwright独立启动"""
from playwright.sync_api import sync_playwright
import time, json

with sync_playwright() as p:
    browser = p.chromium.launch(
        channel='msedge',
        headless=False,
        args=['--disable-blink-features=AutomationControlled']
    )
    ctx = browser.new_context()
    page = ctx.new_page()
    
    # 1. 登录
    page.goto('https://jfcec.cc/auth/login', wait_until='networkidle')
    time.sleep(2)
    
    # 处理可能的反bot页面
    try:
        page.click('text=点击访问网站', timeout=5000)
        page.wait_for_url('**/auth/login**', timeout=10000)
    except:
        pass
    
    page.fill('input[placeholder="邮箱"], input[name="email"]', 'jfcloud_test_2026@outlook.com')
    page.fill('input[placeholder="密码"], input[name="password"], input[type="password"]', 'VpnTest2026')
    page.click('button:has-text("登录"), button[type="submit"]')
    page.wait_for_url('**/user**', timeout=15000)
    print("登录成功!")
    
    time.sleep(3)
    
    # 2. Hook fetch和clipboard
    page.evaluate("""
        window.__captured_urls = [];
        window.__cap = null;
        
        // Hook fetch
        var origFetch = window.fetch;
        window.fetch = function() {
            var url = arguments[0];
            if(typeof url === 'string' && (url.indexOf('subscribe') >= 0 || url.indexOf('sub_link') >= 0 || url.indexOf('/sub/') >= 0 || url.indexOf('token=') >= 0)) {
                window.__captured_urls.push('FETCH:' + url);
            }
            return origFetch.apply(this, arguments).then(function(response) {
                var clone = response.clone();
                if(typeof url === 'string' && (url.indexOf('subscribe') >= 0 || url.indexOf('sub_link') >= 0 || url.indexOf('/sub/') >= 0)) {
                    clone.text().then(function(body) {
                        window.__captured_urls.push('RESP:' + url + '=' + body);
                    });
                }
                return response;
            });
        };
        
        // Hook XMLHttpRequest
        var origXHROpen = XMLHttpRequest.prototype.open;
        XMLHttpRequest.prototype.open = function(method, url) {
            if(url.indexOf('subscribe') >= 0 || url.indexOf('sub_link') >= 0) {
                window.__captured_urls.push('XHR:' + method + ' ' + url);
                this.addEventListener('load', function() {
                    window.__captured_urls.push('XHR-RESP:' + url + '=' + this.responseText);
                });
            }
            return origXHROpen.apply(this, arguments);
        };
        
        // Hook clipboard
        navigator.clipboard.writeText = function(t) {
            window.__cap = t;
            window.__captured_urls.push('CLIPBOARD:' + t);
            return Promise.resolve();
        };
        
        document.addEventListener('copy', function(e) {
            if(e.clipboardData) {
                var t = e.clipboardData.getData('text');
                window.__cap = t;
                window.__captured_urls.push('COPY:' + t);
            }
        });
        
        // 关闭modal
        document.querySelectorAll('.modal').forEach(function(m){
            m.classList.remove('show');
            m.style.display='none';
        });
        document.querySelectorAll('.modal-backdrop').forEach(function(b){b.remove()});
    """)
    
    time.sleep(1)
    
    # 3. 依次点击每个订阅按钮
    # 先尝试V2Ray
    print("\n=== 尝试点击V2Ray订阅 ===")
    page.evaluate("""
        var es = document.querySelectorAll('a.btn,[role=button]');
        for(var i=0;i<es.length;i++){
            if(es[i].textContent.indexOf('V2Ray')>=0){
                es[i].click();
                break;
            }
        }
    """)
    time.sleep(2)
    cap = page.evaluate("() => window.__cap")
    print(f"Clipboard: {cap}")
    
    if not cap:
        # 点Clash
        print("\n=== 尝试点击Clash订阅 ===")
        page.evaluate("""
            var es = document.querySelectorAll('a.btn,[role=button]');
            for(var i=0;i<es.length;i++){
                if(es[i].textContent.indexOf('Clash')>=0 && es[i].textContent.indexOf('教程')===-1){
                    es[i].click();
                    break;
                }
            }
        """)
        time.sleep(2)
        cap = page.evaluate("() => window.__cap")
        print(f"Clipboard: {cap}")
    
    if not cap:
        # 点Shadowrocket
        print("\n=== 尝试点击Shadowrocket ===")
        page.evaluate("""
            var es = document.querySelectorAll('a.btn,[role=button]');
            for(var i=0;i<es.length;i++){
                if(es[i].textContent.indexOf('Shadowrocket')>=0 || es[i].textContent.indexOf('小火箭')>=0){
                    es[i].click();
                    break;
                }
            }
        """)
        time.sleep(2)
        cap = page.evaluate("() => window.__cap")
        print(f"Clipboard: {cap}")
    
    # 4. 输出所有捕获
    captured = page.evaluate("() => window.__captured_urls")
    print("\n=== 所有捕获的信息 ===")
    for c in captured:
        print(f"  {c[:300]}")
    
    if cap and cap != 'null':
        print(f"\n>>> 疾风云订阅链接: {cap}")
    else:
        print("\n>>> 未捕获到订阅链接")
    
    # 输出结果
    with open('jifeng_result.json', 'w', encoding='utf-8') as f:
        json.dump({'cap': cap, 'captured': captured}, f, ensure_ascii=False, indent=2)
    print(f"\n结果已保存到 jifeng_result.json")
    browser.close()
