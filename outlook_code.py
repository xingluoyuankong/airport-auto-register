#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
outlook_code.py — IMAP 密码登录Outlook，提取验证码/链接
用法:
  python3 outlook_code.py <email> <password> [--sender keyword] [--timeout 60]
"""
import imaplib, email, re, sys, json, time, html
from email.header import decode_header

IMAP_HOSTS = [
    ("outlook.office365.com", 993),
    ("outlook.live.com", 993),
]
TIMEOUT = 15

def decode_val(v):
    if not v: return ""
    parts = []
    for chunk, charset in decode_header(v):
        if isinstance(chunk, bytes):
            parts.append(chunk.decode(charset or "utf-8", errors="ignore"))
        else:
            parts.append(str(chunk))
    return "".join(parts)

def extract_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_maintype() == "multipart":
                continue
            if "attachment" in str(part.get("Content-Disposition") or "").lower():
                continue
            payload = part.get_payload(decode=True) or b""
            charset = part.get_content_charset() or "utf-8"
            text = payload.decode(charset, errors="ignore").strip()
            ct = part.get_content_type()
            if ct == "text/plain" and text:
                return text
            if ct == "text/html" and text:
                return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(text))).strip()
        return ""
    payload = msg.get_payload(decode=True) or b""
    charset = msg.get_content_charset() or "utf-8"
    text = payload.decode(charset, errors="ignore").strip()
    if msg.get_content_type() == "text/html":
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(text))).strip()
    return text

def extract_code(text):
    """Extract verification code from text"""
    source = str(text or "")
    patterns = [
        r"(?:verification|security|confirmation|login|sign.?in|验证|激活|注册|一次性|6.?digit)\s*(?:code|码|号)?\s*(?:is|:|：|,)?\s*(\d{4,8})",
        r"(?:代码为|验证码[^0-9]*?)[\s：:]*(\d{4,8})",
        r"(?:log-?in\s+code|enter\s+this\s+code|one\s*time\s*code|security\s+code)[^0-9]{0,24}(\d{4,8})",
        r"code(?:\s+is|[\s:])+(\d{4,8})",
        r"\b(\d{6})\b",
    ]
    for p in patterns:
        m = re.search(p, source, re.IGNORECASE)
        if m:
            code = m.group(1)
            if 4 <= len(code) <= 8:
                return code
    return None

def extract_links(text):
    """Extract all http(s) links from text"""
    dec = text.replace("&amp;","&").replace("&#x3D;","=").replace("&#x2F;","/").replace("&#38;","&").replace("&#61;","=")
    links = set()
    for m in re.finditer(r'https?://[^\s"\'<>]+', dec):
        u = m.group(0).rstrip(")>,\\];:!?").replace("&amp;","&").replace("&#38;","&").replace("&#61;","=").replace("&#x3D;","=")
        links.add(u)
    hrefs = re.findall(r'href\s*=\s*["\']([^"\']+)["\']', dec, re.I)
    for h in hrefs:
        if h.startswith("http"):
            links.add(h.replace("&amp;","&").replace("&#38;","&").replace("&#61;","=").replace("&#x3D;","="))
    return sorted(links)

def fetch_and_extract(email_addr, password, sender_filter="", keyword="", timeout=60, interval=3.0, top=10):
    """Login via IMAP, poll inbox, extract code/link"""
    deadline = time.time() + timeout
    seen = set()
    poll = 0
    
    # Try IMAP hosts
    client = None
    last_err = ""
    for host, port in IMAP_HOSTS:
        try:
            client = imaplib.IMAP4_SSL(host, port, timeout=TIMEOUT)
            client.login(email_addr, password)
            print(f"[IMAP] Connected to {host}", flush=True)
            break
        except Exception as e:
            last_err = str(e)
            if client:
                try: client.logout()
                except: pass
                client = None
    if not client:
        return {"success": False, "error": f"IMAP login failed: {last_err}"}
    
    try:
        while time.time() < deadline:
            poll += 1
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
                
                if poll <= 2 or poll % 10 == 0:
                    print(f"[IMAP] #{poll}: {len(msg_ids)} total, checking last {len(latest)}", flush=True)
                
                for mid in latest:
                    if mid in seen:
                        continue
                    seen.add(mid)
                    
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
                    
                    msg = email.message_from_bytes(raw_bytes)
                    subject = decode_val(msg.get("Subject", ""))
                    from_addr = decode_val(msg.get("From", ""))
                    body = extract_body(msg)
                    combined = f"{subject} {from_addr} {body}"
                    combined_lower = combined.lower()
                    
                    # Filter
                    if sender_filter:
                        if sender_filter.lower() not in from_addr.lower() and sender_filter.lower() not in subject.lower():
                            continue
                    if keyword:
                        if keyword.lower() not in combined_lower:
                            continue
                    
                    print(f"[IMAP] #{poll} Match: {subject[:60]} | {from_addr[:40]}", flush=True)
                    
                    code = extract_code(body)
                    links = extract_links(body)
                    
                    result = {
                        "success": True,
                        "email": email_addr,
                        "subject": subject,
                        "from": from_addr,
                        "code": code,
                        "links": links,
                    }
                    
                    # Send a verification-needed email filter hint
                    print(f"[IMAP] RESULT: {json.dumps({k:v for k,v in result.items() if k not in ('links',)}, ensure_ascii=False)}", flush=True)
                    if links:
                        print(f"[IMAP] links: {json.dumps(links[:5], ensure_ascii=False)}", flush=True)
                    
                    return result
                
            except imaplib.IMAP4.abort:
                print(f"[IMAP] Connection abort, reconnecting...", flush=True)
                try: client.logout()
                except: pass
                # Retry login
                for host, port in IMAP_HOSTS:
                    try:
                        client = imaplib.IMAP4_SSL(host, port, timeout=TIMEOUT)
                        client.login(email_addr, password)
                        break
                    except:
                        pass
            
            time.sleep(interval)
        
        return {"success": False, "error": f"Timeout ({timeout}s), checked {poll} rounds, {len(seen)} msgs"}
    
    finally:
        try: client.logout()
        except: pass


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("email")
    ap.add_argument("password")
    ap.add_argument("--sender", default="")
    ap.add_argument("--keyword", default="")
    ap.add_argument("--timeout", type=int, default=60)
    ap.add_argument("--interval", type=float, default=3.0)
    ap.add_argument("--top", type=int, default=10)
    args = ap.parse_args()
    
    result = fetch_and_extract(
        args.email, args.password,
        sender_filter=args.sender,
        keyword=args.keyword,
        timeout=args.timeout,
        interval=args.interval,
        top=args.top,
    )
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0 if result.get("success") else 1)
