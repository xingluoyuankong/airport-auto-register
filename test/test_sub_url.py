"""测试宝可梦机场订阅链接是否有效"""
import requests, base64, json

SUB_URL = "https://jkun.waimaosass.icu/api/v1/client/subscribe?token=ebc132ec414e9d5d865b14d92173dbc0"

print(f"Testing: {SUB_URL}")
print()

try:
    r = requests.get(SUB_URL, headers={"User-Agent": "ClashMeta/1.0"}, timeout=30)
    print(f"Status: {r.status_code}")
    print(f"Content-Type: {r.headers.get('Content-Type', 'unknown')}")
    print(f"Content-Length: {len(r.content)} bytes")
    print()

    content = r.text

    # 尝试base64解码
    try:
        decoded = base64.b64decode(content).decode('utf-8', errors='replace')
        print(f"Base64 decoded ({len(decoded)} chars):")
        lines = decoded.strip().split('\n')
        print(f"  Total lines: {len(lines)}")
        
        # 分析节点类型
        types = {}
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('//'):
                if line and (line.startswith('#') or line.startswith('//')):
                    print(f"  [Header] {line[:120]}")
                continue
            proto = line.split('://')[0] if '://' in line else 'unknown'
            types[proto] = types.get(proto, 0) + 1
        
        print(f"\n  Node types: {json.dumps(types, indent=2)}")
        
        # 打印前5个节点
        node_lines = [l for l in lines if l.strip() and not l.startswith('#') and not l.startswith('//')]
        print(f"\n  First 5 nodes:")
        for nl in node_lines[:5]:
            print(f"    {nl[:150]}")
            
    except Exception as e:
        print(f"Base64 decode failed: {e}")
        print(f"Raw content (first 500 chars): {content[:500]}")
        
except Exception as e:
    print(f"Request failed: {e}")
