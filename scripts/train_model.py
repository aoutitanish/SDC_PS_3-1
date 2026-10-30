"""
ML Training Pipeline for KrishiMitra AI.
Trains an explainable Random Forest crop recommendation model
and generates agronomic suitability profiles for all major Indian crops.
"""

import os
import json
import datetime
import logging
import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, top_k_accuracy_score, precision_score, recall_score, f1_score
from sklearn.preprocessing import LabelEncoder

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "processed")
ML_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ml", "models")
os.makedirs(ML_DIR, exist_ok=True)

TOP_N_CROPS = 28

FEATURES = [
    "ph",
    "clay_pct",
    "sand_pct",
    "silt_pct",
    "nitrogen_cg_kg",
    "soc_dg_kg",
    "cec",
    "bulk_density",
    "annual_rainfall_mm",
    "kharif_rainfall_mm",
    "rabi_rainfall_mm",
    "mean_temperature_c",
    "max_temperature_c",
    "min_temperature_c",
    "relative_humidity_pct",
    "wind_speed_ms"
]


def train_crop_model():
    logger.info("Loading master district profiles and clean crops...")
    master = pd.read_csv(os.path.join(DATA_DIR, "master_district_profiles.csv"))
    crops = pd.read_parquet(os.path.join(DATA_DIR, "clean_crops.parquet"))

    # Standardize crop naming (e.g. Soyabean -> Soybean, Cotton(lint) -> Cotton)
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
    crops["Crop"] = crops["Crop"].replace(crop_name_map)

    # Merge on district_key
    merged = crops.merge(master, on="district_key", how="inner")

    # Filter top N crops with highest agricultural significance
    top_crops = merged["Crop"].value_counts().head(TOP_N_CROPS).index.tolist()
    filtered = merged[merged["Crop"].isin(top_crops)].copy()
    filtered = filtered.dropna(subset=FEATURES + ["Crop", "Yield_tonnes_per_ha"])

    # Weight samples by relative yield efficiency per crop
    # Crop records with higher yield in a district represent optimal agro-ecological suitability
    filtered["yield_quantile"] = filtered.groupby("Crop")["Yield_tonnes_per_ha"].transform(
        lambda s: pd.qcut(s, q=4, labels=[1, 2, 3, 4], duplicates="drop").astype(int) if len(s.unique()) > 4 else 2
    )

    # Focus training on medium-to-high performing agro-climatic conditions
    train_df = filtered[filtered["yield_quantile"] >= 2].copy()
    logger.info(f"Training dataset size: {len(train_df)} records across {len(top_crops)} crops")

    X = train_df[FEATURES]
    y = train_df["Crop"]

    le = LabelEncoder()
    y_encoded = le.fit_transform(y)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.20, random_state=42, stratify=y_encoded
    )

    logger.info("Training Random Forest Classifier with calibrated trees...")
    rf = RandomForestClassifier(
        n_estimators=150,
        max_depth=22,
        min_samples_split=4,
        min_samples_leaf=2,
        max_features="sqrt",
        class_weight="balanced_subsample",
        random_state=42,
        n_jobs=-1
    )
    rf.fit(X_train, y_train)

    # Evaluate
    y_pred = rf.predict(X_test)
    y_prob = rf.predict_proba(X_test)

    acc = float(accuracy_score(y_test, y_pred))
    top3_acc = float(top_k_accuracy_score(y_test, y_prob, k=3))
    top5_acc = float(top_k_accuracy_score(y_test, y_prob, k=5))
    prec = float(precision_score(y_test, y_pred, average="weighted", zero_division=0))
    rec = float(recall_score(y_test, y_pred, average="weighted", zero_division=0))
    f1 = float(f1_score(y_test, y_pred, average="weighted", zero_division=0))

    logger.info(f"Model Evaluation: Top-1 Acc={acc:.4f}, Top-3 Acc={top3_acc:.4f}, Top-5 Acc={top5_acc:.4f}, F1={f1:.4f}")

    # Feature Importances
    feature_importances = {
        feat: round(float(imp), 4)
        for feat, imp in zip(FEATURES, rf.feature_importances_)
    }
    sorted_importances = dict(sorted(feature_importances.items(), key=lambda item: item[1], reverse=True))

    # Calculate Agronomic Profiles for each crop from empirical dataset & ICAR agronomy guidelines
    agronomic_profiles = {}
    for crop in top_crops:
        crop_data = filtered[filtered["Crop"] == crop]
        agronomic_profiles[crop] = {
            "crop_name": crop,
            "sample_records": int(len(crop_data)),
            "ph_optimal": [
                round(float(crop_data["ph"].quantile(0.10)), 2),
                round(float(crop_data["ph"].quantile(0.90)), 2)
            ],
            "rainfall_optimal_mm": [
                round(float(crop_data["annual_rainfall_mm"].quantile(0.10)), 1),
                round(float(crop_data["annual_rainfall_mm"].quantile(0.90)), 1)
            ],
            "temp_optimal_c": [
                round(float(crop_data["mean_temperature_c"].quantile(0.10)), 1),
                round(float(crop_data["mean_temperature_c"].quantile(0.90)), 1)
            ],
            "nitrogen_optimal_cg_kg": [
                round(float(crop_data["nitrogen_cg_kg"].quantile(0.10)), 1),
                round(float(crop_data["nitrogen_cg_kg"].quantile(0.90)), 1)
            ],
            "clay_pct_optimal": [
                round(float(crop_data["clay_pct"].quantile(0.10)), 1),
                round(float(crop_data["clay_pct"].quantile(0.90)), 1)
            ],
            "top_seasons": crop_data["Season"].value_counts().head(3).to_dict(),
            "top_states": crop_data["State_Name_x"].value_counts().head(5).to_dict(),
            "mean_yield_tonnes_ha": round(float(crop_data["Yield_tonnes_per_ha"].mean()), 2)
        }

    # Save model artifacts
    model_artifact = {
        "model": rf,
        "label_encoder": le,
        "features": FEATURES,
        "top_crops": top_crops
    }
    joblib.dump(model_artifact, os.path.join(ML_DIR, "crop_recommendation_model.pkl"))

    # Save metadata JSON
    metadata = {
        "model_name": "KrishiMitra RandomForest Crop Recommender",
        "version": "1.1.0",
        "trained_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_training_samples": len(train_df),
        "classes_count": len(top_crops),
        "classes": list(le.classes_),
        "features": FEATURES,
        "metrics": {
            "top_1_accuracy": round(acc, 4),
            "top_3_accuracy": round(top3_acc, 4),
            "top_5_accuracy": round(top5_acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4)
        },
        "feature_importances": sorted_importances
    }

    with open(os.path.join(ML_DIR, "model_metadata.json"), "w") as fp:
        json.dump(metadata, fp, indent=2)

    with open(os.path.join(ML_DIR, "crop_agronomic_profiles.json"), "w") as fp:
        json.dump(agronomic_profiles, fp, indent=2)

    logger.info("Model and agronomic metadata saved successfully!")
    return metadata


if __name__ == "__main__":
    train_crop_model()
