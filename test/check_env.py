#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量重跑6个已跑通机场 — 带代理环境 + Graph API 验证码
先验证: v2ny→FLYBIT→99ba→COCODUCK
"""
import sys, os, io, json, time, re
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7897'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7897'
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 找可用token
TD = r"E:\.Outlook邮箱\批量注册邮箱\已经使用\1"
def find_token(email):
    for f in os.listdir(TD):
        if email.lower() in f.lower() and f.endswith("_combo.txt"):
            with open(os.path.join(TD, f), encoding="utf-8") as fh:
                p = fh.read().strip().split("----")
                if len(p) >= 4:
                    return {"email": p[0], "password": p[1], "clientId": p[2], "refreshToken": p[3]}
    return None

# 找所有可用token
tokens = []
for f in os.listdir(TD):
    if f.endswith("_combo.txt"):
        with open(os.path.join(TD, f), encoding="utf-8") as fh:
            p = fh.read().strip().split("----")
            if len(p) >= 4:
                tokens.append({"email": p[0], "password": p[1], "clientId": p[2], "refreshToken": p[3]})

print(f"共 {len(tokens)} 个可用token")
for t in tokens:
    print(f"  {t['email'][:40]}")

# 测试Graph API连接
import requests as req
test_tk = tokens[0]
print(f"\n测试Graph API: {test_tk['email'][:30]}...")
try:
    r = req.post("https://login.microsoftonline.com/consumers/oauth2/v2.0/token",
        data={"client_id": test_tk["clientId"], "grant_type": "refresh_token",
              "refresh_token": test_tk["refreshToken"],
              "scope": "offline_access https://graph.microsoft.com/Mail.Read"},
        timeout=20)
    print(f"  Token请求: {r.status_code}")
    if r.status_code == 200:
        at = r.json().get("access_token", "")
        print(f"  ✅ Graph API正常! AT长度={len(at)}")
    else:
        print(f"  ❌ {r.text[:200]}")
except Exception as e:
    print(f"  ❌ 连接失败: {e}")

print("\n✅ 代理检测完成")
