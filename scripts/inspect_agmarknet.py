import httpx
import re

def inspect():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    client = httpx.Client(timeout=20.0, headers=headers, follow_redirects=True)
    r = client.get("https://agmarknet.gov.in/")
    print("Main Page HTML length:", len(r.text))
    
    # Extract script src tags
    scripts = re.findall(r'src="([^"]+)"', r.text)
    print("Found script tags:", scripts)

    for script_path in scripts:
        if script_path.startswith('/'):
            script_url = "https://agmarknet.gov.in" + script_path
        else:
            script_url = script_path
        
        print(f"\nFetching script: {script_url}")
        try:
            sr = client.get(script_url)
            print("  Status:", sr.status_code, "Length:", len(sr.text))
            # Search for API endpoints in JS code
            api_matches = re.findall(r'https?://[^\s"\']+', sr.text)
            api_filtered = [url for url in api_matches if 'api' in url.lower() or 'agmarknet' in url.lower() or 'data' in url.lower()]
            print("  API URLs found in script:", api_filtered[:10])
        except Exception as e:
            print("  Error fetching script:", e)

if __name__ == "__main__":
    inspect()
