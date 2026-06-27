# -*- coding: utf-8 -*-
# Zetsal VPN auto register via API - ddddocr + no proxy
import requests
import random
import string
import json
import time
import ddddocr

CAPTCHA_URL = "https://zetsal.com/api/captcha"
REGISTER_URL = "https://zetsal.com/api/register"

# Explicitly disable all proxies
NO_PROXY = {"http": None, "https": None}

ocr = ddddocr.DdddOcr(show_ad=False)

def nanoid(n=10):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=n))

def solve_captcha(session):
    """Get and solve captcha with ddddocr"""
    for attempt in range(10):
        try:
            resp = session.get(CAPTCHA_URL, timeout=15, proxies=NO_PROXY)
            captcha_text = ocr.classification(resp.content)
            if 3 <= len(captcha_text) <= 8:
                return captcha_text
            print(f"  OCR too short/long: '{captcha_text}' ({len(captcha_text)} chars)")
        except Exception as e:
            print(f"  Captcha fetch error: {e}")
    return None

def register():
    username = nanoid(10)
    email = nanoid(8) + "@KiNpNAk4EDbyhp5RPsBxpEisR8.com"
    password = nanoid(16)
    
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })
    
    # Solve captcha
    captcha_text = solve_captcha(session)
    if not captcha_text:
        print("[ERR] Failed to solve captcha")
        return None
    
    print(f"[INFO] User: {username}, Captcha: {captcha_text}")
    
    # Register
    data = {
        "username": username,
        "email": email,
        "password": password,
        "password2": password,
        "captcha": captcha_text
    }
    
    try:
        resp = session.post(REGISTER_URL, data=data, timeout=15, proxies=NO_PROXY)
        result = resp.json()
        
        if result.get('status'):
            with open("zetsal.txt", "a", encoding="utf-8") as f:
                f.write(f"{username}:{password}\n")
            print(f"[OK] {username}:{password}")
            return {"username": username, "password": password}
        else:
            msg = str(result.get('message', ''))
            if 'Captcha' in msg or 'captcha' in msg:
                print(f"[RETRY] Captcha wrong: {captcha_text}")
            else:
                print(f"[FAIL] {msg[:150]}")
            return None
    except Exception as e:
        print(f"[ERR] {e}")
        return None

print("=== Zetsal VPN Auto Register (ddddocr) ===")
success = 0
for i in range(3):
    print(f"\n--- Account {i+1}/3 ---")
    for retry in range(5):
        result = register()
        if result:
            success += 1
            break
        time.sleep(1)
    time.sleep(1)

print(f"\nDone! {success} accounts registered")
