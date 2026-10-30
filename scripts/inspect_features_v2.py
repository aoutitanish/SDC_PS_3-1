import os
import sys
import json
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

root_dir = r"c:\Users\aouti\Desktop\PS-3\FarmerHelp"
data_dir = os.path.join(root_dir, "data")
proc_dir = os.path.join(data_dir, "processed")

print("=== 1. INSPECTING DATASET COLUMNS & NULLS ===")

crop_expert = pd.read_csv(os.path.join(data_dir, "crop_expert.csv"))
master = pd.read_csv(os.path.join(proc_dir, "master_district_profiles.csv"))
soil = pd.read_csv(os.path.join(proc_dir, "clean_soil.csv"))
weather = pd.read_csv(os.path.join(proc_dir, "clean_weather.csv"))

print(f"\n--- CROP EXPERT ({len(crop_expert)} rows) ---")
for col in crop_expert.columns:
    nulls = crop_expert[col].isnull().sum()
    null_pct = (nulls / len(crop_expert)) * 100
    dtype = str(crop_expert[col].dtype)
    print(f"  {col:<28}: dtype={dtype:<10} nulls={nulls:>6} ({null_pct:>5.2f}%)")

print(f"\n--- MASTER DISTRICT PROFILES ({len(master)} rows) ---")
for col in master.columns:
    nulls = master[col].isnull().sum()
    null_pct = (nulls / len(master)) * 100
    dtype = str(master[col].dtype)
    print(f"  {col:<28}: dtype={dtype:<10} nulls={nulls:>6} ({null_pct:>5.2f}%)")

print("\n--- MERGING CROP + MASTER TO CHECK FEATURE AVAILABILITY ---")
crop_name_map = {
    "Cotton(lint)": "Cotton",
    "Soyabean": "Soybean",
    "Moong (Green Gram)": "Moong (Green Gram)",
    "Gram": "Gram (Chickpea)",
    "Arhar/Tur": "Arhar/Tur (Pigeon Pea)",
    "Jowar": "Jowar (Sorghum)",
    "Bajra": "Bajra (Pearl Millet)",
    "Ragi": "Ragi (Finger Millet)",
    "Rapeseed &Mustard": "Mustard / Rapeseed"
}
crop_expert["Crop"] = crop_expert["Crop"].astype(str).str.strip().replace(crop_name_map)
crop_expert["district_key"] = crop_expert["State_Name"].astype(str).str.strip().str.lower() + "__" + crop_expert["District_Name"].astype(str).str.strip().str.lower()

merged = crop_expert.merge(master, on="district_key", how="inner")
print(f"Merged Total Rows: {len(merged)}")

print("\nSample values of key potential features in Merged dataset:")
cols_to_check = ["Season", "State_Name_x", "District_Name_x", "usda_texture", "indian_soil_group", "nitrogen_level", "ph_category", "annual_rainfall_mm", "kharif_rainfall_mm", "rabi_rainfall_mm", "Crop"]
for col in cols_to_check:
    if col in merged.columns:
        print(f"\nFeature [{col}] unique count = {merged[col].nunique()}:")
        print("  Top 5 values:", merged[col].value_counts().head(5).to_dict())
