"""免费订阅节点收集器 - 从GitHub/公开源抓取可用节点"""
import requests, base64, re, json, os, time

OUTDIR = os.path.join(os.path.dirname(__file__), "..", "register_results")

SOURCES = [
    # GitHub免费订阅
    "https://raw.githubusercontent.com/free-clash-v2ray/free-clash-v2ray.github.io/main/clash.yaml",
    "https://raw.githubusercontent.com/xiaoji235/airport-free/main/clash.yaml",
    "https://raw.githubusercontent.com/John19187/v2ray-SSR-Clash-Verge-Shadowrocke/main/clash.yaml",
    # freenode.biz
    "https://freenode.biz/clash.yaml",
    # surgenode
    "https://raw.githubusercontent.com/surgenode/free-nodes/main/clash.yaml",
    "https://raw.githubusercontent.com/clashnode/free-nodes/main/clash.yaml",
]

def fetch_and_parse(url):
    try:
        r = requests.get(url, headers={"User-Agent": "ClashMeta/1.0"}, timeout=20)
        if r.status_code != 200:
            return None
        text = r.text
        # base64 decode
        try:
            text = base64.b64decode(text).decode("utf-8")
        except:
            pass
        return text
    except:
        return None

def count_nodes(text):
    if not text:
        return 0, 0, 0, 0
    ssr = len(re.findall(r"type:\s*ssr", text, re.I))
    vmess = len(re.findall(r"type:\s*vmess", text, re.I))  
    trojan = len(re.findall(r"type:\s*trojan", text, re.I))
    vless = len(re.findall(r"type:\s*vless", text, re.I))
    proxy_lines = len(re.findall(r"^\s*- name:", text, re.M))
    return proxy_lines, ssr, vmess, trojan+vless

def merge_and_save(all_texts):
    """合并所有订阅到一个文件"""
    proxies = []
    names_seen = set()
    
    for text in all_texts:
        if not text:
            continue
        # 提取所有proxy块
        blocks = re.split(r"(?=^  - name:)", text, flags=re.M)
        for block in blocks:
            name_match = re.search(r'name:\s*"?([^"\n]+)"?', block)
            if name_match:
                name = name_match.group(1).strip()
                if name not in names_seen:
                    names_seen.add(name)
                    proxies.append(block)
    
    header = """# 免费节点合集 - 自动收集
# 更新时间: {}
# 节点总数: {}
proxies:
""".format(time.strftime("%Y-%m-%d %H:%M"), len(proxies))
    
    result = header + "\n".join(proxies)
    
    fname = os.path.join(OUTDIR, "free_nodes_merged.yaml")
    with open(fname, "w", encoding="utf-8") as f:
        f.write(result)
    
    return fname, len(proxies)

if __name__ == "__main__":
    print("Fetching free subscriptions...")
    os.makedirs(OUTDIR, exist_ok=True)
    
    all_texts = []
    for url in SOURCES:
        print(f"  {url.split('/')[-2]}/{url.split('/')[-1]} ... ", end="")
        text = fetch_and_parse(url)
        if text:
            cnt, ssr, vmess, trojan = count_nodes(text)
            print(f"OK: {cnt} nodes (ssr={ssr}, vmess={vmess}, trojan={trojan})")
            all_texts.append(text)
        else:
            print("FAIL")
    
    if all_texts:
        fname, total = merge_and_save(all_texts)
        print(f"\nMerged: {fname} ({total} nodes total)")
    else:
        print("No subscriptions found")
