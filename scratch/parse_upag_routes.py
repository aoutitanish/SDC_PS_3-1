import urllib.request
import ssl
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

# Main JS bundles on UPAg
js_files = [
    "https://upag.gov.in/static/js/main-7c00ec34.5e795c1d.js",
    "https://upag.gov.in/static/js/vendors-1a3e72dd.dd946400.js",
    "https://upag.gov.in/static/js/vendors-343d68cf.f4ed646c.js"
]

print("Parsing UPAg JS bundles for API endpoints...")
for js_url in js_files:
    try:
        req = urllib.request.Request(js_url, headers=headers)
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            content = resp.read().decode('utf-8', errors='ignore')
            apis = re.findall(r'["\'](/api/[^"\']+)["\']', content)
            urls = re.findall(r'["\'](https?://[^"\']+)["\']', content)
            print(f"\n--- {js_url} ---")
            print("API routes found:", set(apis))
            backend_urls = [u for u in set(urls) if 'gov.in' in u or 'api' in u or 'backend' in u]
            print("Backend URLs found:", backend_urls[:10])
    except Exception as e:
        print(f"Error parsing {js_url}: {e}")
