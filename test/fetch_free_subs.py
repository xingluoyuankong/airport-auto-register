import requests, base64, re, json, os

sources = [
    "https://raw.githubusercontent.com/xiaoji235/airport-free/main/clash.yaml",
    "https://raw.githubusercontent.com/SIQILZ/Free-VPN/main/clash.yaml",
    "https://raw.githubusercontent.com/ggborr/FREEE-VPN/main/clash.yaml",
    "https://raw.githubusercontent.com/Vikutorika/Airports/main/clash.yaml",
]

out_dir = os.path.join(os.path.dirname(__file__), "..", "register_results")
os.makedirs(out_dir, exist_ok=True)

all_proxies = []

for url in sources:
    try:
        print(f"Trying: {url}")
        r = requests.get(url, timeout=20, headers={"User-Agent": "ClashMeta/1.0"})
        if r.status_code != 200:
            print(f"  Failed: {r.status_code}")
            continue
        
        text = r.text
        
        # Try base64 decode
        try:
            text = base64.b64decode(text).decode("utf-8")
        except:
            pass
        
        # Count nodes
        proxy_count = text.count("  - name:")
        ssr_count = len(re.findall(r"type:\s*ssr", text))
        vmess_count = len(re.findall(r"type:\s*vmess", text))
        trojan_count = len(re.findall(r"type:\s*trojan", text))
        
        print(f"  OK: {proxy_count} proxies (ssr={ssr_count}, vmess={vmess_count}, trojan={trojan_count})")
        
        if proxy_count > 0:
            fname = os.path.join(out_dir, f"free_sub_{url.split('/')[-2]}_{url.split('/')[-1]}")
            with open(fname, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"  Saved: {fname}")
            all_proxies.append({"source": url, "count": proxy_count, "file": fname})
            
    except Exception as e:
        print(f"  Error: {e}")

print(f"\n=== TOTAL: {len(all_proxies)} working sources ===")
for p in all_proxies:
    print(f"  {p['source']}: {p['count']} nodes")
