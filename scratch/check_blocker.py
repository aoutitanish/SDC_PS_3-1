import urllib.request
import ssl
import json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

resource_id = "9ef74e57-d41d-415f-8056-0502ed3fe763"
api_key = "579b464db66ec23bdd000001cdd3946368f54e197a9229e708f970a5"
url = f"https://api.data.gov.in/resource/{resource_id}?api-key={api_key}&format=json&limit=10"

headers = {'User-Agent': 'Mozilla/5.0'}

print("Testing direct HTTP GET to api.data.gov.in...")
try:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
        print("Success! Status:", resp.status)
        content = resp.read()
        print("Content snippet:", content[:300])
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code} {e.reason}")
    print("Response Body:", e.read().decode('utf-8', errors='ignore'))
except Exception as e:
    print(f"Connection Exception: {e}")
