import requests, json

base = 'https://web4.52pokemon.cc'
token = 'ebc132ec414e9d5d865b14d92173dbc0'
headers = {'Authorization': token, 'Content-Type': 'application/json'}

# Try user info
r = requests.get(f'{base}/api/v1/user/info', headers=headers, timeout=10)
print('=== /api/v1/user/info ===')
print(r.text[:3000])

# Try get subscribe
r2 = requests.get(f'{base}/api/v1/user/getSubscribe', headers=headers, timeout=10)
print('\n=== /api/v1/user/getSubscribe ===')
print(r2.text[:3000])

# Try without v1
r3 = requests.get(f'{base}/api/user/info', headers=headers, timeout=10)
print('\n=== /api/user/info ===')
print(r3.text[:3000])
