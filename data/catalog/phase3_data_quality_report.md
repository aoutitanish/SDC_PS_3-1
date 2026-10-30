# KrishiMitra Phase 3: Comprehensive Agricultural Intelligence Data Foundation Report

**Project**: KrishiMitra AI Agricultural Advisory System  
**Audit Date**: 2026-10-15 07:23:13 UTC  
**Status**: Completed, Audited & Acceptance Tested  
**Mandatory Invariants**: Zero model retraining, zero modification to production recommendation logic or weights, zero synthetic data contamination, and zero label fabrication.

---

## 1. Executive Summary: The Phase 3 Agricultural Intelligence Foundation

Phase 3 established an evidence-backed data foundation for Indian agriculture, resolving core data quality, spatial alignment, and evaluation design challenges:

| Workstream | Dimension | Baseline (Start of Phase 3) | Phase 3 Expansion (Completed) | Impact & Scientific Rigor |
| :--- | :--- | :--- | :--- | :--- |
| **A: Weather** | Geographic Coverage | 20 districts (10,320 monthly rows) | **55 districts** (28,380 monthly rows, 1981–2023) + **10 anchor districts daily** (14,610 daily rows) | Covers all 15 Agro-Climatic Zones of India. Introduces daily heat stress days, dry spells, and GDD metrics. |
| **B: Agronomy** | Suitability Knowledge | 28 heuristic quantile ranges (derived from historical occurrence) | **Authoritative ICAR-SAU-FAO compendium** (28 crop master, 16 crop regimes, 10 institutes) | Disentangles historical cultivation from physiological suitability. Records explicit uncertainty. |
| **C: Soil** | Depth & Nutrients | 0–5 cm surface layer only; no Available P or K; 2 missing districts | **Root-zone depth stratification (0–30cm, 30–100cm)**; **ICAR P & K fertility integration**; missing districts flagged | 643 districts covered with AWC water capacity; Alappuzha & Jaisalmer flagged (no constant imputation). |
| **D: Targets** | Learning Objectives | Conflated occurrence with suitability | **4 strictly distinct target layers** across 54,012 condition-crop combinations | Separate evaluation for Occurrence, Suitability (3-valued), Yield, and Economics. No synthetic class balancing. |
| **E & F: Benchmark** | Model Evaluation | Theoretical Bayes limit unaddressed; single-label accuracy | **Spatio-Temporal Holdout Benchmark** (4 splits, 96 held-out districts, Precision@K, NDCG@K, ECE) | Leakage-safe feature quarantine (X contains only pre-sowing data). Established rule & frequency baselines. |

---

## 2. Workstream A: Expanded Weather Coverage & Agro-Climatology

### 2.1 Quantitative Summary
- **Expanded Monthly Weather**: `28,380` monthly observations across **`55` districts** (1981–2023, 43 continuous calendar years, 516 months each). 0.00% missingness.
- **Empirical Daily Weather**: `14,610` daily observations across **`10` anchor districts** (2020–2023, 1,461 daily records each).
- **Computed Agroclimatic Metrics**: `40` district-years quantifying heat stress days (Tmax >= 35°C), extreme heat (Tmax >= 40°C), cold stress (Tmin <= 10°C), monsoon rainfall share %, consecutive dry spell days, and growing degree days (GDD10).

### 2.2 Spatial Representativeness & Scientific Nuances
- **Macroclimate Fidelity**: Flat alluvial plains (Indo-Gangetic) and Deccan plateau districts have high spatial adequacy under 0.5° (~55 km) MERRA-2 reanalysis.
- **Topographic Smoothing Warning**: Montane districts (Mandi, Shimla, Dehradun) have steep lapse rates. 0.5° reanalysis represents **valley macroclimate** and must not be conflated with high-altitude microclimates.
- **Coastal/Deltaic Transitions**: Maritime humidity and cyclonic monsoon precipitation adequately captured with APMC inland centroid anchoring.

---

## 3. Workstream B: Authoritative Agronomic Knowledge Base

### 3.1 Normalized Crop Master & Requirements
- **Normalized Crop Master**: **`28` canonical crops** catalogued with botanical classification, family, Hindi/vernacular names, rooting depth classes, and water sensitivity indexes (`normalized_crop_master.csv`).
- **Evidence-Based Requirements**: **`16` detailed crop-season regimes** with physiological limits (`crop_suitability_requirements.csv`):
  - Soil pH: Absolute min, optimal min, optimal max, absolute max.
  - Thermal requirements: Germination min/opt, vegetative opt min/max, flowering critical max.
  - Seasonal water requirements: Minimum, optimal, and maximum water in mm.
  - Critical irrigation stages & duration (days).
  - Documented N-P-K nutrient recommendations (kg/ha).
  - Abiotic stress tolerance: Salinity threshold (dS/m), drought tolerance, and waterlogging tolerance.

### 3.2 Citations & Institutional Grounding
- **10 Institutional Research Compendia**: Detailed in `agronomic_evidence_catalog.csv` covering ICAR-IIRR (Rice), ICAR-IIWBR (Wheat/Barley), ICAR-IIMR (Maize/Millets), ICAR-IIPR (Pulses), ICAR-CICR (Cotton), ICAR-DRMR (Mustard), ICAR-DGR (Groundnut), ICAR-DOGR (Onion), PAU Ludhiana, and FAO Irrigation & Drainage Papers 24, 33, 56.
- **Explicit Uncertainty Report**: Documented in `unresolved_agronomic_evidence_report.md` analyzing cultivar-specific contradictions (short vs long duration pulses, Desi vs Kabuli chana, NWPZ vs Peninsular wheat heat tolerance).

---

## 4. Workstream C: Soil Depth & Geographic Feature Improvements

### 4.1 Root-Zone Depth Stratification
In `enhanced_district_soil_profiles.csv` (643 districts), surface observations (`0–5 cm`) are explicitly decoupled from root-zone dynamics:
- **Surface Layer (0–5 cm)**: Direct SoilGrids 250m observations (pH, clay, sand, silt, SOC, CEC, bulk density).
- **Subsoil & Root Zone (0–100 cm)**: Plant-Available Water Capacity (AWC, in mm/m), root depth limitation class, and subsoil drainage behavior from ICAR-NBSS&LUP.

### 4.2 Available Phosphorus (P2O5) & Potassium (K2O) Integration
- SoilGrids does not predict Available P and K. Integrated district-level macro-fertility ratings from ICAR-NBSS&LUP Soil Fertility Atlases & Soil Health Card national status:
  - **Available P2O5**: Categorized as Low, Medium, High with regional benchmark kg/ha.
  - **Available K2O**: Categorized as Low, Medium, High with regional benchmark kg/ha.
  - **Vertisols**: Characterized by High Potassium (>400 kg K2O/ha) and low-to-medium P.
  - **Laterites**: Characterized by severe P-fixation (<15 kg P2O5/ha).

### 4.3 Audit of Missing Soil Evidence Districts
- **Kerala / Alappuzha (Alleppey)**: Coastal backwaters lagoon; flagged as `INSUFFICIENT_EVIDENCE (Backwaters Lagoon)`.
- **Rajasthan / Jaisalmer**: Shifting sand dunes of the Thar desert; flagged as `INSUFFICIENT_EVIDENCE (Arid Sand Dunes)`.
- **Zero Arbitrary Imputation**: These districts remain explicitly flagged in `soil_missing_features_report.csv` rather than being assigned synthetic constants.

---

## 5. Workstream D: Defensible Learning Targets & Multi-Label Framing

In `multilabel_suitability_dataset.parquet` (**`54,012` rows** across 643 districts × 3 seasons × 28 crops), four learning targets are maintained with strict separation:

1. **Target 1: Historical Crop Occurrence (`is_historically_cultivated`)**:
   - Binary indicator (1 if recorded in historical DES APY, 0 if not).
   - *Rule*: Historical occurrence reflects past farmer adoption, NOT physiological suitability or optimality.
2. **Target 2: Agronomic Suitability (`agronomic_suitability_label`)**:
   - 3-valued classification: **`1` = Suitable (`22,714` rows)**; **`0` = Unsuitable (`8,054` rows)**; **`-1` = Unknown (`23,244` rows)**.
   - Negative labels are assigned ONLY when an explicit physiological constraint is violated (e.g. thermal limits, severe pH toxicity, waterlogging).
   - Missing evidence remains `Unknown` (`-1`) rather than being treated as unsuitable.
3. **Target 3: Observed Historical Yield (`observed_mean_yield_tonnes_ha`)**:
   - Continuous metric (tonnes/ha) conditional on occurrence. `NaN` for uncultivated crops.
4. **Target 4: Economic Outcomes (`projected_gross_revenue_inr_ha`, `projected_net_margin_inr_ha`)**:
   - Revenue and net margins calculated from CACP MSP and Cost of Cultivation (C2).

---

## 6. Workstream E & F: Leakage-Safe Evaluation Benchmark & Selection Plan

### 6.1 Spatio-Temporal Benchmark Splits (`benchmark_splits_index.json`)
- **Temporal Holdout**: Train on 1997–2011; Validate on 2012–2013; Test on 2014–2015.
- **Spatial Holdout**: 96 held-out districts (15%) stratified across all 15 agro-climatic zones.
- **Feature Quarantine**: X contains strictly pre-sowing variables (Soil properties, Climate normals up to T-1, Irrigation status, Geography). Post-sowing variables (`Yield`, `Production`, `Area`, `yield_quantile`, harvest market prices) are strictly forbidden.

### 6.2 Baseline Model Evaluation Results (`baseline_benchmark_results.json`)
- **Model 0 (ICAR Agronomic Rule Filter)**: Achieves **100% physiological validity** (zero hallucinated crops exceeding thermal/pH limits).
- **Model 1 (Historical Frequency Baseline)**:
  - **Precision@1**: `0.8990`
  - **Precision@3**: `0.7859`
  - **Precision@5**: `0.7698`
  - **Recall@3**: `0.1925`
  - **Recall@5**: `0.3300`

### 6.3 Target Model Selection Plan (Phase 4 Blueprint)
The future Phase 4 modeling experiments will benchmark Random Forest, LightGBM/CatBoost, Tabular Neural Networks (TabNet), and Ranking Ensembles (LambdaMART) against the hybrid architecture:
`Production Engine = Deterministic ICAR Constraint Filter -> Gradient Boosted Ranker (ML + Economics) -> Grounded LLM Explanation Layer`

---

## 7. Master Dataset Inventory Update (D01 to D24)

| ID | Dataset Name | Category | Scope / Records | Status |
| :--- | :--- | :--- | :---: | :--- |
| **D01–D12** | Core Phase 1 & 2 Datasets | APY, Soil, Geography, DES PDF, Sample Weather | Catalogued | Unmodified & preserved |
| **D13** | `des_apy_national_2015_2026_raw.json` | Raw DES Time Series | 682 rows | Standardized |
| **D14** | `des_national_production_2015_2026.csv` | Processed DES Production | 682 rows (2015–2026) | Standardized |
| **D15** | `district_crosswalk.csv` | Historical Crosswalk | 17 pairs (7,066 rows) | 100% Resolved |
| **D16** | `nasa_power_coverage_assessment.csv` | Weather Spatial Audit | 20 districts | Audited |
| **D17** | `nasa_power_monthly_district_weather_20.csv` | Aligned Monthly Weather | 10,320 rows | Aligned (1981–2023) |
| **D18** | `expanded_district_monthly_weather.csv` | Expanded Weather Normals | **28,380 rows (55 dists)** | Aligned (1981–2023) |
| **D19** | `representative_district_daily_weather.csv` | Daily Historical Weather | **14,610 rows (10 dists)** | 2020–2023 daily |
| **D20** | `daily_agroclimatic_metrics.csv` | Daily Stress Metrics | **40 district-years** | Heat/dry spell indices |
| **D21** | `normalized_crop_master.csv` | Crop Master Taxonomy | **28 canonical crops** | Normalized taxonomy |
| **D22** | `crop_suitability_requirements.csv` | Agronomic Bounds Compendium | **16 crop-season regimes** | ICAR/SAU evidence |
| **D23** | `enhanced_district_soil_profiles.csv` | Stratified Soil Profiles | **643 districts** | 0-5cm + root zone P/K |
| **D24** | `multilabel_suitability_dataset.parquet` | Multi-Label Benchmark Target | **54,012 condition rows** | 4 distinct target layers |

---

## 8. Verification Invariants

```
[Phase 3 Invariant Checks]
1. Production recommendation model weights: UNTOUCHED
2. Backend API recommendation endpoints: UNTOUCHED
3. Original raw datasets: UNTOUCHED
4. Synthetic market price quarantine: ENFORCED
5. Zero arbitrary constant imputation: ENFORCED
6. Leakage-safe feature quarantine: ENFORCED
```

*Report generated by `scripts/generate_phase3_reports.py` — KrishiMitra Phase 3*
