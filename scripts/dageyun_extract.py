"""大哥云订阅链接暴力提取"""
from playwright.sync_api import sync_playwright
from io import BytesIO
import json, re, time, base64

def solve_svg(svg_b64):
    """解析SVG base64提取验证码数字"""
    import xml.etree.ElementTree as ET
    svg_bytes = base64.b64decode(svg_b64.split(',')[1] if ',' in svg_b64 else svg_b64)
    tree = ET.fromstring(svg_bytes)
    ns = {'svg': 'http://www.w3.org/2000/svg'}
    texts = []
    for text_el in tree.findall('.//svg:text', ns):
        texts.append(text_el.text)
    code = ''.join(texts)
    print(f"  SVG验证码: {code}")
    return code

with sync_playwright() as p:
    browser = p.chromium.launch(channel='msedge', headless=False)
    page = browser.new_page()
    
    # === Step 1: 登录 ===
    print("1. 登录大哥云...")
    page.goto('https://a03.dgy02.com/#/login', wait_until='networkidle')
    time.sleep(3)
    
    # 获取验证码
    svg_src = page.evaluate('() => document.querySelector("img").getAttribute("src")')
    code = solve_svg(svg_src)
    
    page.fill('[placeholder*="邮箱"]', 'dageyun_test_2026@outlook.com')
    page.fill('[placeholder*="密码"]', 'VpnTest2026')
    page.fill('[placeholder*="验证码"]', code)
    page.click('button:has-text("登入")')
    page.wait_for_url('**/dashboard**', timeout=15000)
    print("  登录成功!")
    time.sleep(2)
    
    # === Step 2: 关闭公告弹窗 ===
    try:
        page.click('button:has-text("Close")', timeout=3000)
    except:
        pass
    time.sleep(1)
    
    # === Step 3: 打开一键订阅弹窗 ===
    print("2. 打开一键订阅...")
    page.click('text=一键订阅', timeout=5000)
    time.sleep(1)
    
    # === Step 4: 深度扫描 ===
    print("3. 扫描订阅相关信息...")
    
    # 4a. 扫描所有Element
    scan = page.evaluate("""() => {
        var results = [];
        
        // 找所有元素里含sub/link/token的
        document.querySelectorAll('[class]').forEach(function(el) {
            var cls = el.className;
            if(typeof cls === 'string' && (cls.indexOf('sub') >= 0 || cls.indexOf('link') >= 0 || cls.indexOf('token') >= 0)) {
                results.push('CLASS:' + cls + ' | TAG:' + el.tagName + ' | TEXT:' + el.textContent.substring(0,80));
            }
        });
        
        // 找隐藏元素
        document.querySelectorAll('input[type=hidden],textarea[style*=display:none],div[style*=display:none]').forEach(function(el){
            var val = el.value || el.textContent || '';
            if(val.indexOf('http') >= 0 || val.indexOf('token') >= 0 || val.indexOf('sub') >= 0) {
                results.push('HIDDEN:' + el.outerHTML.substring(0,300));
            }
        });
        
        // 找script标签内URL
        document.querySelectorAll('script').forEach(function(s){
            var t = s.textContent;
            if(t.indexOf('subscribe') >= 0 || t.indexOf('sub_url') >= 0 || t.indexOf('sublink') >= 0){
                var ms = t.match(/https?:\\/\\/[^"'\s]+(?:sub|token|subscribe)[^"'\s]*/gi);
                if(ms) results.push('SCRIPT_URL:' + ms.join('|'));
            }
        });
        
        return results;
    }""")
    
    for line in scan:
        print(f"  {line}")
    
    # 4b. 尝试读取React fiber state
    print("4. 尝试读取React state...")
    fiber = page.evaluate("""() => {
        var root = document.getElementById('root');
        if(!root) return 'no root';
        var keys = Object.keys(root);
        for(var i=0;i<keys.length;i++){
            var k = keys[i];
            if(k.startsWith('__react')){
                try {
                    var fiber = root[k];
                    // 递归找subscribe
                    var found = [];
                    function walk(node, depth) {
                        if(!node || depth > 30) return;
                        if(node.memoizedState && typeof node.memoizedState === 'object'){
                            try { found.push('STATE:' + JSON.stringify(node.memoizedState).substring(0,300)); } catch(e){}
                        }
                        if(node.memoizedProps && typeof node.memoizedProps === 'object'){
                            var s = JSON.stringify(node.memoizedProps);
                            if(s.indexOf('subscribe')>=0||s.indexOf('sub_url')>=0){
                                found.push('PROPS:' + s.substring(0,500));
                            }
                        }
                        if(node.child) walk(node.child, depth+1);
                        if(node.sibling) walk(node.sibling, depth);
                    }
                    walk(fiber, 0);
                    return found.length ? found : 'walked but no sub found';
                } catch(e) { return 'error:'+e.message; }
            }
        }
        return 'no react key';
    }""")
    
    print(f"  React fiber: {fiber}")
    
    # 4c. Hook点击事件然后点击
    print("5. 安装拦截器并点击复制...")
    
    page.evaluate("""() => {
        window.__captured_data = [];
        window.__captured_url = null;
        
        // Hook clipboard
        navigator.clipboard.writeText = function(t) {
            window.__captured_url = t;
            window.__captured_data.push('CLIPBOARD:' + t);
            return navigator.clipboard.writeText.__proto__.call(navigator.clipboard, t);
        };
        
        // Hook document.execCommand
        var _exec = document.execCommand;
        document.execCommand = function(cmd) {
            window.__captured_data.push('execCommand:' + cmd);
            if(cmd === 'copy') {
                var sel = window.getSelection();
                if(sel) window.__captured_data.push('SELECTION:' + sel.toString());
            }
            return _exec.apply(document, arguments);
        };
        
        // Hook fetch
        var _fetch = window.fetch;
        window.fetch = function(url, opts) {
            if(typeof url === 'string') {
                window.__captured_data.push('FETCH:' + url);
                return _fetch.apply(window, arguments).then(function(r) {
                    var clone = r.clone();
                    clone.text().then(function(t) {
                        window.__captured_data.push('FETCH-RESP:' + url + '=' + t.substring(0,500));
                    }).catch(function(){});
                    return r;
                });
            }
            return _fetch.apply(window, arguments);
        };
        
        // Hook XHR
        var _open = XMLHttpRequest.prototype.open;
        XMLHttpRequest.prototype.open = function(method, url) {
            this.__url = url;
            window.__captured_data.push('XHR:' + method + ' ' + url);
            var xhr = this;
            xhr.addEventListener('load', function() {
                window.__captured_data.push('XHR-RESP:' + xhr.__url + '=' + xhr.responseText.substring(0,500));
            });
            return _open.apply(this, arguments);
        };
        
        // 观察DOM突变
        new MutationObserver(function(mutations) {
            mutations.forEach(function(m) {
                m.addedNodes.forEach(function(n) {
                    if(n.nodeType === 1) {
                        var html = n.outerHTML || n.textContent || '';
                        if(html.indexOf('http') >= 0 && (html.indexOf('sub') >= 0 || html.indexOf('token') >= 0)) {
                            window.__captured_data.push('DOM+:' + html.substring(0,300));
                        }
                        // 检查data属性
                        if(n.getAttribute) {
                            var da = n.getAttribute('data-clipboard-text');
                            if(da) window.__captured_data.push('DOM+clipboard:' + da.substring(0,200));
                        }
                    }
                });
            });
        }).observe(document.body, {childList: true, subtree: true, attributes: true, attributeFilter: ['data-clipboard-text']});
    }""")
    
    # 点击复制订阅地址
    page.evaluate("""
        var el = document.querySelector('.subsrcibe-for-link');
        if(el) el.click();
        else {
            var all = document.querySelectorAll('*');
            for(var i=0;i<all.length;i++){
                if(all[i].textContent.trim() === '复制订阅地址' && all[i].children.length === 0){
                    all[i].click();
                    break;
                }
            }
        }
    """)
    
    time.sleep(3)
    
    # 收集结果
    captured = page.evaluate("() => window.__captured_data || []")
    cap_url = page.evaluate("() => window.__captured_url")
    
    print(f"\n  捕获的URL: {cap_url}")
    print(f"\n  所有拦截数据:")
    for item in captured:
        print(f"    {item}")
    
    # 再检查一遍DOM中有没有新出现的URL
    after = page.evaluate("() => {
        var r = [];
        document.querySelectorAll('*').forEach(function(el){
            var attrs = ['data-clipboard-text', 'data-url', 'value', 'href'];
            attrs.forEach(function(a){
                var v = el.getAttribute ? el.getAttribute(a) : null;
                if(v && v.indexOf('http') >= 0 && (v.indexOf('token') >= 0 || v.indexOf('sub') >= 0)) {
                    r.push(a + ':' + v);
                }
            });
        });
        return r;
    }")
    print(f"\n  DOM中的URLs: {after}")
    
    # 检查React state（点击后）
    time.sleep(2)
    
    result = {
        'url': cap_url,
        'captured': captured,
        'dom_urls': after,
    }
    
    with open('dageryun_result.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print("\n结果已保存。浏览器保持打开，检查...")
    time.sleep(60)
    browser.close()
