# -*- coding: utf-8 -*-
"""
机场自动注册生产脚本
支持: hidexx系统 (a.aiguobit.com, a.hidexx.com 等)
功能: 自动注册 -> 领取免费试用 -> 获取订阅链接 -> 保存结果

用法: python auto_register.py [--site a.aiguobit.com] [--count 5] [--wait 15]

依赖: pip install requests ddddocr
"""
import requests, sys, re, random, string, time, json, os, argparse
from urllib.parse import unquote
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

try:
    import ddddocr
    OCR = ddddocr.DdddOcr(show_ad=False)
    OCR_OK = True
except ImportError:
    OCR_OK = False
    print("[WARN] ddddocr not installed. Run: pip install ddddocr")

# ============ 配置 ============
HIDEXX_SITES = {
    "a.aiguobit.com": "https://a.aiguobit.com",
    "a.hidexx.com": "https://a.hidexx.com",
}

V2BOARD_SITES = {
    # 这些站点可能随时失效，需要自行更新
    "fastestcloud.xyz": "https://fastestcloud.xyz",
    "v2aky.com": "https://www.v2aky.com",  # 需要邀请码
}

WORKSPACE = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(WORKSPACE, "注册结果")

# ============ 工具 ============
def rand_email():
    return f"{''.join(random.choices(string.ascii_lowercase+string.digits, k=10))}@outlook.com"

def rand_pwd():
    return ''.join(random.choices(string.ascii_letters + string.digits + "!@#$%", k=14))

def ua():
    return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"

def solve_captcha(img_bytes):
    if not OCR_OK:
        return ""
    try:
        result = OCR.classification(img_bytes)
        return re.sub(r'[^a-zA-Z0-9]', '', result)[:4]
    except:
        return ""

# ============ hidexx 注册 ============
def register_hidexx(base_url, wait_sec=15, max_attempts=10):
    """hidexx 系统完整注册流程"""
    s = requests.Session()
    s.headers.update({"User-Agent": ua()})
    
    email = rand_email()
    password = rand_pwd()
    
    # 1. 注册
    s.get(f"{base_url}/users/register", timeout=10)
    
    registered = False
    for attempt in range(max_attempts):
        r = s.get(f"{base_url}/users/vcode", timeout=10)
        code = solve_captcha(r.content)
        if not code or len(code) < 4:
            continue
        
        r = s.post(f"{base_url}/users/register", data={
            "email": email, "pass1": password, "pass2": password, "checkcode": code
        }, timeout=10, allow_redirects=True)
        
        if "/users/ucenter" in r.url:
            registered = True
            break
        elif "已注册" in r.text or "已存在" in r.text:
            email = rand_email()
            continue
        elif "验证码" not in r.text:
            break
    
    if not registered:
        return None
    
    # 2. 领取试用
    r = s.get(f"{base_url}/users/ucenter", timeout=10)
    sid_match = re.search(r"name=['\"]?sid['\"]?\s+value\s*=\s*['\"]?(\d+)", r.text)
    checksum_match = re.search(r"name=['\"]?checksum['\"]?\s+value\s*=\s*['\"]?([a-f0-9]+)", r.text)
    
    trial = "N/A"
    if sid_match and checksum_match:
        sid = sid_match.group(1)
        checksum = checksum_match.group(1)
        for line_id in ["1", "11"]:
            r = s.post(f"{base_url}/orders/request_day_trial", data={
                "sid": sid, "checksum": checksum, "line_id": line_id, "quantity": "1"
            }, timeout=10, allow_redirects=True)
            if "success" in unquote(r.url) or "领取成功" in r.text:
                trial = "成功"
                break
            elif "已申请" in unquote(r.url) or "已申请" in r.text:
                trial = "已领取"
                break
    
    # 3. 等待订阅发放
    time.sleep(wait_sec)
    
    # 4. 获取订阅
    r = s.get(f"{base_url}/users/ucenter", timeout=10)
    copy = re.findall(r"copyText\(['\"]([^'\"]+)['\"]\)", r.text)
    labeled = re.findall(r"onclick=\"copyText\('([^']+)'\)\"[^>]*>([^<]+)<", r.text)
    
    subs = []
    for url in copy:
        url = url.replace("&amp;", "&")
        label = ""
        for lu, ll in labeled:
            if lu.replace("&amp;", "&") == url:
                label = ll.strip()
                break
        subs.append({"url": url, "label": label})
    
    return {
        "email": email,
        "password": password,
        "trial": trial,
        "subscriptions": subs,
        "site": base_url,
        "time": datetime.now().isoformat(),
    }

# ============ V2Board 注册 ============
def register_v2board(base_url, invite_code="", email_code=""):
    """V2Board 系统注册"""
    email = rand_email()
    password = rand_pwd()
    
    url = f"{base_url.rstrip('/')}/api/v1/passport/auth/register"
    payload = {
        "email": email,
        "password": password,
        "email_code": email_code,
        "invite_code": invite_code,
        "recaptcha_data": ""
    }
    
    try:
        r = requests.post(url, json=payload, headers={
            "Content-Type": "application/json",
            "User-Agent": ua(),
            "Origin": base_url,
            "Referer": f"{base_url}/",
        }, timeout=15, allow_redirects=True)
        
        if r.status_code == 200:
            data = r.json()
            token = data.get("data", {}).get("token", "")
            auth_data = data.get("data", {}).get("auth_data", "")
            if token:
                return {"email": email, "password": password, "token": token, "auth_data": auth_data, "site": base_url}
        
        return {"error": r.text[:200], "status": r.status_code}
    except Exception as e:
        return {"error": str(e)[:100]}

# ============ 主程序 ============
def main():
    parser = argparse.ArgumentParser(description="机场自动注册")
    parser.add_argument("--site", default="a.aiguobit.com", help="目标站点")
    parser.add_argument("--count", type=int, default=1, help="注册数量")
    parser.add_argument("--wait", type=int, default=15, help="等待订阅发放秒数")
    parser.add_argument("--type", default="hidexx", choices=["hidexx", "v2board"], help="站点类型")
    args = parser.parse_args()
    
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    print(f"{'='*60}")
    print(f"  机场自动注册器")
    print(f"  站点: {args.site} | 数量: {args.count} | 类型: {args.type}")
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    all_results = []
    
    for i in range(args.count):
        print(f"\n--- 第 {i+1}/{args.count} 个 ---")
        
        if args.type == "hidexx":
            base = HIDEXX_SITES.get(args.site, f"https://{args.site}")
            result = register_hidexx(base, wait_sec=args.wait)
        else:
            base = V2BOARD_SITES.get(args.site, f"https://{args.site}")
            result = register_v2board(base)
        
        if result and "error" not in result:
            all_results.append(result)
            print(f"  ✅ 成功: {result['email']}")
            if result.get("subscriptions"):
                for sub in result["subscriptions"]:
                    print(f"    [{sub['label']}] {sub['url']}")
        else:
            print(f"  ❌ 失败: {result}")
        
        if i < args.count - 1:
            time.sleep(random.uniform(2, 5))
    
    # 保存结果
    if all_results:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out = os.path.join(RESULTS_DIR, f"注册_{args.site}_{ts}.json")
        with open(out, "w", encoding="utf-8") as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        
        # 同时保存简洁的文本格式
        txt_out = os.path.join(RESULTS_DIR, f"注册_{args.site}_{ts}.txt")
        with open(txt_out, "w", encoding="utf-8") as f:
            f.write(f"# 机场注册结果 - {args.site}\n")
            f.write(f"# 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# 数量: {len(all_results)}\n\n")
            for r in all_results:
                f.write(f"# {r['email']}\n")
                f.write(f"# 密码: {r['password']}\n")
                f.write(f"# 试用: {r.get('trial', 'N/A')}\n")
                for sub in r.get("subscriptions", []):
                    f.write(f"{sub['url']}\n")
                f.write("\n")
        
        print(f"\n{'='*60}")
        print(f"  完成! 成功: {len(all_results)}/{args.count}")
        print(f"  JSON: {out}")
        print(f"  TXT: {txt_out}")
        print(f"{'='*60}")

if __name__ == "__main__":
    main()
