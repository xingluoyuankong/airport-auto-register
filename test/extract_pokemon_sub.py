"""透过playwright-cli状态文件提取宝可梦订阅链接"""
import subprocess, json, yaml, os, re, glob

CLI_DIR = r"E:\API获取工具\.playwright-cli"

# 1. 找到最新的page snapshot yml文件
snapshots = sorted(glob.glob(os.path.join(CLI_DIR, "page-*.yml")), reverse=True)
latest = snapshots[0] if snapshots else None
if not latest:
    print("No snapshot found")
    exit()

print(f"Reading: {latest}")
with open(latest, encoding='utf-8') as f:
    data = yaml.safe_load(f)

# 2. 搜索订阅链接
def search_dict(d, results, path=""):
    if isinstance(d, dict):
        for k, v in d.items():
            p = f"{path}.{k}" if path else k
            search_dict(v, results, p)
    elif isinstance(d, list):
        for i, v in enumerate(d):
            p = f"{path}[{i}]"
            search_dict(v, results, p)
    elif isinstance(d, str):
        if "subscribe" in d.lower() or "sub?" in d.lower() or "api/v1/" in d.lower():
            results.append((path, d))

results = []
search_dict(data, results)
for path, val in results:
    print(f"\n[{path}] = {val}")

# 3. 如果快照里没有，尝试在HTML里搜
html_files = sorted(glob.glob(os.path.join(CLI_DIR, "page-*.html")), reverse=True)
if not html_files:
    print("\nNo HTML files found, checking console logs...")
    console_files = sorted(glob.glob(os.path.join(CLI_DIR, "console-*.log")), reverse=True)
    for cf in console_files[:3]:
        print(f"\n--- {cf} ---")
        with open(cf, encoding='utf-8', errors='replace') as f:
            content = f.read()
        urls = re.findall(r'https?://[^\s"\'<>]+', content)
        for u in urls:
            if 'subscribe' in u or 'sub?' in u:
                print(f"  SUB URL: {u}")
