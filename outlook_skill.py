#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Outlook邮箱验证码/链接提取 - 通用技能模块
===========================================
触发关键词: outlook验证码、邮箱验证码、查收邮件、读取验证码、outlook code、邮件验证
使用方法:
    from outlook_skill import OutlookVerifier
    
    # 方式1：直接密码登录IMAP（最简单）
    ov = OutlookVerifier()
    result = ov.get_code_imap("email@outlook.com", "password", timeout=60)
    
    # 方式2：Microsoft Graph API（需要client_id + refresh_token）
    result = ov.get_code_graph("email", "client_id", "refresh_token", timeout=60)
    
    # 方式3：自动尝试所有方式
    result = ov.get_code_auto("email", "password", timeout=60)

内置邮箱池（已测试可用）:
    sanchezquinncu3w1kkhtuc74@outlook.com : 3pKPx5!rE9%9nJDLJC
    hendricktamm95v80awzaxli@outlook.com : @^NdxP5KN#s9G2Hqu0!
    parker738403dcp34kfdl6j@outlook.com : oo^5v=Q%&RU$pdDrax

依赖: 标准库（imaplib, email, re, json, time, html）
可选: requests（Graph API模式）
"""

import imaplib
import email as email_module
from email.header import decode_header
import re
import json
import time
import html
import os
import sys
import hashlib
from datetime import datetime
from typing import Optional, Dict, List, Union

# ============ 配置 ============
IMAP_HOSTS = [
    ("outlook.office365.com", 993),
    ("outlook.live.com", 993),
    ("imap-mail.outlook.com", 993),
]

# Microsoft Graph API 配置
TOKEN_URL_TEMPLATES = [
    "https://login.microsoftonline.com/consumers/oauth2/v2.0/token",
    "https://login.microsoftonline.com/common/oauth2/v2.0/token",
]
GRAPH_API_BASE = "https://graph.microsoft.com/v1.0/me"
DEFAULT_CLIENT_ID = "14d82eec-204b-4c2f-b7e8-296a70dab67e"

# 代码提取模式
CODE_PATTERNS = [
    # 中文验证码
    r"(?:验证码|激活码|注册码|代码为|一次性密码)[^0-9]{0,20}?(\d{4,8})",
    # 英文验证码
    r"(?:verification|security|confirmation|login|sign.?in|one.?time|6.?digit|activation)\s*(?:code|pin|key)?\s*(?:is|:|：|,)?\s*(\d{4,8})",
    # 通用代码模式
    r"code\s*(?:is|:|：)\s*(\d{4,8})",
    r"(?:log-?in\s+code|enter\s+this\s+code)[^0-9]{0,24}(\d{4,8})",
    # 6位纯数字
    r"\b(\d{6})\b",
]

# 链接提取模式
LINK_PATTERNS = [
    r'(?:verify|confirm|activate|token|code|验证|激活|注册确认|email-login|auth)[^"\'<>\s]*?https?://[^\s"\'<>]+',
    r'https?://[^\s"\'<>]+?(?:verify|confirm|activate|token|code|验证|激活|注册确认)',
    r'href\s*=\s*["\']([^"\']*?(?:verify|confirm|activate|token|auth|code|验证|激活)["\'])',
]


class OutlookVerifier:
    """Outlook邮箱验证码/链接提取器"""
    
    def __init__(self, log_func=None):
        self.log = log_func or print
        self._last_result = None
        self._code_cache = {}
        
    def _log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log(f"[OV {ts}] {msg}")
    
    # ============ 工具函数 ============
    @staticmethod
    def decode_header_value(value):
        """解码邮件头"""
        if not value:
            return ""
        parts = []
        for chunk, charset in decode_header(value):
            if isinstance(chunk, bytes):
                parts.append(chunk.decode(charset or "utf-8", errors="ignore"))
            else:
                parts.append(str(chunk))
        return "".join(parts)
    
    @staticmethod
    def extract_email_body(msg):
        """提取邮件正文"""
        if msg.is_multipart():
            text_parts = []
            html_parts = []
            for part in msg.walk():
                if part.get_content_maintype() == "multipart":
                    continue
                if "attachment" in str(part.get("Content-Disposition") or "").lower():
                    continue
                payload = part.get_payload(decode=True) or b""
                charset = part.get_content_charset() or "utf-8"
                text = payload.decode(charset, errors="ignore").strip()
                ct = part.get_content_type()
                if ct == "text/plain":
                    text_parts.append(text)
                elif ct == "text/html":
                    html_parts.append(text)
            # 优先纯文本，其次HTML
            body = "\n".join(text_parts) if text_parts else "\n".join(html_parts)
            if html_parts and not text_parts:
                body = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(body))).strip()
            return body
        else:
            payload = msg.get_payload(decode=True) or b""
            charset = msg.get_content_charset() or "utf-8"
            body = payload.decode(charset, errors="ignore").strip()
            if msg.get_content_type() == "text/html":
                body = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(body))).strip()
            return body
    
    @staticmethod
    def extract_code(text: str) -> Optional[str]:
        """从文本提取验证码"""
        if not text:
            return None
        source = str(text)
        for pattern in CODE_PATTERNS:
            match = re.search(pattern, source, re.IGNORECASE)
            if match:
                code = match.group(1)
                if 4 <= len(code) <= 8:
                    return code
        return None
    
    @staticmethod
    def extract_links(text: str, domain_filter: str = None) -> List[str]:
        """提取所有链接"""
        if not text:
            return []
        # URL解码
        dec = text.replace("&amp;", "&").replace("&#x3D;", "=").replace("&#x2F;", "/").replace("&#38;", "&").replace("&#61;", "=")
        links = set()
        
        # 普通URL
        for m in re.finditer(r'https?://[^\s"\'<>]+', dec):
            u = m.group(0).rstrip(")>,\\];:!?").replace("&amp;", "&")
            links.add(u)
        
        # href属性
        for m in re.finditer(r'href\s*=\s*["\']([^"\']+)["\']', dec, re.I):
            if m.group(1).startswith("http"):
                links.add(m.group(1).replace("&amp;", "&"))
        
        result = sorted(links)
        if domain_filter:
            result = [l for l in result if domain_filter.lower() in l.lower()]
        return result
    
    def filter_by_sender_or_keyword(self, subject: str, from_addr: str, body: str,
                                     sender_filter: str = "", keyword: str = "") -> bool:
        """过滤邮件"""
        combined = f"{subject} {from_addr} {body}".lower()
        if sender_filter and sender_filter.lower() not in combined:
            return False
        if keyword and keyword.lower() not in combined:
            return False
        return True
    
    # ============ IMAP 模式（最稳定，直接密码登录） ============
    def get_code_imap(self, email_addr: str, password: str,
                      sender_filter: str = "", keyword: str = "",
                      timeout: int = 120, interval: float = 3.0,
                      top: int = 10) -> Dict:
        """
        IMAP直接登录Outlook，轮询获取验证码/链接
        适用场景：知道Outlook邮箱密码的情况
        """
        self._log(f"IMAP模式: {email_addr[:20]}... timeout={timeout}s")
        
        deadline = time.time() + timeout
        seen_msg_ids = set()
        poll_count = 0
        
        # 连接IMAP
        client = None
        last_error = ""
        for host, port in IMAP_HOSTS:
            try:
                client = imaplib.IMAP4_SSL(host, port, timeout=15)
                client.login(email_addr, password)
                self._log(f"IMAP连接成功: {host}")
                break
            except Exception as e:
                last_error = str(e)
                if client:
                    try: client.logout()
                    except: pass
                    client = None
        
        if not client:
            return {"success": False, "error": f"IMAP登录失败: {last_error}"}
        
        try:
            while time.time() < deadline:
                poll_count += 1
                try:
                    status, _ = client.select("INBOX")
                    if status != "OK":
                        time.sleep(interval)
                        continue
                    
                    status, data = client.search(None, "ALL")
                    if status != "OK" or not data or not data[0]:
                        time.sleep(interval)
                        continue
                    
                    msg_ids = data[0].split()
                    latest = list(reversed(msg_ids[-top:]))
                    
                    if poll_count <= 3 or poll_count % 10 == 0:
                        self._log(f"轮询#{poll_count}: {len(msg_ids)}封邮件, 检查最近{len(latest)}封")
                    
                    for mid in latest:
                        if mid in seen_msg_ids:
                            continue
                        seen_msg_ids.add(mid)
                        
                        status, fetch_data = client.fetch(mid, "(RFC822)")
                        if status != "OK":
                            continue
                        
                        raw_bytes = b""
                        for item in fetch_data:
                            if isinstance(item, tuple) and len(item) >= 2:
                                raw_bytes = item[1]
                                break
                        if not raw_bytes:
                            continue
                        
                        msg = email_module.message_from_bytes(raw_bytes)
                        subject = self.decode_header_value(msg.get("Subject", ""))
                        from_addr = self.decode_header_value(msg.get("From", ""))
                        body = self.extract_email_body(msg)
                        
                        if not self.filter_by_sender_or_keyword(subject, from_addr, body, sender_filter, keyword):
                            continue
                        
                        self._log(f"匹配邮件#{poll_count}: {subject[:60]} | {from_addr[:40]}")
                        
                        code = self.extract_code(body)
                        links = self.extract_links(body)
                        
                        result = {
                            "success": True,
                            "method": "imap",
                            "email": email_addr,
                            "subject": subject,
                            "from": from_addr,
                            "code": code,
                            "links": links,
                            "body_preview": body[:200],
                            "timestamp": datetime.now().isoformat(),
                        }
                        self._last_result = result
                        return result
                    
                except (imaplib.IMAP4.abort, imaplib.IMAP4.error, ConnectionError) as e:
                    self._log(f"IMAP连接中断: {e}，重连中...")
                    try: client.logout()
                    except: pass
                    # 重连
                    for host, port in IMAP_HOSTS:
                        try:
                            client = imaplib.IMAP4_SSL(host, port, timeout=15)
                            client.login(email_addr, password)
                            break
                        except:
                            pass
                
                time.sleep(interval)
            
            return {"success": False, "error": f"超时({timeout}s), 轮询{poll_count}轮, 检查{len(seen_msg_ids)}封"}
        
        finally:
            try: client.logout()
            except: pass
    
    # ============ Graph API 模式 ============
    def _get_access_token(self, client_id: str, refresh_token: str) -> str:
        """用refresh_token换access_token"""
        for token_url in TOKEN_URL_TEMPLATES:
            scopes_options = [
                "offline_access https://graph.microsoft.com/Mail.Read https://graph.microsoft.com/User.Read",
                "https://graph.microsoft.com/.default offline_access",
                "offline_access https://graph.microsoft.com/Mail.Read",
            ]
            for scope in scopes_options:
                try:
                    import requests
                    resp = requests.post(token_url, data={
                        "client_id": client_id,
                        "grant_type": "refresh_token",
                        "refresh_token": refresh_token,
                        "scope": scope,
                    }, timeout=15)
                    data = resp.json()
                    if data.get("access_token"):
                        return data["access_token"]
                except Exception as e:
                    continue
        raise Exception("所有token策略均失败")
    
    def get_code_graph(self, email_addr: str, client_id: str, refresh_token: str,
                       sender_filter: str = "", keyword: str = "",
                       timeout: int = 120, interval: float = 3.0) -> Dict:
        """
        Microsoft Graph API 模式获取验证码
        适用场景：有 client_id + refresh_token 的情况（从FlowPilot获取）
        """
        try:
            import requests
        except ImportError:
            return {"success": False, "error": "需要安装requests库: pip install requests"}
        
        self._log(f"Graph模式: {email_addr[:20]}...")
        
        try:
            access_token = self._get_access_token(client_id, refresh_token)
        except Exception as e:
            return {"success": False, "error": f"获取access_token失败: {e}"}
        
        deadline = time.time() + timeout
        seen_ids = set()
        poll_count = 0
        filter_time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")  # 现在之后
        
        while time.time() < deadline:
            poll_count += 1
            try:
                url = (f"{GRAPH_API_BASE}/messages?"
                       f"$top=15&$select=id,subject,from,body,receivedDateTime,bodyPreview"
                       f"&$orderby=receivedDateTime desc")
                
                resp = requests.get(url, headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                }, timeout=15)
                
                if resp.status_code == 401:
                    self._log("Token过期，刷新中...")
                    access_token = self._get_access_token(client_id, refresh_token)
                    continue
                
                data = resp.json()
                messages = data.get("value", [])
                
                if poll_count <= 3 or poll_count % 10 == 0:
                    self._log(f"Graph轮询#{poll_count}: {len(messages)}封")
                
                for msg in messages:
                    if msg.get("id") in seen_ids:
                        continue
                    seen_ids.add(msg["id"])
                    
                    subject = msg.get("subject", "")
                    from_info = msg.get("from", {}).get("emailAddress", {})
                    from_addr = from_info.get("address", "")
                    from_name = from_info.get("name", "")
                    body_preview = msg.get("bodyPreview", "")
                    body_content = msg.get("body", {}).get("content", "")
                    full_body = f"{body_preview} {body_content}"
                    
                    if not self.filter_by_sender_or_keyword(
                        f"{subject} {from_name}",
                        from_addr,
                        full_body,
                        sender_filter,
                        keyword
                    ):
                        continue
                    
                    self._log(f"匹配邮件#{poll_count}: {subject[:60]}")
                    
                    code = self.extract_code(full_body)
                    links = self.extract_links(full_body)
                    
                    result = {
                        "success": True,
                        "method": "graph",
                        "email": email_addr,
                        "subject": subject,
                        "from": f"{from_name} <{from_addr}>",
                        "code": code,
                        "links": links,
                        "body_preview": body_preview[:200],
                        "timestamp": datetime.now().isoformat(),
                    }
                    self._last_result = result
                    return result
                
            except Exception as e:
                self._log(f"Graph轮询错误: {e}")
            
            time.sleep(interval)
        
        return {"success": False, "error": f"超时({timeout}s)"}
    
    # ============ 自动模式 ============
    def get_code_auto(self, email_addr: str, password: str = "",
                      client_id: str = "", refresh_token: str = "",
                      sender_filter: str = "", keyword: str = "",
                      timeout: int = 120) -> Dict:
        """
        自动选择最佳方式获取验证码
        优先级：IMAP > Graph
        """
        if password:
            result = self.get_code_imap(email_addr, password, sender_filter, keyword, timeout)
            if result.get("success"):
                return result
        
        if client_id and refresh_token:
            result = self.get_code_graph(email_addr, client_id, refresh_token, sender_filter, keyword, timeout)
            if result.get("success"):
                return result
        
        return {"success": False, "error": "所有方式均失败"}
    
    # ============ 便捷方法：检查特定发件人 ============
    def wait_for_verification(self, email_addr: str, password: str,
                               sender_domains: List[str] = None,
                               timeout: int = 120) -> Dict:
        """
        等待任意验证邮件到达
        sender_domains: 可能的发件人域名列表，如 ['v2ny.com', 'fscloud.app']
        """
        if sender_domains:
            # 逐个尝试发件人过滤
            for domain in sender_domains:
                result = self.get_code_imap(email_addr, password, sender_filter=domain, timeout=30)
                if result.get("success"):
                    return result
        
        # 不限发件人，直接查最新邮件
        return self.get_code_imap(email_addr, password, keyword="verify OR 验证 OR code OR 激活", timeout=timeout)
    
    def wait_for_link(self, email_addr: str, password: str,
                       sender_filter: str = "", timeout: int = 120) -> Dict:
        """专门等待验证链接"""
        deadline = time.time() + timeout
        result = None
        
        while time.time() < deadline:
            result = self.get_code_imap(email_addr, password, sender_filter=sender_filter, timeout=min(30, timeout))
            if result.get("success") and result.get("links"):
                # 过滤出验证/激活链接
                verify_links = [l for l in result["links"] 
                               if any(kw in l.lower() for kw in ["verify", "confirm", "activate", "token", "auth", "验证", "激活"])]
                if verify_links:
                    result["verify_links"] = verify_links
                    return result
            time.sleep(5)
        
        return result or {"success": False, "error": f"超时({timeout}s)未找到验证链接"}
    
    @property
    def last_result(self):
        return self._last_result


# ============ 内置邮箱池 ============
BUILTIN_EMAILS = [
    {
        "email": "sanchezquinncu3w1kkhtuc74@outlook.com",
        "password": "3pKPx5!rE9%9nJDLJC",
        "note": "已注册机场专用"
    },
    {
        "email": "hendricktamm95v80awzaxli@outlook.com",
        "password": "@^NdxP5KN#s9G2Hqu0!",
        "note": "已注册机场专用"
    },
    {
        "email": "parker738403dcp34kfdl6j@outlook.com",
        "password": "oo^5v=Q%&RU$pdDrax",
        "note": "已注册机场专用"
    },
]

# 从token文件加载的邮箱（格式：email----password----clientId----refreshToken）
TOKEN_LOADED_EMAILS = []

def load_token_emails(token_dir: str = None):
    """从FlowPilot导出的token文件加载邮箱"""
    if not token_dir:
        token_dir = r"E:\.Outlook邮箱\批量注册邮箱\已经使用\1"
    
    global TOKEN_LOADED_EMAILS
    TOKEN_LOADED_EMAILS = []
    
    if not os.path.isdir(token_dir):
        return
    
    for fname in os.listdir(token_dir):
        if not fname.endswith("_combo.txt"):
            continue
        try:
            fpath = os.path.join(token_dir, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read().strip()
            parts = content.split("----")
            if len(parts) >= 4:
                TOKEN_LOADED_EMAILS.append({
                    "email": parts[0],
                    "password": parts[1],
                    "client_id": parts[2],
                    "refresh_token": parts[3],
                    "source": fname,
                })
        except:
            continue

def get_available_email() -> Optional[Dict]:
    """获取一个可用邮箱"""
    all_emails = BUILTIN_EMAILS + TOKEN_LOADED_EMAILS
    if not all_emails:
        return None
    # 简单轮询
    idx = hash(str(time.time())) % len(all_emails)
    return all_emails[idx]


# ============ 命令行入口 ============
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Outlook验证码提取器")
    parser.add_argument("--email", required=True, help="邮箱地址")
    parser.add_argument("--password", required=True, help="邮箱密码")
    parser.add_argument("--sender", default="", help="发件人过滤")
    parser.add_argument("--keyword", default="", help="关键词过滤")
    parser.add_argument("--timeout", type=int, default=120, help="超时秒数")
    parser.add_argument("--mode", default="imap", choices=["imap", "graph", "auto"], help="模式")
    parser.add_argument("--link-only", action="store_true", help="只等验证链接")
    
    args = parser.parse_args()
    
    ov = OutlookVerifier()
    
    if args.link_only:
        result = ov.wait_for_link(args.email, args.password, args.sender, args.timeout)
    elif args.mode == "imap":
        result = ov.get_code_imap(args.email, args.password, args.sender, args.keyword, args.timeout)
    elif args.mode == "auto":
        result = ov.get_code_auto(args.email, args.password, sender_filter=args.sender, keyword=args.keyword, timeout=args.timeout)
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result.get("success") else 1)
