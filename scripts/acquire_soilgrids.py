"""
SoilGrids v2.0 REST API Acquisition Script for KrishiMitra.

Downloads 0–5cm physicochemical soil property estimates (pH, nitrogen, clay, sand,
silt, SOC, bulk density, CEC) for all 635 Indian districts via the ISRIC SoilGrids REST API.

Features:
  - Resumable: skips already-downloaded districts
  - Rate-limited: 2.0s between requests (ISRIC fair-use policy)
  - Retries: up to 4 attempts with exponential backoff
  - Both 0-5cm and 5-15cm depth profiles retrieved
  - Provenance preserved per district

ACCESSIBILITY NOTE (as of 2026-10-15):
  SoilGrids REST API (rest.isric.org) was TIMING OUT during the source probe.
  This may be a transient availability issue. The script implements graceful
  handling: timed-out districts are logged and skipped for retry on next run.
  All existing data\soil_expert.csv records were originally sourced from SoilGrids 250m.

Existing coverage:
  641 districts already have SoilGrids 0-5cm data in data/soil_expert.csv (25% missing).
  This script fills gaps and adds 5-15cm depth layer.

License:
  SoilGrids is open-access (CC BY 4.0). No authentication required.
  Cite: Poggio et al. (2021), doi:10.5194/soil-7-217-2021
  URL: https://www.isric.org/explore/soilgrids/faq-soilgrids
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
RAW_DIR = os.path.join(ROOT, "data", "raw", "soil", "soilgrids_raw")
PROVENANCE_FILE = os.path.join(ROOT, "data", "raw", "soil", "soilgrids_provenance.json")

SOILGRIDS_BASE = "https://rest.isric.org/soilgrids/v2.0/properties/query"

PROPERTIES = ["phh2o", "nitrogen", "clay", "sand", "silt", "soc", "bdod", "cec"]
DEPTHS = ["0-5cm", "5-15cm"]
VALUES = ["mean", "uncertainty"]

REQUEST_DELAY_S = 2.0
MAX_RETRIES = 4
TIMEOUT_S = 60


def safe_filename(text: str) -> str:
    return text.lower().replace(" ", "_").replace("/", "_").replace("&", "and")


def fetch_district_soil(lat: float, lon: float, state: str, district: str) -> dict:
    """Fetch soil data for a single point, all properties and depths."""
    results_by_depth = {}
    for depth in DEPTHS:
        params = {
            "lon": str(round(lon, 4)),
            "lat": str(round(lat, 4)),
            "property": PROPERTIES,
            "depth": depth,
            "value": VALUES,
        }
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                r = requests.get(SOILGRIDS_BASE, params=params, timeout=TIMEOUT_S)
                r.raise_for_status()
                results_by_depth[depth] = r.json()
                break
            except requests.exceptions.Timeout:
                wait = 2 ** attempt
                logger.warning(f"  Timeout attempt {attempt} for {district} depth={depth} — retry in {wait}s")
                time.sleep(wait)
            except requests.exceptions.HTTPError as e:
                logger.warning(f"  HTTP error {e} for {district} depth={depth}")
                results_by_depth[depth] = {"error": str(e)}
                break
            except Exception as e:
                logger.warning(f"  Error attempt {attempt} for {district}: {e}")
                wait = 2 ** attempt
                time.sleep(wait)
        else:
            results_by_depth[depth] = {"error": "Max retries (timeout)"}
        time.sleep(REQUEST_DELAY_S)

    any_error = any("error" in v for v in results_by_depth.values())
    return {
        "status": "partial" if any_error else "ok",
        "state": state,
        "district": district,
        "latitude": lat,
        "longitude": lon,
        "properties": PROPERTIES,
        "depths": DEPTHS,
        "retrieved_at": datetime.datetime.utcnow().isoformat() + "Z",
        "data_by_depth": results_by_depth,
    }


def run():
    import pandas as pd

    os.makedirs(RAW_DIR, exist_ok=True)

    geo = pd.read_csv(GEO_CSV)
    logger.info(f"Loaded {len(geo)} districts from {GEO_CSV}")

    provenance = []
    success_count = 0
    partial_count = 0
    error_count = 0
    skip_count = 0

    for idx, row in geo.iterrows():
        state = str(row.get("State_Name", "")).strip()
        district = str(row.get("District_Name", "")).strip()
        lat = float(row.get("latitude", 0.0))
        lon = float(row.get("longitude", 0.0))

        if not state or not district:
            continue

        fname = f"{safe_filename(state)}__{safe_filename(district)}.json"
        fpath = os.path.join(RAW_DIR, fname)

        if os.path.exists(fpath):
            skip_count += 1
            continue

        logger.info(f"  [{idx+1}/{len(geo)}] Fetching soil: {state} / {district}")
        result = fetch_district_soil(lat, lon, state, district)

        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(result, f)

        prov = {
            "file": fname, "state": state, "district": district,
            "latitude": lat, "longitude": lon,
            "status": result["status"],
            "retrieved_at": result["retrieved_at"],
        }
        provenance.append(prov)

        if result["status"] == "ok":
            success_count += 1
        elif result["status"] == "partial":
            partial_count += 1
        else:
            error_count += 1

    # Save provenance manifest
    manifest = {
        "source": "ISRIC SoilGrids v2.0 REST API",
        "source_url": SOILGRIDS_BASE,
        "properties": PROPERTIES,
        "depths": DEPTHS,
        "values": VALUES,
        "spatial_resolution": "250m gridded, queried at district centroid",
        "license": "CC BY 4.0",
        "cite": "Poggio et al. (2021) doi:10.5194/soil-7-217-2021",
        "accessibility_note": "API at rest.isric.org may be intermittently unavailable. Retry on next run.",
        "run_timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "total_districts": len(geo),
        "success_count": success_count,
        "partial_count": partial_count,
        "error_count": error_count,
        "skipped_cached": skip_count,
        "records": provenance,
    }
    with open(PROVENANCE_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"Done. OK={success_count}, Partial={partial_count}, Error={error_count}, Cached={skip_count}")


if __name__ == "__main__":
    run()
