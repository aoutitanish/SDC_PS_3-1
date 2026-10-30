"""
Process and standardize NASA POWER monthly weather data into a clean CSV.

Reads raw JSON files from data/raw/weather/nasa_power_monthly_raw/,
computes seasonal aggregates (Kharif, Rabi, Summer), and merges into a
standardized district-level weather dataset.

Outputs:
  data/processed/weather/nasa_power_monthly_clean.csv
  data/processed/weather/nasa_power_processing_report.json

IMPORTANT: Historical cultivation records and climate normals MUST NOT be
joined unless crop growing periods are explicitly aligned. This script
produces ONLY climate normals — do not join to crop_expert.csv records
without season-period alignment.
"""

import os
import sys
import json
import glob
import datetime
import logging
import pandas as pd
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(ROOT, "data", "raw", "weather", "nasa_power_monthly_raw")
OUT_DIR = os.path.join(ROOT, "data", "processed", "weather")
OUT_CSV = os.path.join(OUT_DIR, "nasa_power_monthly_clean.csv")
REPORT_FILE = os.path.join(OUT_DIR, "nasa_power_processing_report.json")

os.makedirs(OUT_DIR, exist_ok=True)

# Month-to-season mapping for Indian agriculture
# Kharif: Jun-Oct (6-10), Rabi: Nov-Mar (11,12,1,2,3), Summer: Apr-May (4-5)
KHARIF_MONTHS = {6, 7, 8, 9, 10}
RABI_MONTHS = {11, 12, 1, 2, 3}
SUMMER_MONTHS = {4, 5}


def extract_annual_normals(param_monthly: dict, param_name: str) -> dict:
    """
    Compute 30-year normals (1981-2010 if available, else full range).
    Returns dict: month->value, plus annual mean and seasonal means.
    """
    # NASA POWER monthly data structure: param_monthly[year][month] = value
    # We want multi-year monthly means
    month_vals = {m: [] for m in range(1, 13)}

    for year, months in param_monthly.items():
        if not isinstance(months, dict):
            continue
        try:
            yr = int(year)
        except (ValueError, TypeError):
            continue
        for month_str, val in months.items():
            try:
                m = int(month_str)
                v = float(val)
                if v != -999.0:  # NASA POWER fill value
                    month_vals[m].append(v)
            except (ValueError, TypeError):
                continue

    normals = {}
    for m in range(1, 13):
        vals = month_vals[m]
        normals[f"month_{m:02d}"] = round(float(np.mean(vals)), 4) if vals else None

    # Seasonal aggregates
    kharif_vals = [v for m in KHARIF_MONTHS for v in month_vals[m]]
    rabi_vals = [v for m in RABI_MONTHS for v in month_vals[m]]
    summer_vals = [v for m in SUMMER_MONTHS for v in month_vals[m]]
    all_vals = [v for vals in month_vals.values() for v in vals]

    normals["kharif_mean"] = round(float(np.mean(kharif_vals)), 4) if kharif_vals else None
    normals["rabi_mean"] = round(float(np.mean(rabi_vals)), 4) if rabi_vals else None
    normals["summer_mean"] = round(float(np.mean(summer_vals)), 4) if summer_vals else None
    normals["annual_mean"] = round(float(np.mean(all_vals)), 4) if all_vals else None

    # For rainfall: sum (not mean) per season
    if "PRECTOCT" in param_name.upper() or "PRECOT" in param_name.upper() or param_name in ("PRECTOTCORR",):
        kharif_sum = sum(kharif_vals) / len({y for y in range(1981, 2024)}) if kharif_vals else None
        rabi_sum = sum(rabi_vals) / len({y for y in range(1981, 2024)}) if rabi_vals else None
        annual_sum = sum(all_vals) / len({y for y in range(1981, 2024)}) if all_vals else None
        normals["kharif_sum_annual"] = round(float(kharif_sum), 2) if kharif_sum else None
        normals["rabi_sum_annual"] = round(float(rabi_sum), 2) if rabi_sum else None
        normals["annual_total"] = round(float(annual_sum), 2) if annual_sum else None

    return normals


def process_file(fpath: str) -> dict:
    """Process a single raw NASA POWER JSON file into a district record."""
    with open(fpath, encoding='utf-8') as f:
        raw = json.load(f)

    if raw.get("status") != "ok":
        return None

    state = raw["state"]
    district = raw["district"]
    lat = raw["latitude"]
    lon = raw["longitude"]
    retrieved_at = raw.get("retrieved_at", "")

    # Navigate NASA POWER JSON structure
    try:
        properties = raw["data"]["properties"]
        param_data = properties["parameter"]
    except (KeyError, TypeError):
        logger.warning(f"  Unexpected structure in {os.path.basename(fpath)}")
        return None

    record = {
        "State_Name": state,
        "District_Name": district,
        "latitude": lat,
        "longitude": lon,
        "district_key": f"{state.strip().lower()}__{district.strip().lower()}",
        "data_source": "NASA POWER AG Monthly API",
        "retrieved_at": retrieved_at,
    }

    param_map = {
        "T2M": "temp_mean_c",
        "T2M_MAX": "temp_max_c",
        "T2M_MIN": "temp_min_c",
        "PRECTOTCORR": "rainfall_mm",
        "RH2M": "rh_pct",
        "WS2M": "windspeed_ms",
    }

    for nasa_param, col_prefix in param_map.items():
        if nasa_param not in param_data:
            continue
        normals = extract_annual_normals(param_data[nasa_param], nasa_param)

        for k, v in normals.items():
            record[f"{col_prefix}_{k}"] = v

        # Create top-level standardized fields
        record[f"{col_prefix}_annual"] = normals.get("annual_mean") or normals.get("annual_total")
        record[f"{col_prefix}_kharif"] = normals.get("kharif_mean") or normals.get("kharif_sum_annual")
        record[f"{col_prefix}_rabi"] = normals.get("rabi_mean") or normals.get("rabi_sum_annual")

    return record


def run():
    files = glob.glob(os.path.join(RAW_DIR, "*.json"))
    logger.info(f"Found {len(files)} raw NASA POWER district files")

    if not files:
        logger.warning(f"No raw files found in {RAW_DIR}. Run acquire_nasa_power_weather.py first.")
        return

    records = []
    error_count = 0
    for fpath in files:
        rec = process_file(fpath)
        if rec:
            records.append(rec)
        else:
            error_count += 1

    if not records:
        logger.error("No valid records processed.")
        return

    df = pd.DataFrame(records)
    df = df.sort_values(["State_Name", "District_Name"]).reset_index(drop=True)

    # Missing value analysis
    missing_pct = df.isnull().mean().mul(100).round(2)

    df.to_csv(OUT_CSV, index=False, encoding='utf-8')
    logger.info(f"Saved {len(df)} district records to {OUT_CSV}")

    report = {
        "processed_at": datetime.datetime.utcnow().isoformat() + "Z",
        "input_files": len(files),
        "valid_records": len(records),
        "error_records": error_count,
        "output_columns": list(df.columns),
        "missing_pct": missing_pct.to_dict(),
        "unique_states": int(df["State_Name"].nunique()),
        "unique_districts": int(df["District_Name"].nunique()),
        "data_provenance": "NASA POWER Agroclimatology API, 1981-2023 monthly data",
        "important_note": (
            "This dataset contains CLIMATE NORMALS (long-term means). "
            "Do NOT join these per-district normals to individual crop-year records "
            "without explicit season-period alignment. Historical cultivation records "
            "and climate normals represent different temporal resolutions."
        ),
    }
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    logger.info(f"Processing report: {REPORT_FILE}")


if __name__ == "__main__":
    run()
