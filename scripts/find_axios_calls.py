import httpx
import re

def find_axios_calls():
    headers = {"User-Agent": "Mozilla/5.0"}
    client = httpx.Client(timeout=20.0, headers=headers)
    r = client.get("https://agmarknet.gov.in/static/js/main.5e8d1f58.js")
    js_text = r.text
    
    # Find all .get("...") and .post("...") calls
    calls = re.findall(r'\.(get|post|put)\(["\']([a-zA-Z0-9_\-\?/&=]+)["\']', js_text)
    print(f"Found {len(calls)} API endpoint calls in JS:")
    unique_endpoints = sorted(list(set([path for method, path in calls])))
    for path in unique_endpoints:
        print(f"  -> {path}")

if __name__ == "__main__":
    find_axios_calls()
