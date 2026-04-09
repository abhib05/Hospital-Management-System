import urllib.request
import json
import ssl

req = urllib.request.Request(
    'http://localhost:8000/api/auth/login', 
    data=json.dumps({"username": "admin", "password": "Password123!"}).encode('utf-8'), 
    headers={'Content-Type': 'application/json'}
)
try:
    with urllib.request.urlopen(req) as response:
        print("SUCCESS:", response.read().decode())
except urllib.error.HTTPError as e:
    print(json.loads(e.read().decode())["detail"])
