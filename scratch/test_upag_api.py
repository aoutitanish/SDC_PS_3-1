import urllib.request
import ssl
import json
import os

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

upag_urls = [
    "https://upag.gov.in/api/v1/prices",
    "https://upag.gov.in/api/mandi-prices",
    "https://upag.gov.in/api/v1/mandi/prices",
    "https://upag.gov.in/static/js/main-7c00ec34.5e795c1d.js"
]

print("Testing UPAg portal endpoints...")
for u in upag_urls:
    try:
        req = urllib.request.Request(u, headers=headers)
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            print(f"{u} => Status: {resp.status}, Content-Length: {len(resp.read())}")
    except urllib.error.HTTPError as e:
        print(f"{u} => HTTP Error: {e.code}")
    except Exception as e:
        print(f"{u} => Error: {e}")
