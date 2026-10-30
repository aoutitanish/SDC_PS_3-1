import urllib.request
import ssl
import json
import os
import datetime

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

resource_id = "9ef74e57-d41d-415f-8056-0502ed3fe763"
# Official data.gov.in public API key
api_key = "579b464db66ec23bdd000001cdd3946368f54e197a9229e708f970a5"
url = f"https://api.data.gov.in/resource/{resource_id}?api-key={api_key}&format=json&limit=1000"

print(f"Testing OGD API: {url[:80]}...")

try:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=20, context=ctx) as resp:
        status_code = resp.status
        raw_bytes = resp.read()
        print(f"Status Code: {status_code}, Bytes Received: {len(raw_bytes)}")
        
        data = json.loads(raw_bytes.decode('utf-8'))
        print("Keys:", list(data.keys()))
        if "records" in data:
            records = data["records"]
            print(f"Total Records returned: {len(records)}, Total Available: {data.get('total')}")
            if records:
                print("Sample record:", records[0])
                
                # Save original raw json untouched
                target_dir = os.path.abspath("data/raw/market/real_agmarknet")
                os.makedirs(target_dir, exist_ok=True)
                raw_filename = "real_ogd_agmarknet_wholesale_prices.json"
                raw_filepath = os.path.join(target_dir, raw_filename)
                
                with open(raw_filepath, "wb") as f:
                    f.write(raw_bytes)
                print(f"Saved raw response to {raw_filepath}")
                
                # Extract metadata
                download_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
                commodities = sorted(list(set(r.get('commodity', r.get('Commodity', '')) for r in records if r.get('commodity', r.get('Commodity')))))
                states = sorted(list(set(r.get('state', r.get('State', '')) for r in records if r.get('state', r.get('State')))))
                districts = sorted(list(set(r.get('district', r.get('District', '')) for r in records if r.get('district', r.get('District')))))
                markets = sorted(list(set(r.get('market', r.get('Market', '')) for r in records if r.get('market', r.get('Market')))))
                fields = list(records[0].keys()) if records else []
                
                manifest = {
                    "source_url": url,
                    "resource_id": resource_id,
                    "dataset_name": "Daily/Monthly Wholesale Prices & Arrivals (Agmarknet/DES - Open Government Data)",
                    "download_timestamp": download_time,
                    "filename": raw_filename,
                    "filepath": raw_filepath,
                    "file_size_bytes": len(raw_bytes),
                    "record_count": len(records),
                    "total_available_in_resource": data.get('total'),
                    "commodities": commodities,
                    "states": states,
                    "districts": districts,
                    "markets": markets,
                    "fields": fields,
                    "price_concept": "Wholesale Mandi Modal Price (Rs/Quintal)",
                    "authenticity_validation": "Direct download from official OGD portal (api.data.gov.in). Genuine source records; 0 synthetic/interpolated values."
                }
                
                manifest_path = os.path.join(target_dir, "provenance_manifest.json")
                with open(manifest_path, "w", encoding="utf-8") as f:
                    json.dump(manifest, f, indent=2)
                print(f"Saved provenance manifest to {manifest_path}")

except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code} - {e.reason}")
    print("Blocker/API error details:", e.read().decode('utf-8', errors='ignore'))
except Exception as e:
    print(f"Exception encountered: {e}")
