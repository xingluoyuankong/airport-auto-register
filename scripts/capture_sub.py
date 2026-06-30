"""捕获所有XHR/Fetch + 查找订阅URL"""
from playwright.sync_api import sync_playwright
import time, json

with sync_playwright() as p:
    browser = p.chromium.launch(channel='msedge', headless=False)
    ctx = browser.new_context()
    page = ctx.new_page()
    
    all_requests = []
    all_responses = []
    
    def on_request(request):
        all_requests.append({
            'url': request.url,
            'method': request.method,
            'resource_type': request.resource_type,
            'headers': dict(request.headers)
        })
        # Remove data URLs to keep log small
        if len(all_requests) > 200:
            all_requests.pop(0)
    
    def on_response(response):
        url = response.url
        if response.resource_type in ['xhr', 'fetch', 'document'] or 'api' in url:
            try:
                body = response.text()
                if body and len(body) < 5000:
                    all_responses.append({
                        'url': url,
                        'status': response.status,
                        'body': body[:500]
                    })
            except:
                all_responses.append({
                    'url': url,
                    'status': response.status,
                    'body': 'failed_to_read'
                })
        if len(all_responses) > 100:
            all_responses.pop(0)
    
    page.on('request', on_request)
    page.on('response', on_response)
    
    # 登录
    print("登录疾风云...")
    page.goto('https://jfcec.cc/auth/login', wait_until='networkidle')
    time.sleep(2)
    
    try:
        page.click('text=点击访问网站', timeout=5000)
        page.wait_for_url('**/auth/login**', timeout=10000)
    except:
        pass
    
    page.fill('[placeholder*="邮箱"]', 'jfcloud_test_2026@outlook.com')
    page.fill('[placeholder*="密码"]', 'VpnTest2026')
    page.click('button:has-text("登录")')
    page.wait_for_url('**/user**', timeout=15000)
    print("  登录成功!")
    time.sleep(3)
    
    # 清除之前的所有请求记录
    all_requests.clear()
    all_responses.clear()
    
    # Hook copy
    page.evaluate("""
        window.__cap = null;
        var origExec = document.execCommand;
        document.execCommand = function(cmd) {
            if(cmd === 'copy') {
                var sel = window.getSelection();
                window.__cap = sel ? sel.toString() : '';
            }
            return origExec.apply(document, arguments);
        };
        document.addEventListener('copy', function(e) {
            e.stopImmediatePropagation();
            window.__cap = e.clipboardData ? e.clipboardData.getData('text') : '';
        }, true);
    """)
    
    # 关闭modal
    page.evaluate("""
        document.querySelectorAll('.modal').forEach(function(m){
            m.classList.remove('show'); m.style.display='none';
        });
        document.querySelectorAll('.modal-backdrop').forEach(function(b){b.remove()});
    """)
    time.sleep(0.5)
    
    # 获取V2Ray按钮的详情
    btn_info = page.evaluate("""() => {
        var es = document.querySelectorAll('a.btn,[role=button]');
        for(var i=0;i<es.length;i++){
            if(es[i].textContent.indexOf('V2Ray')>=0){
                var el = es[i];
                return {
                    tag: el.tagName,
                    href: el.href,
                    id: el.id,
                    className: el.className,
                    outerHTML: el.outerHTML.substring(0,500),
                    onclick: el.onclick ? el.onclick.toString() : 'no onclick',
                    attached: typeof el.click === 'function'
                };
            }
        }
        return null;
    }""")
    print(f"  V2Ray按钮: {json.dumps(btn_info, ensure_ascii=False)[:500]}")
    
    # 阻止链接导航，然后点击
    page.evaluate("""
        var es = document.querySelectorAll('a.btn,[role=button]');
        for(var i=0;i<es.length;i++){
            if(es[i].textContent.indexOf('V2Ray')>=0){
                // 阻止默认行为
                es[i].addEventListener('click', function(e){
                    e.preventDefault();
                    e.stopPropagation();
                }, true);
                es[i].click();
                break;
            }
        }
    """)
    time.sleep(3)
    
    cap = page.evaluate("() => window.__cap")
    print(f"  Clipboard: {cap}")
    
    # 检查是否有弹出modal
    modals = page.evaluate("""() => {
        var ms = document.querySelectorAll('.modal.show, [class*=modal].show, dialog[open]');
        var r = [];
        ms.forEach(function(m){
            r.push(m.textContent ? m.textContent.substring(0,1000) : '');
        });
        return r;
    }""")
    print(f"  Modals after click: {json.dumps(modals, ensure_ascii=False)[:500]}")
    
    # 打印所有API响应
    print("\n=== XHR/Fetch响应 ===")
    for r in all_responses:
        if any(k in r['url'].lower() for k in ['api', 'subscribe', 'sub', 'user', 'token']):
            print(f"  [{r['status']}] {r['url']}: {r['body'][:300]}")
    
    # 也检查所有请求
    print("\n=== API请求 ===")
    for r in all_requests:
        if any(k in r['url'].lower() for k in ['api', 'subscribe', 'sub']) or r['resource_type'] in ['xhr', 'fetch']:
            print(f"  [{r['method']}] {r['url']}")
    
    with open('capture_result.json', 'w', encoding='utf-8') as f:
        json.dump({
            'clipboard': cap,
            'modals': modals,
            'btn_info': btn_info,
            'responses': [r for r in all_responses if any(k in r['url'].lower() for k in ['api', 'subscribe', 'sub', 'user', 'token'])],
            'requests': [r for r in all_requests if r['resource_type'] in ['xhr', 'fetch'] or any(k in r['url'].lower() for k in ['api', 'subscribe'])]
        }, f, ensure_ascii=False, indent=2)
    
    print("\n结果已保存到 capture_result.json")
    browser.close()
