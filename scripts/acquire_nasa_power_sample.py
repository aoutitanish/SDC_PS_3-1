"""
Run a sample NASA POWER acquisition for 20 diverse districts across India.
Used to validate the API works and produce sample raw data for catalog reporting.
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
RAW_DIR = os.path.join(ROOT, "data", "raw", "weather", "nasa_power_monthly_raw")
os.makedirs(RAW_DIR, exist_ok=True)

NASA_BASE = "https://power.larc.nasa.gov/api/temporal/monthly/point"
PARAMS = "T2M,T2M_MAX,T2M_MIN,PRECTOTCORR,RH2M,WS2M"
COMMUNITY = "AG"
START = "1981"
END = "2023"

# Representative sample: 1 district per major agro-climate zone / state
SAMPLE_DISTRICTS = [
    # North India - IGP belt
    ("Punjab", "Ludhiana", 30.9, 75.85),
    ("Haryana", "Karnal", 29.68, 76.99),
    ("Uttar Pradesh", "Agra", 27.18, 78.02),
    ("Bihar", "Patna", 25.59, 85.14),
    # Northwest Arid
    ("Rajasthan", "Jodhpur", 26.29, 73.02),
    ("Rajasthan", "Sri Ganganagar", 29.9, 73.88),
    # Central India
    ("Madhya Pradesh", "Indore", 22.72, 75.86),
    ("Maharashtra", "Nashik", 20.01, 73.79),
    ("Maharashtra", "Nagpur", 21.14, 79.08),
    # South India - Deccan
    ("Andhra Pradesh", "Kurnool", 15.83, 78.04),
    ("Telangana", "Warangal", 18.00, 79.58),
    ("Karnataka", "Dharwad", 15.46, 75.01),
    ("Karnataka", "Raichur", 16.20, 77.36),
    # East India
    ("West Bengal", "Midnapore", 22.43, 87.32),
    ("Odisha", "Cuttack", 20.46, 85.88),
    # Northeast
    ("Assam", "Kamrup", 26.18, 91.74),
    # South India - Coastal
    ("Tamil Nadu", "Coimbatore", 11.02, 76.97),
    ("Kerala", "Thrissur", 10.52, 76.21),
    # Hilly regions
    ("Himachal Pradesh", "Mandi", 31.71, 76.92),
    ("Gujarat", "Rajkot", 22.30, 70.78),
]


def fetch(lat, lon, state, district):
    safe = lambda t: t.lower().replace(" ", "_").replace("/", "_").replace("&", "and")
    fname = f"{safe(state)}__{safe(district)}.json"
    fpath = os.path.join(RAW_DIR, fname)

    if os.path.exists(fpath):
        logger.info(f"  Cache hit: {state}/{district}")
        return True

    params = {
        "parameters": PARAMS, "community": COMMUNITY,
        "longitude": str(lon), "latitude": str(lat),
        "start": START, "end": END, "format": "JSON",
    }
    for attempt in range(1, 4):
        try:
            r = requests.get(NASA_BASE, params=params, timeout=45)
            r.raise_for_status()
            result = {
                "status": "ok", "state": state, "district": district,
                "latitude": lat, "longitude": lon,
                "start_year": START, "end_year": END, "parameters": PARAMS,
                "retrieved_at": datetime.datetime.utcnow().isoformat() + "Z",
                "data": r.json(),
            }
            with open(fpath, "w", encoding="utf-8") as f:
                json.dump(result, f)
            logger.info(f"  OK: {state}/{district} -> {fname}")
            return True
        except Exception as e:
            logger.warning(f"  Attempt {attempt} failed for {district}: {e}")
            time.sleep(2 ** attempt)
    return False


def run():
    success = 0
    fail = 0
    for state, district, lat, lon in SAMPLE_DISTRICTS:
        logger.info(f"Fetching {state} / {district} (lat={lat}, lon={lon})")
        ok = fetch(lat, lon, state, district)
        if ok:
            success += 1
        else:
            fail += 1
        time.sleep(1.5)

    logger.info(f"\nSample acquisition complete: {success} OK, {fail} FAILED")
    logger.info(f"Files saved to: {RAW_DIR}")


if __name__ == "__main__":
    run()
