"""大哥云登录+订阅提取——深度逆向分析版"""
import base64, re, time, json, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from playwright.sync_api import sync_playwright

EMAIL = "dageyun_test_2026@outlook.com"
PASSWORDS = ["VpnTest2026!", "VpnTest2026"]  # 两种都试

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=False,
        args=["--ignore-certificate-errors", "--no-sandbox",
              "--proxy-server=http://127.0.0.1:7897"])
    ctx = browser.new_context(viewport={"width":1280,"height":900},
        ignore_https_errors=True)
    page = ctx.new_page()
    
    # ===== STEP 1: 登录 =====
    print("[1] 登录...", flush=True)
    page.goto("https://a03.dgy02.com/#/login", wait_until="networkidle", timeout=20000)
    time.sleep(3)
    
    # 破解SVG验证码
    src = page.evaluate('()=>document.querySelector("img[alt=点击刷新]").src')
    b64 = src.split("base64,")[1]
    svg = base64.b64decode(b64).decode()
    codes = re.findall(r'<text[^>]*>(\d)</text>', svg)
    code = ''.join(codes)
    print(f"  验证码: {code}", flush=True)
    
    logged_in = False
    for pwd in PASSWORDS:
        print(f"  尝试密码: {pwd}", flush=True)
        page.fill('[placeholder="邮箱"]', EMAIL)
        page.fill('[placeholder="密码"]', pwd)
        page.fill('[placeholder="验证码"]', code)
        page.click('button:has-text("登入")')
        time.sleep(3)
        
        if "dashboard" in page.url:
            logged_in = True
            correct_pwd = pwd
            print(f"  ✓ 登录成功! 密码: {pwd}", flush=True)
            break
        else:
            # 刷新验证码重试
            print("  失败，刷新验证码...", flush=True)
            page.click('img[alt="点击刷新"]')
            time.sleep(1)
            src = page.evaluate('()=>document.querySelector("img[alt=点击刷新]").src')
            b64 = src.split("base64,")[1]
            svg = base64.b64decode(b64).decode()
            codes = re.findall(r'<text[^>]*>(\d)</text>', svg)
            code = ''.join(codes)
    
    if not logged_in:
        print("  登录失败! 截图保存", flush=True)
        page.screenshot(path="dgy_login_fail.png")
        browser.close()
        sys.exit(1)
    
    # ===== STEP 2: Dashboard分析 =====
    print("\n[2] Dashboard深度分析...", flush=True)
    
    # 关公告弹窗
    try:
        page.click('button:has-text("Close")', timeout=3000)
        time.sleep(1)
    except:
        pass
    
    # 深度扫描——不只是点按钮
    print("  扫描localStorage...", flush=True)
    ls = page.evaluate("""() => {
        let r = {};
        for (let i = 0; i < localStorage.length; i++) {
            let k = localStorage.key(i);
            let v = localStorage.getItem(k);
            r[k] = v.substring(0, 200);
        }
        return r;
    }""")
    for k, v in ls.items():
        print(f"    LS[{k}]: {v}", flush=True)
    
    # Hook网络请求
    print("\n  拦截网络请求...", flush=True)
    page.evaluate("""() => {
        window.__dgy_requests = [];
        let origFetch = window.fetch;
        window.fetch = function(url, opts) {
            window.__dgy_requests.push('FETCH:' + url);
            return origFetch.apply(this, arguments).then(r => {
                let clone = r.clone();
                clone.text().then(t => {
                    window.__dgy_requests.push('FETCH_RESP:' + url + '=' + t.substring(0, 300));
                }).catch(()=>{});
                return r;
            });
        };
        let origXHR = XMLHttpRequest.prototype.open;
        XMLHttpRequest.prototype.open = function(m, url) {
            window.__dgy_requests.push('XHR:' + m + ' ' + url);
            this.addEventListener('load', function() {
                window.__dgy_requests.push('XHR_RESP:' + this.responseURL + '=' + (this.responseText||'').substring(0, 300));
            });
            return origXHR.apply(this, arguments);
        };
    }""")
    
    # ===== STEP 3: 一键订阅 → 深度提取 =====
    print("\n[3] 点击一键订阅...", flush=True)
    page.click('text=一键订阅', timeout=5000)
    time.sleep(2)
    
    print("  点击复制订阅地址...", flush=True)
    page.click('text=复制订阅地址', timeout=5000)
    time.sleep(2)
    
    # 读取拦截到的请求
    requests = page.evaluate("() => window.__dgy_requests || []")
    print("  拦截请求:", flush=True)
    for req in requests:
        print(f"    {req[:200]}", flush=True)
    
    # 读取页面所有含URL的元素
    urls_in_page = page.evaluate("""() => {
        let r = [];
        // 所有元素的data-clipboard-text
        document.querySelectorAll('[data-clipboard-text]').forEach(e => r.push('data-clipboard:'+e.getAttribute('data-clipboard-text')));
        // a标签href
        document.querySelectorAll('a[href*="http"]').forEach(e => r.push('link:'+e.href));
        // 文本中的URL
        let text = document.body.innerText;
        let ms = text.match(/https?:\\/\\/[^\\s]+/g);
        if (ms) ms.forEach(m => r.push('text:' + m));
        return [...new Set(r)];
    }""")
    print("  页面URLs:", flush=True)
    for u in urls_in_page:
        print(f"    {u}", flush=True)
    
    # ===== STEP 4: 验证订阅链接 =====
    # 用浏览器fetch验证
    sub_validations = page.evaluate("""async () => {
        let results = [];
        // 找到所有订阅候选URL
        let candidates = [];
        document.querySelectorAll('[data-clipboard-text]').forEach(e => {
            let u = e.getAttribute('data-clipboard-text');
            if (u) candidates.push(u);
        });
        
        for (let url of candidates) {
            try {
                let r = await fetch(url, {method:'HEAD'});
                results.push({url: url, status: r.status});
            } catch(e) {
                results.push({url: url, error: e.message});
            }
        }
        return results;
    }""")
    print("\n  订阅可用性:", flush=True)
    for v in sub_validations:
        print(f"    {v}", flush=True)
    
    page.screenshot(path=os.path.join(os.path.dirname(__file__), "dgy_final.png"))
    print("\n  截图保存!", flush=True)
    
    time.sleep(3)
    browser.close()
