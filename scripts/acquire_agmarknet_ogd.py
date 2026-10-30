"""
Agmarknet / OGD Mandi Price Acquisition Script for KrishiMitra.

Downloads real wholesale mandi price arrivals for India's 28 canonical crops
from the Agmarknet data.gov.in OGD API (api.data.gov.in).

ACCESSIBILITY NOTE (as of 2026-10-15):
  - Agmarknet main site (agmarknet.gov.in) returns HTTP 200 but serves a minimal
    HTML page — the main interface requires JavaScript / form POST with CAPTCHA.
  - The OGD/data.gov.in API (api.data.gov.in) returned HTTP 403 with a guest key
    but returns 200 with a valid registered API key.
  - Action Required: Register for a free API key at https://data.gov.in/user/register
    and set environment variable DATAGOV_API_KEY before running this script.

Dataset Resource: "Daily Agmarknet Price and Arrival Data"
Resource ID: 9ef84268-d588-465a-a308-a864a43d0070 (Agmarknet daily prices)

Responsible scraping constraints enforced:
  - 1s delay between paginated API requests
  - Maximum 5000 records per request (API limit)
  - No CAPTCHA bypass attempted

Output:
  data/raw/market/agmarknet/  — per-crop raw JSON pages
  data/raw/market/agmarknet_provenance.json

License:
  Government Open Data License India (GODL-India) v1.0 — open for research use.
  URL: https://data.gov.in/government-open-data-license-india
"""

import os
import sys
import json
import time
import logging
import datetime
import requests

sys.stdout.reconfigure(encoding='utf-8')
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(ROOT, "data", "raw", "market", "agmarknet")
PROV_FILE = os.path.join(ROOT, "data", "raw", "market", "agmarknet_provenance.json")
os.makedirs(RAW_DIR, exist_ok=True)

# IMPORTANT: Register at https://data.gov.in/user/register and set your key
API_KEY = os.environ.get("DATAGOV_API_KEY", "")

OGD_BASE = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"

# 28 canonical crops and their common Agmarknet commodity names
CROP_COMMODITY_MAP = {
    "Rice": ["Paddy(Dhan)(Common)", "Paddy", "Rice"],
    "Wheat": ["Wheat"],
    "Maize": ["Maize"],
    "Arhar/Tur (Pigeon Pea)": ["Arhar (Tur/Red Gram)(Whole)", "Arhar Dal(Tur Dal)"],
    "Moong (Green Gram)": ["Green Gram (Moong)(Whole)", "Green Gram Dal (Moong Dal)"],
    "Urad": ["Black Gram (Urad)(Whole)", "Black Gram Dal (Urd Dal)"],
    "Gram (Chickpea)": ["Gram Raw(Whole)", "Bengal Gram(Whole)"],
    "Groundnut": ["Groundnut", "Groundnut (Split)"],
    "Mustard / Rapeseed": ["Mustard", "Rapeseed"],
    "Sesamum": ["Sesamum(Sesame,Gingelly,Til)"],
    "Sugarcane": ["Sugarcane"],
    "Jowar (Sorghum)": ["Jowar(Sorghum)"],
    "Bajra (Pearl Millet)": ["Bajra(Pearl Millet/Cumbu)"],
    "Ragi (Finger Millet)": ["Ragi (Finger Millet)"],
    "Sunflower": ["Sunflower"],
    "Cotton": ["Cotton(Kapas)", "Cotton", "Cotton Seed"],
    "Barley": ["Barley (Jau)"],
    "Masoor": ["Masoor(Lentil)"],
    "Onion": ["Onion"],
    "Potato": ["Potato"],
    "Dry chillies": ["Dry Chillies", "Red Chillies"],
    "Turmeric": ["Turmeric"],
    "Sweet potato": ["Sweet Potato"],
    "Linseed": ["Linseed"],
    "Horse-gram": ["Horse-gram"],
    "Small millets": ["Small Millets", "Kodo Millet"],
    "Peas & beans (Pulses)": ["Peas", "Field Pea"],
    "Other Kharif pulses": ["Moth(Moth Beans)", "Cowpea(Lobia/Karamani)"],
}

REQUEST_DELAY_S = 1.0
TIMEOUT_S = 30
PAGE_SIZE = 5000


def check_api_key():
    if not API_KEY:
        logger.error(
            "DATAGOV_API_KEY environment variable not set. "
            "Register at https://data.gov.in/user/register and set the key. "
            "Running in documentation mode only."
        )
        return False
    return True


def fetch_page(commodity: str, offset: int) -> dict:
    params = {
        "api-key": API_KEY,
        "format": "json",
        "limit": PAGE_SIZE,
        "offset": offset,
        "filters[Commodity]": commodity,
    }
    try:
        r = requests.get(OGD_BASE, params=params, timeout=TIMEOUT_S)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.HTTPError as e:
        return {"error": str(e), "status_code": r.status_code}
    except Exception as e:
        return {"error": str(e)}


def fetch_crop(canonical_crop: str, commodities: list) -> dict:
    all_records = []
    for commodity in commodities:
        offset = 0
        while True:
            result = fetch_page(commodity, offset)
            if "error" in result:
                logger.warning(f"  Error fetching {commodity}: {result['error']}")
                break
            records = result.get("records", [])
            total = int(result.get("total", 0))
            all_records.extend(records)
            logger.info(f"    {commodity}: offset={offset}, got={len(records)}, total={total}")
            if offset + PAGE_SIZE >= total or len(records) == 0:
                break
            offset += PAGE_SIZE
            time.sleep(REQUEST_DELAY_S)
    return {
        "canonical_crop": canonical_crop,
        "commodities_queried": commodities,
        "record_count": len(all_records),
        "retrieved_at": datetime.datetime.utcnow().isoformat() + "Z",
        "records": all_records,
    }


def run():
    if not check_api_key():
        # Create a stub provenance file with instructions
        stub_prov = {
            "source": "Agmarknet / data.gov.in OGD API",
            "resource_id": "9ef84268-d588-465a-a308-a864a43d0070",
            "source_url": "https://data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070",
            "status": "REQUIRES_API_KEY",
            "action_required": (
                "1. Register at https://data.gov.in/user/register (free)\n"
                "2. Obtain your API key from your account dashboard\n"
                "3. Set environment variable: set DATAGOV_API_KEY=your_key_here\n"
                "4. Re-run: python scripts/acquire_agmarknet_ogd.py"
            ),
            "existing_mandi_data": (
                "See data/raw/market/raw_agmarknet_historical.json (8.5 MB, synthetic benchmarks) "
                "and data/processed/historical_market/historical_mandi_prices.json (10.1 MB, cleaned)."
            ),
            "license": "Government Open Data License India (GODL-India) v1.0",
            "run_timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        }
        with open(PROV_FILE, "w", encoding="utf-8") as f:
            json.dump(stub_prov, f, indent=2)
        logger.info(f"Stub provenance saved: {PROV_FILE}")
        return

    provenance = []
    for canonical_crop, commodities in CROP_COMMODITY_MAP.items():
        safe_name = canonical_crop.lower().replace(" ", "_").replace("/", "_")
        out_file = os.path.join(RAW_DIR, f"{safe_name}.json")

        if os.path.exists(out_file):
            logger.info(f"  Cache hit: {canonical_crop} — skipping")
            continue

        logger.info(f"  Fetching {canonical_crop}...")
        result = fetch_crop(canonical_crop, commodities)

        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        provenance.append({
            "canonical_crop": canonical_crop,
            "file": os.path.basename(out_file),
            "record_count": result["record_count"],
            "retrieved_at": result["retrieved_at"],
        })
        time.sleep(REQUEST_DELAY_S)

    manifest = {
        "source": "Agmarknet / data.gov.in OGD API",
        "resource_id": "9ef84268-d588-465a-a308-a864a43d0070",
        "license": "Government Open Data License India (GODL-India) v1.0",
        "cite": "National Informatics Centre & Ministry of Agriculture, data.gov.in",
        "run_timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "crops": provenance,
    }
    with open(PROV_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"Done. Provenance: {PROV_FILE}")


if __name__ == "__main__":
    run()
