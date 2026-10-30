import httpx
import json

def test_v1_api():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://agmarknet.gov.in",
        "Referer": "https://agmarknet.gov.in/"
    }
    client = httpx.Client(timeout=15.0, headers=headers)
    
    # 1. Inspect commodities response
    r = client.get("https://api.agmarknet.gov.in/v1/commodities")
    if r.status_code == 200:
        data = r.json()
        print("Commodities total count:", data.get("pagination"))
        sample_comm = data.get("data", [])[:5]
        print("Sample commodities:", sample_comm)

    # 2. Test common REST endpoints in Agmarknet 2.0 API
    candidate_endpoints = [
        "https://api.agmarknet.gov.in/v1/commodity-prices",
        "https://api.agmarknet.gov.in/v1/price-arrival",
        "https://api.agmarknet.gov.in/v1/price-arrivals",
        "https://api.agmarknet.gov.in/v1/market-prices",
        "https://api.agmarknet.gov.in/v1/mandis",
        "https://api.agmarknet.gov.in/v1/district",
        "https://api.agmarknet.gov.in/v1/state",
        "https://api.agmarknet.gov.in/v1/today-prices",
        "https://api.agmarknet.gov.in/v1/daily-report"
    ]

    for ep in candidate_endpoints:
        try:
            resp = client.get(ep)
            print(f"Endpoint: {ep} -> Status: {resp.status_code}")
            if resp.status_code == 200:
                print("  Success JSON keys:", list(resp.json().keys()))
        except Exception as e:
            print(f"Error {ep}: {e}")

if __name__ == "__main__":
    test_v1_api()
