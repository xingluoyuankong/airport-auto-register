import imaplib
c = imaplib.IMAP4_SSL('outlook.office365.com', 993, timeout=15)
try:
    c.login('sanchezquinncu3w1kkhtuc74@outlook.com', '3pKPx5!rE9%9nJDLJC')
    print('LOGIN: OK')
    s, d = c.select('INBOX')
    print(f'SELECT: {s}')
    s, d = c.search(None, 'ALL')
    ids = d[0].split() if d[0] else []
    print(f'TOTAL: {len(ids)}')
    if len(ids) > 0:
        s, d = c.fetch(ids[-1], '(BODY[HEADER.FIELDS (SUBJECT FROM DATE)])')
        print(f'LATEST: {d[0][1][:200]}')
    c.logout()
except Exception as e:
    print(f'ERR: {e}')
