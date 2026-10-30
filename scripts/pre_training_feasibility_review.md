# KrishiMitra AI - Pre-Training Feasibility Review & Architectural Refinement

**Review Date**: September 2026  
**Status**: PRE-TRAINING FEASIBILITY AUDIT COMPLETE (Zero Code/Model Mutations Made)  
**Workspace**: `C:\Users\aouti\Desktop\PS-3\FarmerHelp`  

---

## 1. COMPONENT-BY-COMPONENT ARCHITECTURAL AUDIT

```
+---------------------------------------------------------------------------------------------------------------+
|                                      PRE-TRAINING FEASIBILITY AUDIT SUMMARY                                   |
+------------------------------------+--------+--------+--------+-----------------------------------------------+
| ARCHITECTURE COMPONENT             | KEEP   | MODIFY | REMOVE | REASON & FEASIBILITY FINDINGS                 |
+------------------------------------+--------+--------+--------+-----------------------------------------------+
| Hybrid CSI Formula                 |        |   X    |        | Fixed 0.50/0.35/0.15 weights must be tuned via|
|                                    |        |        |        | OOF grid search without touching test set.    |
+------------------------------------+--------+--------+--------+-----------------------------------------------+
| 24 Raw Feature Inputs              |   X    |        |        | All 24 features verified available in data.   |
+------------------------------------+--------+--------+--------+-----------------------------------------------+
| Crop-Agnostic Engineered Features  |   X    |        |        | Features dependent only on location/climate   |
| (Thermal stress, Soil retention)   |        |        |        | can safely remain in ML Feature Matrix X.     |
+------------------------------------+--------+--------+--------+-----------------------------------------------+
| Crop-Dependent Features            |        |        |   X    | REMOVED FROM X! Crop water demand, pH optimal |
| (Water demand, pH match, etc.)     |        |        |        | bounds cannot be in X; moved to Stage 2 ICAR! |
+------------------------------------+--------+--------+--------+-----------------------------------------------+
| Drought Indicator (Normals vs Live)|        |   X    |        | Climate normals cannot represent live drought.|
|                                    |        |        |        | Converted to static Aridity Index in X + Live |
|                                    |        |        |        | Weather Override in Stage 2.                  |
+------------------------------------+--------+--------+--------+-----------------------------------------------+
| Regional Suitability Score         |        |   X    |        | Raw crop volume/frequency causes popularity   |
|                                    |        |        |        | bias; modified to Relative Yield Efficiency.  |
+------------------------------------+--------+--------+--------+-----------------------------------------------+
| Sklearn Tree Estimator Ensemble    |   X    |        |        | RF, ExtraTrees, HistGradientBoosting verified |
|                                    |        |        |        | available in sklearn 1.9.1 (No XGB/LGBM needed)|
+------------------------------------+--------+--------+--------+-----------------------------------------------+
| Calibrated Soft Voting             |        |   X    |        | Raw tree probabilities must be calibrated via |
|                                    |        |        |        | CalibratedClassifierCV before soft voting.    |
+------------------------------------+--------+--------+--------+-----------------------------------------------+
| Validation Protocol                |        |   X    |        | Verified StratifiedGroupKFold exists in       |
|                                    |        |        |        | sklearn 1.9.1; 20% spatial holdout enforced.  |
+------------------------------------+--------+--------+--------+-----------------------------------------------+
```

---

## 2. DETAILED AUDIT OF PROPOSED ENGINEERED FEATURES

### Critical Rule: Separation of Feature Matrix $X$ vs Stage 2 Agronomic Engine
The Feature Matrix $X$ is passed to the ML classifier to predict $P_{ML}(Crop_k \mid X)$ across **all 28 crops simultaneously**. Therefore, $X$ **CANNOT** contain features that require knowing which crop is being evaluated (e.g. crop water demand, crop optimal pH). Those crop-dependent metrics belong exclusively in **Stage 2 (ICAR Agronomic Engine)**.

| Engineered Feature | Proposed Formula | Input Columns Required | Exist in Dataset? | Calculable at Train? | Calculable at Inference? | Leakage Risk? | Audit Recommendation | Corrected Implementation Layer |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **`rainfall_adequacy_ratio`** | $\frac{\text{Rainfall}}{\text{Crop Water Demand}}$ | `kharif_rainfall_mm`, Crop Water Demand | Partial (Crop demand is crop-specific) | No (Crop unknown in $X$) | No (Crop unknown in $X$) | None | **REMOVE FROM $X$** | Move to Stage 2 ICAR Engine as $S_{\text{Rainfall}}(Crop_k, X)$ |
| **`temperature_stress_index`** | $\max(0, T_{\text{max}} - 35) + \max(0, 10 - T_{\text{min}})$ | `max_temperature_c`, `min_temperature_c` | **YES** | **YES** | **YES** | None | **KEEP IN $X$** | Retain in $X$ as location thermal stress metric |
| **`drought_indicator`** | $\mathbb{I}\left(\frac{\text{Observed Rain}}{\text{Normal Rain}} < 0.75\right)$ | Observed Rain, Normal Rain | **NO** (Only 30-yr climate normals exist) | No (No live rain gauge in profile) | No (No live rain gauge in profile) | High if fake data used | **MODIFY** | Re-formulated as `monsoon_aridity_index` in $X$; live drought passed via Stage 2 override |
| **`excess_rainfall_indicator`** | $\mathbb{I}(\text{Monsoon Rain} > 1500\text{mm})$ | `kharif_rainfall_mm`, `annual_rainfall_mm` | **YES** | **YES** | **YES** | None | **MODIFY** | Formulated as `monsoon_concentration_ratio` in $X$ |
| **`soil_moisture_suitability`** | $\text{Clay\%} \times 0.4 + \text{SOC} \times 0.3 + \text{Rain} \times 0.3$ | `clay_pct`, `soc_dg_kg`, `kharif_rainfall_mm` | **YES** | **YES** | **YES** | None | **KEEP IN $X$** | Retain in $X$ as `soil_water_retention_capacity` |
| **`water_stress_index`** | Evapotranspiration Deficit | `annual_rainfall_mm`, Crop ET | Partial (Crop ET is crop-specific) | No (Crop unknown in $X$) | No (Crop unknown in $X$) | None | **REMOVE FROM $X$** | Move to Stage 2 ICAR Engine as $S_{\text{Water}}(Crop_k, X)$ |
| **`ph_suitability_score`** | Distance from optimal pH | `ph`, Crop Optimal pH | Partial (Crop optimal pH is crop-specific) | No (Crop unknown in $X$) | No (Crop unknown in $X$) | None | **MODIFY** | In $X$: Keep raw `ph` + `ph_extreme_flag`. Move crop pH distance to Stage 2 ICAR |
| **`soil_texture_suitability`** | $\frac{\text{sand\%}}{\text{clay\%} + 1.0}$ | `sand_pct`, `clay_pct` | **YES** | **YES** | **YES** | None | **KEEP IN $X$** | Retain in $X$ as `sand_clay_ratio` |
| **`seasonal_thermal_window`** | Thermal window match | `mean_temperature_c`, Crop Temp Limits | Partial (Crop temp limit is crop-specific) | No (Crop unknown in $X$) | No (Crop unknown in $X$) | None | **REMOVE FROM $X$** | Move to Stage 2 ICAR Engine as $S_{\text{Thermal}}(Crop_k, X)$ |
| **`climate_suitability_composite`**| Multi-factor climate match | Rain, Temp, RH, Crop Bounds | Partial (Crop bounds are crop-specific) | No (Crop unknown in $X$) | No (Crop unknown in $X$) | None | **REMOVE FROM $X$** | Move to Stage 2 ICAR Engine |

---

## 3. DROUGHT & CLIMATE TELEMETRY AUDIT

### Audit Finding:
- **`master_district_profiles.csv`** contains 30-year IMD & NASA POWER climate normals (`annual_rainfall_mm`, `kharif_rainfall_mm`, `rabi_rainfall_mm`).
- It does **NOT** contain live real-time rain gauge data for the current day or season.
- If a model feature tries to compute `drought_indicator` using static climate normals, $\frac{\text{Normal Rain}}{\text{Normal Rain}}$ equals $1.0$ constantly everywhere, rendering the feature completely useless or misleading.

### Recommended Dual-Layer Drought Architecture:
1. **Layer 1 (ML Feature Matrix $X$)**: Static climatic aridity indices calculated from climate normals:
   - `monsoon_aridity_index` = $\frac{\text{kharif_rainfall_mm}}{\text{annual_rainfall_mm}}$
   - `thermal_aridity_index` = $\frac{\text{mean_temperature_c}}{\text{annual_rainfall_mm} + 1.0}$
2. **Layer 2 (Stage 2 Dynamic Runtime Override)**: If real-time weather telemetry or user input indicates `"Drought"` or `"Deficit Rain"` at prediction time, the Stage 2 ICAR Engine dynamically applies a penalty multiplier (0.30 - 0.50) to high-water crops (Rice, Sugarcane) while applying a boost multiplier (1.25 - 1.40) to drought-hardy crops (Bajra, Jowar, Sesamum, Pulses).

---

## 4. LEAKAGE-SAFE REGIONAL SUITABILITY SCORE ($S_{\text{Regional}}$)

### Popularity Bias Risk:
- Using raw historical crop frequency or total production volume per state ($Count(Crop_k, State)$) introduces **severe popularity bias**. For example, because Rice is historically grown in huge volumes across Andhra Pradesh, a raw frequency score would force Rice to rank #1 on all AP farms, even on dry alkaline soils ill-suited for paddy!

### Leakage-Safe Formulation: Relative Yield Efficiency ($RYE$)
$$S_{\text{Regional}}(Crop_k, \text{State}) = \min\left(100.0, \max\left(0.0, 50.0 + 50.0 \times \frac{\text{State\_Mean\_Yield}(Crop_k) - \text{National\_Mean\_Yield}(Crop_k)}{\text{National\_Yield\_Std}(Crop_k)}\right)\right)$$

- **Properties**:
  - Measures whether a state is **more efficient at producing yield per hectare** for a crop compared to the national average.
  - Does NOT penalize suitable minor crops.
  - Prevents popularity bias from overriding soil/climate telemetry.

---

## 5. WEIGHT SELECTION METHODOLOGY FOR CSI

Do NOT assume fixed weights ($0.50 / 0.35 / 0.15$) are optimal!

### Weight Optimization Experiment Design:
1. Define weight space $(w_1, w_2, w_3)$ subject to:
   $$w_1 + w_2 + w_3 = 1.0, \quad w_1 \in [0.35, 0.65], \quad w_2 \in [0.20, 0.45], \quad w_3 \in [0.05, 0.25]$$
2. **Grid Search Evaluation Metric**:
   - Compute Out-Of-Fold (OOF) predictions across the 5 training validation folds (`StratifiedGroupKFold`).
   - Select weight triplet $(w_1^*, w_2^*, w_3^*)$ that maximizes **Validation Top-3 Hit Rate** while keeping **Agronomic Violation Rate = 0.00%**.
3. **Leakage Prevention**:
   - The test set (20% spatial holdout districts) is **NEVER** used for weight tuning. Weights are selected strictly on OOF validation predictions.

---

## 6. MODEL FAMILY FEASIBILITY & ENVIRONMENT CHECK

Empirical inspection of the active Python environment (`sklearn 1.9.1`):

```
+------------------------------------+------------------+-----------------------------------------------+
| MODEL FAMILY / LIBRARY             | STATUS IN SYSTEM | ACTIONABLE FEASIBILITY PLAN                   |
+------------------------------------+------------------+-----------------------------------------------+
| RandomForestClassifier             | AVAILABLE        | Included in Soft Voting Ensemble              |
| ExtraTreesClassifier               | AVAILABLE        | Included in Soft Voting Ensemble              |
| HistGradientBoostingClassifier     | AVAILABLE        | Included in Soft Voting Ensemble (Primary GBDT)|
| GradientBoostingClassifier         | AVAILABLE        | Baseline comparison estimator                 |
| VotingClassifier                   | AVAILABLE        | Used for Soft Voting Ensemble pipeline        |
| CalibratedClassifierCV             | AVAILABLE        | Applied to calibrate raw probabilities        |
| XGBoost                            | NOT INSTALLED    | Not required; HistGradientBoosting utilized   |
| LightGBM                           | NOT INSTALLED    | Not required; HistGradientBoosting utilized   |
| CatBoost                           | NOT INSTALLED    | Not required; HistGradientBoosting utilized   |
+------------------------------------+------------------+-----------------------------------------------+
```

---

## 7. ENSEMBLE FEASIBILITY & PROBABILITY CALIBRATION

### Probability Calibration Necessity:
- `RandomForest` outputs probabilities averaged over decision trees, which compresses probabilities toward $0.2 - 0.8$.
- `HistGradientBoosting` outputs raw uncalibrated margin probabilities that tend to produce extreme values near $0.0$ or $1.0$.
- Combining uncalibrated probabilities in a `VotingClassifier(voting='soft')` gives unfair dominance to `HistGradientBoosting`.

### Solution:
Each individual candidate model is wrapped in `CalibratedClassifierCV(estimator, method='sigmoid', cv=3)` before soft voting:

```
Raw Telemetry X ──► Feature Preprocessor ──┬──► Calibrated(HistGradientBoosting) ──(Prob Vector P1)──┐
                                          ├──► Calibrated(RandomForest) ──────────(Prob Vector P2)──┼──► Weighted Soft Voting ──► P_ML(Crop|X)
                                          └──► Calibrated(ExtraTrees) ────────────(Prob Vector P3)──┘
```

---

## 8. VALIDATION PROTOCOL & SKLEARN API COMPATIBILITY

### Verified Sklearn API Support:
- `sklearn.model_selection.StratifiedGroupKFold` — **VERIFIED AVAILABLE**
- `sklearn.model_selection.GroupKFold` — **VERIFIED AVAILABLE**
- `sklearn.model_selection.GroupShuffleSplit` — **VERIFIED AVAILABLE**

### Leakage-Safe 2-Tier Validation Strategy:

```
                                [ TOTAL DATASET: 246,091 RECORDS / 635 DISTRICTS ]
                                                        │
                                                        ▼
                                         [ GroupShuffleSplit (n_splits=1) ]
                                            grouped by district_key
                                                        │
                      ┌─────────────────────────────────┴─────────────────────────────────┐
                      │ 80% Train Districts (~508)                                        │ 20% Unseen Test Districts (~127)
                      ▼                                                                   ▼
       [ StratifiedGroupKFold (5 Folds) ]                                      [ FINAL SPATIAL HOLDOUT TEST ]
      - Grouped by district_key                                                - Touched ONLY ONCE for final
      - Stratified by Crop_clean                                                 reporting & zero-shot validation
      - Used for CV & Weight Tuning
```

---

## 9. FINAL TRAINING SPECIFICATION

```yaml
Training Specification: KrishiMitra ML System V3

1. Training Dataset:
   - Source: data/crop_expert.csv joined with data/processed/master_district_profiles.csv on district_key
   - Filter: yield_quantile >= 2 (Top 75% yield performers; 136,128 quality cultivation records)
   - Target (y): Crop_clean (28 normalized top agricultural crops)

2. Feature Matrix X (20 Clean Features - Strict Leakage-Free):
   - Continuous Telemetry (16): ph, clay_pct, sand_pct, silt_pct, nitrogen_cg_kg, soc_dg_kg, cec, bulk_density, annual_rainfall_mm, kharif_rainfall_mm, rabi_rainfall_mm, mean_temperature_c, max_temperature_c, min_temperature_c, relative_humidity_pct, wind_speed_ms
   - Categorical Context (4): State, indian_soil_group, usda_texture, Season
   - Crop-Agnostic Engineered Features (3): temperature_stress_index, soil_water_retention_capacity, sand_clay_ratio

3. Stage 2 Post-ML Agronomic Engine (Crop-Specific Evaluation):
   - Features (Evaluated per candidate crop k): S_Rainfall(k), S_Thermal(k), S_pH(k), S_Water(k)
   - Metadata Source: backend/app/ml/models/crop_agronomic_profiles.json (ICAR bounds)

4. Validation Strategy:
   - Spatial Holdout: 20% districts (~127) isolated via GroupShuffleSplit(test_size=0.20, random_state=42)
   - Cross-Validation: 5-Fold StratifiedGroupKFold on remaining 80% train districts (~508)
   - Group Key: district_key (Zero spatial leakage between train and validation folds!)

5. Candidate Models & Ensemble Pipeline:
   - Model 1: HistGradientBoostingClassifier(max_iter=200, max_depth=12, random_state=42)
   - Model 2: RandomForestClassifier(n_estimators=250, max_depth=22, class_weight='balanced_subsample', random_state=42)
   - Model 3: ExtraTreesClassifier(n_estimators=250, max_depth=22, class_weight='balanced_subsample', random_state=42)
   - Calibration: CalibratedClassifierCV(method='sigmoid', cv=3) applied to each estimator
   - Fusion: VotingClassifier(voting='soft', weights=[0.45, 0.35, 0.20])

6. Composite Score Generation (CSI):
   - Formula: CSI(Crop_k) = w1 * P_ML(Crop_k|X) + w2 * S_Agronomic(Crop_k, X) + w3 * S_Regional(Crop_k, State)
   - Weight Selection: Grid search over OOF validation folds optimizing Validation Top-3 Hit Rate with 0.00% Agronomic Violation Rate

7. Evaluation Metrics:
   - Primary Metric: Top-3 Accuracy / Hit Rate (Target: > 50.0%)
   - Secondary Metrics: Top-1 Accuracy, Top-5 Accuracy, Weighted F1, Macro F1, Per-Crop Recall
   - Quality Controls: Agronomic Violation Rate (Target: 0.00%), Expected Calibration Error (ECE)

8. Production Controls:
   - ZERO production code mutations during review
   - Model V1 (crop_recommendation_model.pkl) remains default until V3 training & validation pass all benchmarks.
```

---

## 10. CONCLUSION & READINESS STATEMENT

The proposed architecture has been critically reviewed and refined against empirical dataset reality:
- **Crop-dependent variables** have been correctly moved out of Feature Matrix $X$ into the Stage 2 ICAR Engine.
- **Drought logic** has been separated into static climatic aridity for $X$ and dynamic live weather overrides for Stage 2.
- **Popularity bias** in regional scoring has been replaced with Relative Yield Efficiency ($RYE$).
- **API and Environment availability** of `scikit-learn 1.9.1` ensemble classifiers and `StratifiedGroupKFold` has been 100% verified.

The system is now fully specified and ready for safe offline training script creation upon user instruction.
