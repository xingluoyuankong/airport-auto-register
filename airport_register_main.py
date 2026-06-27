#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
机场自动发现 & 批量注册系统 - 主控制器
=========================================
功能:
  1. 发现: 从GitHub/网页/已知源收集可注册的免费机场
  2. 注册: 用Outlook邮箱自动注册V2Board/SSPanel/hidexx等面板
  3. 验证: 自动从Outlook邮箱提取验证码
  4. 提取: 获取订阅链接并保存

使用方法:
  python airport_register_main.py --mode discover    # 发现新机场
  python airport_register_main.py --mode register    # 批量注册
  python airport_register_main.py --mode full        # 发现+注册完整流程

依赖: pip install requests ddddocr playwright
"""

import requests
import random
import string
import threading
import time
import json
import os
import sys
import re
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse, parse_qs

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from outlook_skill import OutlookVerifier, BUILTIN_EMAILS

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ============ 配置 ============
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BASE_DIR, "register_results")
SUBS_DIR = os.path.join(BASE_DIR, "订阅链接")
DISCOVERY_DIR = os.path.join(BASE_DIR, "发现的机场")
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(SUBS_DIR, exist_ok=True)
os.makedirs(DISCOVERY_DIR, exist_ok=True)

# ============ 已知机场库 ============
# 已确认可注册的机场（带免费试用）
KNOWN_AIRPORTS = [
    # V2Board 面板
    {"name": "FSCloud", "url": "https://dash.fscloud.app", "type": "v2board", "trial": "3天试用", "api_path": "/api/v1/passport/auth/register"},
    {"name": "奈云v2ny", "url": "https://www.v2ny.com", "type": "v2board", "trial": "3天5G", "api_path": "/api/v1/passport/auth/register"},
    {"name": "Speedy", "url": "https://cloud.speedypro.xyz", "type": "v2board", "trial": "7天10G", "api_path": "/api/v1/passport/auth/register"},
    {"name": "雨燕云", "url": "https://yuyan.online", "type": "v2board", "trial": "8h 1G", "api_path": "/api/v1/passport/auth/register"},
    {"name": "逗猫", "url": "https://doucat.top", "type": "v2board", "trial": "试用", "api_path": "/api/v1/passport/auth/register"},
    {"name": "泰山Net", "url": "https://www.taishan.pro", "type": "v2board", "trial": "试用", "api_path": "/api/v1/passport/auth/register"},
    {"name": "一元机场", "url": "https://xn--4gq62f52gdss.top", "type": "v2board", "trial": "¥11/年", "api_path": "/api/v1/passport/auth/register"},
    {"name": "魔戒", "url": "https://www.mojie.me", "type": "v2board", "trial": "试用", "api_path": "/api/v1/passport/auth/register"},
    {"name": "狗头加速", "url": "https://lksi.xyz", "type": "v2board", "trial": "试用", "api_path": "/api/v1/passport/auth/register"},
    {"name": "极光加速", "url": "https://jiguang.pro", "type": "v2board", "trial": "2天10G", "api_path": "/api/v1/passport/auth/register"},
    {"name": "besnow", "url": "https://besnow.me", "type": "v2board", "trial": "试用", "api_path": "/api/v1/passport/auth/register"},
    {"name": "tly", "url": "https://tly.one", "type": "v2board", "trial": "签到续", "api_path": "/api/v1/passport/auth/register"},
    
    # SSPanel 面板
    {"name": "69云", "url": "https://69yun69.com", "type": "sspanel", "trial": "签到送流量", "register_path": "/auth/register"},
    {"name": "GLaDOS", "url": "https://glados.rocks", "type": "custom", "trial": "4天+签到续", "register_path": "/landing"},
    
    # hidexx 面板
    {"name": "aiguobit", "url": "https://a.aiguobit.com", "type": "hidexx", "trial": "1天试用", "register_path": "/users/register"},
    {"name": "hidexx", "url": "https://a.hidexx.com", "type": "hidexx", "trial": "1天试用", "register_path": "/users/register"},
]

# 新发现的机场（GateRank + 搜索）
NEWLY_DISCOVERED = [
    {"name": "大象网络", "url": "https://daxiang.pro", "type": "v2board", "trial": "待验证"},
    {"name": "瞬云", "url": "https://shunyun.xyz", "type": "v2board", "trial": "待验证"},
    {"name": "仙路湾", "url": "https://xianluwan.com", "type": "v2board", "trial": "待验证"},
    {"name": "山水云", "url": "https://shanshuiyun.com", "type": "v2board", "trial": "待验证"},
    {"name": "锦云", "url": "https://jinyun.pro", "type": "v2board", "trial": "待验证"},
    {"name": "寰宇云", "url": "https://huanyuyun.com", "type": "v2board", "trial": "待验证"},
    {"name": "秒秒云", "url": "https://miaomiaoyun.com", "type": "v2board", "trial": "待验证"},
    {"name": "稳连云", "url": "https://wenlianyun.com", "type": "v2board", "trial": "待验证"},
    {"name": "宇宙云", "url": "https://yuzhouyun.com", "type": "v2board", "trial": "待验证"},
    {"name": "NOW加速", "url": "https://nowjiasu.com", "type": "v2board", "trial": "待验证"},
    {"name": "NICE加速", "url": "https://nicejiasu.com", "type": "v2board", "trial": "待验证"},
    {"name": "SKYLUMO", "url": "https://skylumo.com", "type": "v2board", "trial": "待验证"},
    {"name": "COCODUCK", "url": "https://cocoduck.com", "type": "v2board", "trial": "待验证"},
    {"name": "大哥云", "url": "https://dageyun.com", "type": "v2board", "trial": "免费试用"},
    {"name": "光年梯", "url": "https://guangnianti.com", "type": "v2board", "trial": "待验证"},
    {"name": "一分机场", "url": "https://1yuan.surf", "type": "v2board", "trial": "免费试用"},
    {"name": "闪狐云", "url": "https://shanhuyun.com", "type": "v2board", "trial": "待验证"},
]

# 新发现的GitHub收集仓库
NEW_REPOS = [
    {"name": "SIQILZ/Free-VPN", "url": "https://github.com/SIQILZ/Free-VPN", "desc": "免费机场公益收集，定时更新"},
    {"name": "maomao533/jc-tizi-tj", "url": "https://github.com/maomao533/jc-tizi-tj", "desc": "2026机场推荐实测"},
    {"name": "Vikutorika/Airports", "url": "https://github.com/Vikutorika/Airports", "desc": "免费订阅+公益节点"},
    {"name": "xiaoji235/airport-free", "url": "https://github.com/xiaoji235/airport-free", "desc": "每3小时自动更新节点"},
    {"name": "ggborr/FREEE-VPN", "url": "https://github.com/ggborr/FREEE-VPN", "desc": "免费VPN节点v2ray/clash"},
    {"name": "dimensionconnex", "url": "https://dimensionconnex.github.io", "desc": "海量免费机场每日更新"},
    {"name": "fastclash", "url": "https://fastclash.github.io", "desc": "免费Clash/V2ray节点订阅"},
    {"name": "clashbest", "url": "https://clashbest.github.io", "desc": "顶级免费Clash节点订阅"},
    {"name": "yoyapai", "url": "https://yoyapai.com", "desc": "2026免费节点每日分享"},
    {"name": "apepine", "url": "https://apepine.com/archives/317", "desc": "免费节点订阅获取教程"},
    {"name": "jiediangou", "url": "https://jiediangou.com/top-node/", "desc": "好用的机场节点推荐"},
    {"name": "jiedianjun", "url": "https://www.jiedianjun.cc/", "desc": "节点君-机场免费试用订阅"},
    {"name": "surfboard.cc", "url": "https://surfboard.cc/free-node/", "desc": "每日免费节点更新"},
    {"name": "freenode.biz", "url": "https://freenode.biz/", "desc": "免费+付费机场自动刷新"},
]

# ============ 工具函数 ============
def ua():
    return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36"

def rand_pwd(length=14):
    return ''.join(random.choices(string.ascii_letters + string.digits + "!@#$%", k=length))

def safe_request(method, url, **kwargs):
    """安全请求，带超时和错误处理"""
    timeout = kwargs.pop("timeout", 15)
    try:
        resp = requests.request(method, url, timeout=timeout, **kwargs)
        return resp
    except requests.exceptions.Timeout:
        return None
    except requests.exceptions.ConnectionError:
        return None
    except Exception as e:
        return None

# ============ 机场发现模块 ============
class AirportDiscoverer:
    """机场发现器 - 从多个来源发现可注册的免费机场"""
    
    def __init__(self):
        self.discovered = []
    
    def probe_v2board_register(self, base_url: str) -> Optional[Dict]:
        """探测V2Board注册API"""
        api_url = f"{base_url.rstrip('/')}/api/v1/passport/auth/register"
        
        # 先用GET探测
        resp = safe_request("GET", api_url, headers={"User-Agent": ua()})
        if resp is None:
            return None
        
        status = resp.status_code
        
        # 尝试POST探测空注册
        payload = {"email": "test@example.com", "password": "test123456"}
        resp2 = safe_request("POST", api_url, json=payload, headers={
            "Content-Type": "application/json",
            "User-Agent": ua(),
        })
        
        result = {
            "url": base_url,
            "api_url": api_url,
            "get_status": status,
            "post_status": resp2.status_code if resp2 else None,
        }
        
        # 分析响应判断是否可注册
        if resp2:
            try:
                data = resp2.json()
                msg = data.get("message", data.get("msg", ""))
                result["message"] = msg[:100]
                
                # 需要邮箱验证码
                if "email" in msg.lower() or "verify" in msg.lower() or "验证" in msg or "code" in msg.lower():
                    result["needs_verification"] = True
                    result["registerable"] = True
                # 需要邀请码
                elif "invite" in msg.lower() or "邀请" in msg:
                    result["needs_invite"] = True
                    result["registerable"] = False
                # 注册关闭
                elif "close" in msg.lower() or "关闭" in msg or "disable" in msg.lower():
                    result["registerable"] = False
                # 可能可以注册
                elif resp2.status_code in [200, 400, 422]:
                    result["registerable"] = True
                else:
                    result["registerable"] = False
            except:
                result["registerable"] = resp2.status_code in [200, 400, 422]
        
        return result if result.get("registerable") else None
    
    def probe_sspanel_register(self, base_url: str) -> Optional[Dict]:
        """探测SSPanel注册页"""
        register_url = f"{base_url.rstrip('/')}/auth/register"
        resp = safe_request("GET", register_url, headers={"User-Agent": ua()})
        if resp is None:
            return None
        
        if resp.status_code == 200:
            html = resp.text.lower()
            has_register = "注册" in html or "register" in html
            
            return {
                "url": base_url,
                "register_url": register_url,
                "type": "sspanel",
                "registerable": has_register,
                "has_captcha": "captcha" in html or "验证码" in html,
            }
        return None
    
    def probe_hidexx_register(self, base_url: str) -> Optional[Dict]:
        """探测hidexx系统注册"""
        register_url = f"{base_url.rstrip('/')}/users/register"
        resp = safe_request("GET", register_url, headers={"User-Agent": ua()})
        if resp is None:
            return None
        
        if resp.status_code == 200 and ("hidexx" in resp.text.lower() or "注册" in resp.text):
            return {
                "url": base_url,
                "register_url": register_url,
                "type": "hidexx",
                "registerable": True,
                "has_captcha": "vcode" in resp.text or "checkcode" in resp.text,
            }
        return None
    
    def discover_from_gaterank(self) -> List[Dict]:
        """从GateRank发现新机场"""
        # GateRank列出了机场名，需要自行拼接常见域名
        gaterank_airports = [
            "daxiang.pro", "nowjiasu.com", "shunyun.xyz", "xianluwan.com",
            "shanshuiyun.com", "nicejiasu.com", "jinyun.pro", "huanyuyun.com",
            "miaomiaoyun.com", "guangnianti.com", "dageyun.com", "cocoduck.com",
            "skylumo.com", "wenlianyun.com", "yuzhouyun.com", "shanhuyun.com",
        ]
        
        results = []
        for domain in gaterank_airports:
            for proto in ["https://", "http://"]:
                url = proto + domain
                result = self.probe_v2board_register(url)
                if result:
                    result["source"] = "gaterank"
                    results.append(result)
                    break
        return results
    
    def discover_all(self) -> List[Dict]:
        """执行全量发现"""
        all_results = []
        
        # 1. 探测已知机场（确认当前状态）
        print("[发现] 探测已知机场...")
        for ap in KNOWN_AIRPORTS:
            if ap["type"] == "v2board":
                result = self.probe_v2board_register(ap["url"])
            elif ap["type"] == "sspanel":
                result = self.probe_sspanel_register(ap["url"])
            elif ap["type"] == "hidexx":
                result = self.probe_hidexx_register(ap["url"])
            else:
                continue
            
            if result:
                result["name"] = ap["name"]
                result["trial"] = ap.get("trial", "")
                result["source"] = "known"
                all_results.append(result)
                print(f"  ✅ {ap['name']}: {ap['trial']}")
            else:
                print(f"  ❌ {ap['name']}: 不可达/不可注册")
        
        # 2. 探测新发现机场
        print("[发现] 探测新机场...")
        for ap in NEWLY_DISCOVERED:
            result = self.probe_v2board_register(ap["url"])
            if result:
                result["name"] = ap["name"]
                result["source"] = "new"
                all_results.append(result)
                print(f"  ✅ {ap['name']}: 可注册")
        
        # 3. GateRank发现
        print("[发现] GateRank探测...")
        gaterank_results = self.discover_from_gaterank()
        all_results.extend(gaterank_results)
        for r in gaterank_results:
            print(f"  ✅ {r.get('url', '')}: 可注册")
        
        self.discovered = all_results
        
        # 保存发现结果
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        fpath = os.path.join(DISCOVERY_DIR, f"discovery_{ts}.json")
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        
        # 汇总
        summary_path = os.path.join(DISCOVERY_DIR, "latest_discovery.md")
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(f"# 机场发现结果 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"共发现 {len(all_results)} 个可注册机场\n\n")
            f.write("| 名称 | URL | 类型 | 试用额度 | 来源 |\n")
            f.write("|------|-----|------|----------|------|\n")
            for r in all_results:
                f.write(f"| {r.get('name', '未知')} | {r.get('url', '')} | {r.get('type', 'v2board')} | {r.get('trial', '待确认')} | {r.get('source', '')} |\n")
        
        print(f"\n[发现] 完成! 共 {len(all_results)} 个可注册机场")
        print(f"[发现] 详细结果: {fpath}")
        
        return all_results


# ============ 注册模块 ============
class AirportRegistrar:
    """机场注册器"""
    
    def __init__(self):
        self.ov = OutlookVerifier()
        self.results_lock = threading.Lock()
        self.results = []
        self.email_index = 0
        self.email_lock = threading.Lock()
    
    def get_next_email(self) -> Optional[Dict]:
        """获取下一个可用邮箱（轮询）"""
        with self.email_lock:
            all_emails = BUILTIN_EMAILS
            if not all_emails:
                return None
            email = all_emails[self.email_index % len(all_emails)]
            self.email_index += 1
            return email
    
    def register_v2board(self, airport: Dict, email_info: Dict) -> Optional[Dict]:
        """V2Board API注册"""
        email = email_info["email"]
        password = email_info["password"]
        
        api_url = airport.get("api_url") or f"{airport['url'].rstrip('/')}/api/v1/passport/auth/register"
        
        payload = {
            "email": email,
            "password": rand_pwd(),
            "email_code": None,
            "invite_code": "",
            "recaptcha_data": "",
        }
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": ua(),
            "Accept": "application/json",
            "Origin": airport["url"],
            "Referer": airport["url"] + "/",
        }
        
        # 步骤1: 发起注册
        resp = safe_request("POST", api_url, json=payload, headers=headers)
        if resp is None:
            return {"error": "连接失败"}
        
        try:
            data = resp.json()
        except:
            data = {"message": resp.text[:200]}
        
        msg = data.get("message", data.get("msg", ""))
        
        # 检查是否需要邮箱验证
        need_verify = any(kw in msg.lower() for kw in 
                         ["email", "verify", "验证", "code", "send", "发送", "邮件"])
        
        if need_verify:
            # 等待验证码
            print(f"  [V2Board] {airport['name']}: 需要邮箱验证，等待验证码...")
            code_result = self.ov.get_code_imap(
                email, password,
                timeout=90,
            )
            
            if code_result.get("success") and code_result.get("code"):
                code = code_result["code"]
                print(f"  [V2Board] {airport['name']}: 获取到验证码 {code}")
                
                # 步骤2: 带验证码重新注册
                payload["email_code"] = code
                resp2 = safe_request("POST", api_url, json=payload, headers=headers)
                
                if resp2 and resp2.status_code == 200:
                    try:
                        data2 = resp2.json()
                        token = data2.get("data", {}).get("token", "")
                        auth_data = data2.get("data", {}).get("auth_data", "")
                        
                        if token:
                            return {
                                "success": True,
                                "airport": airport["name"],
                                "email": email,
                                "password": payload["password"],
                                "token": token,
                                "auth_data": auth_data,
                            }
                    except:
                        pass
            
            return {"error": f"邮箱验证失败: {msg[:100]}"}
        
        # 直接注册成功（少数情况）
        if resp.status_code == 200 and data.get("data", {}).get("token"):
            return {
                "success": True,
                "airport": airport["name"],
                "email": email,
                "password": payload["password"],
                "token": data["data"]["token"],
                "auth_data": data["data"].get("auth_data", ""),
            }
        
        return {"error": msg[:100]}
    
    def get_v2board_subscribe(self, auth_data: str, base_url: str) -> Optional[str]:
        """用auth_data获取V2Board订阅链接"""
        api_url = f"{base_url.rstrip('/')}/api/v1/user/getSubscribe"
        
        headers = {
            "Authorization": auth_data,
            "User-Agent": ua(),
            "Accept": "application/json",
        }
        
        resp = safe_request("GET", api_url, headers=headers)
        if resp and resp.status_code == 200:
            try:
                data = resp.json()
                sub = data.get("data", {})
                return sub.get("subscribe_url", sub.get("url", sub.get("link", "")))
            except:
                pass
        
        # 备用：从用户信息获取
        info_url = f"{base_url.rstrip('/')}/api/v1/user/info"
        resp2 = safe_request("GET", info_url, headers=headers)
        if resp2 and resp2.status_code == 200:
            try:
                data2 = resp2.json()
                sub = data2.get("data", {})
                return sub.get("subscribe_url", "")
            except:
                pass
        
        return None
    
    def register_and_get_sub(self, airport: Dict, thread_id: int = 0) -> Dict:
        """注册机场并获取订阅链接"""
        name = airport.get("name", airport.get("url", "unknown"))
        print(f"[线程{thread_id}] {name} 开始注册...")
        
        email_info = self.get_next_email()
        if not email_info:
            return {"error": "无可用邮箱"}
        
        # 注册
        result = self.register_v2board(airport, email_info)
        
        if result and result.get("success"):
            # 获取订阅链接
            auth = result.get("auth_data", "") or result.get("token", "")
            base_url = airport["url"]
            sub_url = self.get_v2board_subscribe(auth, base_url)
            result["subscribe_url"] = sub_url
            
            if sub_url:
                print(f"[线程{thread_id}] ✅ {name}: {email_info['email'][:20]}... -> {sub_url[:60]}...")
            else:
                print(f"[线程{thread_id}] ⚠️ {name}: 注册成功但无订阅链接")
        else:
            print(f"[线程{thread_id}] ❌ {name}: {result.get('error', '未知错误')}")
        
        # 保存结果
        with self.results_lock:
            self.results.append(result)
        
        return result
    
    def batch_register(self, airports: List[Dict], threads: int = 3, delay: float = 3.0) -> List[Dict]:
        """批量注册"""
        self.results = []
        
        print(f"\n{'='*60}")
        print(f"  批量注册开始: {len(airports)} 个机场, {threads} 线程")
        print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        def worker(thread_id, task_list):
            for i, ap in enumerate(task_list):
                self.register_and_get_sub(ap, thread_id)
                if i < len(task_list) - 1:
                    time.sleep(random.uniform(1, delay))
        
        # 分配任务
        per_thread = len(airports) // threads
        remainder = len(airports) % threads
        
        thread_list = []
        start_idx = 0
        for t in range(threads):
            count = per_thread + (1 if t < remainder else 0)
            tasks = airports[start_idx:start_idx + count]
            start_idx += count
            
            if tasks:
                th = threading.Thread(target=worker, args=(t+1, tasks))
                thread_list.append(th)
                th.start()
        
        for th in thread_list:
            th.join()
        
        # 保存结果
        self.save_results()
        
        return self.results
    
    def save_results(self):
        """保存注册结果"""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON 格式
        json_path = os.path.join(RESULTS_DIR, f"register_{ts}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        # 文本格式（方便查看订阅链接）
        txt_path = os.path.join(RESULTS_DIR, f"register_{ts}.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"# 机场注册结果 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            success_count = sum(1 for r in self.results if r.get("success"))
            f.write(f"成功: {success_count}/{len(self.results)}\n\n")
            
            for r in self.results:
                if r.get("success"):
                    f.write(f"## {r['airport']}\n")
                    f.write(f"邮箱: {r['email']}\n")
                    f.write(f"密码: {r['password']}\n")
                    f.write(f"Token: {r.get('token', '')}\n")
                    f.write(f"订阅: {r.get('subscribe_url', '无')}\n")
                    f.write("\n")
                else:
                    f.write(f"## {r.get('airport', '?')} ❌ {r.get('error', '')}\n\n")
        
        # 订阅链接专用文件
        sub_path = os.path.join(SUBS_DIR, f"subscriptions_{ts}.txt")
        with open(sub_path, "w", encoding="utf-8") as f:
            f.write(f"# 订阅链接 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            for r in self.results:
                if r.get("success") and r.get("subscribe_url"):
                    f.write(f"# {r['airport']} - {r['email'][:20]}...\n")
                    f.write(f"{r['subscribe_url']}\n\n")
        
        print(f"\n[保存] JSON: {json_path}")
        print(f"[保存] 详情: {txt_path}")
        print(f"[保存] 订阅: {sub_path}")


# ============ 新仓库克隆模块 ============
def generate_clone_script(repos: List[Dict]) -> str:
    """生成克隆新仓库的脚本"""
    clone_dir = os.path.join(BASE_DIR, "collected_repos")
    os.makedirs(clone_dir, exist_ok=True)
    
    script_lines = [
        "@echo off",
        "echo 克隆机场收集仓库...",
        f"cd /d \"{clone_dir}\"",
        "",
    ]
    
    for repo in repos:
        url = repo["url"]
        name = repo["name"].split("/")[-1] if "/" in repo["name"] else repo["name"]
        # 从GitHub URL构造克隆地址
        if "github.com" in url:
            clone_url = url if url.endswith(".git") else url + ".git"
            script_lines.append(f"echo 克隆 {name}...")
            script_lines.append(f"git clone {clone_url} 2>nul || echo 已存在: {name}")
        else:
            # 非GitHub仓库，尝试用web_fetch抓取
            script_lines.append(f"echo 跳过非Git仓库: {name} ({url})")
    
    script_lines.append("")
    script_lines.append("echo 完成!")
    script_lines.append("pause")
    
    bat_path = os.path.join(BASE_DIR, "clone_new_repos.bat")
    with open(bat_path, "w", encoding="gbk") as f:
        f.write("\n".join(script_lines))
    
    return bat_path


# ============ 主程序 ============
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="机场自动发现与批量注册系统")
    parser.add_argument("--mode", default="full", choices=["discover", "register", "full", "clone"], 
                       help="discover=仅发现, register=仅注册, full=发现+注册, clone=克隆仓库")
    parser.add_argument("--threads", type=int, default=3, help="注册线程数")
    parser.add_argument("--delay", type=float, default=3.0, help="请求间隔秒")
    
    args = parser.parse_args()
    
    print(f"{'='*60}")
    print(f"  机场自动发现 & 批量注册系统 v2.0")
    print(f"  模式: {args.mode}")
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    if args.mode == "clone":
        # 生成克隆脚本
        bat_path = generate_clone_script(NEW_REPOS)
        print(f"\n[克隆] 脚本已生成: {bat_path}")
        print(f"[克隆] 共 {len(NEW_REPOS)} 个新仓库")
        print("\n新发现的GitHub仓库:")
        for i, repo in enumerate(NEW_REPOS, 1):
            print(f"  {i}. {repo['name']}: {repo['desc']}")
        return
    
    if args.mode in ("discover", "full"):
        # 机场发现
        discoverer = AirportDiscoverer()
        airports = discoverer.discover_all()
        
        if args.mode == "discover":
            return
    
    if args.mode in ("register", "full"):
        # 加载机场列表（优先用已知+已发现的）
        airports = KNOWN_AIRPORTS + NEWLY_DISCOVERED
        # 只保留V2Board类型（API可自动化）
        airports = [ap for ap in airports if ap.get("type") == "v2board"]
        
        # 批量注册
        registrar = AirportRegistrar()
        results = registrar.batch_register(airports, threads=args.threads, delay=args.delay)
        
        # 汇总
        success = [r for r in results if r.get("success")]
        print(f"\n{'='*60}")
        print(f"  注册完成!")
        print(f"  成功: {len(success)}/{len(results)}")
        
        if success:
            print(f"\n成功注册的机场:")
            for r in success:
                sub = r.get("subscribe_url", "无")
                print(f"  ✅ {r['airport']}: {r['email'][:25]}... | 订阅: {sub[:50] if sub else '无'}...")
        
        print(f"{'='*60}")


if __name__ == "__main__":
    main()
