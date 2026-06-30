#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests,base64,urllib3
urllib3.disable_warnings()

subs={
    'v2ny_new':'https://c0d97821eafa5.nydy.cc/sleep/96c0e07c0c503cb31c949c34e1705c8c',
    'v2ny_old1':'https://c0d97821eafa5.nydy.cc/sleep/35348eeac78327d3215b48e4a8075dfc',
    'v2ny_old2':'https://c0d97821eafa5.nydy.cc/sleep/80e835e3615e3482df0ebeae5454b278',
    'FLYBIT_new':'https://s.fb.22na.cn/api/v1/ss/9728287fbc6d93ba75fcbe668bac0056',
    'FLYBIT_old':'https://s.fb.22na.cn/api/v1/ss/b863fc913dd8c330db22aa5bf5293816',
    '99ba_new':'https://ycexbktkoctx.sealosgzg.site/api/sub/27402f01d057a6bea4f8cef3fca2fa0e',
    '99ba_old':'https://ycexbktkoctx.sealosgzg.site/api/sub/4927953a89eed51ba3ee3f01b3b29223',
    'COCODUCK':'https://sub.cocoduck.cc/sub/037e8dd1f3c566ee/clash',
    'cd520':'https://cdc502.online/api/v1/client/subscribe?token=344152b3febea62d68208b5696615036',
}
proxies={'http':'http://127.0.0.1:7897','https':'http://127.0.0.1:7897'}

for name,url in subs.items():
    try:
        r=requests.get(url,timeout=15,proxies=proxies,verify=False)
        ok=200<=r.status_code<300 and len(r.text)>20
        nodes='?'
        try:
            text=base64.b64decode(r.text.strip()).decode('utf-8')
            nodes=len([l for l in text.split('\n') if l.strip() and not l.startswith('#')])
        except: pass
        status='OK' if ok else 'DEAD'
        print(f'[{status}] {name}: nodes={nodes} len={len(r.text)}')
    except Exception as e:
        print(f'[DEAD] {name}: {e}')
