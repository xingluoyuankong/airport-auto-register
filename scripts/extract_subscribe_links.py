"""
订阅链接提取脚本 — 大哥云 / 疾风云 / 尔湾云
用Python playwright直接操作浏览器，突破playwright-cli eval的分号限制
"""
import asyncio, json, re, time
from playwright.async_api import async_playwright

USER_DATA = r"E:\API获取工具\.playwright-cli\browser-profile"

AIRPORTS = {
    "疾风云": {
        "url": "https://jfcec.cc/auth/login",
        "email": "jfcloud_test_2026@outlook.com",
        "pwd": "VpnTest2026",
        "login_check": "/user",
    },
    "尔湾云": {
        "url": "https://erwance34.cc/auth/login",
        "email": "erwantest_2026@outlook.com",
        "pwd": "VpnTest2026",
        "login_check": "/user",
    },
    "大哥云": {
        "url": "https://a03.dgy02.com/#/login",
        "email": "dageyun_test_2026@outlook.com",
        "pwd": "VpnTest2026",
        "login_check": "/dashboard",
    },
}

async def login_and_extract(browser, name, cfg):
    print(f"\n{'='*50}")
    print(f"开始处理: {name}")
    ctx = await browser.new_context()
    page = await ctx.new_page()
    
    # 拦截网络请求，捕获subscribe URL
    captured_urls = []
    async def capture_request(request):
        url = request.url
        if any(k in url for k in ['subscribe', 'sub_link', 'sub?', '/sub/', 'token=']):
            captured_urls.append(url)
            print(f"  [NET] 捕获请求: {url}")
    page.on('request', capture_request)
    
    # 拦截复制事件
    await page.goto(cfg['url'], wait_until='networkidle')
    
    # 检查是否已登录
    await asyncio.sleep(1)
    
    if name == "大哥云":
        result = await extract_dageyun(page, cfg)
    elif name == "疾风云":
        result = await extract_jifeng(page, cfg)
    elif name == "尔湾云":
        result = await extract_erwan(page, cfg)
    
    # 打印捕获的网络请求
    if captured_urls:
        print(f"  [NET] 捕获到的subscribe请求: {json.dumps(captured_urls, indent=2)}")
    
    await ctx.close()
    return result

async def extract_jifeng(page, cfg):
    """疾风云 - JFCLOUND自定义面板"""
    await asyncio.sleep(2)
    current_url = page.url
    
    # 如果在登录页，先登录
    if '/auth/login' in current_url or 'login' in current_url.lower():
        print("  在登录页，开始登录...")
        try:
            await page.fill('input[placeholder*="邮箱"], [name="email"]', cfg['email'])
            await page.fill('input[placeholder*="密码"], [name="password"], input[type="password"]', cfg['pwd'])
            await page.click('button:has-text("登录"), button[type="submit"]')
            await page.wait_for_url('**/user**', timeout=10000)
            print("  登录成功!")
        except Exception as e:
            print(f"  登录失败: {e}")
            # 可能已登录，直接跳转
            await page.goto("https://jfcec.cc/user", wait_until='networkidle')
    
    await asyncio.sleep(3)
    
    # 关闭modal弹窗
    try:
        await page.evaluate("""() => {
            document.querySelectorAll('.modal').forEach(function(m) {
                m.classList.remove('show');
                m.style.display = 'none';
            });
            document.querySelectorAll('.modal-backdrop').forEach(function(b) {
                b.remove();
            });
            document.body.classList.remove('modal-open');
            document.body.style.overflow = '';
        }""")
    except:
        pass
    
    await asyncio.sleep(1)
    
    # 方法1: 直接调API获取订阅链接
    result = await page.evaluate("""() => {
        // 尝试多种方式获取订阅信息
        var results = {};
        
        // 方式1: 尝试getSubscribe API (V2Board)
        var p1 = fetch('/api/v1/user/getSubscribe')
            .then(function(r) { return r.json(); })
            .then(function(d) { results.api_getSubscribe = d; })
            .catch(function() { results.api_getSubscribe = 'failed'; });
        
        // 方式2: 查localStorage
        var ks = {};
        for (var i = 0; i < localStorage.length; i++) {
            var key = localStorage.key(i);
            try { ks[key] = localStorage.getItem(key).substring(0, 200); }
            catch(e) { ks[key] = 'error'; }
        }
        results.localStorage = ks;
        
        // 方式3: 查页面上的订阅相关data属性
        var dataEls = [];
        document.querySelectorAll('[data-subscribe], [data-url], [data-link]').forEach(function(el) {
            var attrs = {};
            for (var i = 0; i < el.attributes.length; i++) {
                var a = el.attributes[i];
                if (a.name.indexOf('sub') >= 0 || a.name.indexOf('url') >= 0 || a.name.indexOf('link') >= 0) {
                    attrs[a.name] = a.value;
                }
            }
            if (Object.keys(attrs).length > 0) dataEls.push(attrs);
        });
        results.dataEls = dataEls;
        
        return JSON.stringify(results);
    }""")
    
    print(f"  API/localStorage结果: {result[:1000] if result else 'None'}")
    parsed = json.loads(result)
    
    # 检查getSubscribe API结果
    if 'api_getSubscribe' in parsed and isinstance(parsed['api_getSubscribe'], dict):
        sub = parsed['api_getSubscribe']
        if 'subscribe_url' in sub:
            print(f"  >>> 订阅链接: {sub['subscribe_url']}")
            return sub['subscribe_url']
    
    # 方式4: 点击复制按钮并拦截
    await page.evaluate("""() => {
        window.__captured_url = null;
        var origWrite = navigator.clipboard.writeText;
        navigator.clipboard.writeText = function(text) {
            window.__captured_url = text;
            return origWrite.call(navigator.clipboard, text);
        };
        document.addEventListener('copy', function(e) {
            window.__captured_url = e.clipboardData ? e.clipboardData.getData('text') : '';
        });
    }""")
    
    # 找"复制Clash订阅"按钮
    btns = page.locator('button, a, div, span').filter(has_text='Clash')
    count = await btns.count()
    print(f"  找到 {count} 个含Clash的元素")
    
    for i in range(min(count, 5)):
        btn = btns.nth(i)
        try:
            text = await btn.inner_text()
            if 'Clash' in text and ('订阅' in text or '复制' in text):
                print(f"  点击: {text.strip()}")
                await btn.click(force=True, timeout=3000)
                await asyncio.sleep(1)
                captured = await page.evaluate("() => window.__captured_url")
                if captured:
                    print(f"  >>> 捕获到订阅链接: {captured}")
                    return captured
        except:
            pass
    
    # 方式5: 检查所有包含subscribe的链接
    links = await page.evaluate("""() => {
        var urls = [];
        document.querySelectorAll('a[href]').forEach(function(a) {
            var h = a.href;
            if (h.indexOf('sub') >= 0 || h.indexOf('token') >= 0) {
                urls.push(h);
            }
        });
        // 也查所有文本含subscribe的元素
        document.querySelectorAll('*').forEach(function(el) {
            if (el.children.length === 0 || el.childNodes.length === 1) {
                var t = el.textContent || '';
                if (t.indexOf('sub?') >= 0 || t.indexOf('subscribe') >= 0) {
                    urls.push('TEXT:' + t);
                }
            }
        });
        return urls;
    }""")
    print(f"  找到的链接: {links}")
    
    # 方式6: 直接用XHR调用getSubscribe
    try:
        await page.evaluate("""() => {
            var xhr = new XMLHttpRequest();
            xhr.open('GET', '/user/getSubscribe', true);
            xhr.onload = function() {
                try { window.__xhrResult = JSON.parse(xhr.responseText); }
                catch(e) { window.__xhrResult = xhr.responseText; }
            };
            xhr.send();
        }""")
        await asyncio.sleep(2)
        xhr_result = await page.evaluate("() => window.__xhrResult")
        if xhr_result:
            print(f"  XHR结果: {json.dumps(xhr_result) if isinstance(xhr_result, dict) else xhr_result}")
    except:
        pass
    
    return None

async def extract_erwan(page, cfg):
    """尔湾云 - 同JFCLOUND框架"""
    await asyncio.sleep(2)
    current_url = page.url
    
    # 如果在登录页，先登录
    if '/auth/login' in current_url or 'login' in current_url.lower():
        print("  在登录页，开始登录...")
        try:
            await page.fill('input[placeholder*="邮箱"], [name="email"]', cfg['email'])
            await page.fill('input[placeholder*="密码"], [name="password"], input[type="password"]', cfg['pwd'])
            await page.click('button:has-text("登录"), button[type="submit"]')
            await page.wait_for_url('**/user**', timeout=10000)
            print("  登录成功!")
        except Exception as e:
            print(f"  登录失败: {e}")
            await page.goto("https://erwance34.cc/user", wait_until='networkidle')
    
    await asyncio.sleep(3)
    
    # 关闭modal
    try:
        await page.evaluate("""() => {
            document.querySelectorAll('.modal').forEach(function(m) {
                m.classList.remove('show');
                m.style.display = 'none';
            });
            document.querySelectorAll('.modal-backdrop').forEach(function(b) {
                b.remove();
            });
            document.body.classList.remove('modal-open');
            document.body.style.overflow = '';
        }""")
    except:
        pass
    await asyncio.sleep(1)
    
    # 尝试getSubscribe API
    result = await page.evaluate("""() => {
        var results = {};
        
        // 方式1: getSubscribe API
        var p1 = fetch('/api/v1/user/getSubscribe')
            .then(function(r) { return r.json(); })
            .then(function(d) { results.api_getSubscribe = d; })
            .catch(function() { results.api_getSubscribe = 'failed'; });
        
        // 方式2: localStorage
        var ks = {};
        for (var i = 0; i < localStorage.length; i++) {
            var key = localStorage.key(i);
            try { ks[key] = localStorage.getItem(key).substring(0, 200); }
            catch(e) { ks[key] = 'error'; }
        }
        results.localStorage = ks;
        
        return JSON.stringify(results);
    }""")
    
    print(f"  API/localStorage: {result[:1000]}")
    parsed = json.loads(result)
    
    if 'api_getSubscribe' in parsed and isinstance(parsed['api_getSubscribe'], dict):
        sub = parsed['api_getSubscribe']
        if 'subscribe_url' in sub:
            print(f"  >>> 订阅链接: {sub['subscribe_url']}")
            return sub['subscribe_url']
    
    # Hook复制并点击订阅按钮
    await page.evaluate("""() => {
        window.__captured_url = null;
        navigator.clipboard.writeText = function(text) {
            window.__captured_url = text;
            return Promise.resolve();
        };
        document.addEventListener('copy', function(e) {
            window.__captured_url = e.clipboardData ? e.clipboardData.getData('text') : '';
        });
    }""")
    
    # 点击V2RayN订阅按钮（无dropdown,直接复制）
    try:
        await page.click('button:has-text("V2RayN")', force=True, timeout=5000)
        await asyncio.sleep(1)
        captured = await page.evaluate("() => window.__captured_url")
        if captured:
            print(f"  >>> V2RayN订阅链接: {captured}")
            return captured
    except Exception as e:
        print(f"  V2RayN点击失败: {e}")
    
    # 检查页面所有链接
    links = await page.evaluate("""() => {
        var urls = [];
        document.querySelectorAll('a[href]').forEach(function(a) {
            var h = a.href;
            if (h.indexOf('sub') >= 0 || h.indexOf('token') >= 0) {
                urls.push(h);
            }
        });
        return urls;
    }""")
    print(f"  页面链接: {links}")
    
    return None

async def extract_dageyun(page, cfg):
    """大哥云 - 自定义面板 v1.7.4"""
    await asyncio.sleep(2)
    current_url = page.url
    
    # 检查是否需要登录
    if '/dashboard' not in current_url:
        print("  需要登录...")
        try:
            # 先打开登录页
            await page.goto("https://a03.dgy02.com/#/login")
            await asyncio.sleep(2)
            
            # 填表登录
            await page.fill('input[placeholder*="邮箱"]', cfg['email'])
            await page.fill('input[placeholder*="密码"]', cfg['pwd'])
            
            # 读取验证码
            captcha_text = await page.evaluate("""() => {
                var svg = document.querySelector('img[class*="captcha"], img[src*="captcha"]');
                if (!svg) {
                    // 在父元素中找
                    var imgs = document.querySelectorAll('img');
                    for (var i = 0; i < imgs.length; i++) {
                        if (imgs[i].src.indexOf('captcha') >= 0) {
                            svg = imgs[i];
                            break;
                        }
                    }
                }
                if (!svg) return 'no_captcha_img';
                var canvas = document.createElement('canvas');
                canvas.width = svg.width || 200;
                canvas.height = svg.height || 60;
                var ctx = canvas.getContext('2d');
                ctx.drawImage(svg, 0, 0);
                return canvas.toDataURL();
            }""")
            print(f"  验证码图片: {captcha_text[:100] if captcha_text else 'None'}")
            
            # 需要手动处理验证码 - 用playwright-cli配合
        except Exception as e:
            print(f"  登录流程异常: {e}")
    
    await asyncio.sleep(2)
    
    # 如果在dashboard, 找订阅
    if '/dashboard' in page.url:
        print("  已在dashboard...")
        
        # 关闭弹窗
        try:
            await page.click('button:has-text("Close"), .close, [data-dismiss="modal"]', timeout=3000)
        except:
            pass
        await asyncio.sleep(1)
        
        # 点击"一键订阅"
        try:
            await page.getByText('一键订阅').first.click(timeout=3000)
            await asyncio.sleep(1)
        except Exception as e:
            print(f"  一键订阅点击失败: {e}")
        
        # Hook复制
        await page.evaluate("""() => {
            window.__captured_url = null;
            navigator.clipboard.writeText = function(text) {
                window.__captured_url = text;
                return Promise.resolve();
            };
            document.addEventListener('copy', function(e) {
                window.__captured_url = e.clipboardData ? e.clipboardData.getData('text') : '';
            });
        }""")
        
        # 点击"复制订阅地址"
        try:
            subs = await page.locator('[class*="subsrcibe"], [class*="subscribe"]').all()
            print(f"  找到 {len(subs)} 个订阅相关元素")
            for s in subs:
                txt = await s.inner_text()
                print(f"    - {txt.strip()[:50]}")
                if '复制' in txt or 'copy' in txt.lower():
                    await s.click(timeout=3000)
                    await asyncio.sleep(1)
                    captured = await page.evaluate("() => window.__captured_url")
                    if captured:
                        print(f"  >>> 捕获订阅链接: {captured}")
                        return captured
        except Exception as e:
            print(f"  复制订阅失败: {e}")
        
        # 尝试API
        try:
            auth = await page.evaluate("() => localStorage.getItem('authorization')")
            if auth:
                print(f"  找到auth token: {auth[:50]}...")
                # 尝试多种API
                for api_path in ['/api/v1/user/getSubscribe', '/api/subscribe', '/user/subscribe', '/api/user/sub']:
                    try:
                        api_result = await page.evaluate(f"""(async () => {{
                            var r = await fetch('{api_path}', {{headers: {{'Authorization': 'Bearer {auth}'}}}});
                            return await r.text();
                        }})()""")
                        if 'subscribe' in str(api_result).lower() or 'http' in str(api_result):
                            print(f"  API {api_path}: {api_result[:200]}")
                    except:
                        pass
        except Exception as e:
            print(f"  API尝试失败: {e}")
    
    return None

async def main():
    async with async_playwright() as p:
        # 使用持久化上下文
        browser = await p.chromium.launch_persistent_context(
            USER_DATA,
            headless=False,
            channel='msedge',
            args=['--disable-blink-features=AutomationControlled']
        )
        
        results = {}
        for name, cfg in AIRPORTS.items():
            try:
                sub_url = await login_and_extract(browser, name, cfg)
                results[name] = sub_url
                if sub_url:
                    print(f"\n>>>> {name} 订阅链接: {sub_url}")
                else:
                    print(f"\n>>>> {name} 未找到订阅链接")
            except Exception as e:
                print(f"\n>>>> {name} 出错: {e}")
                import traceback
                traceback.print_exc()
        
        print("\n" + "="*50)
        print("最终结果:")
        for name, url in results.items():
            print(f"  {name}: {url or '未获取'}")
        
        # 保持浏览器打开
        input("\n按Enter关闭浏览器...")
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
