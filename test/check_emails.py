#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests,json,os,io,sys
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')

TOKEN_DIR=r"E:\.Outlook邮箱\批量注册邮箱\已经使用\1"
to_check=["mx9433499602","bushuozaijian2026","landsanchehrqvrw49590ycpji","mxih36u8zfmxj42v75fid"]

for em in to_check:
    for f in os.listdir(TOKEN_DIR):
        fname=f.replace("tokens_","")
        if em.lower() in fname.lower() and f.endswith("_combo.txt"):
            with open(os.path.join(TOKEN_DIR,f)) as fh:
                p=fh.read().strip().split("----")
                if len(p)>=4:
                    try:
                        r=requests.post("https://login.microsoftonline.com/consumers/oauth2/v2.0/token",
                            data={"client_id":p[2],"grant_type":"refresh_token","refresh_token":p[3],
                            "scope":"offline_access https://graph.microsoft.com/Mail.Read"},timeout=15)
                        at=r.json().get("access_token","") if r.status_code==200 else None
                        if at:
                            r2=requests.get("https://graph.microsoft.com/v1.0/me/messages?$top=3&$select=subject,receivedDateTime",
                                headers={"Authorization":f"Bearer {at}"},timeout=10)
                            if r2.status_code==200:
                                msgs=r2.json().get("value",[])
                                print(f'{em}: OK ({len(msgs)} msgs)')
                                for m in msgs:
                                    print(f'  {m["receivedDateTime"]} {m["subject"]}')
                            else:
                                print(f'{em}: graph_err {r2.status_code}')
                        else:
                            print(f'{em}: token_err {r.status_code}')
                    except Exception as e:
                        print(f'{em}: {e}')
