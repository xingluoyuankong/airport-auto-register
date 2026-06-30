#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Outlook验证码专业获取模块 V2 — 精确匹配 + 缓冲等待 + 截图回调 + 重试
=================================================================
机场验证码特征（每机场不同发件人/主题）:
  FLYBIT:  发件人含"FlyBit"或"flybit", 主题含"验证码"或"verification"
  99吧:     发件人含"99ba"或"99吧", 主题含"验证码"
  cd520:    发件人含"cd520"或"cd1314", 主题含"验证码"
  v2ny:     发件人含"v2ny"或"奈云"或"naiun", 主题含"验证码"
  cocoduck: 发件人含"cocoduck", 主题含"验证码"或"verification"

用法:
  from outlook_verify_v2 import OutlookCodeFetcher
  fetcher = OutlookCodeFetcher(email="xxx@outlook.com")
  code = fetcher.fetch(sender_keywords=["FlyBit","flybit"], timeout=90)
"""

import os, re, time, json, requests as req
from datetime import datetime, timezone

TK = r"E:\.Outlook邮箱\批量注册邮箱\已经使用\1"
TOKEN_URL = "https://login.microsoftonline.com/consumers/oauth2/v2.0/token"
GRAPH_MAIL_URL = "https://graph.microsoft.com/v1.0/me/messages"
SCOPE = "offline_access https://graph.microsoft.com/Mail.Read"


class OutlookCodeFetcher:
    """专业的Outlook验证码获取器 V2"""

    def __init__(self, email: str, screenshot_dir: str = None):
        self.email = email
        self.screenshot_dir = screenshot_dir or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "screenshots")
        os.makedirs(self.screenshot_dir, exist_ok=True)
        self.cid, self.rt = self._find_token()
        self.at = None
        self.at_time = 0
        self.send_time = None  # 记录点击"发送"的时间，只取此后的邮件
        self.seen_ids = set()
        self.poll_log = []

    # ───────────────── 内部工具 ─────────────────
    def _find_token(self):
        for f in os.listdir(TK):
            if self.email.lower() in f.lower() and f.endswith("_combo.txt"):
                with open(os.path.join(TK, f), encoding="utf-8") as fh:
                    p = fh.read().strip().split("----")
                    if len(p) >= 4:
                        cid = p[2].strip()
                        # 清理可能的前导-或空格（combo文件格式不一致）
                        cid = cid.lstrip("- ")
                        return cid, p[3]
        return None, None

    def _ensure_token(self):
        """确保有有效的access_token"""
        if not self.cid:
            return False
        now = time.time()
        if self.at and now - self.at_time < 900:  # token有效期15分钟，提前刷新
            return True
        try:
            r = req.post(TOKEN_URL, data={
                "client_id": self.cid,
                "grant_type": "refresh_token",
                "refresh_token": self.rt,
                "scope": SCOPE
            }, timeout=15)
            if r.status_code == 200:
                self.at = r.json().get("access_token", "")
                self.at_time = now
                return bool(self.at)
        except:
            pass
        return False

    def _log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        entry = f"[OV2 {ts}] {msg}"
        print(entry, flush=True)
        self.poll_log.append(entry)

    # ───────────────── 截图回调 ─────────────────
    def mark_send_time(self):
        """标记点击发送按钮的时间，此后只收新邮件"""
        self.send_time = datetime.now(timezone.utc)
        self._log(f"📌 标记发送时间: {self.send_time.strftime('%H:%M:%S')}")

    # ───────────────── 核心：提取验证码 ─────────────────
    def _extract_code(self, text: str, airport: str = "") -> str:
        """从文本中多模式提取验证码"""
        if not text:
            return ""
        src = str(text)
        patterns = [
            # 精确模式：6-8位数字前有验证码相关关键词
            r"(?:[验证检确]码[：:是为\s]*)(\d{4,8})",
            r"(?:code|Code|CODE)\s*(?:is|:|：|=|为)\s*(\d{4,8})",
            r"(?:[验证检测]身份[码代码])\s*[：:]*\s*(\d{4,8})",
            # 通用6位数字
            r"\b(\d{6})\b",
        ]
        for pat in patterns:
            m = re.search(pat, src, re.I)
            if m:
                code = m.group(1)
                # 过滤假码
                if code in ("000000", "111111", "222222", "333333",
                            "444444", "555555", "666666", "777777",
                            "888888", "999999", "123456", "654321",
                            "012345", "098765", "131452"):
                    continue
                if 4 <= len(code) <= 8:
                    return code
        return ""

    def _match_sender(self, sender_name: str, sender_addr: str,
                      subject: str, keywords: list) -> bool:
        """检查发件人/主题是否匹配机场"""
        combined = f"{sender_name} {sender_addr} {subject}".lower()
        for kw in keywords:
            if kw.lower() in combined:
                return True
        return False

    # ───────────────── 主流程：获取验证码 ─────────────────
    def fetch(self, sender_keywords: list = None,
              timeout: int = 90, retries: int = 3) -> str:
        """
        获取验证码主入口

        Args:
            sender_keywords: 发件人关键词列表，如 ["FlyBit","flybit"]
            timeout: 总超时秒数（不包含初始缓冲时间）
            retries: 重新发送重试次数

        Returns:
            验证码字符串，失败返回None
        """
        if not self.cid:
            self._log("❌ 未找到Graph API凭据")
            return None

        sender_keywords = sender_keywords or []

        for attempt in range(1, retries + 1):
            self._log(f"\n{'='*50}")
            self._log(f"第{attempt}/{retries}次尝试获取验证码")
            self._log(f"发送时间: {self.send_time.strftime('%H:%M:%S') if self.send_time else '未标记'}")
            self._log(f"超时限制: {timeout}s")
            self._log(f"发件人过滤: {sender_keywords if sender_keywords else '无(匹配任何)'}")
            self._log(f"{'='*50}")

            code = self._poll_loop(sender_keywords, timeout, attempt)
            if code:
                return code

            if attempt < retries:
                self._log(f"⚠️ 第{attempt}次超时，{3}秒后重试...")
                time.sleep(3)

        self._log("❌ 所有重试均失败")
        return None

    def _poll_loop(self, sender_keywords: list, timeout: int,
                   attempt: int) -> str:
        """轮询循环"""
        deadline = time.time() + timeout
        poll_count = 0
        initial_buffers = [6, 8, 10]  # 每轮尝试不同的初始缓冲
        buffer = initial_buffers[min(attempt - 1, len(initial_buffers) - 1)]

        self._log(f"⏳ 初始缓冲 {buffer}秒 (邮件到达需要时间)...")
        time.sleep(buffer)

        start = time.time()

        while time.time() < deadline:
            poll_count += 1

            if not self._ensure_token():
                time.sleep(2)
                continue

            try:
                # 获取最新邮件 (取15封)
                resp = req.get(
                    f"{GRAPH_MAIL_URL}?$top=15&$orderby=receivedDateTime desc"
                    f"&$select=id,subject,from,bodyPreview,body,receivedDateTime",
                    headers={"Authorization": f"Bearer {self.at}"},
                    timeout=15)

                if resp.status_code != 200:
                    self._log(f"  [poll#{poll_count}] HTTP {resp.status_code}")
                    time.sleep(2)
                    continue

                messages = resp.json().get("value", [])
                elapsed = time.time() - start

                # 每5轮或首次详细日志
                if poll_count <= 3 or poll_count % 5 == 0:
                    new_cnt = sum(1 for m in messages if m.get("id") not in self.seen_ids)
                    self._log(f"  [poll#{poll_count}] {elapsed:.1f}s | "
                              f"共{len(messages)}封邮件, {new_cnt}封新 | "
                              f"摘要: {[m.get('subject','')[:30] for m in messages[:3]]}")

                for msg in messages:
                    mid = msg.get("id", "")
                    if mid in self.seen_ids:
                        continue
                    self.seen_ids.add(mid)

                    subject = msg.get("subject", "") or ""
                    from_info = msg.get("from", {}).get("emailAddress", {})
                    sender_name = from_info.get("name", "")
                    sender_addr = from_info.get("address", "")
                    body_preview = msg.get("bodyPreview", "") or ""
                    body_content = msg.get("body", {}).get("content", "") or ""
                    full_body = f"{body_preview} {body_content}"
                    received_str = msg.get("receivedDateTime", "")

                    # 检查邮件是否在发送时间之后
                    if self.send_time and received_str:
                        try:
                            received_time = datetime.fromisoformat(
                                received_str.replace("Z", "+00:00"))
                            if received_time < self.send_time:
                                continue  # 跳过旧邮件
                        except:
                            pass

                    # 发件人匹配
                    if sender_keywords and not self._match_sender(
                            sender_name, sender_addr, subject, sender_keywords):
                        continue

                    # 提取验证码
                    code = self._extract_code(full_body)
                    if code:
                        elapsed = time.time() - start
                        self._log(f"\n{'─'*40}")
                        self._log(f"✅ [{elapsed:.1f}s] 找到验证码!")
                        self._log(f"   发件人: {sender_name} <{sender_addr}>")
                        self._log(f"   主题: {subject[:80]}")
                        self._log(f"   验证码: {code}")
                        self._log(f"   接收时间: {received_str}")
                        self._log(f"   正文预览: {body_preview[:100]}")
                        self._log(f"{'─'*40}")
                        return code

                time.sleep(2)

            except Exception as e:
                self._log(f"  [poll#{poll_count}] 异常: {e}")
                time.sleep(3)

        return None


# ───────────────── 机场发件人关键词配置 ─────────────────
AIRPORT_SENDERS = {
    "flybit":   ["FlyBit", "flybit", "flybit.vip", "FLYBIT"],
    "99ba":     ["99ba", "99吧", "99ba2026", "99ba公司"],
    "cd520":    ["cd520", "cd1314", "nivpn"],
    "v2ny":     ["v2ny", "奈云", "naiun", "v2ny.com"],
    "cocoduck": ["cocoduck", "COCODUCK"],
}


def get_sender_keywords(airport: str) -> list:
    """根据机场名获取发件人关键词"""
    return AIRPORT_SENDERS.get(airport.lower(), [])


# ───────────────── 快速入口 ─────────────────
def fetch_code(email: str, airport: str, timeout: int = 90,
               retries: int = 3, screenshot_dir: str = None) -> str:
    """
    一站式获取验证码

    Args:
        email: Outlook邮箱
        airport: 机场名 (flybit/99ba/cd520/v2ny/cocoduck)
        timeout: 超时秒数
        retries: 重试次数
        screenshot_dir: 截图目录

    Returns:
        验证码字符串，失败返回None
    """
    fetcher = OutlookCodeFetcher(email=email, screenshot_dir=screenshot_dir)
    keywords = get_sender_keywords(airport)
    return fetcher.fetch(sender_keywords=keywords, timeout=timeout,
                         retries=retries)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("用法: python outlook_verify_v2.py <email> <airport> [timeout]")
        print("  airport: flybit | 99ba | cd520 | v2ny | cocoduck")
        sys.exit(1)

    email = sys.argv[1]
    airport = sys.argv[2]
    timeout = int(sys.argv[3]) if len(sys.argv) > 3 else 90

    code = fetch_code(email, airport, timeout)
    if code:
        print(f"\n✅ 成功获取验证码: {code}")
        sys.exit(0)
    else:
        print(f"\n❌ 获取验证码失败")
        sys.exit(1)
