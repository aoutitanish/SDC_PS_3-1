import sys
import urllib.request
import re
import ssl
import json
import os

sys.stdout.reconfigure(encoding='utf-8')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = 'https://desagri.gov.in/'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

print(f"Fetching {url}...")
try:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
        
    doc_links = re.findall(r'href=["\']([^"\']+\.(?:pdf|csv|xlsx|xls|zip))["\']', html, re.IGNORECASE)
    print(f"Found {len(doc_links)} document links:")
    for link in sorted(list(set(doc_links))):
        print(" -", link)
except Exception as e:
    print(f"Error fetching DES homepage: {e}")

