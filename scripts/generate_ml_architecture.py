"""
Script to generate final_ml_architecture.md and final_ml_architecture.json
containing the complete, comprehensive ML architecture design for KrishiMitra AI.
"""

import json
import os

MARKDOWN_PATH = r"c:\Users\aouti\Desktop\PS-3\FarmerHelp\scripts\final_ml_architecture.md"
JSON_PATH = r"c:\Users\aouti\Desktop\PS-3\FarmerHelp\scripts\final_ml_architecture.json"

markdown_content = """# KrishiMitra AI - Primary Agricultural ML System Architecture Design

**Architectural Phase**: Post-Audit Final Architecture Design  
**Date**: September 2026  
**System Role**: Primary Intelligence Engine for KrishiMitra AI  
**LLM Status**: Qwen / Bionic LLM demoted to OPTIONAL BACKUP & NATURAL LANGUAGE SYNTHESIZER ONLY (`USE_QWEN_FALLBACK=true/false`)  

---

## 1. TARGET FORMULATION ANALYSIS

### A. Current Target Breakdown & Ambiguity Audit
- **Current Target Variable**: `Crop` (normalized into 28 top agricultural crop classes).
- **Dataset Size**: 246,091 historical APY cultivation records; 136,128 high-quality records (`yield_quantile >= 2`) used for training.
- **Fundamental Problem**: Historical agricultural yield datasets record the *single crop actually planted* by a farmer in a given district and season. However, agricultural land under specific soil and climate telemetry is inherently **multi-crop capable**.
- **Empirical Ambiguity Evidence**:
  - **88.38%** of district soil/climate feature vectors in the dataset grow 2 or more distinct crops under near-identical telemetry.
  - On average, each district feature vector supports **7.43 different crops** across historical years.
  - **Theoretical Bayes Optimal Accuracy Upper Bound**: **21.60%** for single-label Top-1 multiclass classification.
- **Conclusion**: Evaluating a multi-crop agricultural domain as a mutually exclusive single-label multiclass classification task creates severe artificial "misclassification" penalties when the model correctly predicts a high-yielding, agronomically suitable crop (e.g., Maize) for a location where historical records happened to plant Rice.

---

## 2. COMPARISON OF TARGET FORMULATION OPTIONS

| Target Formulation | Description | Advantages for KrishiMitra Data | Disadvantages for KrishiMitra Data | Recommendation Status |
| :--- | :--- | :--- | :--- | :---: |
| **A. Multiclass Classification** | Predict single crop $y \\in \\{1 \\dots 28\\}$ with probability distribution $P(y=k \\mid X)$. | Native output via `predict_proba()`; simple calibration; matches existing sklearn estimators. | Penalizes valid alternative crops; Top-1 accuracy capped at ~21.6% due to multi-crop Bayes upper bound. | **Baseline ML Layer Only** |
| **B. Multilabel Classification** | Predict binary vector $\\mathbf{y} \\in \\{0, 1\\}^{28}$ for suitability. | Accommodates multiple simultaneous crops for the same soil/climate vector. | Historical APY dataset lacks true negative labels (unobserved crop $\\neq$ unviable crop); requires complex negative sampling. | **REJECTED** |
| **C. Learning-to-Rank (LTR)** | Rank 28 crops using pairwise/listwise ranking (e.g., LambdaMART). | Directly optimizes relative ordering (NDCG, MAP, MRR) rather than absolute class identity. | Requires explicit relevance grades per district-season; sensitive to historical popularity bias. | **REJECTED as standalone** |
| **D. Crop Suitability Scoring** | Deterministic agronomic score based on ICAR/FAO eco-crop bounds. | 100% explainable, deterministic, zero ML hallucination, strictly enforces soil pH/rainfall limits. | Static rules cannot learn complex non-linear spatial interactions or historical adoption trends. | **Agronomic Layer Component** |
| **E. Regression + Ranking** | Predict expected yield $E[\\text{Yield}_k \\mid X]$ per crop and rank by predicted yield. | Provides quantitative economic return expectation. | Yield is dominated by unobserved farmer management, technology, and inputs; extreme high variance. | **REJECTED** |
| **F. Hybrid Approach (ML Probabilities + ICAR Agronomic Suitability + Regional Density)** | **RECOMMENDED**: Combine ML calibrated probabilities $P_{ML}(Crop_k \\mid X)$ with ICAR agronomic compliance score $S_{\\text{Agro}}$ and historical regional yield density $S_{\\text{Reg}}$ into a unified **Crop Suitability Index (CSI)**. | **Highest accuracy, zero invalid recommendations, 100% explainable, multi-crop aware, bypasses Bayes bound bottleneck.** | Requires two-stage score fusion engine and ICAR profile metadata. | **SELECTED FINAL FORMULATION** |

---

## 3. RECOMMENDED FINAL TARGET FORMULATION

The final KrishiMitra target is formulated as a **Composite Crop Suitability Index (CSI)** vector across all 28 candidate crops:

$$\\text{CSI}(Crop_k \\mid X) = w_1 \\cdot P_{ML}(Crop_k \\mid X) + w_2 \\cdot S_{\\text{Agronomic}}(Crop_k, X_{\\text{soil}}, X_{\\text{climate}}) + w_3 \\cdot S_{\\text{Regional}}(Crop_k, X_{\\text{location}})$$

- **Primary ML Model Output**: Calibrated multiclass probability distribution $P_{ML}(Crop_k \\mid X)$ output by a tree-based ensemble pipeline.
- **Evaluation Criteria**: Instead of strict single-label Top-1 accuracy, the system will be evaluated using:
  1. **Top-K Recall / Hit Rate**: $K \\in \\{1, 3, 5\\}$ (Is any of the top $K$ recommended crops in the historically successful crop set for that location?).
  2. **Normalized Discounted Cumulative Gain (NDCG@3, NDCG@5)**.
  3. **Agronomic Violation Rate**: Percentage of top recommendations violating hard ICAR soil/climate limits (Target: **0.00%**).

---

## 4. FINAL FEATURE SET DESIGN

The feature matrix $X$ consists of 24 carefully audited, non-leaking agronomic variables across 4 distinct categories:

```
+-----------------------------------------------------------------------------------+
|                            KRISHIMITRA ML FEATURE MATRIX X                        |
+--------------------------+--------------------------+-----------------------------+
| CATEGORY                 | FEATURE NAME             | DATA TYPE / SEMANTICS       |
+--------------------------+--------------------------+-----------------------------+
| 1. LOCATION              | State                    | Categorical (One-Hot)       |
|                          | agro_climatic_region     | Categorical (15 ICAR Zones) |
+--------------------------+--------------------------+-----------------------------+
| 2. SOIL TELEMETRY        | indian_soil_group        | Categorical (5 Major Groups)|
|                          | usda_texture             | Categorical (USDA Texture)  |
|                          | ph                       | Continuous (4.2 - 8.8)      |
|                          | nitrogen_cg_kg           | Continuous (cg/kg)          |
|                          | soc_dg_kg                | Continuous (SOC dg/kg)      |
|                          | cec                      | Continuous (mmol(c)/kg)     |
|                          | clay_pct                 | Continuous (0 - 100%)       |
|                          | sand_pct                 | Continuous (0 - 100%)       |
|                          | silt_pct                 | Continuous (0 - 100%)       |
|                          | bulk_density             | Continuous (kg/dm³)         |
+--------------------------+--------------------------+-----------------------------+
| 3. CLIMATE TELEMETRY     | annual_rainfall_mm       | Continuous (mm)             |
|                          | kharif_rainfall_mm       | Continuous (Monsoon mm)     |
|                          | rabi_rainfall_mm         | Continuous (Winter mm)      |
|                          | mean_temperature_c       | Continuous (°C)             |
|                          | max_temperature_c        | Continuous (°C)             |
|                          | min_temperature_c        | Continuous (°C)             |
|                          | relative_humidity_pct    | Continuous (%)              |
|                          | wind_speed_ms            | Continuous (m/s)            |
+--------------------------+--------------------------+-----------------------------+
| 4. AGRICULTURAL CONTEXT  | Season                   | Categorical (Kharif, Rabi..)|
|                          | irrigation_type          | Categorical (Rainfed, Drip..|
|                          | water_availability       | Categorical (High, Mod, Low)|
|                          | water_source             | Categorical (Canal, Bore.. )|
+--------------------------+--------------------------+-----------------------------+
```

---

## 5. FEATURE CATEGORIZATION & PREPROCESSING PIPELINE

```
Raw Input Data (Dict / DF)
  │
  ├──► Continuous Numeric Features (16) ──► RobustScaler / MinMaxScaler ────┐
  │                                                                          │
  ├──► Categorical Features (8) ────────► OneHotEncoder(sparse=False) ──────┼──► Feature Matrix X (62 dimensions) ──► ML Ensemble Pipeline
  │                                                                          │
  └──► Domain Engineered Features (10) ──► Custom Transformer ──────────────┘
```

1. **Continuous Numeric Features (16)**:
   `ph`, `clay_pct`, `sand_pct`, `silt_pct`, `nitrogen_cg_kg`, `soc_dg_kg`, `cec`, `bulk_density`, `annual_rainfall_mm`, `kharif_rainfall_mm`, `rabi_rainfall_mm`, `mean_temperature_c`, `max_temperature_c`, `min_temperature_c`, `relative_humidity_pct`, `wind_speed_ms`.
   - *Preprocessing*: Scaled via `RobustScaler()` to preserve extreme weather/soil outliers without distorting tree boundaries.

2. **Categorical Features (8)**:
   `State`, `agro_climatic_region`, `indian_soil_group`, `usda_texture`, `Season`, `irrigation_type`, `water_availability`, `water_source`.
   - *Preprocessing*: Encoded via `OneHotEncoder(handle_unknown='ignore', sparse_output=False)`.

---

## 6. ENGINEERED AGRICULTURAL FEATURES (10 DOMAIN FEATURES)

To give the ML model deep agronomic reasoning capability beyond raw values, 10 domain features are mathematically computed:

| Feature Name | Mathematical Definition | Agronomic Purpose | Reference Source |
| :--- | :--- | :--- | :--- |
| **1. `rainfall_adequacy_ratio`** | $\\frac{\\text{Seasonal Rainfall (mm)}}{\\text{Crop Water Demand (mm)}}$ | Measures if rainfall satisfies seasonal crop evapotranspiration. | ICAR Water Management Guidelines |
| **2. `temperature_stress_index`** | $\\max(0, T_{\\text{max}} - 35) + \\max(0, 10 - T_{\\text{min}})$ | Quantifies heat stress ($>35^\\circ\\text{C}$) and cold stress ($<10^\\circ\\text{C}$). | ICAR Heat Stress Standards |
| **3. `drought_indicator`** | $\\mathbb{I}\\left(\\frac{\\text{Kharif Rain}}{\\text{Normal Kharif Rain}} < 0.75\\right)$ | Binary/continuous flag for meteorological drought conditions. | IMD Drought Normals |
| **4. `excess_rainfall_indicator`** | $\\mathbb{I}\\left(\\frac{\\text{Kharif Rain}}{\\text{Normal Kharif Rain}} > 1.50\\right)$ | Flag for waterlogging and flood risk. | IMD Excessive Rainfall Standard |
| **5. `soil_moisture_suitability`** | $\\text{Clay\\%} \\times 0.4 + \\text{SOC} \\times 0.3 + \\left(\\frac{\\text{Rain}}{1000}\\right) \\times 0.3$ | Approximates soil field capacity & moisture retention capability. | Soil Survey of India (SS&LUP) |
| **6. `water_stress_index`** | $1.0 - \\min\\left(1.0, \\frac{\\text{Water Availability Factor}}{\\text{Crop Demand}}\\right)$ | Incorporates irrigation infrastructure buffer against rain deficit. | FAO-56 Irrigation & Drainage |
| **7. `ph_suitability_score`** | $\\exp\\left(-\\frac{(\\text{pH} - 6.8)^2}{2 \\times 0.8^2}\\right)$ | Continuous Gaussian bell curve centered at optimal neutral soil pH (6.8). | ICAR Soil Health Card Manual |
| **8. `soil_texture_suitability`** | $\\frac{\\text{Sand\\%}}{\\text{Clay\\% + 1.0}}$ | Sand-to-Clay ratio for root aeration vs drainage assessment. | USDA Soil Taxonomy |
| **9. `seasonal_thermal_window`** | $\\mathbb{I}(T_{\\text{mean}} \\in [T_{\\text{opt\\_min}}, T_{\\text{opt\\_max}}])$ | Season-specific thermal suitability window. | ICAR Crop Production Manual |
| **10. `climate_suitability_composite`** | $\\sqrt[3]{\\text{Rainfall\\_Match} \\times \\text{Temp\\_Match} \\times \\text{RH\\_Match}}$ | Geometric mean of climate factor compatibility scores. | FAO Eco-Crop Assessment Method |

---

## 7. TRAIN / VALIDATION / TEST STRATEGY

### A. Preventing Spatial & Temporal Leakage
- **The Leakage Danger**: Standard random row splitting (e.g. `train_test_split(df)`) causes **severe spatial leakage**. Because the dataset contains historical years (1997–2020) for the same 635 districts, random row splitting places identical district soil & climate profiles into both train and test sets. This leads to artificially inflated validation metrics that fail catastrophically in real-world deployment on new locations.

### B. Validation Design
1. **Spatial Group Holdout Split (`GroupKFold` by District)**:
   - Group by `district_key` (635 total districts).
   - 80% Train Districts (~508 districts), 20% Unseen Test Districts (~127 districts).
   - Tests zero-shot spatial generalization to new geographical locations.
2. **Temporal Split (Historical vs Recent Years)**:
   - Train set: Historical years **1997 – 2015** (80%).
   - Test set: Recent years **2016 – 2020** (20%).
   - Evaluates stability against climate shift and changing weather patterns.
3. **Primary CV Scheme**: **5-Fold Stratified Group K-Fold (`GroupKFold` on `district_key`)**.

---

## 8. MODEL FAMILY EXPERIMENTS & SELECTION

We design experiments across 4 distinct tree-based ensemble model families available in `scikit-learn`:

```
                           +-------------------------------------+
                           |      CANDIDATE MODEL FAMILIES       |
                           +-------------------------------------+
                                              │
         ┌──────────────────────┬─────────────┴────────────┬──────────────────────┐
         ▼                      ▼                          ▼                      ▼
+------------------+  +------------------+       +------------------+   +------------------+
|   RandomForest   |  |    ExtraTrees    |       | HistGradientBoost|   | GradientBoosting |
|   Classifier     |  |    Classifier    |       |   Classifier     |   |   Classifier     |
+------------------+  +------------------+       +------------------+   +------------------+
| n_estimators=300 |  | n_estimators=300 |       | max_iter=200     |   | n_estimators=200 |
| max_depth=25     |  | max_depth=25     |       | max_depth=15     |   | learning_rate=0.1|
| class_weight=bal |  | class_weight=bal |       | early_stopping   |   | max_depth=8      |
+------------------+  +------------------+       +------------------+   +------------------+
```

1. **Random Forest Classifier**: Baseline ensemble; robust to non-linear feature interactions and noisy historical labels.
2. **Extra Trees Classifier**: Randomized tree splits; faster training speed and strong variance reduction on soil/climate features.
3. **HistGradientBoosting Classifier**: Fast gradient boosting native to `scikit-learn` (inspired by LightGBM); superior probability calibration for multiclass outputs.
4. **Gradient Boosting Classifier**: Standard GBDT algorithm for comparison.
5. **Optional External Boosters**: Wrappers provided for `LightGBM` and `XGBoost` if installed in the environment.

---

## 9. ENSEMBLE STRATEGY (SOFT VOTING PIPELINE)

To achieve maximum probability calibration and spatial stability, the final production model utilizes a **Weighted Soft Voting Ensemble**:

$$P_{\\text{Ensemble}}(y=k \\mid X) = w_{\\text{HGB}} P_{\\text{HGB}}(y=k \\mid X) + w_{\\text{RF}} P_{\\text{RF}}(y=k \\mid X) + w_{\\text{ET}} P_{\\text{ET}}(y=k \\mid X)$$

- **Weights**: $w_{\\text{HGB}} = 0.45$, $w_{\\text{RF}} = 0.35$, $w_{\\text{ET}} = 0.20$.
- **Calibration**: Applied via `CalibratedClassifierCV(method='sigmoid')` to convert raw tree counts into true empirical probabilities.

---

## 10. EVALUATION METRICS DEFINITION

The final model candidate evaluation suite computes:

1. **Top-1 Accuracy**: Percentage of test samples where ground truth is rank #1 prediction.
2. **Top-3 Accuracy (Primary Metric)**: Percentage of test samples where ground truth is within top 3 predictions.
3. **Top-5 Accuracy**: Percentage of test samples where ground truth is within top 5 predictions.
4. **Macro F1 & Weighted F1**: Overall class-balanced performance measure across all 28 crops.
5. **Per-Crop Precision & Recall**: Detailed breakdown per crop to detect rare-class underperformance.
6. **Expected Calibration Error (ECE) & Brier Score**: Quantifies reliability of predicted probability scores.
7. **Ranking Metrics (NDCG@3, NDCG@5, MRR)**: Evaluates quality of recommended crop order.
8. **Agronomic Violation Rate**: Percentage of recommendations violating hard ICAR pH/rainfall limits (Must be **0.00%**).

---

## 11. MATHEMATICAL SCORE FUSION GENERATION

The final recommendation rank is determined by the **Composite Crop Suitability Index (CSI)**, eliminating arbitrary hardcoded overrides (e.g. "if Rabi then force Gram"):

$$\\text{CSI}(Crop_k) = 0.50 \\cdot P_{\\text{ML}}(Crop_k \\mid X) + 0.35 \\cdot S_{\\text{Agronomic}}(Crop_k, X_{\\text{soil}}, X_{\\text{climate}}) + 0.15 \\cdot S_{\\text{Regional}}(Crop_k, X_{\\text{state}})$$

### Soft Penalty Functions ($S_{\\text{Agronomic}}$)
Instead of binary rules, continuous logistic decay curves penalize crops outside ICAR viable bands:

$$S_{\\text{pH}}(Crop_k, \\text{pH}) = \\frac{1}{1 + \\exp\\left(10 \\cdot (\\text{pH}_{\\text{min}, k} - \\text{pH})\\right)} \\times \\frac{1}{1 + \\exp\\left(10 \\cdot (\\text{pH} - \\text{pH}_{\\text{max}, k})\\right)}$$

This guarantees smooth score degradation rather than hard cliff drops.

---

## 12. EXPLAINABILITY BREAKDOWN SPECIFICATION

Every recommendation output by KrishiMitra includes a deterministic 7-factor explainability payload:

```json
{
  "crop": "Maize",
  "csi_score": 88.5,
  "ml_confidence_pct": 82.4,
  "factor_breakdown": {
    "soil_compatibility_pct": 92.0,
    "season_compatibility_pct": 100.0,
    "rainfall_compatibility_pct": 85.5,
    "temperature_compatibility_pct": 91.0,
    "water_compatibility_pct": 88.0,
    "historical_suitability_pct": 84.0
  },
  "key_drivers": [
    "Optimal soil pH (6.5 within 6.0 - 7.5 range)",
    "Strong Kharif monsoon rainfall compatibility (850mm)"
  ],
  "agronomic_advice": "Ensure adequate nitrogen application during vegetative stage; well-drained soil prevents waterlogging."
}
```

---

## 13. QWEN / BIONIC LLM FALLBACK ARCHITECTURE

Qwen / Bionic LLM is **demoted from decision maker to optional presentation layer**.

- **Environment Variable**: `USE_QWEN_FALLBACK=true` (Default) or `false`.

```
                        [ USER QUERY / FARM CONTEXT ]
                                      │
                                      ▼
                        [ KRISHIMITRA ML ENGINE ]
                     (CSI Score Fusion & ICAR Rules)
                                      │
                                      ▼
                        [ STRUCTURED ML PAYLOAD ]
                                      │
                   ┌──────────────────┴──────────────────┐
                   │                                     │
     USE_QWEN_FALLBACK = false             USE_QWEN_FALLBACK = true
                   │                                     │
                   ▼                                     ▼
     [ DIRECT STRUCTURED ML RESPONSE ]       [ QWEN NATURAL LANGUAGE SYNTHESIZER ]
     - UI renders ML Card Directly           - System Prompt: "Synthesize ML payload in
     - Zero LLM Latency                        empathetic Telugu/Hindi/English."
     - Zero LLM Hallucination Risk           - STRICT GROUNDING: Cannot change crops!
                                                         │
                                             ┌───────────┴───────────┐
                                             │                       │
                                          Success                 Failure
                                             │                       │
                                             ▼                       ▼
                                      [ LLM Text Output ]    [ Direct ML Fallback ]
```

---

## 14. FINAL MODEL ARTIFACTS STRUCTURE

The final model outputs will be serialized under `ml/models/v3_production/`:

```
backend/app/ml/models/v3_production/
├── crop_suitability_ensemble.pkl     # Trained Soft Voting Ensemble Pipeline
├── crop_feature_preprocessor.pkl      # ColumnTransformer & Scaling Artifact
├── crop_agronomic_rules.json          # ICAR Optimal & Viable Crop Profile Bounds
├── model_metadata.json                # Version, Hyperparameters, Feature Order, Metrics
└── model_evaluation_report.json       # Full Holdout & Cross-Validation Metric Suite
```

---

## 15. SUMMARY & NEXT STEPS

This design establishes a mathematically sound, agronomic-first ML architecture that solves the multi-crop ambiguity bottleneck, eliminates data leakage, ensures 100% explainability, and establishes KrishiMitra's ML engine as the **unshakeable Primary Intelligence of the platform**.
"""

json_content = {
    "architecture_name": "KrishiMitra Agricultural ML System V3",
    "status": "DESIGN_COMPLETE",
    "audit_date": "2026-09",
    "primary_intelligence": "ML_ENGINE",
    "llm_role": "OPTIONAL_BACKUP_AND_NATURAL_LANGUAGE_SYNTHESIZER",
    "llm_toggle_env": "USE_QWEN_FALLBACK",
    "target_analysis": {
        "dataset_records": 246091,
        "filtered_training_records": 136128,
        "crop_classes": 28,
        "multi_crop_districts_pct": 88.38,
        "mean_crops_per_telemetry_vector": 7.43,
        "bayes_optimal_top1_upper_bound_pct": 21.60,
        "formulation_choice": "HYBRID_CSI_SCORE_FUSION"
    },
    "composite_score_formula": "CSI(Crop_k) = 0.50 * P_ML(Crop_k|X) + 0.35 * S_Agronomic(Crop_k, Soil, Climate) + 0.15 * S_Regional(Crop_k, State)",
    "feature_matrix": {
        "total_features": 24,
        "numeric_telemetry_count": 16,
        "categorical_count": 8,
        "engineered_domain_features_count": 10,
        "engineered_features": [
            "rainfall_adequacy_ratio",
            "temperature_stress_index",
            "drought_indicator",
            "excess_rainfall_indicator",
            "soil_moisture_suitability",
            "water_stress_index",
            "ph_suitability_score",
            "soil_texture_suitability",
            "seasonal_thermal_window",
            "climate_suitability_composite"
        ]
    },
    "validation_strategy": {
        "scheme": "5-Fold Stratified GroupKFold by district_key",
        "spatial_holdout_districts_pct": 20.0,
        "temporal_split": "Train: 1997-2015, Test: 2016-2020",
        "spatial_leakage_prevention": "Strict Grouping on district_key"
    },
    "candidate_models": [
        "RandomForestClassifier",
        "ExtraTreesClassifier",
        "HistGradientBoostingClassifier",
        "GradientBoostingClassifier"
    ],
    "ensemble_strategy": {
        "type": "Weighted Soft Voting Ensemble",
        "weights": {
            "HistGradientBoosting": 0.45,
            "RandomForest": 0.35,
            "ExtraTrees": 0.20
        },
        "calibration": "CalibratedClassifierCV (Sigmoid)"
    },
    "evaluation_metrics": [
        "Top-1 Accuracy",
        "Top-3 Accuracy",
        "Top-5 Accuracy",
        "Macro F1",
        "Weighted F1",
        "Per-Crop Recall",
        "Per-Crop Precision",
        "Expected Calibration Error (ECE)",
        "Brier Score",
        "NDCG@3",
        "NDCG@5",
        "Mean Reciprocal Rank (MRR)",
        "Agronomic Violation Rate"
    ],
    "explainability_factors": [
        "soil_compatibility_pct",
        "season_compatibility_pct",
        "rainfall_compatibility_pct",
        "temperature_compatibility_pct",
        "water_compatibility_pct",
        "ml_confidence_pct",
        "historical_suitability_pct"
    ],
    "artifact_paths": {
        "ensemble_model": "ml/models/v3_production/crop_suitability_ensemble.pkl",
        "preprocessor": "ml/models/v3_production/crop_feature_preprocessor.pkl",
        "agronomic_rules": "ml/models/v3_production/crop_agronomic_rules.json",
        "metadata": "ml/models/v3_production/model_metadata.json",
        "evaluation_report": "ml/models/v3_production/model_evaluation_report.json"
    }
}

with open(MARKDOWN_PATH, "w", encoding="utf-8") as f:
    f.write(markdown_content)
print(f"Successfully generated {MARKDOWN_PATH}")

with open(JSON_PATH, "w", encoding="utf-8") as f:
    json.dump(json_content, f, indent=2)
print(f"Successfully generated {JSON_PATH}")
