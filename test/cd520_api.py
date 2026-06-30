#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests,urllib3,json
urllib3.disable_warnings()
proxies={'http':'http://127.0.0.1:7897','https':'http://127.0.0.1:7897'}

# Test cd520 new domain
for url in ['https://www.cd520.xyz/api/v1/client/subscribe?token=344152b3febea62d68208b5696615036',
           'https://cd520.xyz/api/v1/client/subscribe?token=344152b3febea62d68208b5696615036']:
    try:
        r=requests.get(url,timeout=15,proxies=proxies,verify=False)
        host=url.split("/")[2]
        print(f'{host}: {r.status_code} len={len(r.text)} preview={r.text[:120]}')
    except Exception as e:
        print(f'{url.split("/")[2]}: {e}')

# Login API + get subscription
try:
    r=requests.post('https://cd520.xyz/api/v1/passport/auth/login',
        json={'email':'hendricktamm95v80awzaxli@outlook.com','password':'VpnTest2026!'},
        timeout=15,proxies=proxies,verify=False)
    print(f'LOGIN: {r.status_code} resp={r.text[:300]}')
    d=json.loads(r.text)
    token=d.get('data',{}).get('auth_data','') or d.get('data',{}).get('token','')
    if token:
        r2=requests.get('https://cd520.xyz/api/v1/user/getSubscribe',
            headers={'Authorization':token},timeout=15,proxies=proxies,verify=False)
        print(f'SUB: {r2.status_code} resp={r2.text[:300]}')
except Exception as e:
    print(f'LOGIN_ERR: {e}')
