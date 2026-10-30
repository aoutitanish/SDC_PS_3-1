"""
Extracts and standardizes official time series data from Directorate of Economics and Statistics (DES),
Ministry of Agriculture & Farmers Welfare: 'Third Advance Estimate of Production of Food Grains, Oilseeds & Commercial Crops for 2025-26'.

Covers:
- Agricultural years: 2015-16 to 2025-26 (11 agricultural years)
- Granularity: National / All-India
- Commodities: 23 individual crops + composite aggregates
- Seasons: Kharif, Rabi, Summer, Total
- Unit conversions:
  - Food grains & Oilseeds: Lakh Tonnes -> Metric Tonnes (* 100,000)
  - Cotton: Lakh Bales (1 bale = 170 kg) -> Metric Tonnes (* 17,000)
  - Jute & Mesta: Lakh Bales (1 bale = 180 kg) -> Metric Tonnes (* 18,000)
"""

import os
import sys
import json
import logging
import datetime
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_PATH = os.path.join(ROOT, "data", "raw", "market", "real_des_historical", "Time-Series-3rd-AE-2025-26-English.pdf")
RAW_OUT_DIR = os.path.join(ROOT, "data", "raw", "crop_production")
PROC_OUT_DIR = os.path.join(ROOT, "data", "processed", "crop_production")
os.makedirs(RAW_OUT_DIR, exist_ok=True)
os.makedirs(PROC_OUT_DIR, exist_ok=True)

YEARS = [
    "2015-16", "2016-17", "2017-18", "2018-19", "2019-20",
    "2020-21", "2021-22", "2022-23", "2023-24", "2024-25", "2025-26"
]

# Structured table definitions from the official publication
PAGE1_SERIES = [
    {"crop": "Rice", "category": "Cereals", "season": "Kharif", "raw_unit": "Lakh Tonnes", "values": [914.13, 963.03, 971.35, 1020.40, 1022.77, 1052.08, 1110.01, 1105.12, 1132.59, 1227.72, 1247.58]},
    {"crop": "Rice", "category": "Cereals", "season": "Rabi", "raw_unit": "Lakh Tonnes", "values": [129.95, 133.96, 156.22, 144.38, 165.94, 191.60, 184.71, 150.04, 146.01, 161.29, 181.07]},
    {"crop": "Rice", "category": "Cereals", "season": "Summer", "raw_unit": "Lakh Tonnes", "values": [None, None, None, None, None, None, None, 102.40, 99.65, 112.84, 111.59], "note": "Included in Rabi prior to 2022-23"},
    {"crop": "Rice", "category": "Cereals", "season": "Total", "raw_unit": "Lakh Tonnes", "values": [1044.08, 1096.98, 1127.58, 1164.78, 1188.70, 1243.68, 1294.71, 1357.55, 1378.25, 1501.84, 1540.24]},
    
    {"crop": "Wheat", "category": "Cereals", "season": "Rabi", "raw_unit": "Lakh Tonnes", "values": [922.88, 985.10, 998.70, 1035.96, 1078.61, 1095.86, 1077.42, 1105.54, 1132.92, 1179.45, 1206.57]},
    
    {"crop": "Maize", "category": "Cereals", "season": "Kharif", "raw_unit": "Lakh Tonnes", "values": [160.53, 189.19, 201.18, 194.14, 194.29, 215.55, 226.81, 236.74, 222.45, 248.08, 305.09]},
    {"crop": "Maize", "category": "Cereals", "season": "Rabi", "raw_unit": "Lakh Tonnes", "values": [65.14, 69.81, 86.34, 83.02, 93.37, 100.92, 110.49, 116.90, 120.28, 147.53, 200.25]},
    {"crop": "Maize", "category": "Cereals", "season": "Summer", "raw_unit": "Lakh Tonnes", "values": [None, None, None, None, None, None, None, 27.21, 33.92, 38.47, 45.59], "note": "Included in Rabi prior to 2022-23"},
    {"crop": "Maize", "category": "Cereals", "season": "Total", "raw_unit": "Lakh Tonnes", "values": [225.67, 259.00, 287.53, 277.15, 287.66, 316.47, 337.30, 380.85, 376.65, 434.09, 550.93]},
    
    {"crop": "Barley", "category": "Cereals", "season": "Rabi", "raw_unit": "Lakh Tonnes", "values": [14.38, 17.47, 17.81, 16.33, 17.22, 16.56, 13.71, 19.13, 16.99, 19.19, 17.96]},
    
    {"crop": "Jowar", "category": "Nutri / Coarse Cereals", "season": "Kharif", "raw_unit": "Lakh Tonnes", "values": [18.16, 19.64, 22.74, 17.35, 16.97, 19.86, 15.98, 14.80, 15.09, 17.37, 13.13]},
    {"crop": "Jowar", "category": "Nutri / Coarse Cereals", "season": "Rabi", "raw_unit": "Lakh Tonnes", "values": [24.22, 26.04, 25.30, 17.40, 30.75, 28.26, 25.52, 23.22, 31.89, 31.87, 30.09]},
    {"crop": "Jowar", "category": "Nutri / Coarse Cereals", "season": "Summer", "raw_unit": "Lakh Tonnes", "values": [None, None, None, None, None, None, None, 0.13, 0.40, 0.30, 0.34], "note": "Included in Rabi prior to 2022-23"},
    {"crop": "Jowar", "category": "Nutri / Coarse Cereals", "season": "Total", "raw_unit": "Lakh Tonnes", "values": [42.38, 45.68, 48.03, 34.75, 47.72, 48.12, 41.51, 38.14, 47.37, 49.55, 43.56]},
    
    {"crop": "Bajra", "category": "Nutri / Coarse Cereals", "season": "Kharif", "raw_unit": "Lakh Tonnes", "values": [80.67, 97.30, 92.09, 86.64, 103.63, 108.63, 97.81, 103.49, 96.63, 99.78, 94.76]},
    {"crop": "Bajra", "category": "Nutri / Coarse Cereals", "season": "Summer", "raw_unit": "Lakh Tonnes", "values": [None, None, None, None, None, None, None, 10.82, 10.53, 12.27, 13.72], "note": "Included in Kharif prior to 2022-23"},
    {"crop": "Bajra", "category": "Nutri / Coarse Cereals", "season": "Total", "raw_unit": "Lakh Tonnes", "values": [80.67, 97.30, 92.09, 86.64, 103.63, 108.63, 97.81, 114.31, 107.16, 112.05, 108.48]},
    
    {"crop": "Ragi", "category": "Nutri / Coarse Cereals", "season": "Kharif", "raw_unit": "Lakh Tonnes", "values": [18.22, 13.85, 19.85, 12.39, 17.55, 19.98, 17.01, 16.91, 16.70, 19.77, 20.00]},
    {"crop": "Small Millets", "category": "Nutri / Coarse Cereals", "season": "Kharif", "raw_unit": "Lakh Tonnes", "values": [3.91, 4.42, 4.39, 3.33, 3.71, 3.47, 3.67, 3.84, 4.49, 4.56, 3.80]},
    
    {"crop": "Shree Anna / Nutri Cereals", "category": "Aggregate", "season": "Total", "raw_unit": "Lakh Tonnes", "values": [145.17, 161.25, 164.36, 137.11, 172.61, 180.21, 160.00, 173.21, 175.72, 185.92, 175.84]},
    {"crop": "Nutri / Coarse Cereals", "category": "Aggregate", "season": "Total", "raw_unit": "Lakh Tonnes", "values": [385.22, 437.72, 469.70, 430.59, 477.48, 513.24, 511.01, 573.19, 569.36, 639.21, 744.72]},
]

PAGE2_SERIES = [
    {"crop": "Total Cereals", "category": "Aggregate", "season": "Total", "raw_unit": "Lakh Tonnes", "values": [2352.18, 2519.81, 2595.97, 2631.33, 2744.79, 2852.79, 2883.14, 3036.28, 3080.52, 3320.50, 3491.54]},
    
    {"crop": "Tur / Arhar", "category": "Pulses", "season": "Kharif", "raw_unit": "Lakh Tonnes", "values": [25.61, 48.73, 42.90, 33.15, 38.92, 43.16, 42.20, 33.12, 34.17, 36.24, 35.92]},
    {"crop": "Gram / Chickpea", "category": "Pulses", "season": "Rabi", "raw_unit": "Lakh Tonnes", "values": [70.58, 93.78, 113.79, 99.38, 110.78, 119.11, 135.44, 122.67, 110.39, 111.14, 125.14]},
    
    {"crop": "Urad", "category": "Pulses", "season": "Kharif", "raw_unit": "Lakh Tonnes", "values": [12.50, 21.76, 27.51, 23.63, 13.30, 15.07, 18.65, 17.68, 16.04, 13.41, 11.32]},
    {"crop": "Urad", "category": "Pulses", "season": "Rabi", "raw_unit": "Lakh Tonnes", "values": [6.96, 6.55, 7.41, 6.97, 7.52, 7.23, 9.11, 6.33, 4.87, 5.53, 5.70]},
    {"crop": "Urad", "category": "Pulses", "season": "Summer", "raw_unit": "Lakh Tonnes", "values": [None, None, None, None, None, None, None, 2.30, 2.28, 3.48, 4.58], "note": "Included in Rabi prior to 2022-23"},
    {"crop": "Urad", "category": "Pulses", "season": "Total", "raw_unit": "Lakh Tonnes", "values": [19.45, 28.32, 34.92, 30.60, 20.81, 22.30, 27.76, 26.31, 23.19, 22.42, 21.60]},
    
    {"crop": "Moong", "category": "Pulses", "season": "Kharif", "raw_unit": "Lakh Tonnes", "values": [10.00, 16.43, 14.33, 17.84, 18.26, 19.96, 14.80, 17.18, 11.54, 17.74, 19.32]},
    {"crop": "Moong", "category": "Pulses", "season": "Rabi", "raw_unit": "Lakh Tonnes", "values": [5.93, 5.22, 5.90, 6.71, 6.83, 10.89, 16.86, 1.10, 1.01, 1.00, 1.28]},
    {"crop": "Moong", "category": "Pulses", "season": "Summer", "raw_unit": "Lakh Tonnes", "values": [None, None, None, None, None, None, None, 18.48, 18.47, 23.70, 24.31], "note": "Included in Rabi prior to 2022-23"},
    {"crop": "Moong", "category": "Pulses", "season": "Total", "raw_unit": "Lakh Tonnes", "values": [15.93, 21.65, 20.23, 24.55, 25.09, 30.85, 31.66, 36.76, 31.03, 42.44, 44.92]},
    
    {"crop": "Lentil / Masoor", "category": "Pulses", "season": "Rabi", "raw_unit": "Lakh Tonnes", "values": [9.76, 12.24, 16.22, 12.28, 11.03, 14.94, 12.69, 15.59, 17.91, 16.54, 17.62]},
    
    {"crop": "Other Pulses", "category": "Pulses", "season": "Kharif", "raw_unit": "Lakh Tonnes", "values": [7.20, 8.89, 8.31, 6.29, 8.73, 7.99, 6.69, 8.24, 7.99, 9.93, 9.46]},
    {"crop": "Other Pulses", "category": "Pulses", "season": "Rabi", "raw_unit": "Lakh Tonnes", "values": [14.70, 17.68, 17.78, 14.50, 14.89, 16.28, 16.58, 17.90, 17.78, 18.11, 19.44]},
    {"crop": "Other Pulses", "category": "Pulses", "season": "Total", "raw_unit": "Lakh Tonnes", "values": [21.91, 26.57, 26.10, 20.79, 23.62, 24.27, 23.27, 26.14, 25.77, 28.04, 28.90]},
    
    {"crop": "Total Pulses", "category": "Aggregate", "season": "Total", "raw_unit": "Lakh Tonnes", "values": [163.23, 231.29, 254.16, 220.76, 230.25, 254.63, 273.02, 260.58, 242.46, 256.83, 274.09]},
    {"crop": "Total Food Grains", "category": "Aggregate", "season": "Total", "raw_unit": "Lakh Tonnes", "values": [2515.41, 2751.10, 2850.14, 2852.09, 2975.04, 3107.42, 3156.16, 3296.87, 3322.98, 3577.32, 3765.63]},
]

PAGE3_SERIES = [
    {"crop": "Groundnut", "category": "Oilseeds", "season": "Kharif", "raw_unit": "Lakh Tonnes", "values": [53.68, 60.48, 75.95, 53.87, 83.89, 85.28, 84.34, 85.62, 86.60, 104.12, 113.42]},
    {"crop": "Groundnut", "category": "Oilseeds", "season": "Rabi", "raw_unit": "Lakh Tonnes", "values": [13.66, 14.14, 16.57, 13.40, 15.63, 17.16, 17.01, 11.03, 7.55, 6.78, 7.59]},
    {"crop": "Groundnut", "category": "Oilseeds", "season": "Summer", "raw_unit": "Lakh Tonnes", "values": [None, None, None, None, None, None, None, 6.32, 7.65, 8.52, 9.73], "note": "Included in Rabi prior to 2022-23"},
    {"crop": "Groundnut", "category": "Oilseeds", "season": "Total", "raw_unit": "Lakh Tonnes", "values": [67.33, 74.62, 92.53, 67.27, 99.52, 102.44, 101.35, 102.97, 101.80, 119.42, 130.74]},
    
    {"crop": "Castorseed", "category": "Oilseeds", "season": "Kharif", "raw_unit": "Lakh Tonnes", "values": [17.52, 13.76, 15.68, 11.97, 18.42, 16.47, 16.19, 19.80, 19.59, 17.86, 21.57]},
    
    {"crop": "Sesamum", "category": "Oilseeds", "season": "Kharif", "raw_unit": "Lakh Tonnes", "values": [8.50, 7.47, 7.55, 6.89, 6.57, 8.17, 7.89, 3.92, 3.95, 4.44, 4.52]},
    {"crop": "Sesamum", "category": "Oilseeds", "season": "Rabi", "raw_unit": "Lakh Tonnes", "values": [None, None, None, None, None, None, None, 0.31, 0.28, 0.19, 0.31], "note": "Included in Kharif prior to 2022-23"},
    {"crop": "Sesamum", "category": "Oilseeds", "season": "Summer", "raw_unit": "Lakh Tonnes", "values": [None, None, None, None, None, None, None, 3.79, 4.24, 4.31, 4.51], "note": "Included in Kharif prior to 2022-23"},
    {"crop": "Sesamum", "category": "Oilseeds", "season": "Total", "raw_unit": "Lakh Tonnes", "values": [8.50, 7.47, 7.55, 6.89, 6.57, 8.17, 7.89, 8.02, 8.47, 8.93, 9.34]},
    
    {"crop": "Nigerseed", "category": "Oilseeds", "season": "Kharif", "raw_unit": "Lakh Tonnes", "values": [0.74, 0.85, 0.70, 0.45, 0.41, 0.42, 0.33, 0.29, 0.27, 0.40, 0.32]},
    {"crop": "Soybean", "category": "Oilseeds", "season": "Kharif", "raw_unit": "Lakh Tonnes", "values": [85.70, 131.59, 109.33, 132.68, 112.26, 126.10, 129.87, 149.85, 130.62, 152.68, 125.96]},
    
    {"crop": "Sunflower", "category": "Oilseeds", "season": "Kharif", "raw_unit": "Lakh Tonnes", "values": [0.66, 0.98, 0.85, 0.90, 0.92, 0.78, 1.11, 2.04, 0.60, 0.72, 0.88]},
    {"crop": "Sunflower", "category": "Oilseeds", "season": "Rabi", "raw_unit": "Lakh Tonnes", "values": [2.30, 1.53, 1.37, 1.26, 1.21, 1.51, 1.39, 1.17, 0.74, 1.21, 1.38]},
    {"crop": "Sunflower", "category": "Oilseeds", "season": "Summer", "raw_unit": "Lakh Tonnes", "values": [None, None, None, None, None, None, None, 0.43, 0.39, 0.43, 0.44], "note": "Included in Rabi prior to 2022-23"},
    {"crop": "Sunflower", "category": "Oilseeds", "season": "Total", "raw_unit": "Lakh Tonnes", "values": [2.96, 2.51, 2.22, 2.16, 2.13, 2.28, 2.50, 3.63, 1.73, 2.36, 2.70]},
    
    {"crop": "Rapeseed & Mustard", "category": "Oilseeds", "season": "Rabi", "raw_unit": "Lakh Tonnes", "values": [67.97, 79.17, 84.30, 92.56, 91.24, 102.10, 119.63, 126.43, 132.59, 126.67, 137.68]},
    {"crop": "Linseed", "category": "Oilseeds", "season": "Rabi", "raw_unit": "Lakh Tonnes", "values": [1.25, 1.84, 1.74, 0.99, 1.21, 1.11, 1.26, 1.67, 1.13, 1.12, 1.61]},
    {"crop": "Safflower", "category": "Oilseeds", "season": "Rabi", "raw_unit": "Lakh Tonnes", "values": [0.53, 0.94, 0.55, 0.25, 0.44, 0.36, 0.61, 0.90, 0.50, 0.43, 0.66]},
    {"crop": "Total Oil Seeds", "category": "Aggregate", "season": "Total", "raw_unit": "Lakh Tonnes", "values": [252.51, 312.76, 314.59, 315.22, 332.19, 359.46, 379.63, 413.55, 396.69, 429.89, 430.59]},
    
    {"crop": "Sugarcane", "category": "Commercial Crops", "season": "Kharif", "raw_unit": "Lakh Tonnes", "values": [3484.48, 3060.69, 3799.05, 4054.16, 3705.00, 4053.99, 4394.25, 4905.33, 4531.58, 4546.11, 5000.63]},
    {"crop": "Cotton", "category": "Commercial Crops", "season": "Kharif", "raw_unit": "Lakh Bales (170 kg/bale)", "values": [300.05, 325.77, 328.05, 280.42, 360.65, 352.48, 311.18, 336.60, 325.22, 297.24, 290.24]},
    {"crop": "Jute", "category": "Commercial Crops", "season": "Kharif", "raw_unit": "Lakh Bales (180 kg/bale)", "values": [99.40, 104.32, 95.91, 94.97, 94.46, 89.53, 97.62, 89.89, 92.52, 84.88, 91.76]},
    {"crop": "Mesta", "category": "Commercial Crops", "season": "Kharif", "raw_unit": "Lakh Bales (180 kg/bale)", "values": [5.83, 5.30, 4.42, 3.23, 4.31, 4.02, 3.87, 4.03, 4.41, 3.13, 2.27]},
    {"crop": "Jute & Mesta", "category": "Commercial Crops", "season": "Kharif", "raw_unit": "Lakh Bales (180 kg/bale)", "values": [105.24, 109.62, 100.33, 98.20, 98.77, 93.54, 101.49, 93.92, 96.92, 88.02, 94.03]}
]

ALL_SERIES = PAGE1_SERIES + PAGE2_SERIES + PAGE3_SERIES


def compute_metric_tonnes(raw_val, raw_unit):
    if raw_val is None:
        return None
    if "170 kg/bale" in raw_unit:
        # 1 Lakh Bales = 100,000 bales * 170 kg = 17,000,000 kg = 17,000 Metric Tonnes
        return round(raw_val * 17000.0, 2)
    elif "180 kg/bale" in raw_unit:
        # 1 Lakh Bales = 100,000 bales * 180 kg = 18,000,000 kg = 18,000 Metric Tonnes
        return round(raw_val * 18000.0, 2)
    elif "Lakh Tonnes" in raw_unit:
        # 1 Lakh Tonne = 100,000 Metric Tonnes
        return round(raw_val * 100000.0, 2)
    else:
        return raw_val


def extract_and_save():
    records = []
    for s in ALL_SERIES:
        crop = s["crop"]
        category = s["category"]
        season = s["season"]
        raw_unit = s["raw_unit"]
        note = s.get("note", "")
        
        for idx, yr in enumerate(YEARS):
            raw_val = s["values"][idx]
            cal_start = int(yr.split("-")[0])
            cal_end = cal_start + 1
            data_status = "3rd Advance Estimate" if yr == "2025-26" else "Final Official Estimate"
            
            tonnes = compute_metric_tonnes(raw_val, raw_unit)
            
            records.append({
                "agricultural_year": yr,
                "calendar_year_start": cal_start,
                "calendar_year_end": cal_end,
                "geographic_granularity": "National / All-India",
                "state": "All India",
                "district": "All India",
                "crop_category": category,
                "crop_name": crop,
                "season": season,
                "production_raw_value": raw_val,
                "production_raw_unit": raw_unit,
                "production_metric_tonnes": tonnes,
                "data_status": data_status,
                "notes": note,
                "source_authority": "Directorate of Economics and Statistics (DES), DA&FW, GoI",
                "source_document": "Time Series of Area, Production and Yield (3rd Advance Estimates 2025-26)",
                "as_on_date": "2026-05-27"
            })
            
    df = pd.DataFrame(records)
    
    # Save structured raw JSON
    raw_json_path = os.path.join(RAW_OUT_DIR, "des_apy_national_2015_2026_raw.json")
    with open(raw_json_path, "w", encoding="utf-8") as f:
        json.dump({
            "metadata": {
                "source_title": "Third Advance Estimate of Production of Food Grains, Oilseeds & Commercial Crops for 2025-26",
                "source_authority": "Ministry of Agriculture & Farmers Welfare, Department of Agriculture & Farmers Welfare (DA&FW)",
                "as_on_date": "2026-05-27",
                "publication_pdf": "data/raw/market/real_des_historical/Time-Series-3rd-AE-2025-26-English.pdf",
                "years_covered": YEARS,
                "record_count": len(records),
                "crops_covered_count": int(len(set(s['crop'] for s in ALL_SERIES))),
                "extracted_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "license": "Government Open Data License India (GODL-India) v1.0"
            },
            "records": records
        }, f, indent=2)
    logger.info(f"Saved raw JSON to {raw_json_path}")
    
    # Save processed standardized CSV
    csv_path = os.path.join(PROC_OUT_DIR, "des_national_production_2015_2026.csv")
    df.to_csv(csv_path, index=False)
    logger.info(f"Saved standardized processed CSV to {csv_path} ({len(df)} rows)")
    
    # Save provenance manifest
    prov_path = os.path.join(PROC_OUT_DIR, "provenance_manifest.json")
    with open(prov_path, "w", encoding="utf-8") as f:
        json.dump({
            "dataset_name": "des_national_production_2015_2026.csv",
            "source": "Directorate of Economics & Statistics (DES), Ministry of Agriculture & Farmers Welfare, GoI",
            "granularity": "National / All-India",
            "years_span": "2015-16 to 2025-26 (11 agricultural years)",
            "total_rows": int(len(df)),
            "crops_count": int(df['crop_name'].nunique()),
            "non_null_production_rows": int(df['production_metric_tonnes'].notna().sum()),
            "unit_conversions": {
                "Lakh Tonnes": "100,000 Metric Tonnes",
                "Cotton Lakh Bales": "17,000 Metric Tonnes (1 bale = 170 kg)",
                "Jute & Mesta Lakh Bales": "18,000 Metric Tonnes (1 bale = 180 kg)"
            },
            "district_level_status": (
                "District-level APY for 2016+ is published on data.desagri.gov.in. "
                "As of 2026-10-15, direct public connection to data.desagri.gov.in is restricted/refused. "
                "No district synthetic interpolation has been performed. This national series is preserved "
                "as authoritative macroeconomic reference data."
            ),
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }, f, indent=2)
    logger.info(f"Saved provenance manifest to {prov_path}")


if __name__ == "__main__":
    extract_and_save()
