"""
Inspect existing datasets to understand current state before acquisition.
"""
import os
import sys
import json
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
PROC = os.path.join(DATA, "processed")

print("=" * 70)
print("EXISTING DATASET INSPECTION")
print("=" * 70)

# crop_expert.csv
crop_path = os.path.join(DATA, "crop_expert.csv")
crop = pd.read_csv(crop_path)
print("\n=== crop_expert.csv ===")
print(f"  Rows       : {len(crop):,}")
print(f"  Columns    : {list(crop.columns)}")
crop_year_col = [c for c in crop.columns if 'year' in c.lower() or 'Year' in c]
if crop_year_col:
    yrs = sorted(crop[crop_year_col[0]].dropna().unique().tolist())
    print(f"  Years      : {yrs[0]} - {yrs[-1]} ({len(yrs)} years)")
state_col = [c for c in crop.columns if 'state' in c.lower()]
if state_col:
    print(f"  States     : {crop[state_col[0]].nunique()} unique")
dist_col = [c for c in crop.columns if 'district' in c.lower()]
if dist_col:
    print(f"  Districts  : {crop[dist_col[0]].nunique()} unique")
crop_col = [c for c in crop.columns if c.lower() == 'crop']
if crop_col:
    print(f"  Crops      : {crop[crop_col[0]].nunique()} unique")
season_col = [c for c in crop.columns if 'season' in c.lower()]
if season_col:
    print(f"  Seasons    : {crop[season_col[0]].unique().tolist()}")
print(f"  Missing %  : {crop.isnull().mean().mul(100).round(2).to_dict()}")

# soil_expert.csv
soil_path = os.path.join(DATA, "soil_expert.csv")
soil = pd.read_csv(soil_path)
print("\n=== soil_expert.csv ===")
print(f"  Rows       : {len(soil):,}")
print(f"  Columns    : {list(soil.columns)}")
print(f"  Missing %  : {soil.isnull().mean().mul(100).round(2).to_dict()}")
print(f"  Head       : {soil.head(2).to_string()}")

# weather_expert.csv
wx_path = os.path.join(DATA, "weather_expert.csv")
wx = pd.read_csv(wx_path)
print("\n=== weather_expert.csv ===")
print(f"  Rows       : {len(wx):,}")
print(f"  Columns    : {list(wx.columns)}")
print(f"  Missing %  : {wx.isnull().mean().mul(100).round(2).to_dict()}")

# master_geography.csv
geo_path = os.path.join(DATA, "master_geography.csv")
geo = pd.read_csv(geo_path)
print("\n=== master_geography.csv ===")
print(f"  Rows       : {len(geo):,}")
print(f"  Columns    : {list(geo.columns)}")
if 'state' in geo.columns:
    print(f"  States     : {geo['state'].nunique()} unique")

# master_district_profiles.csv
mdp_path = os.path.join(PROC, "master_district_profiles.csv")
if os.path.exists(mdp_path):
    mdp = pd.read_csv(mdp_path)
    print("\n=== master_district_profiles.csv ===")
    print(f"  Rows       : {len(mdp):,}")
    print(f"  Columns    : {list(mdp.columns)}")
    print(f"  Missing %  : {mdp.isnull().mean().mul(100).round(2).to_dict()}")

# clean_crops.parquet
parquet_path = os.path.join(PROC, "clean_crops.parquet")
if os.path.exists(parquet_path):
    cc = pd.read_parquet(parquet_path)
    print("\n=== clean_crops.parquet ===")
    print(f"  Rows       : {len(cc):,}")
    print(f"  Columns    : {list(cc.columns)}")

# historical_mandi_prices.json
mandi_path = os.path.join(PROC, "historical_market", "historical_mandi_prices.json")
if os.path.exists(mandi_path):
    with open(mandi_path) as f:
        mandi = json.load(f)
    print("\n=== historical_mandi_prices.json ===")
    print(f"  Records    : {len(mandi):,}")
    if mandi:
        print(f"  Keys       : {list(mandi[0].keys())}")
        dates = sorted(set(r.get('date','') for r in mandi if r.get('date','')))
        if dates:
            print(f"  Date range : {dates[0]} to {dates[-1]}")

print("\n" + "=" * 70)
print("INSPECTION COMPLETE")
print("=" * 70)
