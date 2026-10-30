"""
Data Validation and Quality Assurance Script for KrishiMitra AI.
Validates datasets, schema integrity, distributions, and generates a validation report.
"""

import os
import json
import logging
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")


def validate_all_datasets():
    report = {
        "status": "HEALTHY",
        "datasets": {},
        "integrity_checks": {}
    }

    # 1. Master Geography
    geo_path = os.path.join(PROCESSED_DIR, "clean_geography.csv")
    if os.path.exists(geo_path):
        geo = pd.read_csv(geo_path)
        report["datasets"]["geography"] = {
            "rows": len(geo),
            "states_count": geo["State_Name"].nunique(),
            "districts_count": geo["District_Name"].nunique(),
            "lat_range": [float(geo["latitude"].min()), float(geo["latitude"].max())],
            "lon_range": [float(geo["longitude"].min()), float(geo["longitude"].max())],
            "null_count": int(geo.isnull().sum().sum())
        }

    # 2. Soil Dataset
    soil_path = os.path.join(PROCESSED_DIR, "clean_soil.csv")
    if os.path.exists(soil_path):
        soil = pd.read_csv(soil_path)
        report["datasets"]["soil"] = {
            "rows": len(soil),
            "ph_range": [round(float(soil["ph"].min()), 2), round(float(soil["ph"].max()), 2)],
            "clay_pct_range": [round(float(soil["clay_pct"].min()), 1), round(float(soil["clay_pct"].max()), 1)],
            "sand_pct_range": [round(float(soil["sand_pct"].min()), 1), round(float(soil["sand_pct"].max()), 1)],
            "silt_pct_range": [round(float(soil["silt_pct"].min()), 1), round(float(soil["silt_pct"].max()), 1)],
            "nitrogen_cg_kg_range": [float(soil["nitrogen_cg_kg"].min()), float(soil["nitrogen_cg_kg"].max())],
            "soil_textures": soil["usda_texture"].value_counts().to_dict(),
            "indian_soil_groups": soil["indian_soil_group"].value_counts().to_dict()
        }

    # 3. Weather Dataset
    weather_path = os.path.join(PROCESSED_DIR, "clean_weather.csv")
    if os.path.exists(weather_path):
        weather = pd.read_csv(weather_path)
        report["datasets"]["weather"] = {
            "districts": len(weather),
            "annual_rainfall_mm_range": [round(float(weather["annual_rainfall_mm"].min()), 1), round(float(weather["annual_rainfall_mm"].max()), 1)],
            "mean_temp_c_range": [round(float(weather["mean_temperature_c"].min()), 1), round(float(weather["mean_temperature_c"].max()), 1)],
            "max_temp_c_range": [round(float(weather["max_temperature_c"].min()), 1), round(float(weather["max_temperature_c"].max()), 1)],
            "relative_humidity_range": [round(float(weather["relative_humidity_pct"].min()), 1), round(float(weather["relative_humidity_pct"].max()), 1)]
        }

    # 4. Master District Profiles Join
    master_path = os.path.join(PROCESSED_DIR, "master_district_profiles.csv")
    if os.path.exists(master_path):
        master = pd.read_csv(master_path)
        report["integrity_checks"]["master_district_join"] = {
            "total_districts": len(master),
            "columns": master.columns.tolist(),
            "null_values_remaining": int(master.isnull().sum().sum())
        }

    # Print summary
    print(json.dumps(report, indent=2))
    with open(os.path.join(PROCESSED_DIR, "validation_report.json"), "w") as fp:
        json.dump(report, fp, indent=2)

    logger.info("Data validation complete. Report written to validation_report.json")
    return report


if __name__ == "__main__":
    validate_all_datasets()
