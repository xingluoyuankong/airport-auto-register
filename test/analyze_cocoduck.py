#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""COCODUCK深度逆向分析 - 分析页面结构和订阅链接提取"""
import sys, os, json, time, io
try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from playwright.sync_api import sync_playwright

EMAIL = "floraide3rb1508k2xlbbi@hotmail.com"
PASSWORD = "VpnTest2026!"

def analyze():
    print("=" * 60)
    print("  COCODUCK 深度逆向分析")
    print("=" * 60)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=False,
            args=["--ignore-certificate-errors",
                  "--disable-blink-features=AutomationControlled",
                  "--no-sandbox"])
        ctx = browser.new_context(viewport={"width": 1280, "height": 900},
            ignore_https_errors=True, locale="zh-CN")
        page = ctx.new_page()
        page.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>false})")
        
        try:
            # ===== PHASE 1: 登录页分析 =====
            print("\n[PHASE 1] 登录页分析")
            page.goto("https://dash.cocoduck.co/auth/login", wait_until="domcontentloaded", timeout=20000)
            time.sleep(2)
            page.screenshot(path=os.path.join(os.path.dirname(__file__), "cocoduck_login.png"))
            
            # 填邮箱密码
            page.locator('#email, input[name="email"]').first.fill(EMAIL)
            page.locator('#passwd, input[name="passwd"]').first.fill(PASSWORD)
            time.sleep(0.5)
            
            # 登录
            page.get_by_role('button', name='登录').click()
            page.wait_for_load_state("networkidle", timeout=15000)
            time.sleep(2)
            print(f"  登录后URL: {page.url}")
            
            # 关弹窗
            try:
                page.get_by_role('button', name='我知道了').click(timeout=5000)
                print("  公告弹窗已关闭")
            except:
                pass
            
            page.screenshot(path=os.path.join(os.path.dirname(__file__), "cocoduck_dashboard.png"))
            
            # ===== PHASE 2: 页面结构分析 =====
            print("\n[PHASE 2] 页面结构分析")
            
            # 分析所有button
            btns = page.evaluate("""() => {
                let btns = document.querySelectorAll('button');
                let result = [];
                for (let b of btns) {
                    let t = (b.textContent || '').trim().replace(/\\s+/g, ' ');
                    let cls = (b.className || '');
                    let dc = b.getAttribute('data-clipboard-text') || '';
                    let onclick = b.getAttribute('onclick') || '';
                    let id = b.id || '';
                    if (t.length > 0 && t.length < 100) {
                        result.push({text: t.substring(0,60), class: cls.substring(0,40), 
                                     clipboard: dc, onclick: onclick.substring(0,100), id: id});
                    }
                }
                return result;
            }""")
            
            print(f"\n  共找到 {len(btns)} 个有效按钮:")
            for b in btns:
                print(f"    [{b['text'][:40]}] clipboard={b['clipboard'][:80]} onclick={b['onclick'][:80]}")
            
            # 分析订阅区域
            print("\n[PHASE 3] 订阅区域深度分析")
            
            # 找所有input/textarea元素
            inputs = page.evaluate("""() => {
                let els = document.querySelectorAll('input, textarea, .copy-area, [class*=sub], [id*=sub]');
                let result = [];
                for (let e of els) {
                    let val = e.value || e.textContent || '';
                    let cls = e.className || '';
                    let id = e.id || '';
                    let name = e.name || e.getAttribute('aria-label') || '';
                    if (val.includes('://') || val.includes('sub') || cls.includes('sub') || id.includes('sub')) {
                        result.push({value: val.substring(0,200), class: cls, id: id, name: name});
                    }
                }
                return result;
            }""")
            
            print(f"  订阅相关元素:")
            for i in inputs:
                print(f"    value={i['value'][:120]}")
                print(f"    class={i['class']} id={i['id']}")
            
            # 找所有a标签含sub或subscribe
            links = page.evaluate("""() => {
                let links = document.querySelectorAll('a');
                let result = [];
                for (let a of links) {
                    let h = a.href || '';
                    if (h.includes('sub') || h.includes('link') || h.includes('token')) {
                        result.push({href: h, text: (a.textContent||'').trim().substring(0,60)});
                    }
                }
                return result;
            }""")
            
            print(f"\n  订阅相关链接:")
            for l in links:
                print(f"    {l['href']} | {l['text']}")
            
            # ===== PHASE 4: 点击Clash订阅按钮提取真实链接 =====
            print("\n[PHASE 4] 点击Clash订阅按钮获取真实链接")
            
            # 方法1: 直接点击Clash订阅按钮
            try:
                clash_btn = page.get_by_role('button', name='Clash订阅链接')
                if clash_btn.count() > 0:
                    print("  找到Clash订阅按钮，点击...")
                    clash_btn.first.click()
                    time.sleep(1)
                    
                    # 读clipboard
                    clipboard_text = page.evaluate("() => navigator.clipboard.readText().catch(e => 'clipboard error: ' + e)")
                    print(f"  Clipboard: {clipboard_text}")
            except Exception as e:
                print(f"  点击Clash按钮出错: {e}")
            
            # 方法2: 检查所有data-属性
            data_attrs = page.evaluate("""() => {
                let result = [];
                let all = document.querySelectorAll('*');
                for (let e of all) {
                    let attrs = e.attributes;
                    for (let a of attrs) {
                        if (a.name.startsWith('data-') && (a.value.includes('://') || a.value.includes('sub'))) {
                            result.push({tag: e.tagName, attr: a.name, value: a.value.substring(0,200),
                                        text: (e.textContent||'').trim().substring(0,60)});
                        }
                    }
                }
                return result;
            }""")
            
            print(f"\n  data-属性含订阅信息:")
            for d in data_attrs:
                print(f"    <{d['tag']}> {d['attr']}={d['value']}")
            
            # 方法3: 检查localStorage
            ls_data = page.evaluate("""() => {
                let result = {};
                for (let i = 0; i < localStorage.length; i++) {
                    let k = localStorage.key(i);
                    let v = localStorage.getItem(k);
                    if (v && v.length > 0) {
                        if (v.length > 300) v = v.substring(0, 300) + '...(truncated)';
                        result[k] = v;
                    }
                }
                return result;
            }""")
            
            print(f"\n  localStorage:")
            for k, v in ls_data.items():
                print(f"    {k}: {v[:200]}")
            
            # 方法4: 检查网络请求
            # 重新加载页面并监控XHR/fetch请求
            print("\n[PHASE 5] 网络请求分析")
            page.goto("https://dash.cocoduck.co/user", wait_until="networkidle", timeout=15000)
            time.sleep(2)
            
            # 点击ShadowRocket按钮看有什么
            try:
                sr_btn = page.get_by_role('button', name='ShadowRocket')
                if sr_btn.count() > 0:
                    print("  找到ShadowRocket按钮，点击...")
                    # 监控clipboard
                    sr_btn.first.click()
                    time.sleep(1)
            except Exception as e:
                print(f"  点击SR按钮出错: {e}")
            
            # 方法5: 查找所有可能含订阅URL的文本节点
            sub_text = page.evaluate("""() => {
                let body = document.body.innerText;
                let lines = body.split('\\n');
                let result = [];
                for (let l of lines) {
                    if (l.includes('://') || l.includes('token=') || l.includes('/sub') || l.includes('/link/')) {
                        result.push(l.trim());
                    }
                }
                return result;
            }""")
            
            print(f"\n  文本中含URL/订阅的行:")
            for t in sub_text:
                print(f"    {t}")
            
            # 方法6: 查看页面源码中隐藏的订阅链接
            print("\n[PHASE 6] 查看HTML源码中隐藏数据")
            html_snippets = page.evaluate("""() => {
                let html = document.body.innerHTML;
                let result = [];
                let idx = -1;
                while ((idx = html.indexOf('subscribe', idx+1)) >= 0) {
                    let start = Math.max(0, idx - 200);
                    let end = Math.min(html.length, idx + 300);
                    result.push(html.substring(start, end).replace(/\\n/g, ' '));
                    if (result.length > 5) break;
                }
                return result;
            }""")
            
            for s in html_snippets:
                print(f"    {s[:300]}")
            
            # 方法7: 直接查找包含订阅链接的DOM节点
            print("\n[PHASE 7] 深度DOM搜索订阅链接")
            sub_els = page.evaluate("""() => {
                let result = [];
                // 找class或id含sub的元素
                let els = document.querySelectorAll('[class*="sub"], [id*="sub"], [class*="link"], [class*="url"], [class*="copy"]');
                for (let e of els) {
                    let html = e.outerHTML;
                    if (html.includes('://') || html.includes('token=')) {
                        result.push({tag: e.tagName, class: e.className, id: e.id, 
                                    html: html.substring(0, 300).replace(/\\n/g, ' ')});
                    }
                }
                if (result.length === 0) {
                    // 扩大搜索：找所有含https://的innerHTML
                    let all = document.querySelectorAll('div, span, input, textarea, pre, code');
                    for (let e of all) {
                        let h = e.innerHTML || '';
                        if (h.includes('https://') && (h.includes('sub') || h.includes('token'))) {
                            result.push({tag: e.tagName, class: e.className.substring(0,60), 
                                        html: h.substring(0, 400)});
                            if (result.length > 5) break;
                        }
                    }
                }
                return result;
            }""")
            
            for e in sub_els:
                print(f"    <{e['tag']} class={e['class'][:60]}>")
                print(f"    HTML: {e['html'][:300]}")
            
            page.screenshot(path=os.path.join(os.path.dirname(__file__), "cocoduck_final.png"))
            
        except Exception as e:
            print(f"  异常: {e}", flush=True)
            import traceback
            traceback.print_exc()
        finally:
            time.sleep(3)
            browser.close()

if __name__ == "__main__":
    analyze()
