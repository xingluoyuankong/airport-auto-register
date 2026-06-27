"""从aiguobit公共SSR节点生成可用Clash订阅"""
import base64, json

# aiguobit公共免费SSR节点（来自 tutorial/trial_port）
NODES = [
    {"server": "159.89.223.112", "port": 8088, "password": "de7558", "method": "aes-256-cfb", "protocol": "origin", "obfs": "http_simple", "obfs_param": "bing.com", "name": "倚天剑-新加坡-01"},
    {"server": "159.89.223.112", "port": 8088, "password": "4d79fb", "method": "aes-256-cfb", "protocol": "origin", "obfs": "http_simple", "obfs_param": "bing.com", "name": "倚天剑-新加坡-02"},
    {"server": "159.89.223.112", "port": 8088, "password": "2170f8", "method": "aes-256-cfb", "protocol": "origin", "obfs": "http_simple", "obfs_param": "bing.com", "name": "倚天剑-新加坡-03"},
]

# 生成Clash YAML格式
yaml_lines = [
    "proxies:",
]

for n in NODES:
    yaml_lines.append(f"  - name: \"{n['name']}\"")
    yaml_lines.append(f"    type: ssr")
    yaml_lines.append(f"    server: {n['server']}")
    yaml_lines.append(f"    port: {n['port']}")
    yaml_lines.append(f"    password: \"{n['password']}\"")
    yaml_lines.append(f"    cipher: {n['method']}")
    yaml_lines.append(f"    protocol: {n['protocol']}")
    yaml_lines.append(f"    obfs: {n['obfs']}")
    yaml_lines.append(f"    obfs-param: {n['obfs_param']}")

yaml_lines.append("")
yaml_lines.append("proxy-groups:")
yaml_lines.append("  - name: Proxy")
yaml_lines.append("    type: select")
yaml_lines.append("    proxies:")
for n in NODES:
    yaml_lines.append(f"      - \"{n['name']}\"")

yaml_content = "\n".join(yaml_lines)

# Base64编码为订阅格式
sub_b64 = base64.b64encode(yaml_content.encode()).decode()

# 保存文件
out_path = r"E:\API获取工具\自动集成免费代理服务\01-机场VPN注册机\register_results\working_sub_aiguobit.yaml"
with open(out_path, "w", encoding="utf-8") as f:
    f.write(yaml_content)

print(f"Clash YAML saved: {out_path}")
print(f"\n订阅链接 (base64):")
print(f"https://example.com/sub?data={sub_b64[:50]}...")
print(f"\n可直接导入Clash的YAML内容:")
print(yaml_content)
print(f"\n节点数: {len(NODES)}")
print("服务器: 159.89.223.112:8088 (新加坡)")
