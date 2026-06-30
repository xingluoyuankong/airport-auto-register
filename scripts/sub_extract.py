"""极简订阅提取 - 连接现有浏览器注入JS"""
import json, sys
from playwright.sync_api import sync_playwright

js_hook = """
(function(){
    var ms = document.querySelectorAll('.modal');
    for(var i=0;i<ms.length;i++){ms[i].classList.remove('show');ms[i].style.display='none'}
    var bk = document.querySelectorAll('.modal-backdrop');
    for(var i=0;i<bk.length;i++){bk[i].remove()}
    document.body.classList.remove('modal-open');
    document.body.style.overflow = '';
    window.__cap = null;
    var ow = navigator.clipboard.writeText;
    navigator.clipboard.writeText = function(t){window.__cap = t; return ow.call(navigator.clipboard, t)};
    document.addEventListener('copy', function(e){if(e.clipboardData)window.__cap=e.clipboardData.getData('text')});
    return 'hooked';
})()
"""

js_click_clash = """
(function(){
    var btns = document.querySelectorAll('button');
    for(var i=0;i<btns.length;i++){
        var t = btns[i].textContent;
        if(t.indexOf('Clash')>=0 && t.indexOf('订阅')>=0){
            btns[i].click();
            return 'clicked clash sub btn';
        }
    }
    return 'no clash btn found';
})()
"""

js_click_v2ray = """
(function(){
    var btns = document.querySelectorAll('button');
    for(var i=0;i<btns.length;i++){
        var t = btns[i].textContent;
        if(t.indexOf('V2Ray')>=0 || t.indexOf('V2ray')>=0){
            btns[i].click();
            return 'clicked v2ray btn';
        }
    }
    return 'no v2ray btn';
})()
"""

js_click_sub = """
(function(){
    var all = document.querySelectorAll('*');
    for(var i=0;i<all.length;i++){
        var el = all[i];
        if(el.childNodes.length===1 && el.textContent.trim()==='复制订阅地址'){
            el.click();
            return 'clicked';
        }
    }
    return 'not found';
})()
"""

js_get_cap = """window.__cap || null"""

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    page = browser.contexts[0].pages[0]
    
    print("URL:", page.url)
    print("Title:", page.title())
    
    # 1. Hook clipboard
    r = page.evaluate(js_hook)
    print("Hook:", r)
    
    # 2. Close modals
    # already done in hook
    
    # 3. Try clicking V2RayN button first
    r = page.evaluate(js_click_v2ray)
    print("Click V2Ray:", r)
    page.wait_for_timeout(500)
    cap = page.evaluate(js_get_cap)
    if cap:
        print(">>> 订阅链接:", cap)
        browser.close()
        sys.exit(0)
    
    # 4. Try Clash button
    r = page.evaluate(js_click_clash)
    print("Click Clash:", r)
    page.wait_for_timeout(500)
    cap = page.evaluate(js_get_cap)
    if cap:
        print(">>> 订阅链接:", cap)
        browser.close()
        sys.exit(0)
    
    # 5. Try "复制订阅地址"
    r = page.evaluate(js_click_sub)
    print("Click 复制订阅:", r)
    page.wait_for_timeout(500)
    cap = page.evaluate(js_get_cap)
    if cap:
        print(">>> 订阅链接:", cap)
        browser.close()
        sys.exit(0)
    
    # 6. Direct API call
    api_result = page.evaluate("""
    (async function(){
        try {
            var r = await fetch('/api/v1/user/getSubscribe');
            if(r.ok){
                var d = await r.json();
                return JSON.stringify(d);
            }
        }catch(e){}
        try {
            var r = await fetch('/user/getSubscribe');
            if(r.ok){
                var d = await r.json();
                return JSON.stringify(d);
            }
        }catch(e){}
        return 'api_failed';
    })()
    """)
    print("API:", api_result)
    
    # 7. Check all links
    links = page.evaluate("""
    (function(){
        var r = [];
        document.querySelectorAll('a[href]').forEach(function(a){
            if(a.href.indexOf('sub')>=0 || a.href.indexOf('token')>=0)
                r.push(a.href);
        });
        return r;
    })()
    """)
    print("Links:", links)
    
    page.wait_for_timeout(3000)
    cap = page.evaluate(js_get_cap)
    print("Final cap:", cap)
    
    browser.close()
