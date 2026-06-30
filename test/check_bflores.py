#!/usr/bin/env python3
"""Check bflores inbox for v2ny verification code"""
import os, json, requests as req
os.environ['HTTP_PROXY']='http://127.0.0.1:7897'
os.environ['HTTPS_PROXY']='http://127.0.0.1:7897'

TK = r'E:\.Outlook邮箱\批量注册邮箱\已经使用\1'
for f in os.listdir(TK):
    if 'bflores' in f.lower() and f.endswith('_combo.txt'):
        with open(os.path.join(TK,f),encoding='utf-8') as fh:
            p = fh.read().strip().split('----')
            client_id, rt = p[2], p[3]
        
        r = req.post('https://login.microsoftonline.com/consumers/oauth2/v2.0/token',
            data={'client_id':client_id,'grant_type':'refresh_token','refresh_token':rt,
                  'scope':'offline_access https://graph.microsoft.com/Mail.Read'}, timeout=20)
        at = r.json().get('access_token','')
        
        resp = req.get('https://graph.microsoft.com/v1.0/me/messages?$top=20&$orderby=receivedDateTime desc&$select=subject,from,receivedDateTime,bodyPreview',
            headers={'Authorization': f'Bearer {at}'}, timeout=15)
        msgs = resp.json().get('value',[])
        print(f'Total {len(msgs)} msgs:')
        for m in msgs[:15]:
            fr_addr = (m.get('from') or {}).get('emailAddress') or {}
            fr = fr_addr.get('name','?') + ' <' + fr_addr.get('address','?') + '>'
            subj = (m.get('subject') or '')[:60]
            dt = (m.get('receivedDateTime') or '')[:19]
            preview = (m.get('bodyPreview') or '')[:100]
            print(f'  [{dt}] {fr} | {subj}')
            print(f'         preview: {preview}')
