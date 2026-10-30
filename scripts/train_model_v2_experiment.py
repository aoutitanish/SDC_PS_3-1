"""
Model V2 Training & Comparison Experiment for KrishiMitra AI.
Trains and compares Model A, Model B, and Model C on identical 80/20 stratified splits.
Includes holdout evaluation, top-k metrics, macro/weighted F1, confusion matrix, and 5-fold CV for the winner.
Saves candidate artifact to ml/models/crop_recommendation_model_v2_candidate.pkl.
"""

import os
import sys
import json
import time
import datetime
import logging
import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_validate
from sklearn.metrics import (
    accuracy_score,
    top_k_accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

sys.stdout.reconfigure(encoding='utf-8')
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, "data", "processed")
RAW_DATA_DIR = os.path.join(ROOT_DIR, "data")
ML_DIR = os.path.join(ROOT_DIR, "ml", "models")
os.makedirs(ML_DIR, exist_ok=True)

TOP_N_CROPS = 28

NUMERIC_FEATURES = [
    "ph", "clay_pct", "sand_pct", "silt_pct", "nitrogen_cg_kg", "soc_dg_kg",
    "cec", "bulk_density", "annual_rainfall_mm", "kharif_rainfall_mm",
    "rabi_rainfall_mm", "mean_temperature_c", "max_temperature_c",
    "min_temperature_c", "relative_humidity_pct", "wind_speed_ms"
]

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


def load_and_preprocess_dataset():
    logger.info("Loading master district profiles and crop expert datasets...")
    master_path = os.path.join(DATA_DIR, "master_district_profiles.csv")
    crop_path = os.path.join(RAW_DATA_DIR, "crop_expert.csv")

    if not os.path.exists(master_path) or not os.path.exists(crop_path):
        raise FileNotFoundError("Required data files missing: master_district_profiles.csv or crop_expert.csv")

    master = pd.read_csv(master_path)
    crops = pd.read_csv(crop_path)

    crops["Crop"] = crops["Crop"].astype(str).str.strip().replace(CROP_NAME_MAP)
    crops["Season"] = crops["Season"].astype(str).str.strip()
    crops["district_key"] = (
        crops["State_Name"].astype(str).str.strip().str.lower() + "__" +
        crops["District_Name"].astype(str).str.strip().str.lower()
    )

    # Filter valid non-zero cultivation records
    valid_crops = crops[
        (crops["zero_production_flag"] == False) &
        (crops["production_missing_flag"] == False) &
        (crops["zero_area_flag"] == False)
    ].copy()
    valid_crops["Yield_tonnes_per_ha"] = pd.to_numeric(valid_crops["Yield_tonnes_per_ha"], errors="coerce")
    valid_crops = valid_crops.dropna(subset=["Yield_tonnes_per_ha", "Crop"])

    # Merge crop records with district soil & climate telemetry
    merged = valid_crops.merge(master, on="district_key", how="inner")

    # Select top 28 crops
    top_crops = merged["Crop"].value_counts().head(TOP_N_CROPS).index.tolist()
    filtered = merged[merged["Crop"].isin(top_crops)].copy()

    # Filter out missing values in feature set
    required_cols = NUMERIC_FEATURES + ["Crop", "Season", "indian_soil_group", "usda_texture", "nitrogen_level", "ph_category", "Yield_tonnes_per_ha"]
    filtered = filtered.dropna(subset=required_cols)

    # Quantile filtering for medium-to-high yield quality (yield_quantile >= 2)
    filtered["yield_quantile"] = filtered.groupby("Crop")["Yield_tonnes_per_ha"].transform(
        lambda s: pd.qcut(s, q=4, labels=[1, 2, 3, 4], duplicates="drop").astype(int) if len(s.unique()) > 4 else 2
    )

    train_df = filtered[filtered["yield_quantile"] >= 2].copy()
    return train_df, top_crops


def evaluate_model(model, X_test, y_test, classes):
    start_time = time.time()
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)
    test_time = time.time() - start_time

    acc = float(accuracy_score(y_test, y_pred))
    top3_acc = float(top_k_accuracy_score(y_test, y_prob, k=3))
    top5_acc = float(top_k_accuracy_score(y_test, y_prob, k=5))
    macro_f1 = float(f1_score(y_test, y_pred, average="macro", zero_division=0))
    weighted_f1 = float(f1_score(y_test, y_pred, average="weighted", zero_division=0))
    weighted_prec = float(precision_score(y_test, y_pred, average="weighted", zero_division=0))
    weighted_rec = float(recall_score(y_test, y_pred, average="weighted", zero_division=0))

    # Per-class metrics
    class_rep = classification_report(y_test, y_pred, target_names=classes, output_dict=True, zero_division=0)
    per_class = {
        cls_name: {
            "precision": round(class_rep[cls_name]["precision"], 4),
            "recall": round(class_rep[cls_name]["recall"], 4),
            "f1": round(class_rep[cls_name]["f1-score"], 4),
            "support": class_rep[cls_name]["support"]
        }
        for cls_name in classes if cls_name in class_rep
    }

    # Probability calibration check
    max_probs = np.max(y_prob, axis=1)
    avg_confidence = float(np.mean(max_probs))

    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred).tolist()

    return {
        "top_1_accuracy": round(acc, 4),
        "top_3_accuracy": round(top3_acc, 4),
        "top_5_accuracy": round(top5_acc, 4),
        "macro_f1": round(macro_f1, 4),
        "weighted_f1": round(weighted_f1, 4),
        "precision": round(weighted_prec, 4),
        "recall": round(weighted_rec, 4),
        "avg_confidence": round(avg_confidence, 4),
        "test_time_sec": round(test_time, 2),
        "per_class_metrics": per_class,
        "confusion_matrix": cm
    }


def run_experiment():
    print("==================================================")
    print("      KRISHIMITRA MODEL V2 RETRAINING EXPERIMENT   ")
    print("==================================================")

    df, top_crops = load_and_preprocess_dataset()

    le = LabelEncoder()
    y = le.fit_transform(df["Crop"])
    classes = list(le.classes_)

    print(f"\n1. PRE-TRAINING DATA SUMMARY:")
    print(f"   • Total Training Samples: {len(df)}")
    print(f"   • Number of Target Classes: {len(classes)}")
    print(f"   • Numeric Features (16): {NUMERIC_FEATURES}")

    # Split dataset into Train (80%) and Test (20%) using random_state=42
    train_df, test_df, y_train, y_test = train_test_split(
        df, y, test_size=0.20, random_state=42, stratify=y
    )

    print(f"   • Train Rows: {len(train_df)}")
    print(f"   • Test Rows: {len(test_df)}")

    print("\n   Class Distribution in Training Set:")
    train_counts = pd.Series(y_train).value_counts().sort_index()
    for idx, count in train_counts.items():
        cls_name = classes[idx]
        pct = (count / len(y_train)) * 100
        print(f"     {cls_name:<28}: {count:>5} samples ({pct:>5.2f}%)")

    results = {}
    models_dict = {}

    # Define Feature Sets
    cat_model_b = ["Season", "indian_soil_group"]
    cat_model_c = ["Season", "indian_soil_group", "usda_texture", "nitrogen_level", "ph_category"]

    experiments = [
        {
            "name": "Model A (Baseline)",
            "cat_cols": [],
            "description": "Existing 16 numeric soil/climate features only"
        },
        {
            "name": "Model B (Season + Soil Group)",
            "cat_cols": cat_model_b,
            "description": "16 numeric features + Season + indian_soil_group"
        },
        {
            "name": "Model C (Full Categorical)",
            "cat_cols": cat_model_c,
            "description": "16 numeric features + 5 categorical features"
        }
    ]

    for exp in experiments:
        exp_name = exp["name"]
        cat_cols = exp["cat_cols"]
        print(f"\n--------------------------------------------------")
        print(f"TRAINING {exp_name.upper()}")
        print(f"Description: {exp['description']}")
        print(f"Categorical Features: {cat_cols if cat_cols else 'None'}")

        all_cols = NUMERIC_FEATURES + cat_cols
        X_tr = train_df[all_cols]
        X_te = test_df[all_cols]

        if cat_cols:
            preprocessor = ColumnTransformer(
                transformers=[
                    ("num", "passthrough", NUMERIC_FEATURES),
                    ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_cols)
                ]
            )
        else:
            preprocessor = ColumnTransformer(
                transformers=[("num", "passthrough", NUMERIC_FEATURES)]
            )

        classifier = RandomForestClassifier(
            n_estimators=150,
            max_depth=22,
            min_samples_split=4,
            min_samples_leaf=2,
            max_features="sqrt",
            class_weight="balanced_subsample",
            random_state=42,
            n_jobs=-1
        )

        pipeline = Pipeline([
            ("preprocessor", preprocessor),
            ("classifier", classifier)
        ])

        start_time = time.time()
        pipeline.fit(X_tr, y_train)
        train_time = time.time() - start_time

        logger.info(f"{exp_name} trained in {train_time:.2f} seconds.")

        # Holdout Evaluation
        eval_metrics = evaluate_model(pipeline, X_te, y_test, classes)
        eval_metrics["train_time_sec"] = round(train_time, 2)
        eval_metrics["num_features_in"] = len(all_cols)
        eval_metrics["categorical_features"] = cat_cols

        results[exp_name] = eval_metrics
        models_dict[exp_name] = (pipeline, all_cols)

    # Print Clean Comparison Table
    print("\n=========================================================================================")
    print("                             MODEL EVALUATION COMPARISON TABLE                           ")
    print("=========================================================================================")
    print(f"{'Model':<30} | {'Features':<10} | {'Top-1 Acc':<9} | {'Top-3 Acc':<9} | {'Top-5 Acc':<9} | {'Macro F1':<9} | {'Weighted F1':<11}")
    print("-" * 97)

    best_model_name = None
    best_weighted_f1 = -1.0

    for name, m in results.items():
        feat_count = str(m["num_features_in"])
        top1 = f"{m['top_1_accuracy']*100:.2f}%"
        top3 = f"{m['top_3_accuracy']*100:.2f}%"
        top5 = f"{m['top_5_accuracy']*100:.2f}%"
        macro_f1 = f"{m['macro_f1']:.4f}"
        w_f1 = f"{m['weighted_f1']:.4f}"
        print(f"{name:<30} | {feat_count:<10} | {top1:<9} | {top3:<9} | {top5:<9} | {macro_f1:<9} | {w_f1:<11}")

        if m["weighted_f1"] > best_weighted_f1:
            best_weighted_f1 = m["weighted_f1"]
            best_model_name = name

    print("=========================================================================================")
    print(f"\n🏆 BEST CANDIDATE MODEL IDENTIFIED: {best_model_name} (Weighted F1: {best_weighted_f1:.4f})")

    # Perform 5-Fold Cross Validation ONLY on the selected best model
    print(f"\n--------------------------------------------------")
    print(f"RUNNING 5-FOLD STRATIFIED CROSS-VALIDATION FOR {best_model_name.upper()}...")
    best_pipeline, best_cols = models_dict[best_model_name]
    X_full = df[best_cols]

    cv_start = time.time()
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_validate(
        best_pipeline,
        X_full,
        y,
        cv=skf,
        scoring={
            "top1": "accuracy",
            "weighted_f1": "f1_weighted",
            "macro_f1": "f1_macro"
        },
        n_jobs=-1
    )
    cv_time = time.time() - cv_start

    cv_summary = {
        "completed": True,
        "n_folds": 5,
        "cv_time_sec": round(cv_time, 2),
        "mean_top1_accuracy": round(float(np.mean(cv_scores["test_top1"])), 4),
        "std_top1_accuracy": round(float(np.std(cv_scores["test_top1"])), 4),
        "mean_weighted_f1": round(float(np.mean(cv_scores["test_weighted_f1"])), 4),
        "std_weighted_f1": round(float(np.std(cv_scores["test_weighted_f1"])), 4),
        "mean_macro_f1": round(float(np.mean(cv_scores["test_macro_f1"])), 4)
    }

    print(f"5-Fold CV Completed in {cv_time:.2f}s:")
    print(f"  • Mean Top-1 Accuracy : {cv_summary['mean_top1_accuracy']*100:.2f}% (± {cv_summary['std_top1_accuracy']*100:.2f}%)")
    print(f"  • Mean Weighted F1    : {cv_summary['mean_weighted_f1']:.4f} (± {cv_summary['std_weighted_f1']:.4f})")
    print(f"  • Mean Macro F1       : {cv_summary['mean_macro_f1']:.4f}")

    # Save Candidate Artifacts (DO NOT OVERWRITE PRODUCTION MODEL)
    candidate_model_path = os.path.join(ML_DIR, "crop_recommendation_model_v2_candidate.pkl")
    report_path = os.path.join(ML_DIR, "model_v2_comparison_report.json")

    candidate_artifact = {
        "model_name": best_model_name,
        "pipeline": best_pipeline,
        "label_encoder": le,
        "feature_cols": best_cols,
        "numeric_features": NUMERIC_FEATURES,
        "categorical_features": results[best_model_name]["categorical_features"],
        "classes": classes,
        "trained_timestamp": datetime.datetime.now().isoformat()
    }
    joblib.dump(candidate_artifact, candidate_model_path)

    comparison_report = {
        "timestamp": datetime.datetime.now().isoformat(),
        "total_samples": len(df),
        "train_samples": len(train_df),
        "test_samples": len(test_df),
        "classes_count": len(classes),
        "classes": classes,
        "results": results,
        "best_candidate": best_model_name,
        "cross_validation_finalist": cv_summary,
        "artifacts_saved": {
            "candidate_pkl": candidate_model_path,
            "report_json": report_path
        }
    }

    with open(report_path, "w", encoding="utf-8") as fp:
        json.dump(comparison_report, fp, indent=2)

    print("\n=========================================================================================")
    print("                               EXPERIMENT COMPLETE                                       ")
    print("=========================================================================================")
    print(f"Candidate Model Artifact : {candidate_model_path}")
    print(f"Comparison Report JSON   : {report_path}")
    print("Note: Production model 'crop_recommendation_model.pkl' remains unchanged.")


if __name__ == "__main__":
    try:
        run_experiment()
    except Exception as e:
        logger.error(f"Experiment failed with error: {e}", exc_info=True)
        sys.exit(1)
