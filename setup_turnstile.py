#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Turnstile 绕过工具 - 安装与配置脚本
=====================================
自动安装以下工具:
1. turnstile-solver (PyPI包) - 自动化Cloudflare Turnstile验证码解决
2. playwright + stealth插件 - 浏览器自动化反检测
3. ddddocr - 验证码OCR识别
4. Camoufox (可选) - 反检测浏览器

安装: python setup_turnstile.py --install
测试: python setup_turnstile.py --test
"""

import subprocess
import sys
import os
import argparse

def run_cmd(cmd, desc=""):
    print(f"  [{desc}] {cmd[:80]}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            print(f"  ✅ {desc} 成功")
            return True
        else:
            print(f"  ⚠️ {desc} 警告: {result.stderr[:200]}")
            return False
    except Exception as e:
        print(f"  ❌ {desc} 失败: {e}")
        return False

def install_basic():
    """安装基础依赖"""
    print("\n[1/4] 安装基础依赖...")
    
    pkgs = [
        "requests>=2.28.0",
        "ddddocr>=1.4.0",
        "Pillow>=9.0.0",
    ]
    
    for pkg in pkgs:
        run_cmd(f"{sys.executable} -m pip install {pkg} -q", pkg)
    
    return True

def install_playwright():
    """安装Playwright + stealth"""
    print("\n[2/4] 安装Playwright浏览器自动化...")
    
    run_cmd(f"{sys.executable} -m pip install playwright playwright-stealth -q", "playwright")
    run_cmd(f"{sys.executable} -m playwright install chromium", "chromium browser")
    
    return True

def install_turnstile_solver():
    """安装Turnstile解决工具"""
    print("\n[3/4] 安装Turnstile绕过工具...")
    
    # turnstile-solver (PyPI)
    run_cmd(f"{sys.executable} -m pip install turnstile-solver -q", "turnstile-solver")
    
    # cfsolver (Cloudflare bypass)
    run_cmd(f"{sys.executable} -m pip install cfsolver -q", "cfsolver")
    
    return True

def install_camoufox():
    """安装Camoufox反检测浏览器（可选）"""
    print("\n[4/4] 安装Camoufox反检测浏览器（可选）...")
    try:
        run_cmd(f"{sys.executable} -m pip install camoufox -q", "camoufox")
    except:
        print("  ⚠️ Camoufox安装跳过（需要Python 3.10+）")
    
    return True

def test_turnstile():
    """测试Turnstile绕过"""
    print("\n[测试] Turnstile绕过测试...")
    
    test_script = '''
try:
    from turnstile_solver import TurnstileSolver
    print("  ✅ turnstile-solver 导入成功")
except ImportError as e:
    print(f"  ❌ turnstile-solver: {e}")

try:
    import ddddocr
    ocr = ddddocr.DdddOcr(show_ad=False)
    print("  ✅ ddddocr 就绪")
except ImportError as e:
    print(f"  ❌ ddddocr: {e}")

try:
    from playwright.sync_api import sync_playwright
    print("  ✅ Playwright 就绪")
except ImportError as e:
    print(f"  ❌ Playwright: {e}")

try:
    from playwright_stealth import stealth_sync
    print("  ✅ playwright-stealth 就绪")
except ImportError as e:
    print(f"  ❌ playwright-stealth: {e}")

try:
    import cfsolver
    print("  ✅ cfsolver 就绪")
except ImportError as e:
    print(f"  ⚠️ cfsolver: {e}")

# 简单功能测试
try:
    import ddddocr
    ocr = ddddocr.DdddOcr(show_ad=False)
    # 测试简单数字识别
    test_img = None  # 实际测试需要真实验证码图片
    print("  ℹ️ ddddocr功能正常（需真实验证码图片验证效果）")
except Exception as e:
    print(f"  ⚠️ ddddocr测试: {e}")
'''
    
    result = subprocess.run([sys.executable, "-c", test_script], 
                          capture_output=True, text=True, timeout=30)
    print(result.stdout)
    if result.stderr:
        print(result.stderr[:500])

def main():
    parser = argparse.ArgumentParser(description="Turnstile绕过工具安装配置")
    parser.add_argument("--install", action="store_true", help="安装所有依赖")
    parser.add_argument("--test", action="store_true", help="测试安装结果")
    parser.add_argument("--all", action="store_true", help="安装+测试")
    
    args = parser.parse_args()
    
    if not any([args.install, args.test, args.all]):
        parser.print_help()
        print("\n用法示例:")
        print("  python setup_turnstile.py --install   # 安装依赖")
        print("  python setup_turnstile.py --test      # 测试")
        print("  python setup_turnstile.py --all       # 安装+测试")
        return
    
    print("=" * 50)
    print("  Turnstile 绕过工具 - 安装配置")
    print("=" * 50)
    
    if args.install or args.all:
        install_basic()
        install_playwright()
        install_turnstile_solver()
        install_camoufox()
        
        print("\n✅ 安装完成!")
        print("\n核心工具:")
        print("  - ddddocr: 验证码OCR识别")
        print("  - turnstile-solver: Cloudflare Turnstile自动化")
        print("  - playwright + stealth: 浏览器自动化反检测")
        print("  - cfsolver: Cloudflare HTTP绕过")
    
    if args.test or args.all:
        test_turnstile()

if __name__ == "__main__":
    main()
