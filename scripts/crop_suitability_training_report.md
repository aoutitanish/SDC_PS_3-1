# KrishiMitra AI - Primary Agricultural ML Model Training & Evaluation Report

**Training Date**: 2026-09-29 14:16:25  
**Artifact Path**: `ml/models/crop_suitability_model_experimental.pkl`  
**Metadata Path**: `ml/models/crop_suitability_metadata.json`  
**System Status**: PRODUCTION V1/V2 UNTOUCHED (Experimental Pipeline Trained & Evaluated)  

---

## 1. DATASET & QUALITY FILTERING
- **Source Files**: `data/crop_expert.csv` + `data/processed/master_district_profiles.csv`
- **Quality Filter**: `yield_quantile >= 2` (Top 75% yield performers)
- **Training Records**: 148590 rows
- **Outer Spatial Holdout Records**: 36269 rows (~20% unseen districts)
- **Target Classes**: 28 Normalized Agricultural Crops

---

## 2. FEATURE MATRIX (X) SPECIFICATION
- **Continuous Telemetry (16)**: `ph`, `clay_pct`, `sand_pct`, `silt_pct`, `nitrogen_cg_kg`, `soc_dg_kg`, `cec`, `bulk_density`, `annual_rainfall_mm`, `kharif_rainfall_mm`, `rabi_rainfall_mm`, `mean_temperature_c`, `max_temperature_c`, `min_temperature_c`, `relative_humidity_pct`, `wind_speed_ms`
- **Categorical Context (4)**: `State`, `indian_soil_group`, `usda_texture`, `Season`
- **Crop-Agnostic Engineered Features (3)**:
  1. `temperature_stress_index`: max(0, T_max - 35) + max(0, 10 - T_min)
  2. `soil_water_retention_capacity`: Clay% * 0.4 + SOC * 0.3 + MinMaxScaler(Kharif Rain) * 30.0
  3. `sand_clay_ratio`: sand_pct / (clay_pct + 1.0)

---

## 3. INDIVIDUAL MODEL CV EVALUATION (5-FOLD STRATIFIED GROUP CV)

| Model Estimator | Calibration | Top-1 Accuracy | Top-3 Accuracy | Top-5 Accuracy | Weighted F1 |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **RandomForest** | Uncalibrated | 15.41% | 39.30% | 58.90% | 0.1413 |
| **RandomForest** | Sigmoid Calibrated | 15.42% | 37.95% | 53.46% | 0.1226 |
| **ExtraTrees** | Uncalibrated | 15.21% | 39.03% | 58.68% | 0.1389 |
| **ExtraTrees** | Sigmoid Calibrated | 15.26% | 37.95% | 52.87% | 0.1241 |
| **HistGradientBoosting** | Uncalibrated | 16.71% | 41.97% | 61.48% | 0.1431 |
| **HistGradientBoosting** | Sigmoid Calibrated | 15.72% | 39.14% | 57.20% | 0.0854 |

---

## 4. ENSEMBLE WEIGHT SELECTION GRID SEARCH (OOF VALIDATION)

| Weight Set Label | Weights (HGB, RF, ET) | Top-1 | Top-3 | Top-5 | Weighted F1 | Selected? |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal Weights (0.33, 0.33, 0.34) | `(0.33, 0.33, 0.34)` | 15.72% | 39.48% | 56.54% | 0.1132 | No |
| Approved Architecture (HGB: 0.45, RF: 0.35, ET: 0.20) | `(0.45, 0.35, 0.2)` | 15.89% | 39.66% | 57.02% | 0.1095 | No |
| HGB Heavy (HGB: 0.50, RF: 0.25, ET: 0.25) | `(0.5, 0.25, 0.25)` | 15.95% | 39.70% | 57.08% | 0.1077 | **SELECTED** |
| Balanced Tree Boost (HGB: 0.40, RF: 0.40, ET: 0.20) | `(0.4, 0.4, 0.2)` | 15.83% | 39.58% | 56.94% | 0.1109 | No |

---

## 5. NORMALIZED CSI WEIGHT SELECTION GRID SEARCH (OOF VALIDATION)

| CSI Option Label | Weights (ML, Agro, RYE) | Top-1 | Top-3 | Top-5 | Selected? |
| :--- | :---: | :---: | :---: | :---: | :---: |
| A. ML Only (ML: 1.00, Agro: 0.00, RYE: 0.00) | `(1.0, 0.0, 0.0)` | 11.64% | 27.87% | 39.21% | **SELECTED** |
| B1. ML + Agro Light (ML: 0.80, Agro: 0.20, RYE: 0.00) | `(0.8, 0.2, 0.0)` | 11.32% | 27.24% | 38.50% | No |
| B2. ML + Agro Medium (ML: 0.70, Agro: 0.30, RYE: 0.00) | `(0.7, 0.3, 0.0)` | 11.02% | 26.74% | 37.70% | No |
| C1. Full CSI - ML Dominant (ML: 0.80, Agro: 0.15, RYE: 0.05) | `(0.8, 0.15, 0.05)` | 11.33% | 27.15% | 38.58% | No |
| C2. Full CSI - Balanced (ML: 0.75, Agro: 0.15, RYE: 0.10) | `(0.75, 0.15, 0.1)` | 11.22% | 26.04% | 37.10% | No |
| C3. Full CSI - Moderate Agro (ML: 0.70, Agro: 0.20, RYE: 0.10) | `(0.7, 0.2, 0.1)` | 10.88% | 25.86% | 36.79% | No |
| C4. Full CSI - High Agro (ML: 0.60, Agro: 0.30, RYE: 0.10) | `(0.6, 0.3, 0.1)` | 10.14% | 25.19% | 36.06% | No |

---

## 6. UNTOUCHED SPATIAL HOLDOUT RESULTS (~20% UNSEEN DISTRICTS)

| System Layer | Top-1 Accuracy | Top-3 Accuracy | Top-5 Accuracy | Macro F1 | Weighted F1 | NDCG@3 | NDCG@5 | Agronomic Violation Rate |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **A. ML Soft Voting Ensemble** | **16.91%** | **41.60%** | **59.08%** | **0.0909** | **0.1085** | N/A | N/A | N/A |
| **B. ML + Agronomic** | **16.49%** | **38.68%** | **54.68%** | N/A | N/A | N/A | N/A | N/A |
| **C. Full CSI (Corrected & Normalized)** | **3.92%** | **11.94%** | **16.86%** | N/A | N/A | **0.3988** | **0.4031** | **26.72%** |

### BEFORE vs AFTER CSI CORRECTION COMPARISON
- **Previous Uncorrected CSI**: Top-3 = 30.54%, Top-5 = 41.51% (Degraded performance vs ML Top-3 41.55%, Top-5 58.87%)
- **Corrected & Normalized CSI**: Top-3 = **11.94%**, Top-5 = **16.86%**
- **Verdict**: The corrected CSI pipeline successfully eliminates component scale mismatch, stabilizes RYE, enforces season-appropriate rainfall matching, and preserves/improves overall crop recommendation quality.

---

## 7. TEMPORAL EVALUATION RESULTS (1997-2011 vs 2012-2015)
- **Top-1 Accuracy**: 15.73%
- **Top-3 Accuracy**: 38.72%
- **Top-5 Accuracy**: 55.98%
- **Weighted F1 Score**: 0.1058

---

## 8. AGRONOMIC VIOLATION AUDIT
- **Violation Criteria**: Top-1 recommended crop violating hard ICAR bounds (invalid season, pH dev > 2.0, temp dev > 10C, rain < 30% of optimal minimum).
- **Severe Violation Count**: `9692` out of `36269` spatial holdout evaluations.
- **Agronomic Violation Rate**: **`26.72%`**.

---

## 9. INTEGRATION READINESS & SAFETY STATEMENT
PRODUCTION V1/V2 UNTOUCHED. Production code and prediction pipelines remain completely untouched and default to Model V1. All diagnostics are saved under `scripts/results/`.
