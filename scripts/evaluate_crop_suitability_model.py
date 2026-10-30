"""
Independent Evaluation Script for KrishiMitra Experimental Crop Suitability Model.
Loads ml/models/crop_suitability_model_experimental.pkl and evaluates performance on spatial holdout districts.
Does NOT modify any production code or models.
"""

import os
import json
import logging
import joblib
import numpy as np
import pandas as pd

from sklearn.metrics import accuracy_score, f1_score, classification_report, confusion_matrix
from sklearn.model_selection import GroupShuffleSplit

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CROP_DATA_PATH = os.path.join(BASE_DIR, "data", "crop_expert.csv")
MASTER_PROFILES_PATH = os.path.join(BASE_DIR, "data", "processed", "master_district_profiles.csv")
MODEL_PATH = os.path.join(BASE_DIR, "ml", "models", "crop_suitability_model_experimental.pkl")
METADATA_PATH = os.path.join(BASE_DIR, "ml", "models", "crop_suitability_metadata.json")

SEED = 42


def evaluate_top_k(y_true: np.ndarray, probs: np.ndarray, classes: list, k: int) -> float:
    hits = 0
    for i, true_label in enumerate(y_true):
        top_k_idx = np.argsort(probs[i])[::-1][:k]
        top_k_classes = [classes[idx] for idx in top_k_idx]
        if true_label in top_k_classes:
            hits += 1
    return hits / len(y_true)


def main():
    if not os.path.exists(MODEL_PATH):
        logger.error(f"Experimental model not found at {MODEL_PATH}. Train the model first.")
        return

    logger.info(f"Loading experimental model artifact from {MODEL_PATH}...")
    artifact = joblib.load(MODEL_PATH)

    preprocessor = artifact["preprocessor"]
    rf_cal = artifact["rf_calibrated"]
    et_cal = artifact["et_calibrated"]
    hgb_cal = artifact["hgb_calibrated"]
    w_hgb, w_rf, w_et = artifact["ensemble_weights"]
    classes = artifact["classes"]
    all_features = artifact["all_features"]

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

    logger.info(f"Loading datasets for evaluation...")
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

    merged = merged[merged["Crop_clean"].isin(classes)].copy()

    if "yield_quantile" in merged.columns:
        df = merged[merged["yield_quantile"] >= 2].copy()
    else:
        df = merged.copy()

    # Re-compute engineered features
    df["temperature_stress_index"] = (
        np.maximum(0, df["max_temperature_c"] - 35.0) +
        np.maximum(0, 10.0 - df["min_temperature_c"])
    )
    rain_min = df["kharif_rainfall_mm"].min()
    rain_max = df["kharif_rainfall_mm"].max()
    rain_norm = (df["kharif_rainfall_mm"] - rain_min) / max(1.0, rain_max - rain_min)
    df["soil_water_retention_capacity"] = (
        df["clay_pct"] * 0.4 + df["soc_dg_kg"] * 0.3 + rain_norm * 30.0
    )
    df["sand_clay_ratio"] = df["sand_pct"] / (df["clay_pct"] + 1.0)

    # Perform same 20% spatial holdout split
    gss = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=SEED)
    _, holdout_idx = next(gss.split(df, groups=df["district_key"]))
    df_holdout = df.iloc[holdout_idx].copy().reset_index(drop=True)

    X_holdout = df_holdout[all_features]
    y_holdout = df_holdout["Crop_clean"].values

    X_proc = preprocessor.transform(X_holdout)

    rf_probs = rf_cal.predict_proba(X_proc)
    et_probs = et_cal.predict_proba(X_proc)
    hgb_probs = hgb_cal.predict_proba(X_proc)

    ensemble_probs = w_hgb * hgb_probs + w_rf * rf_probs + w_et * et_probs
    y_pred = [classes[idx] for idx in np.argmax(ensemble_probs, axis=1)]

    t1 = accuracy_score(y_holdout, y_pred)
    t3 = evaluate_top_k(y_holdout, ensemble_probs, classes, 3)
    t5 = evaluate_top_k(y_holdout, ensemble_probs, classes, 5)
    f1_w = f1_score(y_holdout, y_pred, average="weighted")
    f1_m = f1_score(y_holdout, y_pred, average="macro")

    print("\n==================================================")
    print("EXPERIMENTAL MODEL SPATIAL HOLDOUT EVALUATION")
    print("==================================================")
    print(f"Evaluated Records: {len(df_holdout)} across {df_holdout['district_key'].nunique()} unseen districts.")
    print(f"  Top-1 Accuracy : {t1*100:.2f}%")
    print(f"  Top-3 Accuracy : {t3*100:.2f}%")
    print(f"  Top-5 Accuracy : {t5*100:.2f}%")
    print(f"  Weighted F1    : {f1_w:.4f}")
    print(f"  Macro F1       : {f1_m:.4f}")
    print("--------------------------------------------------")
    print("\nCLASSIFICATION REPORT:")
    print(classification_report(y_holdout, y_pred, zero_division=0))


if __name__ == "__main__":
    main()
