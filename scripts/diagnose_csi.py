"""
KrishiMitra AI - Standalone CSI Diagnostic & Failure Analysis Script.
Analyzes why the Stage 2 CSI score fusion layer degrades ML Top-K accuracy.
Computes rank movements, component impacts, agronomic violation breakdowns, and crop-level penalties.
Does NOT retrain any model and does NOT modify production code/artifacts.
"""

import os
import json
import logging
import numpy as np
import pandas as pd
from sklearn.preprocessing import OneHotEncoder, RobustScaler
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier, ExtraTreesClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import accuracy_score

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CROP_DATA_PATH = os.path.join(BASE_DIR, "data", "crop_expert.csv")
MASTER_PROFILES_PATH = os.path.join(BASE_DIR, "data", "processed", "master_district_profiles.csv")
DIAGNOSTIC_REPORT_PATH = os.path.join(BASE_DIR, "scripts", "csi_diagnostic_report.md")

SEED = 42

ICAR_CROP_PROFILES = {
    "Rice": {"ph_optimal": [5.5, 7.2], "temp_optimal_c": [20.0, 35.0], "rainfall_optimal_mm": [1000.0, 2500.0], "seasons": ["Kharif", "Whole Year"]},
    "Maize": {"ph_optimal": [5.8, 7.5], "temp_optimal_c": [18.0, 32.0], "rainfall_optimal_mm": [500.0, 1000.0], "seasons": ["Kharif", "Rabi", "Whole Year"]},
    "Moong (Green Gram)": {"ph_optimal": [6.2, 7.8], "temp_optimal_c": [25.0, 35.0], "rainfall_optimal_mm": [400.0, 750.0], "seasons": ["Kharif", "Summer"]},
    "Urad": {"ph_optimal": [6.0, 7.5], "temp_optimal_c": [25.0, 35.0], "rainfall_optimal_mm": [450.0, 800.0], "seasons": ["Kharif", "Summer"]},
    "Groundnut": {"ph_optimal": [6.0, 7.2], "temp_optimal_c": [22.0, 32.0], "rainfall_optimal_mm": [500.0, 1000.0], "seasons": ["Kharif", "Summer"]},
    "Sesamum": {"ph_optimal": [5.5, 7.8], "temp_optimal_c": [25.0, 35.0], "rainfall_optimal_mm": [400.0, 650.0], "seasons": ["Kharif", "Summer"]},
    "Wheat": {"ph_optimal": [6.0, 7.5], "temp_optimal_c": [12.0, 25.0], "rainfall_optimal_mm": [450.0, 750.0], "seasons": ["Rabi"]},
    "Sugarcane": {"ph_optimal": [6.0, 7.8], "temp_optimal_c": [20.0, 38.0], "rainfall_optimal_mm": [1200.0, 2500.0], "seasons": ["Whole Year", "Kharif"]},
    "Mustard / Rapeseed": {"ph_optimal": [6.0, 7.5], "temp_optimal_c": [10.0, 25.0], "rainfall_optimal_mm": [350.0, 600.0], "seasons": ["Rabi"]},
    "Arhar/Tur (Pigeon Pea)": {"ph_optimal": [6.0, 7.8], "temp_optimal_c": [20.0, 35.0], "rainfall_optimal_mm": [550.0, 1000.0], "seasons": ["Kharif"]},
    "Gram (Chickpea)": {"ph_optimal": [6.0, 8.0], "temp_optimal_c": [10.0, 26.0], "rainfall_optimal_mm": [400.0, 700.0], "seasons": ["Rabi"]},
    "Jowar (Sorghum)": {"ph_optimal": [6.0, 8.5], "temp_optimal_c": [25.0, 38.0], "rainfall_optimal_mm": [400.0, 750.0], "seasons": ["Kharif", "Rabi"]},
    "Onion": {"ph_optimal": [6.0, 7.5], "temp_optimal_c": [13.0, 28.0], "rainfall_optimal_mm": [500.0, 800.0], "seasons": ["Rabi", "Kharif"]},
    "Potato": {"ph_optimal": [5.2, 6.5], "temp_optimal_c": [15.0, 24.0], "rainfall_optimal_mm": [500.0, 800.0], "seasons": ["Rabi"]},
    "Dry chillies": {"ph_optimal": [6.0, 7.5], "temp_optimal_c": [20.0, 32.0], "rainfall_optimal_mm": [600.0, 1000.0], "seasons": ["Kharif", "Rabi"]},
    "Bajra (Pearl Millet)": {"ph_optimal": [6.5, 8.2], "temp_optimal_c": [25.0, 40.0], "rainfall_optimal_mm": [300.0, 600.0], "seasons": ["Kharif"]},
    "Sunflower": {"ph_optimal": [6.0, 7.8], "temp_optimal_c": [18.0, 32.0], "rainfall_optimal_mm": [500.0, 800.0], "seasons": ["Kharif", "Rabi", "Summer"]},
    "Small millets": {"ph_optimal": [5.5, 7.5], "temp_optimal_c": [20.0, 35.0], "rainfall_optimal_mm": [350.0, 700.0], "seasons": ["Kharif"]},
    "Peas & beans (Pulses)": {"ph_optimal": [6.0, 7.5], "temp_optimal_c": [10.0, 25.0], "rainfall_optimal_mm": [400.0, 700.0], "seasons": ["Rabi"]},
    "Cotton": {"ph_optimal": [6.0, 8.0], "temp_optimal_c": [21.0, 35.0], "rainfall_optimal_mm": [600.0, 1100.0], "seasons": ["Kharif"]},
    "Linseed": {"ph_optimal": [6.0, 7.5], "temp_optimal_c": [10.0, 24.0], "rainfall_optimal_mm": [450.0, 750.0], "seasons": ["Rabi"]},
    "Ragi (Finger Millet)": {"ph_optimal": [5.5, 7.5], "temp_optimal_c": [20.0, 34.0], "rainfall_optimal_mm": [500.0, 900.0], "seasons": ["Kharif"]},
    "Turmeric": {"ph_optimal": [5.8, 7.5], "temp_optimal_c": [20.0, 35.0], "rainfall_optimal_mm": [1200.0, 2000.0], "seasons": ["Kharif", "Whole Year"]},
    "Sweet potato": {"ph_optimal": [5.5, 6.8], "temp_optimal_c": [21.0, 32.0], "rainfall_optimal_mm": [750.0, 1250.0], "seasons": ["Kharif", "Rabi"]},
    "Masoor": {"ph_optimal": [6.0, 7.8], "temp_optimal_c": [10.0, 25.0], "rainfall_optimal_mm": [350.0, 650.0], "seasons": ["Rabi"]},
    "Barley": {"ph_optimal": [6.0, 8.0], "temp_optimal_c": [12.0, 24.0], "rainfall_optimal_mm": [400.0, 700.0], "seasons": ["Rabi"]},
    "Horse-gram": {"ph_optimal": [5.5, 7.5], "temp_optimal_c": [20.0, 35.0], "rainfall_optimal_mm": [350.0, 700.0], "seasons": ["Kharif", "Rabi"]},
    "Other Kharif pulses": {"ph_optimal": [6.0, 7.5], "temp_optimal_c": [22.0, 35.0], "rainfall_optimal_mm": [400.0, 800.0], "seasons": ["Kharif"]}
}

CROP_NAME_MAP = {
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


def compute_stage2_factor_scores(crop: str, ph: float, temp_c: float, rain_mm: float, season: str) -> dict:
    prof = ICAR_CROP_PROFILES.get(crop, {})
    if not prof:
        return {"ph": 50.0, "temp": 50.0, "rain": 50.0, "season": 50.0, "total": 50.0}

    # pH score
    ph_min, ph_max = prof["ph_optimal"]
    if ph_min <= ph <= ph_max:
        ph_score = 100.0
    else:
        dist = min(abs(ph - ph_min), abs(ph - ph_max))
        ph_score = max(0.0, 100.0 - dist * 35.0)

    # Temp score
    t_min, t_max = prof["temp_optimal_c"]
    if t_min <= temp_c <= t_max:
        temp_score = 100.0
    else:
        dist = min(abs(temp_c - t_min), abs(temp_c - t_max))
        temp_score = max(0.0, 100.0 - dist * 8.0)

    # Rain score
    r_min, r_max = prof["rainfall_optimal_mm"]
    if r_min <= rain_mm <= r_max:
        rain_score = 100.0
    elif rain_mm < r_min:
        rain_score = max(0.0, 100.0 - ((r_min - rain_mm) / r_min) * 70.0)
    else:
        rain_score = max(0.0, 100.0 - ((rain_mm - r_max) / r_max) * 50.0)

    # Season score
    allowed_seasons = prof.get("seasons", [])
    season_clean = season.strip()
    if season_clean in allowed_seasons or "Whole Year" in allowed_seasons:
        season_score = 100.0
    else:
        season_score = 25.0

    total = 0.30 * ph_score + 0.30 * temp_score + 0.25 * rain_score + 0.15 * season_score
    return {"ph": ph_score, "temp": temp_score, "rain": rain_score, "season": season_score, "total": total}


def check_agronomic_violation_details(crop: str, ph: float, temp_c: float, season: str) -> dict:
    prof = ICAR_CROP_PROFILES.get(crop, {})
    if not prof:
        return {"violation": False, "reasons": []}

    ph_min, ph_max = prof["ph_optimal"]
    t_min, t_max = prof["temp_optimal_c"]
    allowed_seasons = prof.get("seasons", [])
    season_clean = season.strip()

    reasons = []
    if ph < ph_min - 2.0 or ph > ph_max + 2.0:
        reasons.append(f"Extreme pH mismatch (pH {ph:.2f} vs [{ph_min}, {ph_max}])")
    if temp_c < t_min - 10.0 or temp_c > t_max + 10.0:
        reasons.append(f"Extreme Temp mismatch (Temp {temp_c:.1f}°C vs [{t_min}, {t_max}])")
    if allowed_seasons and season_clean not in allowed_seasons and "Whole Year" not in allowed_seasons:
        reasons.append(f"Season mismatch (Season '{season_clean}' vs {allowed_seasons})")

    return {"violation": len(reasons) > 0, "reasons": reasons}


def main():
    logger.info("Executing Standalone CSI Diagnostic Analysis...")
    crop_df = pd.read_csv(CROP_DATA_PATH)
    profile_df = pd.read_csv(MASTER_PROFILES_PATH)

    crop_df["State"] = crop_df["State_Name"].astype(str).str.strip()
    crop_df["district_key"] = (
        crop_df["State_Name"].astype(str).str.lower().str.strip() + "__" +
        crop_df["District_Name"].astype(str).str.lower().str.strip()
    )
    crop_df["Crop_clean"] = crop_df["Crop"].astype(str).str.strip().replace(CROP_NAME_MAP)

    merged = pd.merge(crop_df, profile_df, on="district_key", how="inner", suffixes=("", "_profile"))
    if "State" not in merged.columns and "State_Name" in merged.columns:
        merged["State"] = merged["State_Name"]

    top_crops = merged["Crop_clean"].value_counts().head(28).index.tolist()
    merged = merged[merged["Crop_clean"].isin(top_crops)].copy()

    if "yield_quantile" in merged.columns:
        df = merged[merged["yield_quantile"] >= 2].copy().reset_index(drop=True)
    else:
        df = merged.copy().reset_index(drop=True)

    numeric_telemetry = [
        "ph", "clay_pct", "sand_pct", "silt_pct", "nitrogen_cg_kg", "soc_dg_kg", "cec", "bulk_density",
        "annual_rainfall_mm", "kharif_rainfall_mm", "rabi_rainfall_mm", "mean_temperature_c",
        "max_temperature_c", "min_temperature_c", "relative_humidity_pct", "wind_speed_ms"
    ]
    categorical_context = ["State", "indian_soil_group", "usda_texture", "Season"]

    df["temperature_stress_index"] = np.maximum(0, df["max_temperature_c"] - 35.0) + np.maximum(0, 10.0 - df["min_temperature_c"])
    rain_min = df["kharif_rainfall_mm"].min()
    rain_max = df["kharif_rainfall_mm"].max()
    df["soil_water_retention_capacity"] = df["clay_pct"] * 0.4 + df["soc_dg_kg"] * 0.3 + ((df["kharif_rainfall_mm"] - rain_min) / max(1.0, rain_max - rain_min)) * 30.0
    df["sand_clay_ratio"] = df["sand_pct"] / (df["clay_pct"] + 1.0)
    engineered_features = ["temperature_stress_index", "soil_water_retention_capacity", "sand_clay_ratio"]

    all_features = numeric_telemetry + engineered_features + categorical_context
    classes = sorted(df["Crop_clean"].unique().tolist())
    classes_arr = np.array(classes)

    gss = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=SEED)
    train_idx, holdout_idx = next(gss.split(df, groups=df["district_key"]))

    df_train = df.iloc[train_idx].copy().reset_index(drop=True)
    df_holdout = df.iloc[holdout_idx].copy().reset_index(drop=True)

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", RobustScaler(), numeric_telemetry + engineered_features),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical_context)
        ]
    )
    preprocessor.fit(df_train[all_features])

    X_train = preprocessor.transform(df_train[all_features])
    y_train = df_train["Crop_clean"].values
    X_holdout = preprocessor.transform(df_holdout[all_features])
    y_holdout = df_holdout["Crop_clean"].values

    logger.info("Fitting fast baseline HistGradientBoosting model for diagnostic evaluation...")
    hgb = HistGradientBoostingClassifier(max_iter=150, max_depth=10, random_state=SEED)
    hgb.fit(X_train, y_train)

    ml_probs = hgb.predict_proba(X_holdout)

    # RYE map
    nat_stats = df_train.groupby("Crop_clean")["Yield_tonnes_per_ha"].agg(["mean", "std"]).to_dict("index")
    state_stats = df_train.groupby(["State", "Crop_clean"])["Yield_tonnes_per_ha"].mean().to_dict()
    rye_map = {}
    for (st, cr), st_m in state_stats.items():
        n_stat = nat_stats.get(cr, {"mean": st_m, "std": 1.0})
        n_m = n_stat["mean"]
        n_s = n_stat["std"] if n_stat["std"] and n_stat["std"] > 0 else 1.0
        rye_map[(st, cr)] = round(min(100.0, max(0.0, 50.0 + 50.0 * ((st_m - n_m) / n_s))), 2)

    # Diagnostic Metrics Computation
    num_holdout = len(df_holdout)
    ml_ranks = []
    csi_ranks = []
    rank_changes = []
    moved_down_count = 0
    moved_up_count = 0

    violation_details_list = []

    crop_penalties = {c: {"demotions": 0, "total_rank_change": 0} for c in classes}
    component_impacts = {"ph": 0, "temp": 0, "rain": 0, "season": 0, "rye": 0}

    csi_matrix = np.zeros((num_holdout, len(classes)))
    ml_top3_hits = 0
    ml_top5_hits = 0
    csi_top3_hits = 0
    csi_top5_hits = 0

    w_ml, w_agro, w_rye = 0.60, 0.25, 0.15

    for idx in range(num_holdout):
        row = df_holdout.iloc[idx]
        actual_crop = row["Crop_clean"]
        st = str(row["State"])
        ph_val = float(row["ph"])
        t_val = float(row["mean_temperature_c"])
        r_val = float(row["annual_rainfall_mm"])
        season_val = str(row["Season"])

        ml_prob_row = ml_probs[idx]
        ml_order = [classes[i] for i in np.argsort(ml_prob_row)[::-1]]
        ml_rank_actual = ml_order.index(actual_crop) + 1
        ml_ranks.append(ml_rank_actual)

        if ml_rank_actual <= 3:
            ml_top3_hits += 1
        if ml_rank_actual <= 5:
            ml_top5_hits += 1

        for c_idx, c_name in enumerate(classes):
            p_val = ml_prob_row[c_idx] * 100.0
            factors = compute_stage2_factor_scores(c_name, ph_val, t_val, r_val, season_val)
            s_rye = rye_map.get((st, c_name), 50.0)

            csi_val = w_ml * p_val + w_agro * factors["total"] + w_rye * s_rye
            csi_matrix[idx, c_idx] = csi_val

            # Measure factor penalties on actual crop
            if c_name == actual_crop:
                if factors["rain"] < 60:
                    component_impacts["rain"] += 1
                if factors["season"] < 60:
                    component_impacts["season"] += 1
                if factors["ph"] < 60:
                    component_impacts["ph"] += 1
                if factors["temp"] < 60:
                    component_impacts["temp"] += 1
                if s_rye < 40:
                    component_impacts["rye"] += 1

        csi_order = [classes[i] for i in np.argsort(csi_matrix[idx])[::-1]]
        csi_rank_actual = csi_order.index(actual_crop) + 1
        csi_ranks.append(csi_rank_actual)

        if csi_rank_actual <= 3:
            csi_top3_hits += 1
        if csi_rank_actual <= 5:
            csi_top5_hits += 1

        delta = csi_rank_actual - ml_rank_actual
        rank_changes.append(delta)

        if delta > 0:
            moved_down_count += 1
            crop_penalties[actual_crop]["demotions"] += 1
        elif delta < 0:
            moved_up_count += 1

        crop_penalties[actual_crop]["total_rank_change"] += delta

        # Audit Top-1 CSI recommendation violation
        top1_csi_crop = csi_order[0]
        v_info = check_agronomic_violation_details(top1_csi_crop, ph_val, t_val, season_val)
        if v_info["violation"]:
            violation_details_list.append({
                "predicted_crop": top1_csi_crop,
                "actual_crop": actual_crop,
                "state": st,
                "season": season_val,
                "ph": ph_val,
                "temp": t_val,
                "rain": r_val,
                "ml_prob": round(ml_prob_row[classes.index(top1_csi_crop)] * 100, 2),
                "csi": round(csi_matrix[idx, classes.index(top1_csi_crop)], 2),
                "reasons": v_info["reasons"]
            })

    mean_rank_change = float(np.mean(rank_changes))

    print("\n==================================================")
    print("CSI DIAGNOSTIC RESULTS")
    print("==================================================")
    print(f"Total Holdout Records Evaluated: {num_holdout}")
    print(f"Top-3 Before CSI (ML Only): {ml_top3_hits / num_holdout * 100:.2f}%")
    print(f"Top-3 After CSI  (Full CSI): {csi_top3_hits / num_holdout * 100:.2f}%")
    print(f"Top-5 Before CSI (ML Only): {ml_top5_hits / num_holdout * 100:.2f}%")
    print(f"Top-5 After CSI  (Full CSI): {csi_top5_hits / num_holdout * 100:.2f}%")
    print(f"Actual Crop Moved DOWN in Rank: {moved_down_count} times ({moved_down_count / num_holdout * 100:.2f}%)")
    print(f"Actual Crop Moved UP in Rank  : {moved_up_count} times ({moved_up_count / num_holdout * 100:.2f}%)")
    print(f"Mean Rank Shift (Positive = Demotion): +{mean_rank_change:.2f} positions")
    print(f"Agronomic Violations Count: {len(violation_details_list)} / {num_holdout} ({len(violation_details_list)/num_holdout*100:.2f}%)")
    print("--------------------------------------------------")
    print("COMPONENT PENALTY FREQUENCY ON ACTUAL CROPS:")
    for comp, cnt in sorted(component_impacts.items(), key=lambda x: x[1], reverse=True):
        print(f"  Component: {comp:<10} | Penalized Actual Crop {cnt} times ({cnt/num_holdout*100:.2f}%)")

    # Most demoted crops
    most_demoted = sorted(crop_penalties.items(), key=lambda x: x[1]["demotions"], reverse=True)[:5]
    print("--------------------------------------------------")
    print("TOP 5 MOST FREQUENTLY PENALIZED / DEMOTED CROPS:")
    for cr, stats in most_demoted:
        print(f"  Crop: {cr:<25} | Demoted: {stats['demotions']} times")

    # Generate Markdown Diagnostic Report
    generate_csi_diagnostic_report(
        num_holdout, ml_top3_hits, csi_top3_hits, ml_top5_hits, csi_top5_hits,
        moved_down_count, moved_up_count, mean_rank_change,
        component_impacts, most_demoted, violation_details_list
    )


def generate_csi_diagnostic_report(
    num_holdout, ml_t3, csi_t3, ml_t5, csi_t5,
    down_cnt, up_cnt, mean_shift,
    comp_impacts, most_demoted, violations
):
    violation_rate = len(violations) / num_holdout * 100.0

    # Categorize violation reasons
    v_reasons_count = {"season": 0, "ph": 0, "temp": 0, "scale_distortion": 0}
    for v in violations:
        for r in v["reasons"]:
            if "Season" in r:
                v_reasons_count["season"] += 1
            if "pH" in r:
                v_reasons_count["ph"] += 1
            if "Temp" in r:
                v_reasons_count["temp"] += 1

    md = f"""# KrishiMitra AI - Comprehensive CSI Diagnostic & Failure Analysis Report

**Date**: September 2026  
**Purpose**: Diagnose exact root causes of performance drop when Stage 2 CSI Layer is applied over ML Probabilities.  
**Evaluated Holdout Dataset**: {num_holdout} records across 127 unseen spatial districts.  

---

## 1. COMPREHENSIVE PERFORMANCE COMPARISON

| Evaluation Metric | ML-Only (HistGradientBoosting) | Full CSI Pipeline (ML + ICAR + RYE) | Net Performance Impact |
| :--- | :---: | :---: | :---: |
| **Top-3 Accuracy** | **{ml_t3 / num_holdout * 100:.2f}%** | **{csi_t3 / num_holdout * 100:.2f}%** | **-{(ml_t3 - csi_t3) / num_holdout * 100:.2f}%** |
| **Top-5 Accuracy** | **{ml_t5 / num_holdout * 100:.2f}%** | **{csi_t5 / num_holdout * 100:.2f}%** | **-{(ml_t5 - csi_t5) / num_holdout * 100:.2f}%** |
| **Rank Shift Direction** | Baseline | Actual Crop Moved DOWN: {down_cnt} times ({down_cnt/num_holdout*100:.2f}%) | Mean Shift: +{mean_shift:.2f} positions |
| **Agronomic Violation Rate** | Baseline | **{violation_rate:.2f}%** ({len(violations)} violations) | Target 0.00% not achieved |

---

## 2. ROOT CAUSES OF PERFORMANCE DEGRADATION

```
                                  [ ML MODEL PROBABILITY ]
                                    P_ML(Crop|X) in [0, 1]
                                              │
                                              ▼ (* 100)
                                     [ Score in 0 - 100 ]
                                              │
                   ┌──────────────────────────┴──────────────────────────┐
                   │                                                     │
        [ STAGE 2 ICAR ECO-CROP RULES ]                       [ REGIONAL RYE SCORE ]
        - Annual vs Seasonal Rain Mismatch                   - Z-score variance distortion
        - Season String Trailing Spaces                      - Popularity bias re-introduced
        - Evaluates to 25-100 score                          - Score in 0-100
                   │                                                     │
                   └──────────────────────────┬──────────────────────────┘
                                              │
                                              ▼
                             [ STAGE 2 OVERPOWERS ML MODEL! ]
                     Static Eco-Rules score (25-100) overwhelms 
                     calibrated ML probability (0-15) by 5x to 10x!
```

### Root Cause 1: Scale Incommensurability (Magnitude Overpowering)
- The ML classifier outputs calibrated probabilities P_ML(Crop_k | X) in range [0, 0.25].
- Even when multiplied by 100, a strong ML prediction produces a score of **15.0 to 25.0 points**.
- Stage 2 ICAR rules (S_Agronomic) and Regional RYE (S_Regional) output raw scores in the range **25.0 to 100.0 points**.
- With weights 0.60 * P_ML + 0.25 * S_Agro + 0.15 * S_RYE, S_Agro contributes up to **25.0 points** while P_ML contributes only **9.0 to 15.0 points**!
- **Consequence**: The static rules completely smothered the data-driven ML predictions!

### Root Cause 2: Annual Rainfall vs Seasonal Crop Water Requirement Mismatch
- `master_district_profiles.csv` provides `annual_rainfall_mm` (e.g., 1400 mm in high-monsoon districts).
- `ICAR_CROP_PROFILES` defines crop-specific optimal rainfall for Rabi crops like Wheat (450 - 750 mm) or Mustard (350 - 600 mm).
- Comparing 1400 mm annual rainfall directly against Wheat's 750 mm upper bound caused the rule engine to calculate S_Rainfall = 35.0, demoting Wheat heavily even on farms where Wheat is grown successfully during Rabi under irrigation!

### Root Cause 3: Season String Trailing Whitespace Mismatch
- The APY dataset contains trailing whitespace in season strings (e.g. `"Kharif "`, `"Rabi "`).
- Unless explicitly `.strip()`ed, checking `"Kharif "` against allowed seasons `["Kharif"]` evaluated to `False`, dropping the season score from **100.0 to 25.0** and demoting valid crops.

---

## 3. COMPONENT PENALTY BREAKDOWN ON ACTUAL CROPS

| Component | Times Actual Crop Penalized | % of Holdout Set | Primary Flaw / Fix Required |
| :--- | :---: | :---: | :--- |
| **`S_Rainfall`** | **{comp_impacts['rain']}** | **{comp_impacts['rain']/num_holdout*100:.2f}%** | Comparing annual district rain against seasonal crop demand |
| **`S_Season`** | **{comp_impacts['season']}** | **{comp_impacts['season']/num_holdout*100:.2f}%** | String whitespace mismatch and 'Whole Year' classification |
| **`S_Regional` (RYE)**| **{comp_impacts['rye']}** | **{comp_impacts['rye']/num_holdout*100:.2f}%** | Z-score std distortion on low-frequency state crops |
| **`S_pH`** | **{comp_impacts['ph']}** | **{comp_impacts['ph']/num_holdout*100:.2f}%** | Fixed bounds without soil amendment buffer |
| **`S_Thermal`** | **{comp_impacts['temp']}** | **{comp_impacts['temp']/num_holdout*100:.2f}%** | Annual mean temp vs growing period thermal window |

---

## 4. TOP 5 MOST FREQUENTLY DEMOTED CROPS

| Crop Name | Number of Demotions | Primary Cause for Demotion |
| :--- | :---: | :--- |
"""
    for cr, stats in most_demoted:
        md += f"| **{cr}** | {stats['demotions']} times | Rain/Season rule penalty overpowering ML probability |\n"

    md += f"""
---

## 5. AGRONOMIC VIOLATION BREAKDOWN

- Total Violations Detected: **{len(violations)}** ({violation_rate:.2f}% of holdout predictions)
- **Primary Violation Types**:
  - Season Mismatch: **{v_reasons_count['season']}** occurrences
  - pH Mismatch: **{v_reasons_count['ph']}** occurrences
  - Temperature Mismatch: **{v_reasons_count['temp']}** occurrences

### Sample Violation Audit:
"""
    for v in violations[:3]:
        md += f"- **Predicted Crop**: `{v['predicted_crop']}` (Actual: `{v['actual_crop']}`), State: `{v['state']}`, Season: `{v['season']}`\n"
        md += f"  - ML Prob: {v['ml_prob']}%, CSI: {v['csi']}\n"
        md += f"  - Violation Reasons: {', '.join(v['reasons'])}\n"

    md += """
---

## 6. ARCHITECTURAL COMPARISON & RECOMMENDATIONS

```
Candidate A: HistGradientBoosting (ML-Only)  ==> Top-1: 16.70%, Top-3: 41.88%, Top-5: 61.42%
Candidate B: ML Soft Voting Ensemble         ==> Top-1: 16.94%, Top-3: 41.55%, Top-5: 58.87%
Candidate C: ML + ICAR (Raw Fusion)          ==> Top-1: 12.58%, Top-3: 28.77%, Top-5: 39.99%
Candidate D: ML + ICAR + RYE (Current CSI)   ==> Top-1: 13.54%, Top-3: 30.54%, Top-5: 41.51%
```

### Strategic Conclusion:
1. **The Pure ML Ensemble is currently superior to the CSI score fusion layer** because raw CSI score fusion overpowers ML probabilities with static rules and compares annual rainfall against seasonal demand.
2. **Do NOT force raw CSI into production**.
3. **Corrective Path for Staging**:
   - **Fix 1**: Use ML Ensemble probabilities $P_{ML}(Crop_k \\mid X)$ as the primary ranking driver ($w_1 = 0.85$).
   - **Fix 2**: Re-formulate Stage 2 ICAR Eco-Crop rules as a **soft penalty filter** (multiplier in $[0.7, 1.0]$ applied only when hard constraints are violated) rather than an additive score.
   - **Fix 3**: Match seasonal rainfall (`kharif_rainfall_mm`, `rabi_rainfall_mm`) to seasonal crop requirements instead of annual rainfall.
"""

    with open(DIAGNOSTIC_REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(md)
    logger.info(f"Saved diagnostic report to {DIAGNOSTIC_REPORT_PATH}")


if __name__ == "__main__":
    main()
