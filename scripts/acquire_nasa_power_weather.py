"""
NASA POWER Monthly Climatology Acquisition Script for KrishiMitra.

Downloads monthly meteorological normals (T2M, PRECTOTCORR, RH2M, WS2M, T2M_MAX, T2M_MIN)
for all 635 districts in master_geography.csv via the NASA POWER AG-community monthly API.

Features:
  - Resumable: skips districts already cached
  - Rate-limited: 1.5s between requests
  - Retries: 3 attempts with exponential backoff
  - Provenance: records retrieval timestamp, coordinates, and API parameters per district

Output:
  data/raw/weather/nasa_power_monthly_raw/
    <state>__<district>.json   — raw API response per district
  data/raw/weather/nasa_power_provenance.json  — manifest

License:
  NASA POWER data is freely available with no registration required.
  Cite: Stackhouse et al. (2018), https://power.larc.nasa.gov/
  License: https://earthdata.nasa.gov/collaborate/open-data-services-and-software/data-use-policy
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
GEO_CSV = os.path.join(ROOT, "data", "master_geography.csv")
RAW_DIR = os.path.join(ROOT, "data", "raw", "weather", "nasa_power_monthly_raw")
PROVENANCE_FILE = os.path.join(ROOT, "data", "raw", "weather", "nasa_power_provenance.json")

NASA_BASE_URL = "https://power.larc.nasa.gov/api/temporal/monthly/point"
NASA_PARAMS = "T2M,T2M_MAX,T2M_MIN,PRECTOTCORR,RH2M,WS2M"
COMMUNITY = "AG"
START_YEAR = "1981"
END_YEAR = "2023"
FORMAT = "JSON"

REQUEST_DELAY_S = 1.5
MAX_RETRIES = 3
TIMEOUT_S = 45


def safe_filename(text: str) -> str:
    """Convert state/district to safe filename component."""
    return text.lower().replace(" ", "_").replace("/", "_").replace("&", "and")


def fetch_district(lat: float, lon: float, state: str, district: str) -> dict:
    """Fetch monthly data for a single district with retry logic."""
    params = {
        "parameters": NASA_PARAMS,
        "community": COMMUNITY,
        "longitude": str(round(lon, 4)),
        "latitude": str(round(lat, 4)),
        "start": START_YEAR,
        "end": END_YEAR,
        "format": FORMAT,
    }
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = requests.get(NASA_BASE_URL, params=params, timeout=TIMEOUT_S)
            r.raise_for_status()
            data = r.json()
            return {
                "status": "ok",
                "state": state,
                "district": district,
                "latitude": lat,
                "longitude": lon,
                "start_year": START_YEAR,
                "end_year": END_YEAR,
                "parameters": NASA_PARAMS,
                "retrieved_at": datetime.datetime.utcnow().isoformat() + "Z",
                "api_url": r.url,
                "data": data,
            }
        except requests.exceptions.RequestException as e:
            wait = 2 ** attempt
            logger.warning(f"  Attempt {attempt} failed for {district}: {e} — retrying in {wait}s")
            time.sleep(wait)
    return {"status": "error", "state": state, "district": district,
            "latitude": lat, "longitude": lon, "error": "Max retries exceeded"}


def run():
    import pandas as pd  # Imported here so the script can be inspected without pandas

    os.makedirs(RAW_DIR, exist_ok=True)

    geo = pd.read_csv(GEO_CSV)
    logger.info(f"Loaded {len(geo)} districts from {GEO_CSV}")

    provenance = []
    success_count = 0
    error_count = 0
    skip_count = 0

    for idx, row in geo.iterrows():
        state = str(row.get("State_Name", "")).strip()
        district = str(row.get("District_Name", "")).strip()
        lat = float(row.get("latitude", 0.0))
        lon = float(row.get("longitude", 0.0))

        if not state or not district or lat == 0.0 or lon == 0.0:
            logger.warning(f"  Skipping invalid row: {state}/{district}")
            continue

        fname = f"{safe_filename(state)}__{safe_filename(district)}.json"
        fpath = os.path.join(RAW_DIR, fname)

        # Resumable: skip if already fetched
        if os.path.exists(fpath):
            skip_count += 1
            continue

        logger.info(f"  [{idx+1}/{len(geo)}] Fetching {state} / {district} (lat={lat}, lon={lon})")
        result = fetch_district(lat, lon, state, district)

        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(result, f)

        prov = {
            "file": fname,
            "state": state,
            "district": district,
            "latitude": lat,
            "longitude": lon,
            "status": result["status"],
            "retrieved_at": result.get("retrieved_at", ""),
        }
        if result["status"] == "ok":
            success_count += 1
        else:
            error_count += 1
            prov["error"] = result.get("error", "")

        provenance.append(prov)
        time.sleep(REQUEST_DELAY_S)

    # Save provenance manifest
    manifest = {
        "source": "NASA POWER Agroclimatology API",
        "source_url": NASA_BASE_URL,
        "parameters": NASA_PARAMS,
        "community": COMMUNITY,
        "temporal_range": f"{START_YEAR}–{END_YEAR}",
        "geographic_coverage": "All India districts (635)",
        "license": "NASA Open Data (no registration required)",
        "cite": "Stackhouse et al. (2018), https://power.larc.nasa.gov/",
        "run_timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "total_districts": len(geo),
        "success_count": success_count,
        "error_count": error_count,
        "skipped_cached": skip_count,
        "records": provenance,
    }
    with open(PROVENANCE_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"Done. Success={success_count}, Errors={error_count}, Cached={skip_count}")
    logger.info(f"Raw data: {RAW_DIR}")
    logger.info(f"Provenance: {PROVENANCE_FILE}")


if __name__ == "__main__":
    run()
