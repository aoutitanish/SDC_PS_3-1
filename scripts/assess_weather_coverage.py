"""
Weather alignment and coverage assessment script for KrishiMitra.

Inspects all 20 NASA POWER raw monthly weather files, evaluating:
- Geographic coordinates vs official district centroids
- Topographic and spatial adequacy
- Temporal resolution, parameters, and physical units
- Explicit labeling: 'NASA POWER 0.5° MERRA-2 Reanalysis Estimate' (NOT ground station observed weather)
- Builds an aligned, defensible monthly weather dataset for 1981-2023 (10,320 rows)
"""

import os
import sys
import glob
import json
import math
import calendar
import logging
import datetime
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_WEATHER_DIR = os.path.join(ROOT, "data", "raw", "weather", "nasa_power_monthly_raw")
GEO_PATH = os.path.join(ROOT, "data", "master_geography.csv")
PROC_WEATHER_DIR = os.path.join(ROOT, "data", "processed", "weather")
os.makedirs(PROC_WEATHER_DIR, exist_ok=True)

OUT_ASSESSMENT_CSV = os.path.join(PROC_WEATHER_DIR, "nasa_power_coverage_assessment.csv")
OUT_ALIGNED_CSV = os.path.join(PROC_WEATHER_DIR, "nasa_power_monthly_district_weather_20.csv")
OUT_PROV_JSON = os.path.join(PROC_WEATHER_DIR, "weather_provenance.json")

# Verified centroids for districts with naming/coordinate reconciliation
VERIFIED_CENTROIDS = {
    ("Rajasthan", "Sri Ganganagar"): (29.9200, 73.8800),
    ("West Bengal", "Midnapore"): (22.4200, 87.3200),
}


def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def assess_topographic_adequacy(state: str, district: str, dist_km: float) -> str:
    """Evaluates whether the 0.5-deg (~55km) grid cell adequately captures district macroclimate."""
    if district in ["Mandi"]:
        return (
            "Moderate spatial adequacy. High-altitude montane terrain (700m–4000m elevation gradient). "
            "0.5° MERRA-2 grid cell provides regional valley/foothill climatic baseline but smooths extreme local microclimates and lapse rates."
        )
    elif district in ["Thrissur", "Cuttack"]:
        return (
            "Adequate spatial adequacy. Coastal/deltaic transition zone with marine maritime humidity. "
            f"Centroid distance is {dist_km:.1f} km, capturing coastal precipitation gradients reasonably."
        )
    elif dist_km > 30:
        return (
            f"Moderate spatial adequacy. Grid query coordinate is {dist_km:.1f} km from geographic centroid, "
            "centered on principal urban/APMC market node rather than rural geometric center."
        )
    else:
        return (
            f"High spatial adequacy for macroclimate. Uniform agricultural plains/plateau terrain. "
            f"Centroid distance is {dist_km:.1f} km, well within 0.5° (~55 km) grid resolution."
        )


def run_assessment():
    geo = pd.read_csv(GEO_PATH)
    files = sorted(glob.glob(os.path.join(RAW_WEATHER_DIR, "*.json")))
    logger.info(f"Analyzing {len(files)} NASA POWER files...")
    
    assessment_records = []
    aligned_weather_records = []
    
    for fpath in files:
        fname = os.path.basename(fpath)
        with open(fpath, "r", encoding="utf-8") as f:
            d = json.load(f)
            
        st = d["state"]
        dt = d["district"]
        nasa_lat = d["latitude"]
        nasa_lon = d["longitude"]
        start_yr = d["start_year"]
        end_yr = d["end_year"]
        raw_power = d.get("data", {})
        param_dict = raw_power.get("properties", {}).get("parameter", {})
        
        # Determine district centroid
        if (st, dt) in VERIFIED_CENTROIDS:
            g_lat, g_lon = VERIFIED_CENTROIDS[(st, dt)]
        else:
            m = geo[(geo["State_Name"].str.lower() == st.lower()) & (geo["District_Name"].str.lower() == dt.lower())]
            if len(m) > 0:
                g_lat = m.iloc[0]["latitude"]
                g_lon = m.iloc[0]["longitude"]
            else:
                g_lat, g_lon = nasa_lat, nasa_lon
                
        dist_km = haversine(nasa_lat, nasa_lon, g_lat, g_lon)
        adequacy_note = assess_topographic_adequacy(st, dt, dist_km)
        
        assessment_records.append({
            "file_name": fname,
            "state": st,
            "district": dt,
            "nasa_grid_latitude": round(nasa_lat, 4),
            "nasa_grid_longitude": round(nasa_lon, 4),
            "district_centroid_latitude": round(g_lat, 4),
            "district_centroid_longitude": round(g_lon, 4),
            "haversine_distance_km": round(dist_km, 2),
            "spatial_resolution": "0.5° x 0.5° (~55 km x 55 km)",
            "temporal_resolution": "Monthly",
            "time_span": f"{start_yr}–{end_yr}",
            "years_count": int(end_yr) - int(start_yr) + 1,
            "parameters_available": "T2M, T2M_MAX, T2M_MIN, PRECTOTCORR, RH2M, WS2M",
            "parameter_units": "T2M/MAX/MIN (°C), PRECTOTCORR (mm/day), RH2M (%), WS2M (m/s)",
            "data_source_authority": "NASA POWER Project / MERRA-2 Assimilation Model",
            "data_type_classification": "Satellite & Assimilation Reanalysis Estimate (Not Ground Observed)",
            "district_representativeness": adequacy_note
        })
        
        # Build aligned monthly series
        # Dates are in YYYYMM format; filter out month '13'
        t2m_p = param_dict.get("T2M", {})
        t2m_max_p = param_dict.get("T2M_MAX", {})
        t2m_min_p = param_dict.get("T2M_MIN", {})
        prec_p = param_dict.get("PRECTOTCORR", {})
        rh_p = param_dict.get("RH2M", {})
        ws_p = param_dict.get("WS2M", {})
        
        for date_key in sorted(t2m_p.keys()):
            if len(date_key) != 6:
                continue
            yr = int(date_key[:4])
            mo = int(date_key[4:])
            if mo < 1 or mo > 12:
                # Month 13 is the annual mean in NASA POWER
                continue
                
            days_in_mo = calendar.monthrange(yr, mo)[1]
            prec_daily = prec_p.get(date_key)
            monthly_prec = round(prec_daily * days_in_mo, 2) if prec_daily is not None else None
            
            aligned_weather_records.append({
                "state": st,
                "district": dt,
                "year": yr,
                "month": mo,
                "t2m_mean_c": t2m_p.get(date_key),
                "t2m_max_c": t2m_max_p.get(date_key),
                "t2m_min_c": t2m_min_p.get(date_key),
                "precipitation_mm": monthly_prec,
                "precipitation_rate_mm_per_day": prec_daily,
                "relative_humidity_pct": rh_p.get(date_key),
                "wind_speed_2m_mps": ws_p.get(date_key),
                "nasa_grid_latitude": round(nasa_lat, 4),
                "nasa_grid_longitude": round(nasa_lon, 4),
                "district_centroid_latitude": round(g_lat, 4),
                "district_centroid_longitude": round(g_lon, 4),
                "centroid_distance_km": round(dist_km, 2),
                "data_source": "NASA POWER Agroclimatology Monthly (MERRA-2 Reanalysis)",
                "data_type_classification": "Satellite & Reanalysis Estimate - Not Ground Station Observed",
                "geographic_adequacy": "Adequate macroclimatic representation; topography-smoothed"
            })
            
    # Save assessment CSV
    df_assess = pd.DataFrame(assessment_records)
    df_assess.to_csv(OUT_ASSESSMENT_CSV, index=False)
    logger.info(f"Saved NASA POWER coverage assessment to {OUT_ASSESSMENT_CSV} ({len(df_assess)} districts).")
    
    # Save aligned weather CSV
    df_aligned = pd.DataFrame(aligned_weather_records)
    df_aligned.to_csv(OUT_ALIGNED_CSV, index=False)
    logger.info(f"Saved aligned monthly weather to {OUT_ALIGNED_CSV} ({len(df_aligned)} rows).")
    
    # Save provenance JSON
    prov_data = {
        "title": "NASA POWER 20-District Aligned Monthly Climatology",
        "dataset_name": "nasa_power_monthly_district_weather_20.csv",
        "source": "NASA Prediction Of Worldwide Energy Resources (POWER) Project",
        "source_url": "https://power.larc.nasa.gov/",
        "retrieval_service": "NASA POWER API v2.0 - Temporal Monthly Point",
        "spatial_resolution": "0.5° latitude x 0.5° longitude (~55 km grid spacing)",
        "temporal_range": "1981 to 2023 (43 complete calendar years)",
        "total_districts": len(df_assess),
        "total_monthly_records": len(df_aligned),
        "expected_records_per_district": 43 * 12,
        "parameters_catalog": {
            "T2M": {"name": "Temperature at 2 Meters", "unit": "°C", "type": "Monthly Average"},
            "T2M_MAX": {"name": "Maximum Temperature at 2 Meters", "unit": "°C", "type": "Monthly Mean Maximum"},
            "T2M_MIN": {"name": "Minimum Temperature at 2 Meters", "unit": "°C", "type": "Monthly Mean Minimum"},
            "PRECTOTCORR": {"name": "Corrected Total Precipitation", "unit": "mm/day", "derived_monthly_unit": "mm/month"},
            "RH2M": {"name": "Relative Humidity at 2 Meters", "unit": "%", "type": "Monthly Average"},
            "WS2M": {"name": "Wind Speed at 2 Meters", "unit": "m/s", "type": "Monthly Average"}
        },
        "critical_methodological_distinctions": [
            "Data represents 0.5-degree grid MERRA-2 assimilation reanalysis, NOT ground-observed weather from an IMD meteorological station.",
            "Month 13 (annual mean from NASA POWER) has been explicitly excluded from monthly time-series.",
            "Monthly precipitation (mm) was derived by multiplying daily mean precipitation rate by exact calendar days in each month.",
            "Elevation smoothing inherent in 0.5-deg grid reduces extreme thermal lapse rates in montane districts (e.g. Mandi)."
        ],
        "license": "NASA Open Data Policy (Free and open worldwide access)",
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    
    with open(OUT_PROV_JSON, "w", encoding="utf-8") as f:
        json.dump(prov_data, f, indent=2)
    logger.info(f"Saved weather provenance JSON to {OUT_PROV_JSON}")


if __name__ == "__main__":
    run_assessment()
