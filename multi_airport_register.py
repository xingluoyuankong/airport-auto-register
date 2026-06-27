# -*- coding: utf-8 -*-
# 通用机场批量注册器 - 支持 V2Board + SSPanel
import requests
import random
import string
import threading
import time
import os
import urllib3
urllib3.disable_warnings()

# ============ 机场列表 ============

# V2Board 机场 (API: /api/v1/passport/auth/register)
V2BOARD_SITES = [
    "https://fastestcloud.xyz",
    "https://feiniaoyun.top",
    "https://shan-cloud.xyz",
    "https://www.ckcloud.xyz",
    "https://www.dgycom.com",
    "https://circlecloud123.com",
]

# SSPanel 机场 (API: /auth/register)
SSPANEL_SITES = [
    "https://www.douluos.xyz",
    "https://jsmao.org",
    "https://www.ckcloud.xyz",
    "https://user.bafang.vip",
    "https://cloud.hhygj.xyz",
    "https://jsm.one",
    "https://www.iacgbt.com",
    "https://www.jafiyun.cc",
    "https://www.liuchangyun.com",
    "https://www.wolaile.icu",
    "https://gflink.net",
    "https://maossr.top",
    "https://www.kuaicloud.xyz",
    "https://htavpn.com",
]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ACCOUNTS_FILE = os.path.join(SCRIPT_DIR, "all_accounts.txt")
SUB_FILE = os.path.join(SCRIPT_DIR, "all_subscriptions.txt")

# ============ 工具函数 ============

def random_email():
    domains = ["gmail.com", "outlook.com", "qq.com", "163.com", "yahoo.com"]
    return f"{''.join(random.choices(string.ascii_lowercase, k=8))}{random.randint(100,999)}@{random.choice(domains)}"

def random_password():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=12))

def random_ua():
    agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    ]
    return random.choice(agents)

# ============ 注册函数 ============

def register_v2board(site_url, email, password):
    """V2Board 注册"""
    try:
        reg_url = site_url.rstrip('/') + '/api/v1/passport/auth/register'
        data = {'email': email, 'password': password, 'email_code': '', 'invite_code': ''}
        headers = {'User-Agent': random_ua(), 'Content-Type': 'application/json', 'Referer': site_url}
        r = requests.post(reg_url, json=data, headers=headers, timeout=15, verify=False)
        if r.status_code == 200:
            j = r.json()
            token = j.get('data', {}).get('token', '')
            auth_data = j.get('data', {}).get('auth_data', '')
            if token:
                sub_url = f"{site_url.rstrip('/')}/api/v1/client/subscribe?token={token}"
                return {'ok': True, 'token': token, 'auth_data': auth_data, 'sub_url': sub_url}
        elif r.status_code == 429:
            return {'ok': False, 'error': '429限速'}
        return {'ok': False, 'error': f'{r.status_code}: {r.text[:60]}'}
    except requests.exceptions.SSLError:
        return {'ok': False, 'error': 'SSL错误'}
    except Exception as e:
        return {'ok': False, 'error': str(e)[:60]}

def register_sspanel(site_url, email, password):
    """SSPanel 注册"""
    try:
        reg_url = site_url.rstrip('/') + '/auth/register'
        data = {'email': email, 'password': password, 'invite_code': ''}
        headers = {'User-Agent': random_ua(), 'Content-Type': 'application/json', 'Referer': site_url}
        r = requests.post(reg_url, json=data, headers=headers, timeout=15, verify=False)
        if r.status_code == 200:
            j = r.json()
            return {'ok': True, 'token': '', 'auth_data': '', 'sub_url': ''}
        elif r.status_code == 429:
            return {'ok': False, 'error': '429限速'}
        return {'ok': False, 'error': f'{r.status_code}: {r.text[:60]}'}
    except requests.exceptions.SSLError:
        return {'ok': False, 'error': 'SSL错误'}
    except Exception as e:
        return {'ok': False, 'error': str(e)[:60]}

def register_one(site_url, site_type, email, password):
    """统一注册入口"""
    if site_type == 'v2board':
        return register_v2board(site_url, email, password)
    elif site_type == 'sspanel':
        return register_sspanel(site_url, email, password)
    return {'ok': False, 'error': '未知类型'}

# ============ 保存结果 ============

def save_result(site_url, site_type, email, password, result):
    """保存注册结果"""
    with open(ACCOUNTS_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{site_type}] {site_url} | {email} | {password} | {result.get('token', '')} | {result.get('auth_data', '')}\n")
    if result.get('sub_url'):
        with open(SUB_FILE, "a", encoding="utf-8") as f:
            f.write(f"# {email} @ {site_url}\n{result['sub_url']}\n\n")

# ============ 批量注册 ============

def batch_register(count_per_site=5):
    """对所有可用机场批量注册"""
    print("=" * 70)
    print("  通用机场批量注册器")
    print(f"  V2Board: {len(V2BOARD_SITES)} 个站点")
    print(f"  SSPanel: {len(SSPANEL_SITES)} 个站点")
    print(f"  每站注册: {count_per_site} 个")
    print("=" * 70)

    # 清空旧文件
    for f in [ACCOUNTS_FILE, SUB_FILE]:
        if os.path.exists(f):
            os.remove(f)

    total_ok = 0
    total_fail = 0

    # 注册 V2Board
    print(f"\n--- V2Board ({len(V2BOARD_SITES)} 个站点) ---")
    for site in V2BOARD_SITES:
        ok = 0
        fail = 0
        for i in range(count_per_site):
            email = random_email()
            password = random_password()
            result = register_one(site, 'v2board', email, password)
            if result['ok']:
                save_result(site, 'v2board', email, password, result)
                ok += 1
                total_ok += 1
                sub = result.get('sub_url', '')[:50]
                print(f"  [OK] {site} -> {email} {sub}...")
            else:
                fail += 1
                total_fail += 1
                print(f"  [FAIL] {site} -> {email} ({result['error']})")
                if '429' in result.get('error', ''):
                    break  # 被限速，跳过此站点
            time.sleep(random.uniform(1, 3))
        print(f"  {site}: {ok}成功 / {fail}失败")

    # 注册 SSPanel
    print(f"\n--- SSPanel ({len(SSPANEL_SITES)} 个站点) ---")
    for site in SSPANEL_SITES:
        ok = 0
        fail = 0
        for i in range(count_per_site):
            email = random_email()
            password = random_password()
            result = register_one(site, 'sspanel', email, password)
            if result['ok']:
                save_result(site, 'sspanel', email, password, result)
                ok += 1
                total_ok += 1
                print(f"  [OK] {site} -> {email}")
            else:
                fail += 1
                total_fail += 1
                print(f"  [FAIL] {site} -> {email} ({result['error']})")
                if '429' in result.get('error', ''):
                    break
            time.sleep(random.uniform(1, 3))
        print(f"  {site}: {ok}成功 / {fail}失败")

    print(f"\n{'=' * 70}")
    print(f"  完成! 总计: {total_ok}成功 / {total_fail}失败")
    print(f"  账号: {ACCOUNTS_FILE}")
    print(f"  订阅: {SUB_FILE}")
    print(f"{'=' * 70}")

if __name__ == "__main__":
    import sys
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    batch_register(count)
