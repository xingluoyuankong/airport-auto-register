#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多机场批量订阅提取 — 大哥云 + SSLAR + FSCloud
"""
import sys, os, json, time, io, re
try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
from playwright.sync_api import sync_playwright

def extract_dageyun():
    """大哥云订阅提取"""
    print("\n" + "="*60)
    print("  大哥云 订阅提取")
    print("="*60)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=False,
            args=["--ignore-certificate-errors", "--no-sandbox"])
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        
        try:
            # 登录
            print("[1/4] 登录...", flush=True)
            page.goto("https://a03.dgy02.com/#/login", wait_until="networkidle", timeout=20000)
            time.sleep(3)
            
            # SVG验证码
            svg_src = page.evaluate("""() => {
                let imgs = document.querySelectorAll('img');
                for (let img of imgs) {
                    let src = img.getAttribute('src') || '';
                    if (src.includes('svg') || src.includes('captcha') || src.startsWith('data:')) {
                        return src;
                    }
                }
                return '';
            }""")
            
            print(f"  SVG验证码: " + ("有" if svg_src else "无"), flush=True)
            
            # 填表
            page.locator('[placeholder*="邮箱"], input[name="email"]').first.fill("dageyun_test_2026@outlook.com")
            page.locator('[placeholder*="密码"], input[type="password"]').first.fill("VpnTest2026")
            
            if svg_src:
                # 解析SVG验证码
                import base64, xml.etree.ElementTree as ET
                try:
                    svg_bytes = base64.b64decode(svg_src.split(',')[1] if ',' in svg_src else svg_src)
                    tree = ET.fromstring(svg_bytes)
                    ns = {'svg': 'http://www.w3.org/2000/svg'}
                    code = ''.join(t.text or '' for t in tree.findall('.//svg:text', ns))
                    print(f"  SVG验证码: {code}", flush=True)
                    page.locator('[placeholder*="验证码"]').first.fill(code)
                except Exception as e:
                    print(f"  SVG解析失败: {e}", flush=True)
            
            # 登录
            page.locator('button:has-text("登入")').first.click()
            time.sleep(3)
            
            current_url = page.url
            print(f"  登录后URL: {current_url}", flush=True)
            
            if "dashboard" not in current_url and "user" not in current_url:
                print("  [FAIL] 登录失败!", flush=True)
                page.screenshot(path=os.path.join(os.path.dirname(__file__), "dageyun_login_fail.png"))
                browser.close()
                return None
            
            print("  登录成功!", flush=True)
            
            # 关弹窗
            time.sleep(2)
            try:
                page.locator('button:has-text("Close"), button:has-text("关闭")').first.click(timeout=3000)
                time.sleep(1)
            except:
                pass
            
            # 找一键订阅
            print("[2/4] 找订阅...", flush=True)
            
            # 方法1: 点一键订阅
            try:
                page.locator('text=一键订阅').first.click(timeout=5000)
                time.sleep(1)
            except:
                print("  未找到一键订阅", flush=True)
            
            # 方法2: 劫持clipboard
            print("[3/4] 提取订阅链接...", flush=True)
            page.evaluate("""() => {
                let old = navigator.clipboard.writeText;
                window.__dageyun_sub = '';
                navigator.clipboard.writeText = function(t) {
                    window.__dageyun_sub = t;
                    return Promise.resolve();
                };
            }""")
            
            # 点击复制订阅地址
            page.evaluate("""() => {
                let all = document.querySelectorAll('*');
                for (let el of all) {
                    let t = (el.textContent || '').trim();
                    if (t === '复制订阅地址' || t.includes('复制订阅') || t.includes('Clash')) {
                        if (el.tagName === 'BUTTON' || el.tagName === 'SPAN' || el.tagName === 'DIV') {
                            el.click();
                            return 'clicked: ' + el.tagName;
                        }
                    }
                }
                return 'not found';
            }""")
            
            time.sleep(2)
            
            sub = page.evaluate("() => window.__dageyun_sub || ''")
            print(f"  订阅: {sub}", flush=True)
            
            # 方法3: 检查XHR请求结果
            if not sub:
                sub = page.evaluate("""() => {
                    // 找所有data-clipboard-text
                    let els = document.querySelectorAll('[data-clipboard-text]');
                    for (let e of els) {
                        let v = e.getAttribute('data-clipboard-text');
                        if (v && v.includes('://')) return v;
                    }
                    // 找文本
                    let text = document.body.innerText;
                    let m = text.match(/https?:\\/\\/[^\\s]+(?:subscribe|sub|token)[^\\s]+/i);
                    return m ? m[0] : '';
                }""")
                print(f"  订阅(备用): {sub}", flush=True)
            
            page.screenshot(path=os.path.join(os.path.dirname(__file__), "dageyun_final.png"))
            
            return sub
            
        except Exception as e:
            print(f"  异常: {e}", flush=True)
            import traceback
            traceback.print_exc()
            return None
        finally:
            time.sleep(3)
            browser.close()

def try_sslar():
    """SSLAR优惠码激活"""
    print("\n" + "="*60)
    print("  SSLAR 优惠码激活")
    print("="*60)
    
    # 尝试API
    url = "https://1.sslar.cn/api/v1/user/coupon_check"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    }
    data = {"code": "iZcnBXiM"}
    
    try:
        r = requests.post(url, json=data, headers=headers, timeout=15)
        print(f"  API响应: {r.status_code}", flush=True)
        print(f"  内容: {r.text[:500]}", flush=True)
    except Exception as e:
        print(f"  API错误: {e}", flush=True)

def check_fscloud():
    """FSCloud检查"""
    print("\n" + "="*60)
    print("  FSCloud 状态检查")
    print("="*60)
    print("  账号: fscloud_test_2026@gmail.com")
    print("  密码: Fscloud2026")
    print("  状态: 验证码已发Gmail，需手动收取")
    print("  Gmail需要IMAP/SMTP凭据才可自动收取")

if __name__ == "__main__":
    print("=" * 60)
    print("  多机场批量提取")
    print("=" * 60)
    
    results = {}
    
    # 大哥云
    sub = extract_dageyun()
    if sub:
        results["大哥云"] = sub
    
    # SSLAR
    try_sslar()
    
    # FSCloud
    check_fscloud()
    
    # 汇总
    print("\n" + "="*60)
    print("  汇总:")
    for k, v in results.items():
        print(f"  {k}: {v}")
    
    if results:
        with open(os.path.join(os.path.dirname(__file__), "multi_extract_results.json"), "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
