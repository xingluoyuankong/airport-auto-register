"""疾风云订阅提取 - 拦截网络请求"""
from playwright.sync_api import sync_playwright
import json, time

with sync_playwright() as p:
    # 连接到已存在的Edge浏览器
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    ctx = browser.contexts[0]
    page = ctx.pages[0]
    
    print("URL:", page.url)
    
    # 拦截所有fetch/XHR
    captured = []
    def on_request(request):
        url = request.url
        if any(k in url for k in ['subscribe', 'sub_link', 'sub?', '/sub/', 'token=']):
            captured.append(url)
            print(f"[REQ] {url}")
    
    def on_response(response):
        url = response.url
        if any(k in url for k in ['subscribe', 'sub_link', 'sub?', '/sub/', 'token=']):
            try:
                body = response.text()
                if body and len(body) < 5000:
                    print(f"[RESP] {url}: {body[:500]}")
                    captured.append(f"RESP:{url}={body}")
            except:
                pass
    
    page.on('request', on_request)
    page.on('response', on_response)
    
    # Hook clipboard
    page.evaluate("""
        window.__cap = null;
        navigator.clipboard.writeText = function(t) {
            window.__cap = t;
            return navigator.clipboard.writeText.__proto__.call(navigator.clipboard, t);
        };
    """)
    
    # 关闭modal
    try:
        page.evaluate("""
            document.querySelectorAll('.modal').forEach(function(m){
                m.classList.remove('show');
                m.style.display='none';
            });
            document.querySelectorAll('.modal-backdrop').forEach(function(b){b.remove()});
            document.body.classList.remove('modal-open');
        """)
    except: pass
    page.wait_for_timeout(500)
    
    # 点击V2Ray订阅
    try:
        # 找到元素
        el = page.evaluate("""() => {
            var es = document.querySelectorAll('a.btn,[role=button]');
            for(var i=0;i<es.length;i++){
                if(es[i].textContent.indexOf('V2Ray')>=0) {
                    // 获取onclick代码
                    return {
                        onclick: es[i].onclick ? es[i].onclick.toString() : 'no onclick',
                        outerHTML: es[i].outerHTML.substring(0,300),
                        attributes: Array.from(es[i].attributes).map(function(a){return a.name+'='+a.value})
                    };
                }
            }
            return null;
        }""")
        print("V2Ray元素:", json.dumps(el, ensure_ascii=False, indent=2))
        
        # 尝试直接点击
        page.evaluate("""() => {
            var es = document.querySelectorAll('a.btn,[role=button]');
            for(var i=0;i<es.length;i++){
                if(es[i].textContent.indexOf('V2Ray')>=0){
                    es[i].click();
                    return;
                }
            }
        }""")
        page.wait_for_timeout(2000)
        
        # 检查结果
        cap = page.evaluate("() => window.__cap")
        print("Clipboard:", cap)
        
    except Exception as e:
        print(f"Error: {e}")
    
    # 输出所有捕获的请求
    print("\n所有捕获的请求:", captured)
    
    # 也检查网络日志
    time.sleep(2)
    
    browser.close()
