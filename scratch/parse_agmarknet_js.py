import urllib.request
import ssl
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
url = "https://agmarknet.gov.in/static/js/main.5e8d1f58.js"

print(f"Fetching {url}...")
try:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
        content = resp.read().decode('utf-8', errors='ignore')
        
        # Search for API endpoints
        v1_endpoints = re.findall(r'/v1/[a-zA-Z0-9_\-/]+', content)
        print("Agmarknet /v1/ API endpoints found:")
        for ep in sorted(list(set(v1_endpoints))):
            print(" -", ep)


        # Search for report routes or keywords
        report_routes = re.findall(r'path:\s*["\']([^"\']+)["\']', content)
        print("\nReport routes found:", sorted(list(set(report_routes)))[:15])

except Exception as e:
    print("Error:", e)
