# KrishiMitra AI - Comprehensive ML Data & System Audit Report

**Audit Date**: September 2026  
**Workspace Root**: `C:\Users\aouti\Desktop\PS-3\FarmerHelp`  
**Purpose**: Complete audit of datasets, data quality, target quality, data leakage, join compatibility, feature availability, current model performance, and recommended ML training dataset design.

---

## 1. DATASET INVENTORY

| File Name | Relative Path | Rows | Columns | Size | Primary Agricultural Contents | Suitable for ML? |
| :--- | :--- | :---: | :---: | :---: | :--- | :---: |
| **`crop_expert.csv`** | `data/crop_expert.csv` | 246,091 | 19 | 31.71 MB | Historical APY crop area, production, and yield per district-year (1997–2020) | **YES** (Target & Yield Grounding) |
| **`master_geography.csv`** | `data/master_geography.csv` | 643 | 4 | 27.6 KB | District administrative names, state mapping, and lat/long coordinates | **YES** (Spatial Join Key) |
| **`soil_expert.csv`** | `data/soil_expert.csv` | 641 | 11 | 41.5 KB | ISRIC SoilGrids 250m physicochemical soil telemetry (pH, CEC, Organic Carbon, Texture) | **YES** (Soil Features) |
| **`weather_expert.csv`** | `data/weather_expert.csv` | 145,236 | 13 | 11.65 MB | IMD & NASA POWER monthly precipitation, temperature (T2M), RH, and wind speed | **YES** (Climate Features) |
| **`master_district_profiles.csv`** | `data/processed/master_district_profiles.csv` | 635 | 33 | 222.2 KB | Unified 635 district telemetry table combining soil properties & climate normals | **YES** (Master Feature Matrix) |
| **`clean_crops.parquet`** | `data/processed/clean_crops.parquet` | 246,091 | 18 | 3.41 MB | Cleaned & normalized crop cultivation records (Parquet format) | **YES** (ML Dataset Base) |

---

## 2. DATA QUALITY REPORT

### A. Duplicate Analysis
- **Exact Duplicate Rows in `crop_expert.csv`**: `0` rows (0.00%).
- **District Geography Duplicates**: `master_geography.csv` contains 643 unique district keys representing all agricultural districts in India.
- **Repeated District-Year Observations**: In `crop_expert.csv`, multiple rows exist for a single district and year because a district cultivates 5 to 25 different crops across Kharif, Rabi, and Summer seasons. This represents valid multi-crop agricultural diversity.

### B. Missing Values & Imputation
- **`crop_expert.csv`**:
  - `Production` & `Yield_tonnes_per_ha`: 3,730 rows (1.52% missing) where production was unrecorded.
  - All state/district/crop names: **0% missing**.
- **`soil_expert.csv`**:
  - Raw SoilGrids 0-5cm depth columns contain ~3.2% missing values for specific remote hill districts.
  - Imputed in `clean_soil.csv` using State-level median imputation followed by overall dataset median.
- **`weather_expert.csv`**:
  - Missing IMD precipitation values (~4.1%) imputed using NASA POWER satellite estimated rainfall and state-level monthly normals.

---

## 3. TARGET QUALITY REPORT

### A. Target Variable Selection
- **Primary Target Column**: `Crop` (normalized into `Crop_clean`).
- **Total Raw Unique Crop Labels**: `123` crops.
- **Normalized Top 28 Crops** (representing 96.7% of all valid agricultural cultivation records):
  `Rice`, `Maize`, `Moong (Green Gram)`, `Urad`, `Groundnut`, `Sesamum`, `Wheat`, `Sugarcane`, `Mustard / Rapeseed`, `Arhar/Tur (Pigeon Pea)`, `Gram (Chickpea)`, `Jowar (Sorghum)`, `Onion`, `Potato`, `Dry chillies`, `Bajra (Pearl Millet)`, `Sunflower`, `Small millets`, `Peas & beans (Pulses)`, `Cotton`, `Linseed`, `Ragi (Finger Millet)`, `Turmeric`, `Sweet potato`, `Masoor`, `Barley`, `Horse-gram`, `Other Kharif pulses`.

### B. Class Distribution & Imbalance
- **Top Class**: `Rice` (10,991 records, 8.07% of training set).
- **Lowest Class**: `Other Kharif pulses` (2,581 records, 1.90% of training set).
- **Imbalance Ratio**: `4.26:1` (Max to Min class ratio).
- **Handling Strategy**: `class_weight="balanced_subsample"` in Random Forest.

### C. Target Ambiguity Analysis
- **Theoretical Bayes Optimal Accuracy Upper Bound**: **21.60%** for single-label Top-1 classification.
- **Reason**: 88.38% of all district feature vectors grow 2 or more valid crops under identical soil/climate telemetry. On average, each district feature vector supports **7.43 different crops**.

---

## 4. DATA LEAKAGE REPORT

The following strict rules are enforced to eliminate data leakage:

| Feature Candidate | Leakage Risk Level | Status | Reason & Action Taken |
| :--- | :---: | :---: | :--- |
| **`Yield_tonnes_per_ha`** | **CRITICAL LEAKAGE** | **EXCLUDED** | Post-harvest outcome measure. Used ONLY for filtering high-performance records (`yield_quantile >= 2`). |
| **`Production`** | **CRITICAL LEAKAGE** | **EXCLUDED** | Post-harvest outcome. Excluded from feature set ($X$). |
| **`Area`** | **CRITICAL LEAKAGE** | **EXCLUDED** | Post-sowing land area allocation. Excluded from feature set ($X$). |
| **`District_Name` / `district_key`** | **HIGH OVERFITTING** | **EXCLUDED** | One-hot encoding 635 district IDs forces tree models to memorize district strings rather than generalizable soil/climate telemetry. Excluded from $X$. |
| **`Crop_Year`** | **TEMPORAL LEAKAGE** | **EXCLUDED** | Excluded from feature set ($X$). |

---

## 5. DATASET JOIN / COMPATIBILITY REPORT

| Left Dataset | Right Dataset | Join Key | Left Rows | Joined Rows | Match Rate | Unmatched Strategy |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| `crop_expert.csv` | `master_district_profiles.csv` | `district_key` | 246,091 | 239,025 | **97.13%** | Unmatched 7,066 rows (2.87%) belong to outdated administrative boundary names; safely dropped. |
| `clean_soil.csv` | `master_geography.csv` | `district_key` | 635 | 635 | **100.00%** | Exact 1-to-1 administrative match across all 635 districts. |
| `clean_weather.csv` | `master_geography.csv` | `district_key` | 635 | 635 | **100.00%** | Exact 1-to-1 administrative match across all 635 districts. |

---

## 6. FEATURE AVAILABILITY MATRIX

| Feature Name | Source Dataset | Raw Available? | Missing % | Useful for ML Model? | Production App Availability | Notes / Encoding |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **State** | `master_geography.csv` | Yes | 0.00% | Partial | Yes | Used for spatial stratification and default lookup |
| **District** | `master_geography.csv` | Yes | 0.00% | No | Yes | Join key (`district_key`). Excluded from $X$ to prevent leakage |
| **Agro-climatic region** | Derived from District | Yes | 0.00% | Yes | Yes | Regional agro-ecological zone grouping |
| **Soil Group** | `soil_expert.csv` | Yes | 0.00% | **YES** | Yes | `indian_soil_group` (One-hot encoded in Model B/C) |
| **Soil Texture** | `soil_expert.csv` | Yes | 0.00% | **YES** | Yes | `usda_texture` (Clay Loam, Loam, Clay, Sandy Loam) |
| **pH** | `soil_expert.csv` | Yes | 0.00% | **YES** | Yes | Continuous numeric topsoil pH (4.2 – 8.8) |
| **Nitrogen** | `soil_expert.csv` | Yes | 0.00% | **YES** | Yes | Continuous numeric Nitrogen (cg/kg) |
| **Phosphorus (P)** | Not in dataset | **No** | **100.00%** | N/A | No | Missing from 250m SoilGrids surface telemetry |
| **Potassium (K)** | Not in dataset | **No** | **100.00%** | N/A | No | Missing from 250m SoilGrids surface telemetry |
| **Organic Carbon** | `soil_expert.csv` | Yes | 0.00% | **YES** | Yes | Continuous numeric Soil Organic Carbon (dg/kg) |
| **CEC** | `soil_expert.csv` | Yes | 0.00% | **YES** | Yes | Cation Exchange Capacity (mmol(c)/kg) |
| **Clay %** | `soil_expert.csv` | Yes | 0.00% | **YES** | Yes | Topsoil clay percentage (0–100%) |
| **Sand %** | `soil_expert.csv` | Yes | 0.00% | **YES** | Yes | Topsoil sand percentage (0–100%) |
| **Silt %** | `soil_expert.csv` | Yes | 0.00% | **YES** | Yes | Topsoil silt percentage (0–100%) |
| **Bulk Density** | `soil_expert.csv` | Yes | 0.00% | **YES** | Yes | Bulk density (kg/dm³) |
| **Annual Rainfall** | `weather_expert.csv` | Yes | 0.00% | **YES** | Yes | Continuous IMD annual rainfall normal (mm) |
| **Kharif Rainfall** | `weather_expert.csv` | Yes | 0.00% | **YES** | Yes | Continuous IMD monsoon rainfall normal (mm) |
| **Rabi Rainfall** | `weather_expert.csv` | Yes | 0.00% | **YES** | Yes | Continuous IMD winter rainfall normal (mm) |
| **Temperature (Mean/Max/Min)** | `weather_expert.csv` | Yes | 0.00% | **YES** | Yes | Continuous monthly thermal normals (°C) |
| **Relative Humidity** | `weather_expert.csv` | Yes | 0.00% | **YES** | Yes | Relative Humidity % |
| **Wind Speed** | `weather_expert.csv` | Yes | 0.00% | **YES** | Yes | Wind Speed at 2m (m/s) |
| **Season** | `crop_expert.csv` | Yes | 0.00% | **YES** | Yes | Sowing window (`Kharif`, `Rabi`, `Summer`, `Whole Year`) |
| **Irrigation Type** | App Input / Inferred | Partial | N/A | Yes | Yes | `irrigation_type` (`Drip`, `Canal`, `Rainfed`) |
| **Water Availability** | App Input / Inferred | Partial | N/A | Yes | Yes | `water_availability` (`High`, `Moderate`, `Limited`) |
| **Water Source** | App Input / Inferred | Partial | N/A | Yes | Yes | `water_source` (`Borewell`, `Canal`, `Rainwater`) |

---

## 7. CURRENT MODEL AUDIT

| Model Property | Production Model V1 | Staging Model V2 Candidate |
| :--- | :--- | :--- |
| **Artifact Path** | `ml/models/crop_recommendation_model.pkl` | `ml/models/crop_recommendation_model_v2_candidate.pkl` |
| **Algorithm** | `RandomForestClassifier` (150 trees, max_depth=22) | `Pipeline` (OneHotEncoder + `RandomForestClassifier`) |
| **Training Dataset** | 136,128 records (28 crops, `yield_quantile >= 2`) | 136,128 records (28 crops, `yield_quantile >= 2`) |
| **Input Features** | 16 Continuous Numeric features | 18 Features (16 Numeric + `Season` + `indian_soil_group`) |
| **Target Classes** | 28 Crop Classes | 28 Crop Classes |
| **Validation Strategy** | 80/20 Stratified Train/Test Split | 80/20 Stratified Split + 5-Fold Stratified Cross-Validation |
| **Top-1 Accuracy** | **6.55%** | **15.92%** (+143% Gain) |
| **Top-3 Accuracy** | **19.61%** | **43.07%** (+119% Gain) |
| **Top-5 Accuracy** | **31.85%** | **62.30%** (+95.6% Gain) |
| **Weighted F1 Score** | **0.0457** | **0.1494** (+226% Gain) |
| **Known Limitations** | Ignores season & soil type categoricals in tree splits | Evaluated on single-label metrics for multi-crop domain |

---

## 8. RECOMMENDED FINAL AGRICULTURAL ML TRAINING DATASET DESIGN

### Recommended Dataset Schema & Pipeline Design:
To serve as the **PRIMARY INTELLIGENCE** for KrishiMitra AI:

1. **Master Feature Matrix Composition**:
   - Join 136,128 quality-filtered historical cultivation records (`crop_expert.csv` with `yield_quantile >= 2`) with district soil telemetry (`master_district_profiles.csv`) on `district_key`.
   - **Features ($X$)**:
     - 16 Continuous SoilGrids & IMD/NASA Telemetry Features: `ph`, `clay_pct`, `sand_pct`, `silt_pct`, `nitrogen_cg_kg`, `soc_dg_kg`, `cec`, `bulk_density`, `annual_rainfall_mm`, `kharif_rainfall_mm`, `rabi_rainfall_mm`, `mean_temperature_c`, `max_temperature_c`, `min_temperature_c`, `relative_humidity_pct`, `wind_speed_ms`.
     - 2 Essential Categorical Features: `Season` (Kharif, Rabi, Summer, Whole Year) and `indian_soil_group` (Black Soil, Alluvial Soil, Red Soil, Laterite Soil, Arid Soil).
   - **Target ($y$)**: Normalized `Crop` (28 Top Agricultural Crops).

2. **Preprocessing & Artifact Packaging**:
   - Use `ColumnTransformer` with `OneHotEncoder(handle_unknown='ignore', sparse_output=False)` for categorical features and `passthrough` for continuous numeric features.
   - Package the entire `Pipeline([('preprocessor', transformer), ('classifier', model)])` into a single standalone `.pkl` artifact.

3. **Inference & Recommendation Integration**:
   - At inference time in `backend/app/ml/predict.py`, query `pipeline.predict_proba(X_df)` across all 28 classes.
   - Fuse the ML multi-crop probability vector with ICAR agronomic rule bounds (pH optimal range, temperature limits, drought/heavy rain adjustments) to output a deterministic, explainable Top-1 Primary Recommendation and Top-3 Alternative Crops.
   - This ensures the ML model is the **Primary Engine** driving crop selection, while Qwen/Bionic LLM serves as an optional conversational natural-language synthesizer.
