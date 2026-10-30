import urllib.request
import ssl
import json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Content-Type': 'application/json'
}

endpoints = [
    "https://api.agmarknet.gov.in/v1/statewholesalemonthanalysis",
    "https://api.agmarknet.gov.in/v1/monthly-wholesale-prices",
    "https://api.agmarknet.gov.in/v1/get-monthly-data",
    "https://agmarknet.gov.in/api/statewholesalemonthanalysis"
]

print("Testing Agmarknet report backend endpoints...")
for ep in endpoints:
    try:
        req = urllib.request.Request(ep, headers=headers)
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            print(f"{ep} => Status: {resp.status}, Content Length: {len(resp.read())}")
    except urllib.error.HTTPError as e:
        print(f"{ep} => HTTP Error: {e.code} {e.reason}")
    except Exception as e:
        print(f"{ep} => Error: {e}")
