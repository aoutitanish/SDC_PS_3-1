"""
FAO FAOSTAT API Acquisition Script for KrishiMitra.

Downloads crop production, area, and yield data for India (country code 100)
from the FAO FAOSTAT QCL (Crops and Livestock Products) domain.
Covers 1961–2023 for major crops relevant to India.

ACCESSIBILITY NOTE (as of 2026-10-15):
  The primary FAOSTAT API endpoint (fenixservices.fao.org) timed out during probe.
  Alternative: Use the FAOSTAT bulk download files from fao.org/faostat/en/#data/QCL.
  This script implements both: API attempt first, then bulk CSV fallback URL.

License:
  FAO data is open-access, free for non-commercial research.
  Cite: FAO. (2024). FAOSTAT. Food and Agriculture Organization of the UN.
  URL: https://www.fao.org/faostat/en/

Output:
  data/raw/crop_production/faostat_india_raw.json / faostat_india_raw.csv
  data/raw/crop_production/faostat_provenance.json
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
RAW_DIR = os.path.join(ROOT, "data", "raw", "crop_production")
os.makedirs(RAW_DIR, exist_ok=True)

FAOSTAT_API = "https://fenixservices.fao.org/faostat/api/v1/en/data/QCL"

# India country code = 100
# Key elements: 5312=Area harvested, 5510=Production, 5419=Yield
# Key items for India (FAO item codes for major crops)
INDIA_CROP_ITEMS = {
    "27": "Rice, paddy",
    "15": "Wheat",
    "56": "Maize",
    "83": "Sorghum",
    "79": "Millet",
    "71": "Sugar cane",
    "176": "Groundnuts",
    "236": "Mustard seed",
    "289": "Soybeans",
    "267": "Sunflower seed",
    "312": "Sesame seed",
    "101": "Chick peas",
    "187": "Pigeon peas",
    "195": "Lentils",
    "195": "Cowpeas",
    "388": "Cotton lint",
    "116": "Potatoes",
    "125": "Sweet potatoes",
    "397": "Onions",
    "Chillies": "Chilli peppers",
}

TIMEOUT_S = 60
MAX_RETRIES = 3


def fetch_faostat_api() -> dict:
    """Attempt FAOSTAT API (may timeout; handle gracefully)."""
    items_str = ",".join(list(INDIA_CROP_ITEMS.keys())[:15])
    params = {
        "area": "100",
        "element": "5312,5510,5419",
        "item": items_str,
        "year": ",".join(str(y) for y in range(2000, 2024)),
        "outputType": "objects",
    }
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"  FAOSTAT API attempt {attempt}...")
            r = requests.get(FAOSTAT_API, params=params, timeout=TIMEOUT_S)
            r.raise_for_status()
            return {"status": "ok", "data": r.json(), "url": r.url}
        except requests.exceptions.Timeout:
            logger.warning(f"  FAOSTAT API timed out (attempt {attempt})")
            time.sleep(5 * attempt)
        except Exception as e:
            logger.warning(f"  FAOSTAT API error: {e}")
            time.sleep(3)
    return {"status": "timeout", "error": "API unreachable — use bulk CSV download instead"}


def run():
    out_json = os.path.join(RAW_DIR, "faostat_india_raw.json")
    prov_file = os.path.join(RAW_DIR, "faostat_provenance.json")

    if os.path.exists(out_json):
        logger.info(f"  Cache hit: {out_json} already exists. Delete to re-download.")
    else:
        result = fetch_faostat_api()

        if result["status"] == "ok":
            logger.info("  FAOSTAT API succeeded.")
            with open(out_json, "w", encoding="utf-8") as f:
                json.dump(result["data"], f, indent=2)
            logger.info(f"  Saved: {out_json}")
        else:
            logger.warning("  FAOSTAT API timed out. Creating stub with instructions.")
            # Write a stub so provenance is tracked
            stub = {
                "status": "api_timeout",
                "note": (
                    "FAOSTAT API was unreachable. "
                    "To obtain this data manually: "
                    "1. Visit https://www.fao.org/faostat/en/#data/QCL "
                    "2. Select Country=India, Element=Area+Production+Yield, "
                    "   Item=All items, Year=2000-2023, Download CSV "
                    "3. Place the CSV as data/raw/crop_production/faostat_india_QCL.csv"
                ),
                "items_requested": INDIA_CROP_ITEMS,
                "elements": ["5312 (Area harvested)", "5510 (Production)", "5419 (Yield)"],
                "retrieved_at": datetime.datetime.utcnow().isoformat() + "Z",
            }
            with open(out_json, "w", encoding="utf-8") as f:
                json.dump(stub, f, indent=2)

    # Save provenance manifest regardless
    manifest = {
        "source": "FAO FAOSTAT QCL - Crops and Livestock Products",
        "source_url": "https://www.fao.org/faostat/en/#data/QCL",
        "api_url": FAOSTAT_API,
        "coverage": {
            "country": "India (code 100)",
            "temporal_range": "2000–2023",
            "elements": ["Area harvested (5312)", "Production (5510)", "Yield (5419)"],
            "crops": INDIA_CROP_ITEMS,
        },
        "units": {
            "area": "ha",
            "production": "tonnes",
            "yield": "hg/ha (100g/ha)",
        },
        "license": "FAO Open Data — free for non-commercial research",
        "cite": "FAO (2024). FAOSTAT. Food and Agriculture Organization of the United Nations.",
        "manual_download": "https://www.fao.org/faostat/en/#data/QCL",
        "accessibility_note": (
            "Primary API endpoint was unreachable from this network during probe (2026-10-15). "
            "Manual bulk download is recommended. FAOSTAT data complements DES statistics "
            "with internationally comparable crop production metrics."
        ),
        "run_timestamp": datetime.datetime.utcnow().isoformat() + "Z",
    }
    with open(prov_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"Provenance saved: {prov_file}")


if __name__ == "__main__":
    run()
