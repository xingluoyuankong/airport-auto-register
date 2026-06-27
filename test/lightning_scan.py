"""闪电扫描：打开→检测→记录 → NEXT。每个15秒。"""
import subprocess, json, time, sys

CD = "E:/API获取工具"
CLI = f'cd "{CD}" && playwright-cli'

ports = [
    ("极光加速", "https://jiguang.pro"),
    ("雨燕云", "https://yuyan.online"),
    ("逗猫", "https://douchat.top"),
    ("泰山Net", "https://www.taishan.pro"),
    ("一元机场old", "https://xn--4gq62f52gdss.top"),
    ("besnow", "https://besnow.me"),
    ("aiguobit", "https://a.aiguobit.com"),
    ("hidexx", "https://a.hidexx.com"),
    ("69云", "https://69yun69.com"),
    ("NOW加速", "https://nowjiasu.com"),
    ("瞬云", "https://shunyun.xyz"),
    ("仙路湾", "https://xianluwan.com"),
    ("山水云", "https://shanshuiyun.com"),
    ("NICE加速", "https://nicejiasu.com"),
    ("锦云", "https://jinyun.pro"),
    ("寰宇云", "https://huanyuyun.com"),
    ("秒秒云", "https://miaomiaoyun.com"),
    ("SKYLUMO", "https://skylumo.com"),
    ("宇宙云", "https://yuzhouyun.com"),
    ("光年梯", "https://guangnianti.com"),
    ("闪狐云", "https://shanhuyun.com"),
]

results = []
for name, url in ports:
    try:
        r = subprocess.run(f'''pwsh -Command "cd '{CD}'; playwright-cli goto '{url}' 2>&1; Start-Sleep 3; playwright-cli eval 'document.title' 2>&1"''', 
                         capture_output=True, text=True, timeout=20, shell=True)
        out = r.stdout + r.stderr
        title = "N/A"
        if '### Result' in out:
            title = out.split('### Result')[1].split('\n')[0].strip().strip('"')
        elif 'Page Title:' in out:
            title = out.split('Page Title:')[1].split('\n')[0].strip()
        
        # Check for registration
        has_reg = "注册" in out or "register" in out.lower() or "sign" in out.lower()
        dead = "domain" in out.lower() or "parked" in out.lower() or "出售" in out
        err = "ERR_" in out or "timeout" in out.lower() or "Connection closed" in out
        
        status = "DEAD" if dead else ("ERROR" if err else ("REG" if has_reg else "ONLINE"))
        print(f"[{name}] {status} | {title[:60]}")
        results.append({"name": name, "url": url, "status": status, "title": title[:80]})
        
    except Exception as e:
        print(f"[{name}] ERROR: {str(e)[:60]}")
        results.append({"name": name, "url": url, "status": "ERROR"})

print("\n===== SUMMARY =====")
for r in results:
    print(f"  {r['name']:<12} {r['status']:<8} {r.get('title','')[:50]}")
