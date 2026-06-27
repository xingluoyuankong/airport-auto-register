# -*- coding: utf-8 -*-
import os
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def _parse_accounts(filepath, min_fields=2):
    """通用: 解析账号文件 email | password | ..."""
    accounts = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= min_fields:
                accounts.append(parts)
    return accounts


def _parse_subs_map(filepath):
    """通用: 解析订阅文件，返回 {email: [url, ...]}"""
    subs_map = {}
    current_email = None
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith("#"):
                # 提取 # 后面的内容
                content = line[2:].strip() if line.startswith("# ") else line[1:].strip()
                # 判断是否是邮箱行: 包含 @ 且 @ 后有 .  且不含"密码"等关键词
                if "@" in content and "." in content.split("@")[-1] and "密码" not in content and ":" not in content.split("@")[0]:
                    current_email = content
                continue
            if line.startswith("http") and current_email:
                subs_map.setdefault(current_email, []).append(line)
    return subs_map


def parse_v2register(base_dir):
    """解析 v2register 格式 -> [{email, password, token, jwt, urls}]"""
    accounts = _parse_accounts(os.path.join(base_dir, "accounts.txt"), min_fields=2)
    subs_map = _parse_subs_map(os.path.join(base_dir, "subscriptions.txt"))
    result = []
    for parts in accounts:
        email = parts[0]
        result.append({
            "email": email,
            "password": parts[1],
            "token": parts[2] if len(parts) > 2 else "",
            "jwt": parts[3] if len(parts) > 3 else "",
            "urls": subs_map.get(email, [])
        })
    return result


def parse_hidexx(base_dir):
    """解析 hidexx 格式 -> [{email, password, urls}]"""
    accounts = _parse_accounts(os.path.join(base_dir, "accounts.txt"), min_fields=1)
    subs_map = _parse_subs_map(os.path.join(base_dir, "订阅链接.txt"))
    result = []
    for parts in accounts:
        email = parts[0]
        result.append({
            "email": email,
            "password": parts[1] if len(parts) > 1 else "",
            "urls": subs_map.get(email, [])
        })
    return result


def format_account_v2(acc, index):
    lines = []
    lines.append(f"#{index}. {acc['email']}")
    lines.append(f"   密码: {acc['password']}")
    if acc['token']:
        lines.append(f"   Token: {acc['token']}")
    if acc['jwt']:
        lines.append(f"   JWT: {acc['jwt']}")
    if acc['urls']:
        for url in acc['urls']:
            lines.append(f"   订阅: {url}")
    else:
        lines.append(f"   订阅: 未获取到")
    lines.append("")
    return "\n".join(lines)


def format_account_hidexx(acc, index):
    lines = []
    lines.append(f"#{index}. {acc['email']}")
    lines.append(f"   密码: {acc['password']}")
    if acc['urls']:
        for url in acc['urls']:
            lines.append(f"   订阅: {url}")
    else:
        lines.append(f"   订阅: 未获取到")
    lines.append("")
    return "\n".join(lines)


def write_split_files(accounts, output_dir, formatter, prefix=""):
    os.makedirs(output_dir, exist_ok=True)
    for f in os.listdir(output_dir):
        if f.endswith(".txt") and f[:-4].isdigit():
            os.remove(os.path.join(output_dir, f))
    total = len(accounts)
    if total == 0:
        print(f"  [!] 没有账号数据")
        return
    file_num = 1
    for i in range(0, total, 100):
        chunk = accounts[i:i+100]
        filename = f"{file_num}.txt"
        filepath = os.path.join(output_dir, filename)
        content_lines = []
        content_lines.append(f"{'='*60}")
        content_lines.append(f"  {prefix} 账号与订阅链接 - 第{file_num}批 ({len(chunk)}个)")
        content_lines.append(f"{'='*60}")
        content_lines.append("")
        for j, acc in enumerate(chunk):
            global_idx = i + j + 1
            content_lines.append(formatter(acc, global_idx))
        content_lines.append(f"{'='*60}")
        content_lines.append(f"  共 {len(chunk)} 个账号")
        content_lines.append(f"{'='*60}")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(content_lines))
        print(f"  [OK] {filepath} ({len(chunk)}个账号)")
        file_num += 1


def main():
    print("=" * 50)
    print("  账号订阅链接切分工具 (每100个/文件)")
    print("=" * 50)
    print()

    v2_dir = r"E:\API获取工具\自动集成免费代理服务\01-机场VPN注册机\v2register"
    v2_output = os.path.join(v2_dir, "订阅链接")
    print("[1] 处理 v2register...")
    v2_accounts = parse_v2register(v2_dir)
    # 统计有订阅的
    v2_with_sub = sum(1 for a in v2_accounts if a['urls'])
    print(f"  解析到 {len(v2_accounts)} 个账号 (有订阅: {v2_with_sub})")
    write_split_files(v2_accounts, v2_output, format_account_v2, "v2register")
    print()

    hx_dir = r"E:\API获取工具\自动集成免费代理服务\01-机场VPN注册机\hidexx"
    hx_output = os.path.join(hx_dir, "订阅链接")
    print("[2] 处理 hidexx...")
    hx_accounts = parse_hidexx(hx_dir)
    hx_with_sub = sum(1 for a in hx_accounts if a['urls'])
    print(f"  解析到 {len(hx_accounts)} 个账号 (有订阅: {hx_with_sub})")
    write_split_files(hx_accounts, hx_output, format_account_hidexx, "hidexx")
    print()

    print("=" * 50)
    print("  完成!")
    print("=" * 50)


if __name__ == "__main__":
    main()
