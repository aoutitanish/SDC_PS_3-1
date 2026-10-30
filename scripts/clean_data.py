"""
Data Cleaning and Feature Engineering Script for KrishiMitra AI.
Processes master_geography, soil_expert, weather_expert, and crop_expert datasets.
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
os.makedirs(PROCESSED_DIR, exist_ok=True)


def determine_usda_texture(sand_pct: float, silt_pct: float, clay_pct: float) -> str:
    """Classify USDA soil texture from percentages."""
    if clay_pct >= 40 and sand_pct <= 45 and silt_pct < 40:
        return "Clay"
    elif clay_pct >= 35 and sand_pct >= 45:
        return "Sandy Clay"
    elif clay_pct >= 40 and silt_pct >= 40:
        return "Silty Clay"
    elif 27 <= clay_pct < 40 and sand_pct <= 45:
        return "Clay Loam"
    elif 20 <= clay_pct < 35 and silt_pct < 28 and sand_pct >= 45:
        return "Sandy Clay Loam"
    elif 27 <= clay_pct < 40 and sand_pct < 20:
        return "Silty Clay Loam"
    elif (clay_pct < 20 and sand_pct > 52) or (clay_pct < 7 and silt_pct < 50 and sand_pct > 43):
        return "Sandy Loam"
    elif (silt_pct >= 50 and 12 <= clay_pct < 27) or (silt_pct >= 50 and clay_pct < 12):
        return "Silt Loam"
    elif silt_pct >= 80 and clay_pct < 12:
        return "Silt"
    elif sand_pct >= 70 and clay_pct < 15:
        return "Loamy Sand"
    elif sand_pct > 85:
        return "Sand"
    else:
        return "Loam"


def determine_indian_soil_group(texture: str, ph: float, soc: float, state: str) -> str:
    """Classify broad Indian soil type."""
    state_lower = str(state).lower()
    if texture in ["Clay", "Silty Clay", "Clay Loam"] and ph >= 6.8:
        return "Black Soil (Regur/Vertisol)"
    elif "rajasthan" in state_lower or texture in ["Sand", "Loamy Sand"]:
        return "Desert / Arid Soil"
    elif ph < 6.0 and ("kerala" in state_lower or "karnataka" in state_lower or "assam" in state_lower or "odisha" in state_lower):
        return "Laterite Soil"
    elif ph < 6.5 and soc > 200:
        return "Red and Yellow Soil"
    elif "punjab" in state_lower or "haryana" in state_lower or "uttar pradesh" in state_lower or "bihar" in state_lower or "bengal" in state_lower:
        return "Alluvial Soil"
    elif ph > 7.8:
        return "Saline / Alkaline Soil"
    else:
        return "Red / Mixed Alluvial Soil"


def clean_geography(filepath: str) -> pd.DataFrame:
    logger.info("Cleaning master geography...")
    df = pd.read_csv(filepath)
    df["State_Name"] = df["State_Name"].astype(str).str.strip()
    df["District_Name"] = df["District_Name"].astype(str).str.strip()
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df = df.dropna(subset=["State_Name", "District_Name"]).drop_duplicates(subset=["State_Name", "District_Name"])
    df["district_key"] = df["State_Name"].str.lower() + "__" + df["District_Name"].str.lower()
    logger.info(f"Geography records: {len(df)}")
    return df


def clean_soil(filepath: str, geo_df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Cleaning soil expert dataset...")
    df = pd.read_csv(filepath)
    df["State_Name"] = df["State_Name"].astype(str).str.strip()
    df["District_Name"] = df["District_Name"].astype(str).str.strip()
    df["district_key"] = df["State_Name"].str.lower() + "__" + df["District_Name"].str.lower()

    # Scale pH (phh2o is stored as pH*10)
    df["ph"] = pd.to_numeric(df["phh2o_0_5cm"], errors="coerce") / 10.0
    df["clay_pct"] = pd.to_numeric(df["clay_0_5cm"], errors="coerce") / 10.0
    df["sand_pct"] = pd.to_numeric(df["sand_0_5cm"], errors="coerce") / 10.0
    df["silt_pct"] = pd.to_numeric(df["silt_0_5cm"], errors="coerce") / 10.0
    df["nitrogen_cg_kg"] = pd.to_numeric(df["nitrogen_0_5cm"], errors="coerce")
    df["soc_dg_kg"] = pd.to_numeric(df["soc_0_5cm"], errors="coerce")
    df["cec"] = pd.to_numeric(df["cec_0_5cm"], errors="coerce")
    df["bulk_density"] = pd.to_numeric(df["bdod_0_5cm"], errors="coerce") / 100.0

    # Impute missing values per state median, then overall median
    num_cols = ["ph", "clay_pct", "sand_pct", "silt_pct", "nitrogen_cg_kg", "soc_dg_kg", "cec", "bulk_density"]
    for col in num_cols:
        state_medians = df.groupby("State_Name")[col].transform("median")
        df[col] = df[col].fillna(state_medians).fillna(df[col].median())

    # Derive USDA texture and Indian Soil Group
    df["usda_texture"] = df.apply(lambda r: determine_usda_texture(r["sand_pct"], r["silt_pct"], r["clay_pct"]), axis=1)
    df["indian_soil_group"] = df.apply(lambda r: determine_indian_soil_group(r["usda_texture"], r["ph"], r["soc_dg_kg"], r["State_Name"]), axis=1)

    # Nitrogen level category
    df["nitrogen_level"] = pd.cut(
        df["nitrogen_cg_kg"],
        bins=[-np.inf, 150, 250, np.inf],
        labels=["Low", "Medium", "High"]
    )

    # pH level category
    df["ph_category"] = pd.cut(
        df["ph"],
        bins=[-np.inf, 6.0, 7.5, np.inf],
        labels=["Acidic", "Neutral / Optimal", "Alkaline"]
    )

    logger.info(f"Cleaned soil records: {len(df)}")
    return df


def clean_weather(filepath: str) -> pd.DataFrame:
    logger.info("Cleaning and aggregating weather expert dataset...")
    df = pd.read_csv(filepath)
    df["State_Name"] = df["State_Name"].astype(str).str.strip()
    df["District_Name"] = df["District_Name"].astype(str).str.strip()
    df["district_key"] = df["State_Name"].str.lower() + "__" + df["District_Name"].str.lower()

    # Aggregate by district across years
    # Kharif = Months 6,7,8,9,10; Rabi = Months 11,12,1,2,3,4; Summer = Months 3,4,5
    df["is_kharif"] = df["MONTH"].isin([6, 7, 8, 9, 10])
    df["is_rabi"] = df["MONTH"].isin([11, 12, 1, 2, 3, 4])
    df["is_summer"] = df["MONTH"].isin([3, 4, 5])

    # Annual rainfall calculation (sum per year per district, then average over years)
    yearly = df.groupby(["district_key", "State_Name", "District_Name", "YEAR"]).agg(
        annual_rain_imd=("Rainfall_mm_IMD", "sum"),
        annual_rain_nasa=("Rainfall_mm_NASA_estimate", lambda x: x.sum() * 30.0),
        mean_t2m=("T2M", "mean"),
        max_t2m=("T2M_MAX", "mean"),
        min_t2m=("T2M_MIN", "mean"),
        mean_rh=("RH2M", "mean"),
        mean_ws=("WS2M", "mean")
    ).reset_index()

    district_weather = yearly.groupby(["district_key", "State_Name", "District_Name"]).agg(
        annual_rainfall_mm=("annual_rain_imd", "mean"),
        mean_temperature_c=("mean_t2m", "mean"),
        max_temperature_c=("max_t2m", "mean"),
        min_temperature_c=("min_t2m", "mean"),
        relative_humidity_pct=("mean_rh", "mean"),
        wind_speed_ms=("mean_ws", "mean")
    ).reset_index()

    # Calculate seasonal rainfall
    kharif_rain = df[df["is_kharif"]].groupby(["district_key", "YEAR"])["Rainfall_mm_IMD"].sum().groupby("district_key").mean().reset_index()
    kharif_rain.rename(columns={"Rainfall_mm_IMD": "kharif_rainfall_mm"}, inplace=True)

    rabi_rain = df[df["is_rabi"]].groupby(["district_key", "YEAR"])["Rainfall_mm_IMD"].sum().groupby("district_key").mean().reset_index()
    rabi_rain.rename(columns={"Rainfall_mm_IMD": "rabi_rainfall_mm"}, inplace=True)

    district_weather = district_weather.merge(kharif_rain, on="district_key", how="left")
    district_weather = district_weather.merge(rabi_rain, on="district_key", how="left")

    district_weather["kharif_rainfall_mm"] = district_weather["kharif_rainfall_mm"].fillna(district_weather["annual_rainfall_mm"] * 0.75)
    district_weather["rabi_rainfall_mm"] = district_weather["rabi_rainfall_mm"].fillna(district_weather["annual_rainfall_mm"] * 0.20)

    # Impute missing with state medians
    for col in ["annual_rainfall_mm", "mean_temperature_c", "max_temperature_c", "min_temperature_c", "relative_humidity_pct", "wind_speed_ms"]:
        state_med = district_weather.groupby("State_Name")[col].transform("median")
        district_weather[col] = district_weather[col].fillna(state_med).fillna(district_weather[col].median())

    logger.info(f"Aggregated weather profiles for {len(district_weather)} districts")
    return district_weather


def clean_crop_expert(filepath: str) -> pd.DataFrame:
    logger.info("Cleaning crop expert dataset...")
    df = pd.read_csv(filepath)
    df["State_Name"] = df["State_Name"].astype(str).str.strip()
    df["District_Name"] = df["District_Name"].astype(str).str.strip()
    df["district_key"] = df["State_Name"].str.lower() + "__" + df["District_Name"].str.lower()
    df["Crop"] = df["Crop"].astype(str).str.strip()
    df["Season"] = df["Season"].astype(str).str.strip()

    # Filter out empty or suspicious yield rows
    valid = df[(df["zero_production_flag"] == False) & (df["production_missing_flag"] == False) & (df["zero_area_flag"] == False)].copy()
    valid["Yield_tonnes_per_ha"] = pd.to_numeric(valid["Yield_tonnes_per_ha"], errors="coerce")
    valid = valid.dropna(subset=["Yield_tonnes_per_ha", "Crop"])

    logger.info(f"Valid crop cultivation records: {len(valid)} across {valid['Crop'].nunique()} crops")
    return valid


def build_unified_master_table():
    logger.info("Building unified agricultural dataset...")
    geo_df = clean_geography(os.path.join(DATA_DIR, "master_geography.csv"))
    soil_df = clean_soil(os.path.join(DATA_DIR, "soil_expert.csv"), geo_df)
    weather_df = clean_weather(os.path.join(DATA_DIR, "weather_expert.csv"))
    crop_df = clean_crop_expert(os.path.join(DATA_DIR, "crop_expert.csv"))

    # Save cleaned individual tables
    geo_df.to_csv(os.path.join(PROCESSED_DIR, "clean_geography.csv"), index=False)
    soil_df.to_csv(os.path.join(PROCESSED_DIR, "clean_soil.csv"), index=False)
    weather_df.to_csv(os.path.join(PROCESSED_DIR, "clean_weather.csv"), index=False)
    crop_df.to_parquet(os.path.join(PROCESSED_DIR, "clean_crops.parquet"), index=False)

    # Build district profile master table (geo + soil + weather)
    master_district = geo_df.merge(
        soil_df.drop(columns=["State_Name", "District_Name", "ph_outlier_flag"], errors="ignore"),
        on="district_key",
        how="inner"
    ).merge(
        weather_df.drop(columns=["State_Name", "District_Name"], errors="ignore"),
        on="district_key",
        how="inner"
    )

    # Impute any remaining nulls
    master_district = master_district.bfill().ffill()
    master_district.to_csv(os.path.join(PROCESSED_DIR, "master_district_profiles.csv"), index=False)
    logger.info(f"Master district profiles saved: {len(master_district)} districts with soil & climate data")

    # Generate Crop Agronomy Summary per crop
    crop_summary = crop_df.groupby("Crop").agg(
        total_records=("Production", "count"),
        total_production=("Production", "sum"),
        mean_yield=("Yield_tonnes_per_ha", "mean"),
        max_yield=("Yield_tonnes_per_ha", "max"),
        top_states=("State_Name", lambda x: list(x.value_counts().head(5).index)),
        top_seasons=("Season", lambda x: list(x.value_counts().head(3).index))
    ).reset_index()

    crop_summary.to_json(os.path.join(PROCESSED_DIR, "crop_summary.json"), orient="records", indent=2)
    logger.info(f"Crop summary saved for {len(crop_summary)} crops")

    return master_district, crop_df


if __name__ == "__main__":
    build_unified_master_table()
