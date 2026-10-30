import os
import sys
import json
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

root_dir = r"c:\Users\aouti\Desktop\PS-3\FarmerHelp"

master = pd.read_csv(os.path.join(root_dir, "data", "processed", "master_district_profiles.csv"))
crops = pd.read_csv(os.path.join(root_dir, "data", "crop_expert.csv"))

print(f"Master District Profiles: {len(master)} rows, {len(master.columns)} cols")
print(f"Raw Crop Expert Records: {len(crops)} rows, {len(crops.columns)} cols")

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
crops["Crop"] = crops["Crop"].astype(str).str.strip().replace(crop_name_map)
crops["district_key"] = crops["State_Name"].astype(str).str.strip().str.lower() + "__" + crops["District_Name"].astype(str).str.strip().str.lower()

valid_crops = crops[(crops["zero_production_flag"] == False) & (crops["production_missing_flag"] == False) & (crops["zero_area_flag"] == False)].copy()
valid_crops["Yield_tonnes_per_ha"] = pd.to_numeric(valid_crops["Yield_tonnes_per_ha"], errors="coerce")
valid_crops = valid_crops.dropna(subset=["Yield_tonnes_per_ha", "Crop"])

merged = valid_crops.merge(master, on="district_key", how="inner")
print(f"Merged Records (Crop x District Soil & Weather): {len(merged)} rows, {len(merged.columns)} cols")

TOP_N_CROPS = 28
FEATURES = [
    "ph", "clay_pct", "sand_pct", "silt_pct", "nitrogen_cg_kg", "soc_dg_kg",
    "cec", "bulk_density", "annual_rainfall_mm", "kharif_rainfall_mm",
    "rabi_rainfall_mm", "mean_temperature_c", "max_temperature_c",
    "min_temperature_c", "relative_humidity_pct", "wind_speed_ms"
]

top_crops = merged["Crop"].value_counts().head(TOP_N_CROPS).index.tolist()
filtered = merged[merged["Crop"].isin(top_crops)].copy()
filtered = filtered.dropna(subset=FEATURES + ["Crop", "Yield_tonnes_per_ha"])

filtered["yield_quantile"] = filtered.groupby("Crop")["Yield_tonnes_per_ha"].transform(
    lambda s: pd.qcut(s, q=4, labels=[1, 2, 3, 4], duplicates="drop").astype(int) if len(s.unique()) > 4 else 2
)

train_df = filtered[filtered["yield_quantile"] >= 2].copy()

print(f"\nTraining Dataset (yield_quantile >= 2): {len(train_df)} rows, {len(train_df.columns)} cols")
print("Missing values in features:", train_df[FEATURES].isnull().sum().sum())

print("\n--- CLASS DISTRIBUTION (28 CROPS) ---")
counts = train_df["Crop"].value_counts()
for crop, count in counts.items():
    pct = (count / len(train_df)) * 100
    print(f"  {crop:<28}: {count:>6} rows ({pct:>5.2f}%)")

min_class = counts.min()
max_class = counts.max()
ratio = max_class / min_class
print(f"\nClass balance check: Max={max_class}, Min={min_class}, Imbalance Ratio={ratio:.2f}:1")
