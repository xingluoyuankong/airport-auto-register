import requests, sys, traceback

try:
    base = 'https://web4.52pokemon.cc'
    token = 'ebc132ec414e9d5d865b14d92173dbc0'
    headers = {'Authorization': token}

    r = requests.get(f'{base}/api/v1/user/info', headers=headers, timeout=10)
    print(f'Status: {r.status_code}')
    print(f'Response: {r.text[:500]}')
except Exception as e:
    traceback.print_exc()
    print(f"Error: {e}", file=sys.stderr)
