"""快速提取大哥云订阅 - 利用已登录的浏览器"""
import sys, os, time, json, io, re, base64, xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from playwright.sync_api import sync_playwright

EMAIL = "dageyun_test_2026@outlook.com"
PASSWORD = "VpnTest2026"
URL = "https://a03.dgy02.com"

def solve_svg(svg_b64):
    """解析SVG base64获取验证码"""
    svg_bytes = base64.b64decode(svg_b64.split(',')[1] if ',' in svg_b64 else svg_b64)
    tree = ET.fromstring(svg_bytes)
    ns = {'svg': 'http://www.w3.org/2000/svg'}
    texts = [t.text for t in tree.findall('.//svg:text', ns)]
    return ''.join(texts)

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=False,
        args=["--ignore-certificate-errors", "--no-sandbox"])
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    
    print("登录大哥云...", flush=True)
    page.goto(f"{URL}/#/login", wait_until="networkidle", timeout=20000)
    time.sleep(3)
    
    # SVGA解析验证码
    svg_src = page.evaluate('()=>document.querySelector("img[alt=点击刷新]").src')
    code = solve_svg(svg_src)
    print(f"验证码: {code}", flush=True)
    
    page.fill('[placeholder="邮箱"]', EMAIL)
    page.fill('[placeholder="密码"]', PASSWORD)
    page.fill('[placeholder="验证码"]', code)
    page.click('button:has-text("登入")')
    
    time.sleep(3)
    page.wait_for_load_state("networkidle", timeout=15000)
    
    if "dashboard" not in page.url:
        print(f"登录失败! URL={page.url}", flush=True)
        page.screenshot(path="dageyun_login_fail.png")
        browser.close()
        sys.exit(1)
    
    print("登录成功!", flush=True)
    
    # 关弹窗
    try:
        page.click('button:has-text("Close")', timeout=3000)
        time.sleep(1)
    except:
        pass
    
    # 点一键订阅
    print("打开一键订阅...", flush=True)
    page.click('text=一键订阅', timeout=5000)
    time.sleep(2)
    
    # 深度扫描页面
    print("扫描订阅信息...", flush=True)
    
    # 方法1: 找data-clipboard-text
    clipboard = page.evaluate("""() => {
        let els = document.querySelectorAll('[data-clipboard-text]');
        let r = [];
        els.forEach(e => r.push(e.getAttribute('data-clipboard-text')));
        return r;
    }""")
    print(f"data-clipboard: {clipboard}", flush=True)
    
    # 方法2: React state
    react = page.evaluate("""() => {
        let root = document.getElementById('root');
        if (!root) return 'no root';
        for (let key of Object.keys(root)) {
            if (key.startsWith('__react')) {
                let fiber = root[key];
                let found = [];
                function walk(node, depth) {
                    if (!node || depth > 30) return;
                    try {
                        let s = JSON.stringify(node.memoizedState || {});
                        if (s.length > 10 && (s.includes('sub') || s.includes('token'))) {
                            found.push('STATE:' + s.substring(0, 500));
                        }
                        s = JSON.stringify(node.memoizedProps || {});
                        if (s.length > 10 && (s.includes('sub') || s.includes('token') || s.includes('subscribe'))) {
                            found.push('PROPS:' + s.substring(0, 500));
                        }
                    } catch(e) {}
                    if (node.child) walk(node.child, depth+1);
                    if (node.sibling) walk(node.sibling, depth);
                }
                walk(fiber, 0);
                return found.length ? found : 'walked_no_sub';
            }
        }
        return 'no_react';
    }""")
    
    for item in react if isinstance(react, list) else [str(react)]:
        print(f"  React: {item[:300]}", flush=True)
    
    # 方法3: 页面文本中的URL
    text = page.evaluate("() => document.body.innerText")
    urls = re.findall(r'https?://[^\s]+', text)
    print(f"页面URLs: {urls}", flush=True)
    
    # 方法4: 所有script内容
    scripts = page.evaluate("""() => {
        let ss = document.querySelectorAll('script');
        let r = [];
        ss.forEach(s => {
            let t = s.textContent || '';
            if (t.includes('subscribe') || t.includes('sub_url')) {
                r.push(t.substring(0, 500));
            }
        });
        return r;
    }""")
    print(f"Script中订阅: {scripts}", flush=True)
    
    # 保存截图
    page.screenshot(path="dageyun_subscription.png")
    print("截图保存", flush=True)
    
    # 最后尝试: hook复制按钮
    page.evaluate("""() => {
        let old = document.execCommand;
        document.execCommand = function(cmd) {
            if (cmd === 'copy') {
                let sel = window.getSelection().toString();
                window.__dgy_selection = sel;
            }
            return old.apply(document, arguments);
        };
    }""")
    
    page.click('text=复制订阅地址', timeout=5000)
    time.sleep(2)
    
    sel = page.evaluate("() => window.__dgy_selection || ''")
    print(f"复制内容: {sel}", flush=True)
    
    time.sleep(5)
    browser.close()
