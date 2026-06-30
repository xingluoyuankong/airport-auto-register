import os, json, time, requests, sys, traceback

try:
    TK = r'E:\.Outlook邮箱\批量注册邮箱\已经使用\1'
    email = 'bfloresrsg7qheo5tgr8hhk@outlook.com'
    cid = rt = None
    for f in os.listdir(TK):
        if email.lower() in f.lower() and f.endswith('_combo.txt'):
            with open(os.path.join(TK, f), encoding="utf-8") as fh:
                p = fh.read().strip().split('----')
                if len(p) >= 4:
                    cid, rt = p[2], p[3]
            break
    
    if not cid:
        print("NO TOKEN FOUND")
        sys.exit(1)
    
    print(f"CID={cid[:10]}... RT={rt[:10]}...")
    
    r = requests.post(
        'https://login.microsoftonline.com/consumers/oauth2/v2.0/token',
        data={
            'client_id': cid,
            'grant_type': 'refresh_token',
            'refresh_token': rt,
            'scope': 'offline_access https://graph.microsoft.com/Mail.Read'
        },
        timeout=15
    )
    
    print(f"Token status: {r.status_code}")
    resp = r.json()
    at = resp.get('access_token')
    if not at:
        print(f"Token error: {resp}")
        sys.exit(1)
    
    print(f"Got Access Token: {at[:20]}...")
    
    r2 = requests.get(
        'https://graph.microsoft.com/v1.0/me/messages?$top=8&$orderby=receivedDateTime desc&$select=subject,from,bodyPreview,receivedDateTime',
        headers={'Authorization': f'Bearer {at}'},
        timeout=15
    )
    
    print(f"Mail status: {r2.status_code}")
    msgs = r2.json().get('value', [])
    print(f"Messages count: {len(msgs)}")
    
    for msg in msgs:
        fi = msg.get('from', {}).get('emailAddress', {})
        name = fi.get('name', 'UNKNOWN')
        addr = fi.get('address', 'UNKNOWN')
        print(f"\nFROM: {name} ({addr})")
        print(f"SUBJ: {msg.get('subject', '')}")
        print(f"TIME: {msg.get('receivedDateTime', '')}")
        preview = msg.get('bodyPreview', '')
        print(f"PREV: {preview[:150]}")
        # Check for code
        import re
        codes = re.findall(r'\b(\d{4,8})\b', preview)
        if codes:
            print(f">>> CODES FOUND: {codes}")
        print("---")

except Exception as e:
    print(f"ERROR: {e}")
    traceback.print_exc()
