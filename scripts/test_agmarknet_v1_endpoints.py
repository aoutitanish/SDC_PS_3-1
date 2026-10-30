import httpx
import json

def test_query_endpoints():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://agmarknet.gov.in",
        "Referer": "https://agmarknet.gov.in/"
    }
    client = httpx.Client(timeout=15.0, headers=headers)

    query_urls = [
        "https://api.agmarknet.gov.in/v1/daily-price-arrival/report?state_id=2&commodity_id=1",
        "https://api.agmarknet.gov.in/v1/prices-and-arrivals/market-report/daily?state_id=2&commodity_id=1",
        "https://api.agmarknet.gov.in/v1/belowmsp-report?state_id=2",
        "https://api.agmarknet.gov.in/v1/price-trend/wholesale-prices-monthly?commodity_id=1&state_id=2",
        "https://api.agmarknet.gov.in/v1/cmdt-below-msp-report?state_id=2"
    ]

    for url in query_urls:
        try:
            r = client.get(url)
            print(f"GET {url[:75]}... -> Status: {r.status_code}")
            if r.status_code == 200:
                print("  SUCCESS! Keys:", list(r.json().keys()) if isinstance(r.json(), dict) else len(r.json()))
                if isinstance(r.json(), dict) and "data" in r.json():
                    print("  Sample data count:", len(r.json()["data"]))
            else:
                print("  Body preview:", r.text[:150])
        except Exception as e:
            print("  Error:", e)

if __name__ == "__main__":
    test_query_endpoints()
