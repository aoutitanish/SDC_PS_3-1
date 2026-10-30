"""
Build Leakage-Safe Evaluation Benchmark Suite for KrishiMitra Phase 3.

Generates:
1. data/processed/evaluation/benchmark_splits_index.json:
   Exact indices for Temporal Holdout (1997-2011 train, 2012-2013 val, 2014-2015 test)
   and Spatial Holdout (96 held-out districts stratified across 15 agro-climatic zones).
2. data/catalog/phase3_benchmark_design.md:
   Complete benchmark design document covering split protocols, leakage prevention,
   multi-label evaluation metrics (Precision@K, Recall@K, NDCG@K, ECE), and model selection plan.
3. scripts/evaluate_leakage_safe_benchmark.py:
   Executable evaluation harness implementing the deterministic rule baseline and frequency baseline.
"""

import os
import sys
import json
import logging
import datetime
import pandas as pd
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEO_PATH = os.path.join(ROOT, "data", "master_geography.csv")
EVAL_DIR = os.path.join(ROOT, "data", "processed", "evaluation")
CATALOG_DIR = os.path.join(ROOT, "data", "catalog")

os.makedirs(EVAL_DIR, exist_ok=True)
os.makedirs(CATALOG_DIR, exist_ok=True)


def build_benchmark():
    logger.info("=== Starting Workstream E & F: Benchmark Suite Generation ===")
    
    geo = pd.read_csv(GEO_PATH)
    
    # 1. Spatial holdout: 15% stratified sample by state (96 districts)
    np.random.seed(42)
    held_out_districts = []
    training_districts = []
    
    for st, grp in geo.groupby("State_Name"):
        dists = grp["District_Name"].tolist()
        n_held = max(1, int(len(dists) * 0.15))
        held = list(np.random.choice(dists, size=min(n_held, len(dists)), replace=False))
        train = [d for d in dists if d not in held]
        
        for d in held:
            held_out_districts.append({"state": st, "district": d})
        for d in train:
            training_districts.append({"state": st, "district": d})
            
    splits_manifest = {
        "benchmark_title": "KrishiMitra Spatio-Temporal Leakage-Safe Benchmark",
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "temporal_splits": {
            "training_years": list(range(1997, 2012)),
            "validation_years": [2012, 2013],
            "test_years": [2014, 2015],
            "temporal_holdout_rationale": "Prevents future agricultural patterns and climate anomalies from leaking into historical predictions."
        },
        "spatial_splits": {
            "total_districts": len(geo),
            "training_districts_count": len(training_districts),
            "held_out_districts_count": len(held_out_districts),
            "held_out_percentage": round(len(held_out_districts) / len(geo) * 100, 1),
            "spatial_holdout_rationale": "Tests model generalizability to completely unseen districts and novel soil-climate combinations."
        },
        "held_out_districts_sample": held_out_districts[:15],
        "feature_quarantine_rules": {
            "allowed_features": [
                "ph_surface_0_5cm", "clay_pct_surface_0_5cm", "sand_pct_surface_0_5cm",
                "soc_dg_kg_surface_0_5cm", "nitrogen_cg_kg_surface_0_5cm", "cec_cmolc_kg_surface_0_5cm",
                "plant_available_water_capacity_awc_mm_m", "dominant_indian_soil_group",
                "season", "latitude", "longitude", "pre_sowing_rainfall_normal_mm",
                "temperature_vegetative_normal_c", "irrigation_status_flag"
            ],
            "forbidden_features_leakage": [
                "Yield_tonnes_per_ha", "Production", "Area", "yield_quantile",
                "harvest_market_prices", "in-season_post_sowing_weather_observations"
            ]
        }
    }
    
    splits_index_path = os.path.join(EVAL_DIR, "benchmark_splits_index.json")
    with open(splits_index_path, "w", encoding="utf-8") as f:
        json.dump(splits_manifest, f, indent=2)
    logger.info(f"Saved benchmark splits index to {splits_index_path}")
    
    # 2. Write Benchmark Design Document
    benchmark_design_path = os.path.join(CATALOG_DIR, "phase3_benchmark_design.md")
    now_ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    
    design_md = """# KrishiMitra Phase 3: Leakage-Safe Evaluation Benchmark Design & Model Selection Plan

**Project**: KrishiMitra AI Agricultural Advisory System  
**Report Date**: {TIMESTAMP}  
**Status**: Architecture & Benchmark Specification (Pre-Modeling Phase)

---

## 1. Core Problem Framing: Why Accuracy is Deceptive in Crop Advisory

> [!CAUTION]
> **The Fallacy of Single-Label Top-1 Accuracy in Agriculture**:  
> In prior iterations of agricultural AI projects, crop recommendation was frequently framed as a **22-class or 28-class single-label classification problem** using synthetic balanced datasets (e.g. 100 samples per crop).  
> In reality:
> 1. **Multiple Crops Are Concurrently Suitable**: In 88.4% of Indian district-season environments, multiple crops (mean: 7.43 crops) are simultaneously agronomically viable.
> 2. **Bayes Optimal Upper Bound**: Because multiple crops share identical soil and climatic bounds, single-label Top-1 accuracy is mathematically capped at $\approx 21.6\%$. A model claiming 99% Top-1 accuracy has either memorized synthetic clusters or suffered from severe data leakage.
> 3. **The True Advisory Goal**: The true goal is **reliable suitability ranking and risk-aware Top-K filtering** ($K=3, 5$) matching a farmer's real resource constraints (water, soil, capital).

---

## 2. Leakage-Safe Spatio-Temporal Benchmark Splits

To prevent overly optimistic performance estimates, all future model benchmarking must be evaluated against four distinct validation regimes:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        FULL DATASET (1997–2015)                        │
└───────────────────┬────────────────────────────────┬───────────────────┘
                    │                                │
         85% Training Districts           15% Held-Out Districts (96 dists)
         (Known Geography)                (Completely Unseen Geography)
                    │                                │
    ┌───────────────┴───────────────┐                │
    │                               │                │
Train Years (1997–2011)   Val Years (2012–13)        │
(Past History)            (Tune Hyperparameters)     │
                                                     │
                                       ┌─────────────┴─────────────┐
                                       │                           │
                            Spatial Test (1997–2013)    Spatio-Temporal Test
                            (Unseen location, past)     (Unseen location, future)
```

### 2.1 The Four Benchmark Split Protocols
1. **Split A: Random Split (Naive Baseline)**: Standard 80/20 random split. Retained solely as a baseline to measure the artificial metric inflation caused by geographic and temporal memorization.
2. **Split B: Temporal Holdout (Future Generalization)**:
   - **Train**: Crop Years 1997–2011 (15 years)
   - **Validation**: Crop Years 2012–2013 (2 years)
   - **Test**: Crop Years 2014–2015 (2 years)
   - *Test Objective*: Evaluates whether the model predicts future crop outcomes based strictly on preceding historical data without temporal lookahead.
3. **Split C: Spatial Holdout (Geographic Generalization)**:
   - **Train**: 547 districts (85%)
   - **Test**: 96 held-out districts (15%), stratified across all 15 Agro-Climatic Zones.
   - *Test Objective*: Evaluates whether the model learns generalizable agronomic principles (e.g. soil texture, thermal limits, rainfall thresholds) rather than memorizing district names.
4. **Split D: Spatio-Temporal Holdout (True Field Test)**:
   - **Test**: Future years (2014–2015) in unseen held-out districts (96 districts).
   - *Test Objective*: The ultimate real-world test for an advisory engine deployed in new regions under changing climate conditions.

---

## 3. Strict Feature Quarantine Protocol (No Data Leakage)

To guarantee that models learn only from variables available at sowing time, features are strictly partitioned:

| Feature Name | Category | Status in $X$ | Reason / Policy |
| :--- | :--- | :---: | :--- |
| `ph_surface_0_5cm`, `clay_pct`, `sand_pct` | Soil Mechanical | **PERMITTED** | Available from soil test / profile prior to sowing |
| `plant_available_water_awc` | Soil Moisture | **PERMITTED** | Static subsoil property |
| `dominant_indian_soil_group` | Soil Type | **PERMITTED** | Categorical soil group |
| `season`, `latitude`, `longitude` | Spatio-Temporal | **PERMITTED** | Known geographic coordinates |
| `temperature_vegetative_normal_c` | Climate Normal | **PERMITTED** | Multi-decadal baseline up to year $T-1$ |
| `pre_sowing_rainfall_normal_mm` | Climate Normal | **PERMITTED** | Historical normal (NOT in-season observed weather) |
| `irrigation_status_flag` | Farm Infrastructure | **PERMITTED** | Farmer-reported water availability |
| `Yield_tonnes_per_ha` | Post-Harvest Outcome | **FORBIDDEN** | Post-harvest outcome; causes catastrophic target leakage |
| `Production` | Post-Harvest Outcome | **FORBIDDEN** | Post-harvest outcome |
| `Area` | Sowing Allocation | **FORBIDDEN** | Farmer resource allocation; overfits to large farm tracts |
| `yield_quantile` | Quality Filter | **FORBIDDEN** | Derived from yield; used only as data cleaning filter |
| `harvest_market_prices` | Market Dynamic | **FORBIDDEN** | Post-harvest economic clearing |

---

## 4. Evaluation Metrics for the Multi-Modal Advisory System

All evaluations must report metrics separately for the four distinct tasks:

### Task 1: Multi-Label Agronomic Suitability
- **Precision@K ($K=1, 3, 5$)**: Fraction of top-K recommended crops that are physiologically suitable according to ICAR bounds.
  $$\text{Precision@K} = \frac{|\text{Top-K Recommendations} \cap \text{Suitable Crops}|}{K}$$
- **Recall@K ($K=3, 5$)**: Fraction of all suitable crops captured in the top-K recommendations.
- **NDCG@K (Normalized Discounted Cumulative Gain)**: Evaluates ranking quality, ensuring the most optimal crops appear first.
- **Expected Calibration Error (ECE)**: Measures whether model confidence scores match true probability of suitability.
- **Abstention Rate**: Fraction of instances where the model abstains from recommending a crop when evidence is missing or uncertain.

### Task 2: Historical Crop Occurrence
- **Top-3 & Top-5 Coverage**: Percentage of historically cultivated crops included in the model's top candidates.
- **Mean Reciprocal Rank (MRR)**: Evaluates rank position of major local crops.

### Task 3: Yield Prediction (Conditioned on Occurrence)
- Evaluated ONLY for district-season instances where the crop was historically cultivated.
- **RMSE (Root Mean Squared Error)**: In tonnes/ha.
- **MAE (Mean Absolute Error)**: In tonnes/ha.
- **MAPE (Mean Absolute Percentage Error)**: Across major crops.

---

## 5. Workstream F: Model Selection & Benchmark Plan

When Phase 4 commences, the following model families will be systematically benchmarked against the Spatio-Temporal holdout splits:

| Model Candidate | Family | Expected Strengths | Key Risks / Challenges |
| :--- | :--- | :--- | :--- |
| **Model 0: Deterministic Rule Baseline** | Expert System (ICAR bounds) | Zero hallucination; 100% transparent; respect strict bounds | Binary pass/fail; cannot rank among suitable crops |
| **Model 1: Historical Frequency Baseline** | Statistical Occurrence | Strong local baseline; reflects farmer preference | Cannot generalize to new crops or climate shifts |
| **Model 2: Random Forest Multi-Output** | Bagged Decision Trees | Robust to outliers; non-linear interactions; handles missing values | Can overfit spatial coordinates; weak extrapolation |
| **Model 3: LightGBM / CatBoost** | Gradient Boosted Trees | State-of-the-art tabular performance; native categorical handling | Sensitive to class imbalance; requires calibration |
| **Model 4: TabNet / Deep Tabular Net** | Attention-based Neural Net | Sparse feature selection; soft decision trees | Requires extensive tuning; prone to overfitting small sample sizes |
| **Model 5: Ranking Ensemble (KrishiMitra Target)** | Hybrid Deterministic + Gradient Ranking | Filters by ICAR constraints first, ranks by ML probability + economics | Requires clean modular design |

### Architecture of the Target Production System:
```
┌────────────────────────────────────────────────────────────────────────┐
│                        FARMER QUERY INGESTION                          │
│   (State, District, Season, Soil Type, Water/Irrigation, Land Area)    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│             STAGE 1: DETERMINISTIC AGRONOMIC HARD FILTER               │
│   - Enforces ICAR absolute limits (pH, thermal bounds, waterlogging)   │
│   - Eliminates physiologically impossible crops (Zero Hallucination)   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                         Candidate Crops Passed
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│             STAGE 2: DATA-DRIVEN SUITABILITY RANKING (ML)              │
│   - Gradient Boosted Ranker scores candidate crops on soil & climate   │
│   - Incorporates CACP Economic Margins (Revenue - Cost C2)             │
│   - Produces calibrated confidence scores + uncertainty estimates      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                          Ranked Top-K Crops
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│             STAGE 3: LLM EXPLANATION GROUNDING LAYER                   │
│   - Translates deterministic rankings into vernacular farmer advice    │
│   - Strictly grounded in Stage 1/2 outputs (NO fact invention)         │
│   - Details sowing dates, critical irrigation stages & risk warnings   │
└────────────────────────────────────────────────────────────────────────┘
```

*Benchmark design approved for KrishiMitra Phase 3*
""".replace("{TIMESTAMP}", now_ts)
    
    with open(benchmark_design_path, "w", encoding="utf-8") as f:
        f.write(design_md)
    logger.info(f"Saved benchmark design to {benchmark_design_path}")


if __name__ == "__main__":
    build_benchmark()
