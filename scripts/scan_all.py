"""提取所有机场订阅链接 - 扫描页面状态"""
from playwright.sync_api import sync_playwright
import time, json, re

AIRPORTS = [
    {
        "name": "疾风云",
        "login_url": "https://jfcec.cc/auth/login",
        "email": "jfcloud_test_2026@outlook.com",
        "pwd": "VpnTest2026",
        "user_url": "https://jfcec.cc/user",
    },
    {
        "name": "尔湾云",
        "login_url": "https://erwance34.cc/auth/login",
        "email": "erwantest_2026@outlook.com",
        "pwd": "VpnTest2026",
        "user_url": "https://erwance34.cc/user",
    },
]

with sync_playwright() as p:
    browser = p.chromium.launch(channel='msedge', headless=False)
    results = {}
    
    for ap in AIRPORTS:
        print(f"\n{'='*60}")
        print(f"处理: {ap['name']}")
        ctx = browser.new_context()
        page = ctx.new_page()
        
        # 登录
        page.goto(ap['login_url'], wait_until='networkidle')
        time.sleep(2)
        
        try:
            page.click('text=点击访问网站', timeout=5000)
            page.wait_for_url('**/auth/login**', timeout=10000)
        except:
            pass
        
        page.fill('[placeholder*="邮箱"], input[name="email"]', ap['email'])
        page.fill('[placeholder*="密码"], input[name="password"], input[type="password"]', ap['pwd'])
        page.click('button:has-text("登录"), button[type="submit"]')
        page.wait_for_url('**/user**', timeout=15000)
        print("  登录成功!")
        time.sleep(3)
        
        # 扫描所有可能包含订阅URL的地方
        found = []
        
        # 1. 扫描页面所有属性
        data = page.evaluate("""() => {
            var results = [];
            
            // 扫描所有元素的data属性
            document.querySelectorAll('[data-url],[data-subscribe],[data-link],[data-clipboard]').forEach(function(el){
                var attrs = {};
                for(var i=0;i<el.attributes.length;i++){
                    var a = el.attributes[i];
                    if(a.name.indexOf('url')>=0 || a.name.indexOf('sub')>=0 || a.name.indexOf('clip')>=0 || a.name.indexOf('link')>=0){
                        attrs[a.name] = a.value;
                    }
                }
                results.push({type:'data-attr', text: el.textContent.trim().substring(0,50), attrs: attrs});
            });
            
            // 扫描localStorage
            var ks={};
            for(var i=0;i<localStorage.length;i++){
                var k=localStorage.key(i);
                try { ks[k]=localStorage.getItem(k).substring(0,200); } catch(e){ ks[k]='error'; }
            }
            if(Object.keys(ks).length>0) results.push({type:'localStorage', data: ks});
            
            // 扫描window全局变量
            var globals = {};
            ['__NUXT__','__NEXT_DATA__','user_info','subscribe_url','token','userToken','auth'].forEach(function(k){
                if(window[k] !== undefined){
                    try { globals[k] = JSON.stringify(window[k]).substring(0,500); } catch(e){ globals[k] = 'error'; }
                }
            });
            if(Object.keys(globals).length>0) results.push({type:'globals', data: globals});
            
            // 扫描所有script标签
            document.querySelectorAll('script').forEach(function(s){
                var t = s.textContent || s.src;
                if(t.indexOf('subscribe')>=0 || t.indexOf('sub_link')>=0 || t.indexOf('token=')>=0){
                    results.push({type:'script', content: t.substring(0,500)});
                }
            });
            
            return results;
        }""")
        
        print(f"  扫描结果: {json.dumps(data, ensure_ascii=False, indent=2)[:2000]}")
        
        # 2. 尝试不同API
        for api in ['/api/v1/user/getSubscribe', '/api/user/getSubscribe', '/api/v1/user/subscribe', '/api/user/sub', '/user/getSubscribe']:
            try:
                resp = page.evaluate(f"""
                    fetch('{api}').then(function(r){{ 
                        return r.json().then(function(d){{ return JSON.stringify(d) }}).catch(function(){{ return 'not_json' }})
                    }}).catch(function(){{ return 'failed' }})
                """)
                if resp and resp != 'failed' and resp != 'not_json':
                    print(f"  API {api}: {resp[:300]}")
                    found.append(f"API:{api}={resp}")
            except Exception as e:
                pass
        
        # 3. 尝试导航到subscribe页面
        for subpage in ['/user/subscribe', '/user#subscribe', '/user#sub', '#subscribe']:
            try:
                page.goto(ap['user_url'] + subpage, wait_until='networkidle', timeout=5000)
                time.sleep(1)
                text = page.evaluate("() => document.body.innerText.substring(0,1000)")
                if 'http' in text and ('subscribe' in text.lower() or 'token=' in text):
                    found.append(f"SUBPAGE:{subpage}={text[:500]}")
            except:
                pass
        
        # 回到user页面
        page.goto(ap['user_url'], wait_until='networkidle')
        time.sleep(1)
        
        # 4. 检查是否有隐藏的URL 
        # 查找所有包含sub/token的URL
        urls = page.evaluate("""() => {
            var r = [];
            document.querySelectorAll('a[href]').forEach(function(a){
                var h = a.href || '';
                if(h.indexOf('sub')>=0 || h.indexOf('token=')>=0 || h.indexOf('subscribe')>=0){
                    r.push(h);
                }
            });
            return r;
        }""")
        found.extend(urls)
        
        # 5. 尝试触发订阅按钮并观察DOM变化
        page.evaluate("""() => {
            document.querySelectorAll('.modal').forEach(function(m){
                m.classList.remove('show'); m.style.display='none';
            });
            document.querySelectorAll('.modal-backdrop').forEach(function(b){b.remove()});
            document.body.classList.remove('modal-open');
            
            // 尝试点击V2Ray订阅按钮
            var es = document.querySelectorAll('a.btn,[role=button]');
            for(var i=0;i<es.length;i++){
                if(es[i].textContent.indexOf('V2Ray')>=0){
                    es[i].click();
                    break;
                }
            }
        }""")
        time.sleep(2)
        
        # 检查是否有modal/alert/dialog出现
        modals = page.evaluate("""() => {
            var ms = document.querySelectorAll('.modal.show, [class*=modal].show, dialog[open], [role=dialog]');
            var r = [];
            ms.forEach(function(m){
                r.push({
                    id: m.id,
                    text: m.textContent ? m.textContent.substring(0,500) : '',
                    class: m.className
                });
            });
            return r;
        }""")
        print(f"  Modals: {json.dumps(modals, ensure_ascii=False)[:500]}")
        
        if modals:
            for m in modals:
                if '订阅' in m.get('text', '') or 'subscribe' in m.get('text', '').lower() or 'token=' in m.get('text', ''):
                    found.append(f"MODAL:{m.get('text','')}")
        
        # 6. 终极方法：拦截所有点击事件
        page.evaluate("""() => {
            window.__all_clicks = [];
            document.addEventListener('click', function(e){
                window.__all_clicks.push({
                    tag: e.target.tagName,
                    text: (e.target.textContent||'').substring(0,40),
                    url: window.location.href
                });
            }, true);
        }""")
        
        results[ap['name']] = found
        print(f"  找到: {found}")
        
        ctx.close()
    
    # 输出结果
    print("\n" + "="*60)
    print("最终结果:")
    for name, f in results.items():
        print(f"\n{name}:")
        for item in f:
            print(f"  {item[:200]}")
    
    with open('all_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    browser.close()
