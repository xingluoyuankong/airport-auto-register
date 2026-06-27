"""批量检测所有剩余机场在线性和注册入口 - 快速扫描"""
import requests
import time

AIRPORTS = [
    # GateRank榜单 - 17个新发现的
    ("NOW加速", "https://nowjiasu.com"),
    ("瞬云", "https://shunyun.xyz"),
    ("仙路湾", "https://xianluwan.com"),
    ("山水云", "https://shanshuiyun.com"),
    ("NICE加速", "https://nicejiasu.com"),
    ("锦云", "https://jinyun.pro"),
    ("寰宇云", "https://huanyuyun.com"),
    ("秒秒云", "https://miaomiaoyun.com"),
    ("大哥云", "https://dageyun.com"),
    ("SKYLUMO", "https://skylumo.com"),
    ("宇宙云", "https://yuzhouyun.com"),
    ("光年梯", "https://guangnianti.com"),
    ("闪狐云", "https://shanhuyun.com"),
    # 已知机场库
    ("FSCloud", "https://dash.fscloud.app"),
    ("奈云v2ny", "https://www.v2ny.com"),
    ("雨燕云", "https://yuyan.online"),
    ("逗猫", "https://douchat.top"),
    ("泰山Net", "https://www.taishan.pro"),
    ("一元机场(old)", "https://xn--4gq62f52gdss.top"),
    ("极光加速", "https://jiguang.pro"),
    ("besnow", "https://besnow.me"),
    ("aiguobit", "https://a.aiguobit.com"),
    ("hidexx", "https://a.hidexx.com"),
    ("69云", "https://69yun69.com"),
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/134.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml"
}

print("=" * 80)
print("批量检测机场在线性 - 24个")
print("=" * 80)

results = {"在线可访问": [], "在线需验证": [], "被墙/不可达": [], "已死/出售": []}

for name, url in AIRPORTS:
    try:
        print(f"\n[{name}] {url} ... ", end="", flush=True)
        r = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        status = r.status_code
        final_url = r.url
        title = ""
        if "<title>" in r.text:
            title = r.text.split("<title>")[1].split("</title>")[0] if "</title>" in r.text.split("<title>")[1] else ""
        title = title[:80]
        
        print(f"Status:{status} Title:{title}")
        
        # 判断状态
        dead_keywords = ["godaddy", "domain names", "parked", "出售", "buy this domain", "hugedomains", "afternic", "namecheap", "domain has expired"]
        is_dead = any(k in r.text.lower()[:2000] for k in dead_keywords)
        
        if is_dead:
            results["已死/出售"].append((name, url, "域名出售"))
            print(f"  ❌ 已死/域名出售")
        elif "注册" in r.text[:3000] or "register" in r.text[:3000].lower() or "登录" in r.text[:3000]:
            # 有注册入口，检查能否找到注册URL
            has_v2board = "/api/v1/passport/auth/register" in r.text or "#/register" in r.text
            has_sspanel = "/users/register" in r.text or "sspanel" in r.text.lower()
            results["在线可访问"].append((name, url, final_url, status, "V2Board" if has_v2board else ("SSPANEL" if has_sspanel else "未知")))
            print(f"  ✅ 在线 | 最终URL: {final_url[:80]}")
        else:
            results["在线需验证"].append((name, url, final_url, status, title))
            print(f"  ⚠️ 需浏览器验证 | 最终URL: {final_url[:80]}")
            
    except requests.exceptions.ConnectionError as e:
        err = str(e)[:100]
        results["被墙/不可达"].append((name, url, err))
        print(f"❌ 被墙/不可达: {err[:60]}")
    except requests.exceptions.Timeout:
        results["被墙/不可达"].append((name, url, "超时"))
        print(f"❌ 超时")
    except Exception as e:
        results["被墙/不可达"].append((name, url, str(e)[:100]))
        print(f"❌ 错误: {str(e)[:60]}")

print("\n" + "=" * 80)
print("汇总")
print("=" * 80)

print(f"\n✅ 在线可访问 ({len(results['在线可访问'])}):")
for name, url, final_url, status, ptype in results["在线可访问"]:
    print(f"  {name}: {url} → {final_url[:60]} [{ptype}]")

print(f"\n⚠️ 需浏览器验证 ({len(results['在线需验证'])}):")
for name, url, final_url, status, title in results["在线需验证"]:
    print(f"  {name}: {url} ({title})")

print(f"\n❌ 被墙/不可达 ({len(results['被墙/不可达'])}):")
for name, url, err in results["被墙/不可达"]:
    print(f"  {name}: {url} - {err[:60]}")

print(f"\n💀 已死/出售 ({len(results['已死/出售'])}):")
for name, url, reason in results["已死/出售"]:
    print(f"  {name}: {url} - {reason}")
