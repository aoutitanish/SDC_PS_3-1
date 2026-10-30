import httpx
import re

def find_routes():
    headers = {"User-Agent": "Mozilla/5.0"}
    client = httpx.Client(timeout=20.0, headers=headers)
    r = client.get("https://agmarknet.gov.in/static/js/main.5e8d1f58.js")
    js_text = r.text
    
    # Search for occurrences of api.agmarknet.gov.in
    indices = [m.start() for m in re.finditer(r'api\.agmarknet\.gov\.in', js_text)]
    print(f"Found {len(indices)} occurrences of api.agmarknet.gov.in:")
    for idx in indices[:10]:
        snippet = js_text[max(0, idx-50):min(len(js_text), idx+150)]
        print("--- Snippet ---")
        print(snippet)

if __name__ == "__main__":
    find_routes()
