"""
NASA POWER Expanded Weather Acquisition and Processing Script for KrishiMitra Phase 3.

Features:
1. Geographic Expansion: Acquires 43-year monthly climate normals (1981–2023) across
   an expanded set of 55 representative districts spanning all 15 Indian Agro-Climatic Zones.
2. Daily Weather Series: Acquires 4-year daily meteorological observations (2020–2023)
   for 10 representative agro-ecological anchor districts to capture extreme heat stress,
   dry spell durations, and growing-degree-day (GDD) dynamics.
3. Resumable & Cached: Skips any files already present on disk.
4. Strict Provenance: Distinguishes satellite/MERRA-2 reanalysis estimates from ground station observations.
5. Standardized Processed Outputs:
   - data/processed/weather/expanded_district_monthly_weather.csv
   - data/processed/weather/representative_district_daily_weather.csv
   - data/processed/weather/daily_agroclimatic_metrics.csv
   - data/catalog/phase3_weather_coverage_report.csv
"""

import os
import sys
import glob
import json
import time
import math
import calendar
import logging
import datetime
import requests
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEO_PATH = os.path.join(ROOT, "data", "master_geography.csv")
RAW_MONTHLY_DIR = os.path.join(ROOT, "data", "raw", "weather", "nasa_power_monthly_raw")
RAW_DAILY_DIR = os.path.join(ROOT, "data", "raw", "weather", "nasa_power_daily_raw")
PROC_WEATHER_DIR = os.path.join(ROOT, "data", "processed", "weather")
CATALOG_DIR = os.path.join(ROOT, "data", "catalog")

os.makedirs(RAW_MONTHLY_DIR, exist_ok=True)
os.makedirs(RAW_DAILY_DIR, exist_ok=True)
os.makedirs(PROC_WEATHER_DIR, exist_ok=True)
os.makedirs(CATALOG_DIR, exist_ok=True)

MONTHLY_URL = "https://power.larc.nasa.gov/api/temporal/monthly/point"
DAILY_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
PARAMS = "T2M,T2M_MAX,T2M_MIN,PRECTOTCORR,RH2M,WS2M"

# 35 additional diverse districts covering all 15 Agro-Climatic Zones of India
ADDITIONAL_TARGET_DISTRICTS = [
    # North / Upper Gangetic / Trans-Gangetic
    ("Uttar Pradesh", "Varanasi", 25.3176, 82.9739, "Middle Gangetic Plain"),
    ("Uttar Pradesh", "Meerut", 28.9845, 77.7064, "Upper Gangetic Plain"),
    ("Uttar Pradesh", "Kanpur Nagar", 26.4499, 80.3319, "Central Plain"),
    ("Punjab", "Amritsar", 31.6340, 74.8723, "Trans-Gangetic Plain"),
    ("Punjab", "Bathinda", 30.2110, 74.9455, "Trans-Gangetic Plain"),
    ("Haryana", "Hisar", 29.1492, 75.7217, "Trans-Gangetic Plain"),
    ("Haryana", "Ambala", 30.3782, 76.7767, "Trans-Gangetic Plain"),
    # Central / Plateau
    ("Madhya Pradesh", "Ujjain", 23.1765, 75.7885, "Central Plateau & Hills (Malwa)"),
    ("Madhya Pradesh", "Bhopal", 23.2599, 77.4126, "Central Plateau & Hills"),
    ("Madhya Pradesh", "Jabalpur", 23.1815, 79.9864, "Central Plateau & Hills"),
    ("Chhattisgarh", "Raipur", 21.2514, 81.6296, "Eastern Plateau & Hills (Chhattisgarh Plains)"),
    ("Chhattisgarh", "Bilaspur", 22.0797, 82.1409, "Eastern Plateau & Hills"),
    ("Jharkhand", "Ranchi", 23.3441, 85.3096, "Eastern Plateau & Hills (Chota Nagpur)"),
    # Western / Arid / Semi-Arid
    ("Rajasthan", "Kota", 25.2138, 75.8648, "Central Plateau & Hills (Hadoti)"),
    ("Rajasthan", "Jaipur", 26.9124, 75.7873, "Semi-Arid Eastern Plain"),
    ("Rajasthan", "Bikaner", 28.0229, 73.3119, "Western Dry Region (Thar Desert)"),
    ("Gujarat", "Ahmedabad", 23.0225, 72.5714, "Gujarat Plains & Hills"),
    ("Gujarat", "Surat", 21.1702, 72.8311, "Gujarat Plains (South Gujarat)"),
    ("Gujarat", "Junagadh", 21.5222, 70.4579, "Gujarat Plains (Saurashtra)"),
    # West Coast / Western Ghats / Maharashtra
    ("Maharashtra", "Pune", 18.5204, 73.8567, "Western Plateau & Hills"),
    ("Maharashtra", "Ahmednagar", 19.0952, 74.7496, "Scarcity Zone / Western Plateau"),
    ("Maharashtra", "Solapur", 17.6599, 75.9064, "Southern Western Plateau"),
    # South / Deccan / Coastal
    ("Andhra Pradesh", "Guntur", 16.3067, 80.4365, "East Coast Plains & Hills (Krishna Delta)"),
    ("Andhra Pradesh", "Anantapur", 14.6819, 77.6006, "Southern Plateau (Rayalaseema Scarcity)"),
    ("Telangana", "Nizamabad", 18.6725, 78.0941, "Southern Plateau & Hills"),
    ("Karnataka", "Belagavi", 15.8497, 74.4977, "Northern Transitional Zone"),
    ("Karnataka", "Mysuru", 12.2958, 76.6394, "Southern Dry / Transition Zone"),
    ("Tamil Nadu", "Thanjavur", 10.7870, 79.1378, "East Coast Plains (Cauvery Delta)"),
    ("Tamil Nadu", "Madurai", 9.9252, 78.1198, "Southern Zone (Vaigai Basin)"),
    ("Kerala", "Palakkad", 10.7867, 76.6548, "West Coast Plains (Palakkad Gap Rice Bowl)"),
    # Eastern / Delta / Himalayan
    ("Bihar", "Muzaffarpur", 26.1209, 85.3647, "Middle Gangetic Plain (North Bihar)"),
    ("West Bengal", "Bardhaman", 23.2324, 87.8615, "Lower Gangetic Plain (Burdwan Rice Bowl)"),
    ("Assam", "Jorhat", 26.7509, 94.2037, "Eastern Himalayan Region (Upper Brahmaputra)"),
    ("Uttarakhand", "Dehradun", 30.3165, 78.0322, "Western Himalayan Region (Valley)"),
    ("Himachal Pradesh", "Shimla", 31.1048, 77.1734, "Western Himalayan Region (High Altitude)")
]

# 10 anchor districts for daily weather (2020–2023)
DAILY_ANCHOR_DISTRICTS = [
    ("Punjab", "Ludhiana", 30.90, 75.85, "Trans-Gangetic (Rice-Wheat intensive)"),
    ("Haryana", "Karnal", 29.68, 76.99, "Trans-Gangetic (Basmati/Wheat)"),
    ("Uttar Pradesh", "Varanasi", 25.32, 82.97, "Middle Gangetic (Intensive cereal-pulse)"),
    ("Madhya Pradesh", "Indore", 22.72, 75.86, "Central Plateau (Soybean-Wheat)"),
    ("Maharashtra", "Nashik", 20.01, 73.79, "Western Plateau (Onion/Horticulture)"),
    ("Maharashtra", "Nagpur", 21.15, 79.08, "Eastern Vidarbha (Cotton-Soybean-Citrus)"),
    ("Gujarat", "Rajkot", 22.30, 70.78, "Saurashtra (Groundnut-Cotton)"),
    ("Andhra Pradesh", "Kurnool", 15.83, 78.04, "Rayalaseema (Groundnut-Millets rainfed)"),
    ("Tamil Nadu", "Thanjavur", 10.79, 79.14, "Cauvery Delta (Triple crop Rice)"),
    ("West Bengal", "Bardhaman", 23.23, 87.86, "Lower Gangetic (Aman/Boro Rice)")
]


def safe_name(text: str) -> str:
    return text.lower().replace(" ", "_").replace("/", "_").replace("&", "and")


def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def fetch_monthly(lat: float, lon: float, state: str, district: str) -> dict:
    fpath = os.path.join(RAW_MONTHLY_DIR, f"{safe_name(state)}__{safe_name(district)}.json")
    if os.path.exists(fpath):
        with open(fpath, "r", encoding="utf-8") as f:
            return json.load(f)
            
    params = {
        "parameters": PARAMS,
        "community": "AG",
        "longitude": str(round(lon, 4)),
        "latitude": str(round(lat, 4)),
        "start": "1981",
        "end": "2023",
        "format": "JSON"
    }
    for attempt in range(1, 4):
        try:
            r = requests.get(MONTHLY_URL, params=params, timeout=30)
            r.raise_for_status()
            data = {
                "status": "ok",
                "state": state,
                "district": district,
                "latitude": lat,
                "longitude": lon,
                "start_year": "1981",
                "end_year": "2023",
                "parameters": PARAMS,
                "retrieved_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "data": r.json()
            }
            with open(fpath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            time.sleep(1.0)
            return data
        except Exception as e:
            time.sleep(2 ** attempt)
    return {"status": "error", "state": state, "district": district, "error": "Fetch failed"}


def fetch_daily(lat: float, lon: float, state: str, district: str) -> dict:
    fpath = os.path.join(RAW_DAILY_DIR, f"{safe_name(state)}__{safe_name(district)}_daily.json")
    if os.path.exists(fpath):
        with open(fpath, "r", encoding="utf-8") as f:
            return json.load(f)
            
    params = {
        "parameters": PARAMS,
        "community": "AG",
        "longitude": str(round(lon, 4)),
        "latitude": str(round(lat, 4)),
        "start": "20200101",
        "end": "20231231",
        "format": "JSON"
    }
    for attempt in range(1, 4):
        try:
            r = requests.get(DAILY_URL, params=params, timeout=40)
            r.raise_for_status()
            data = {
                "status": "ok",
                "state": state,
                "district": district,
                "latitude": lat,
                "longitude": lon,
                "start_date": "20200101",
                "end_date": "20231231",
                "parameters": PARAMS,
                "retrieved_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "data": r.json()
            }
            with open(fpath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            time.sleep(1.2)
            return data
        except Exception as e:
            time.sleep(2 ** attempt)
    return {"status": "error", "state": state, "district": district, "error": "Fetch failed"}


def run_expanded_acquisition():
    logger.info("=== Starting Workstream A: NASA POWER Weather Expansion ===")
    
    # 1. Acquire monthly files
    logger.info(f"Checking & acquiring monthly series for {len(ADDITIONAL_TARGET_DISTRICTS)} target districts...")
    monthly_results = []
    for st, dt, lat, lon, zone in ADDITIONAL_TARGET_DISTRICTS:
        res = fetch_monthly(lat, lon, st, dt)
        monthly_results.append((st, dt, lat, lon, zone, res.get("status") == "ok"))
        
    # 2. Acquire daily files for 10 anchor districts
    logger.info(f"Checking & acquiring daily weather for {len(DAILY_ANCHOR_DISTRICTS)} anchor districts...")
    daily_results = []
    for st, dt, lat, lon, desc in DAILY_ANCHOR_DISTRICTS:
        res = fetch_daily(lat, lon, st, dt)
        daily_results.append((st, dt, lat, lon, desc, res.get("status") == "ok"))

    # 3. Process all monthly files into unified expanded dataset
    all_monthly_files = sorted(glob.glob(os.path.join(RAW_MONTHLY_DIR, "*.json")))
    logger.info(f"Processing {len(all_monthly_files)} total raw monthly weather files...")
    
    monthly_rows = []
    coverage_rows = []
    
    for fpath in all_monthly_files:
        with open(fpath, "r", encoding="utf-8") as f:
            d = json.load(f)
            
        st = d.get("state", "Unknown")
        dt = d.get("district", "Unknown")
        lat = d.get("latitude")
        lon = d.get("longitude")
        raw_power = d.get("data", {})
        param_dict = raw_power.get("properties", {}).get("parameter", {})
        
        t2m_p = param_dict.get("T2M", {})
        t2m_max_p = param_dict.get("T2M_MAX", {})
        t2m_min_p = param_dict.get("T2M_MIN", {})
        prec_p = param_dict.get("PRECTOTCORR", {})
        rh_p = param_dict.get("RH2M", {})
        ws_p = param_dict.get("WS2M", {})
        
        valid_months_count = 0
        
        for date_key in sorted(t2m_p.keys()):
            if len(date_key) != 6:
                continue
            yr = int(date_key[:4])
            mo = int(date_key[4:])
            if mo < 1 or mo > 12:
                continue
                
            days_in_mo = calendar.monthrange(yr, mo)[1]
            prec_daily = prec_p.get(date_key)
            monthly_prec = round(prec_daily * days_in_mo, 2) if prec_daily is not None else None
            
            monthly_rows.append({
                "state": st,
                "district": dt,
                "year": yr,
                "month": mo,
                "t2m_mean_c": t2m_p.get(date_key),
                "t2m_max_c": t2m_max_p.get(date_key),
                "t2m_min_c": t2m_min_p.get(date_key),
                "precipitation_monthly_mm": monthly_prec,
                "precipitation_rate_mm_day": prec_daily,
                "relative_humidity_pct": rh_p.get(date_key),
                "wind_speed_2m_mps": ws_p.get(date_key),
                "latitude": lat,
                "longitude": lon,
                "data_source": "NASA POWER MERRA-2 (0.5° Reanalysis Estimate)"
            })
            valid_months_count += 1
            
        coverage_rows.append({
            "state": st,
            "district": dt,
            "latitude": lat,
            "longitude": lon,
            "status": "SUCCESS" if valid_months_count >= 516 else "PARTIAL",
            "months_recorded": valid_months_count,
            "expected_months": 43 * 12,
            "years_span": "1981–2023",
            "temporal_resolution": "Monthly",
            "spatial_resolution": "0.5° x 0.5°",
            "data_type": "Satellite & Assimilation Reanalysis Estimate"
        })
        
    df_monthly = pd.DataFrame(monthly_rows)
    monthly_out_csv = os.path.join(PROC_WEATHER_DIR, "expanded_district_monthly_weather.csv")
    df_monthly.to_csv(monthly_out_csv, index=False)
    logger.info(f"Saved expanded monthly weather to {monthly_out_csv} ({len(df_monthly)} rows, {df_monthly['district'].nunique()} districts).")
    
    # 4. Process daily files & compute agro-climatic stress metrics
    all_daily_files = sorted(glob.glob(os.path.join(RAW_DAILY_DIR, "*.json")))
    logger.info(f"Processing {len(all_daily_files)} daily weather files...")
    
    daily_rows = []
    stress_metrics_rows = []
    
    for fpath in all_daily_files:
        with open(fpath, "r", encoding="utf-8") as f:
            d = json.load(f)
            
        st = d.get("state", "")
        dt = d.get("district", "")
        lat = d.get("latitude")
        lon = d.get("longitude")
        raw_power = d.get("data", {})
        param_dict = raw_power.get("properties", {}).get("parameter", {})
        
        t2m_p = param_dict.get("T2M", {})
        t2m_max_p = param_dict.get("T2M_MAX", {})
        t2m_min_p = param_dict.get("T2M_MIN", {})
        prec_p = param_dict.get("PRECTOTCORR", {})
        rh_p = param_dict.get("RH2M", {})
        ws_p = param_dict.get("WS2M", {})
        
        district_daily = []
        for dstr in sorted(t2m_p.keys()):
            if len(dstr) != 8:
                continue
            yr = int(dstr[:4])
            mo = int(dstr[4:6])
            day = int(dstr[6:])
            
            t_max = t2m_max_p.get(dstr)
            t_min = t2m_min_p.get(dstr)
            t_mean = t2m_p.get(dstr)
            prec = prec_p.get(dstr, 0.0)
            
            rec = {
                "state": st,
                "district": dt,
                "date": f"{yr:04d}-{mo:02d}-{day:02d}",
                "year": yr,
                "month": mo,
                "day": day,
                "t2m_mean_c": t_mean,
                "t2m_max_c": t_max,
                "t2m_min_c": t_min,
                "precipitation_mm": prec,
                "relative_humidity_pct": rh_p.get(dstr),
                "wind_speed_2m_mps": ws_p.get(dstr)
            }
            daily_rows.append(rec)
            district_daily.append(rec)
            
        # Compute annual agro-climatic stress metrics per district-year
        df_dist = pd.DataFrame(district_daily)
        for yr, grp in df_dist.groupby("year"):
            heat_days_35 = int((grp["t2m_max_c"] >= 35.0).sum())
            heat_days_40 = int((grp["t2m_max_c"] >= 40.0).sum())
            cold_days_10 = int((grp["t2m_min_c"] <= 10.0).sum())
            total_rain_mm = round(float(grp["precipitation_mm"].sum()), 1)
            rainy_days = int((grp["precipitation_mm"] >= 2.5).sum())
            
            # Monsoon rainfall (June–September: months 6, 7, 8, 9)
            monsoon_rain = round(float(grp[grp["month"].isin([6, 7, 8, 9])]["precipitation_mm"].sum()), 1)
            monsoon_pct = round((monsoon_rain / total_rain_mm * 100), 1) if total_rain_mm > 0 else 0.0
            
            # Consecutive dry spell max during monsoon (rain < 2.5 mm)
            monsoon_df = grp[grp["month"].isin([6, 7, 8, 9])].sort_values("date")
            max_dry_spell = 0
            cur_dry_spell = 0
            for r in monsoon_df["precipitation_mm"]:
                if r < 2.5:
                    cur_dry_spell += 1
                    if cur_dry_spell > max_dry_spell:
                        max_dry_spell = cur_dry_spell
                else:
                    cur_dry_spell = 0
                    
            # Growing Degree Days (GDD) with Base Temp = 10 C
            gdd_series = grp.apply(lambda r: max(0.0, ((r["t2m_max_c"] + r["t2m_min_c"]) / 2.0) - 10.0), axis=1)
            total_gdd = round(float(gdd_series.sum()), 1)
            
            stress_metrics_rows.append({
                "state": st,
                "district": dt,
                "year": yr,
                "annual_rainfall_mm": total_rain_mm,
                "rainy_days_count": rainy_days,
                "monsoon_rainfall_mm": monsoon_rain,
                "monsoon_rainfall_share_pct": monsoon_pct,
                "max_monsoon_dry_spell_days": max_dry_spell,
                "heat_stress_days_above_35c": heat_days_35,
                "extreme_heat_days_above_40c": heat_days_40,
                "cold_stress_days_below_10c": cold_days_10,
                "annual_growing_degree_days_gdd10": total_gdd,
                "data_source": "NASA POWER Daily AG Reanalysis (MERRA-2)"
            })
            
    df_daily = pd.DataFrame(daily_rows)
    daily_out_csv = os.path.join(PROC_WEATHER_DIR, "representative_district_daily_weather.csv")
    df_daily.to_csv(daily_out_csv, index=False)
    logger.info(f"Saved representative daily weather to {daily_out_csv} ({len(df_daily)} rows, {df_daily['district'].nunique()} districts).")
    
    df_metrics = pd.DataFrame(stress_metrics_rows)
    metrics_out_csv = os.path.join(PROC_WEATHER_DIR, "daily_agroclimatic_metrics.csv")
    df_metrics.to_csv(metrics_out_csv, index=False)
    logger.info(f"Saved daily agroclimatic metrics to {metrics_out_csv} ({len(df_metrics)} district-years).")
    
    # 5. Coverage and spatial report
    df_cov = pd.DataFrame(coverage_rows)
    cov_out_csv = os.path.join(CATALOG_DIR, "phase3_weather_coverage_report.csv")
    df_cov.to_csv(cov_out_csv, index=False)
    logger.info(f"Saved weather coverage report to {cov_out_csv} ({len(df_cov)} districts).")


if __name__ == "__main__":
    run_expanded_acquisition()
