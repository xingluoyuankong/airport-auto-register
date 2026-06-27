# -*- coding: utf-8 -*-
"""
Zetsal VPN 自动注册 - 完整版 v2
注册 → 登录 → 领取试用(/trial) → 获取订阅链接
"""
import sys, requests, random, string, time, re, os, subprocess, json
import ddddocr
from PIL import Image, ImageEnhance

sys.stdout.reconfigure(encoding='utf-8')

BASE = "https://zetsal.com"
NO_PROXY = {"http": None, "https": None}
TESSERACT = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
OUT_DIR = r"E:\API获取工具\自动集成免费代理服务\01-机场VPN注册机\zetsalvpn-fresh"

ocr = ddddocr.DdddOcr(show_ad=False)

def nanoid(n=10):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=n))

def preprocess(img_bytes):
    import io
    img = Image.open(io.BytesIO(img_bytes))
    img = img.resize((img.width*3, img.height*3), Image.LANCZOS)
    gray = img.convert('L')
    gray = ImageEnhance.Contrast(gray).enhance(2.0)
    return gray.point(lambda x: 255 if x>140 else 0, '1')

def tesseract_ocr(img_bytes):
    import tempfile
    img = preprocess(img_bytes)
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        img.save(f.name); tmp=f.name
    try:
        for psm in ['7','8','13']:
            r = subprocess.run([TESSERACT,tmp,"-","--psm",psm,
                "-c","tessedit_char_whitelist=0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ+="],
                capture_output=True,text=True,timeout=10)
            t = r.stdout.strip().replace(" ","").replace("\n","")
            if 2<=len(t)<=10: return t
    finally: os.unlink(tmp)
    return ""

def solve_captcha(img_bytes):
    candidates = []
    for _ in range(3):
        raw = ocr.classification(img_bytes).strip().replace(" ","")
        if raw and raw not in candidates: candidates.append(raw)
    tess = tesseract_ocr(img_bytes)
    if tess and tess not in candidates: candidates.append(tess)
    answers = []
    for c in candidates:
        if '+' in c:
            m = re.match(r'(\d+)\+(\d+)',c)
            if m: answers.append(str(int(m.group(1))+int(m.group(2))))
        clean = re.sub(r'[^a-zA-Z0-9]','',c)
        if clean and clean not in answers: answers.append(clean)
        digits = re.sub(r'[^0-9]','',c)
        if digits and 2<=len(digits)<=5:
            for i in range(1,len(digits)):
                a_s,b_s=digits[:i],digits[i:]
                if a_s.startswith('0') and len(a_s)>1: continue
                if b_s.startswith('0') and len(b_s)>1: continue
                a,b=int(a_s),int(b_s)
                if 1<=a<=200 and 1<=b<=200:
                    s=str(a+b)
                    if s not in answers: answers.append(s)
    return answers

def get_page_token(session, path):
    """从页面获取隐藏 token"""
    try:
        resp = session.get(f"{BASE}{path}", timeout=15, proxies=NO_PROXY)
        m = re.search(r'id="token"\s+value="([a-f0-9]+)"', resp.text)
        return m.group(1) if m else None
    except:
        return None

def do_register(session, username, email, password):
    """注册"""
    token = get_page_token(session, "/register")
    if not token: return False
    for _ in range(10):
        cap = session.get(f"{BASE}/api/captcha", timeout=15, proxies=NO_PROXY)
        answers = solve_captcha(cap.content)
        for ans in answers[:6]:
            resp = session.post(f"{BASE}/api/register", data={
                "username":username,"password":password,"password2":password,
                "email":email,"captcha":ans,"tos":"1","token":token
            }, timeout=15, proxies=NO_PROXY,
               headers={"Content-Type":"application/x-www-form-urlencoded"})
            r = resp.json()
            if r.get('status'): return True
            if 'captcha' not in str(r.get('message','')).lower(): return False
    return False

def do_login(session, username, password):
    """登录"""
    token = get_page_token(session, "/login")
    if not token: return False
    data = f"username={username}&password={requests.utils.quote(password)}&token={token}&tos=1"
    resp = session.post(f"{BASE}/api/login", data=data, timeout=15, proxies=NO_PROXY,
                        headers={"Content-Type":"application/x-www-form-urlencoded"})
    try:
        return resp.json().get('status', False)
    except:
        return False

def do_claim_trial(session):
    """领取免费试用 - 访问 /trial"""
    try:
        resp = session.get(f"{BASE}/trial", timeout=15, proxies=NO_PROXY, allow_redirects=True)
        if "login" in resp.url:
            return False
        # 检查是否成功
        text = resp.text
        if 'success' in text.lower() or 'claimed' in text.lower() or '已领取' in text or 'activated' in text.lower():
            return True
        # /trial 可能是一个页面，需要点击按钮
        # 找 form 提交
        token_m = re.search(r'id="token"\s+value="([a-f0-9]+)"', text)
        if token_m:
            # 有表单，提交
            resp2 = session.post(f"{BASE}/api/trial", data={"token": token_m.group(1)}, timeout=15, proxies=NO_PROXY)
            try:
                r = resp2.json()
                if r.get('status'): return True
            except: pass
        # 只要没重定向到登录页就算部分成功
        return "login" not in resp.url
    except:
        return False

def do_get_subscriptions(session):
    """获取订阅链接"""
    subs = []
    # 检查多个可能的页面
    for path in ["/dashboard", "/panel", "/vpn/panel"]:
        try:
            resp = session.get(f"{BASE}{path}", timeout=15, proxies=NO_PROXY, allow_redirects=True)
            if "login" in resp.url:
                continue
            html = resp.text
            # 找订阅链接
            found = re.findall(r'copyText\([\'"]([^\'"]+)[\'"]\)', html)
            found += re.findall(r'(https?://[^"\'<>\s]+\.yaml[^"\'<>\s]*)', html)
            found += re.findall(r'(https?://sub[^"\'<>\s]+)', html)
            for u in found:
                u = u.replace("&amp;","&").replace("&#39;","'")
                if u not in subs:
                    subs.append(u)
        except:
            pass
    return subs

# ===== 主程序 =====
print("=" * 60)
print("  Zetsal VPN 完整注册器 v2")
print("  注册 → 登录 → 领取试用 → 获取订阅")
print("=" * 60)

total = int(sys.argv[1]) if len(sys.argv) > 1 else 5
success = 0
results = []

for i in range(total):
    print(f"\n{'─'*40}")
    print(f"  [{i+1}/{total}]")
    print(f"{'─'*40}")
    
    username = nanoid(10)
    email = nanoid(8)+"@outlook.com"
    password = nanoid(16)+"!Aa1"
    
    session = requests.Session()
    session.headers.update({"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
    
    # 注册
    print(f"  注册中...")
    if not do_register(session, username, email, password):
        print(f"  [注册失败]")
        continue
    print(f"  [注册OK] {username}")
    
    # 登录
    print(f"  登录中...")
    logged = do_login(session, username, password)
    print(f"  [登录] {'OK' if logged else '失败(可能已自动登录)'}")
    
    # 领取试用
    print(f"  领取试用...")
    claimed = do_claim_trial(session)
    print(f"  [试用] {'OK' if claimed else '失败'}")
    
    # 获取订阅
    time.sleep(2)
    print(f"  获取订阅...")
    subs = do_get_subscriptions(session)
    print(f"  [订阅] {len(subs)} 个")
    for s in subs:
        print(f"    {s}")
    
    results.append({
        "username": username, "password": password,
        "email": email, "trial": claimed, "subs": subs
    })
    success += 1
    time.sleep(random.uniform(1, 2))

# 保存结果
if results:
    ts = time.strftime('%Y%m%d_%H%M%S')
    out = os.path.join(OUT_DIR, f"注册结果_{ts}.txt")
    with open(out, "w", encoding="utf-8") as f:
        f.write(f"# Zetsal VPN 注册结果\n")
        f.write(f"# 时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# 成功: {success}/{total}\n\n")
        for r in results:
            f.write(f"用户名: {r['username']}\n")
            f.write(f"密码: {r['password']}\n")
            f.write(f"试用: {'✓' if r['trial'] else '✗'}\n")
            if r['subs']:
                f.write(f"订阅:\n")
                for s in r['subs']:
                    f.write(f"  {s}\n")
            else:
                f.write(f"订阅: 未获取到\n")
            f.write("\n")
    
    all_out = os.path.join(OUT_DIR, "注册结果.txt")
    with open(all_out, "a", encoding="utf-8") as f:
        f.write(f"\n# 批次 {time.strftime('%Y-%m-%d %H:%M:%S')} ({success}/{total})\n")
        for r in results:
            f.write(f"{r['username']}:{r['password']}\n")
    
    print(f"\n结果已保存: {out}")

print(f"\n{'=' * 60}")
print(f"  完成! 成功: {success}/{total}")
print(f"{'=' * 60}")
