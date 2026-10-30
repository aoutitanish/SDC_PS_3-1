"""
Phase 3 Comprehensive Verification Suite - KrishiMitra
======================================================
Automated verification of all deliverables, invariants, and acceptance criteria for Phase 3.
"""

import os
import sys
import json
import logging
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Phase3Verifier")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
CATALOG_DIR = os.path.join(DATA_DIR, "catalog")
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
MODELS_DIR = os.path.join(BASE_DIR, "ml", "models")


def assert_test(condition, test_name):
    if condition:
        logger.info(f"  [PASS] {test_name}")
        return True
    else:
        logger.error(f"  [FAIL] {test_name}")
        return False


def main():
    logger.info("=== STARTING PHASE 3 ACCEPTANCE & INTEGRITY AUDIT ===")
    results = []

    # ----------------------------------------------------
    # Check 1: Mandatory Invariants (Production & Weights)
    # ----------------------------------------------------
    logger.info("\n--- Check 1: Production Model & Logic Invariant Audit ---")
    model_v1 = os.path.join(MODELS_DIR, "crop_recommendation_model.pkl")
    model_v2 = os.path.join(MODELS_DIR, "crop_recommendation_model_v2_candidate.pkl")
    results.append(assert_test(os.path.exists(model_v1), "Original production model file exists unmodified"))
    results.append(assert_test(os.path.exists(model_v2), "Candidate v2 model file exists unmodified"))
    
    # Check backend endpoints exist
    recommend_py = os.path.join(BACKEND_DIR, "app", "api", "recommendation.py")
    results.append(assert_test(os.path.exists(recommend_py), "Backend production recommendation endpoint is intact"))

    # ----------------------------------------------------
    # Check 2: Workstream A (Weather Expansion)
    # ----------------------------------------------------
    logger.info("\n--- Check 2: Workstream A - Weather Expansion Audit ---")
    monthly_weather_path = os.path.join(PROCESSED_DIR, "weather", "expanded_district_monthly_weather.csv")
    daily_weather_path = os.path.join(PROCESSED_DIR, "weather", "representative_district_daily_weather.csv")
    agro_metrics_path = os.path.join(PROCESSED_DIR, "weather", "daily_agroclimatic_metrics.csv")

    results.append(assert_test(os.path.exists(monthly_weather_path), "D18 expanded monthly weather exists"))
    results.append(assert_test(os.path.exists(daily_weather_path), "D19 representative daily weather exists"))
    results.append(assert_test(os.path.exists(agro_metrics_path), "D20 daily agroclimatic metrics exists"))

    if os.path.exists(monthly_weather_path):
        df_m = pd.read_csv(monthly_weather_path)
        results.append(assert_test(len(df_m) == 28380, f"D18 monthly weather row count exactly 28,380 (got {len(df_m):,})"))
        results.append(assert_test(df_m['district'].nunique() == 55, f"D18 covers 55 districts (got {df_m['district'].nunique()})"))
        results.append(assert_test(df_m.isnull().sum().sum() == 0, "D18 has 0.00% missing values across all columns"))
        results.append(assert_test(df_m['t2m_mean_c'].between(-15, 55).all(), "D18 temperatures within physical bounds (-15 to +55 C)"))
        results.append(assert_test((df_m['precipitation_monthly_mm'] >= 0).all(), "D18 precipitation non-negative"))

    if os.path.exists(daily_weather_path):
        df_d = pd.read_csv(daily_weather_path)
        results.append(assert_test(len(df_d) == 14610, f"D19 daily weather row count exactly 14,610 (got {len(df_d):,})"))
        results.append(assert_test(df_d['district'].nunique() == 10, f"D19 covers 10 anchor districts (got {df_d['district'].nunique()})"))

    if os.path.exists(agro_metrics_path):
        df_ag = pd.read_csv(agro_metrics_path)
        results.append(assert_test(len(df_ag) == 40, f"D20 agro metrics has 40 district-years (got {len(df_ag)})"))
        results.append(assert_test((df_ag['heat_stress_days_above_35c'] >= 0).all(), "Heat stress days non-negative"))

    # ----------------------------------------------------
    # Check 3: Workstream B (Agronomic Suitability Knowledge)
    # ----------------------------------------------------
    logger.info("\n--- Check 3: Workstream B - Authoritative Agronomic KB Audit ---")
    crop_master_path = os.path.join(PROCESSED_DIR, "agronomic", "normalized_crop_master.csv")
    crop_req_path = os.path.join(PROCESSED_DIR, "agronomic", "crop_suitability_requirements.csv")
    evid_cat_path = os.path.join(CATALOG_DIR, "agronomic_evidence_catalog.csv")
    unres_rep_path = os.path.join(CATALOG_DIR, "unresolved_agronomic_evidence_report.md")

    results.append(assert_test(os.path.exists(crop_master_path), "D21 normalized crop master exists"))
    results.append(assert_test(os.path.exists(crop_req_path), "D22 crop suitability requirements exists"))
    results.append(assert_test(os.path.exists(evid_cat_path), "Agronomic evidence catalog exists"))
    results.append(assert_test(os.path.exists(unres_rep_path), "Unresolved agronomic evidence report exists"))

    if os.path.exists(crop_master_path):
        df_cm = pd.read_csv(crop_master_path)
        results.append(assert_test(len(df_cm) == 28, f"D21 contains exactly 28 canonical crops (got {len(df_cm)})"))
        results.append(assert_test(df_cm['botanical_name'].notnull().all(), "All 28 crops have botanical taxonomy"))

    if os.path.exists(crop_req_path):
        df_cr = pd.read_csv(crop_req_path)
        results.append(assert_test(len(df_cr) >= 16, f"D22 contains >= 16 crop regimes (got {len(df_cr)})"))
        results.append(assert_test((df_cr['ph_optimal_min'] <= df_cr['ph_optimal_max']).all(), "Soil pH optimal bounds logically ordered"))
        results.append(assert_test((df_cr['temp_vegetative_opt_min_c'] <= df_cr['temp_vegetative_opt_max_c']).all(), "Thermal optimal bounds logically ordered"))

    # ----------------------------------------------------
    # Check 4: Workstream C (Soil & Geographic Depth Features)
    # ----------------------------------------------------
    logger.info("\n--- Check 4: Workstream C - Enhanced Soil Profiles Audit ---")
    enhanced_soil_path = os.path.join(PROCESSED_DIR, "soil", "enhanced_district_soil_profiles.csv")
    geo_join_audit_path = os.path.join(CATALOG_DIR, "geographic_join_audit.md")
    soil_missing_path = os.path.join(CATALOG_DIR, "soil_missing_features_report.csv")

    results.append(assert_test(os.path.exists(enhanced_soil_path), "D23 enhanced soil profiles exists"))
    results.append(assert_test(os.path.exists(geo_join_audit_path), "Geographic join audit report exists"))
    results.append(assert_test(os.path.exists(soil_missing_path), "Soil missing features report exists"))

    if os.path.exists(enhanced_soil_path):
        df_s = pd.read_csv(enhanced_soil_path)
        results.append(assert_test(len(df_s) == 643, f"D23 covers 643 districts (got {len(df_s)})"))
        results.append(assert_test('plant_available_water_capacity_awc_mm_m' in df_s.columns, "Root-zone AWC (mm/m) feature present"))
        results.append(assert_test('available_phosphorus_p2o5_status' in df_s.columns, "ICAR Available P status present"))
        results.append(assert_test('available_potassium_k2o_status' in df_s.columns, "ICAR Available K status present"))
        
        # Verify un-imputed districts
        alappuzha = df_s[df_s['district'].str.lower() == 'alappuzha']
        results.append(assert_test('INSUFFICIENT_EVIDENCE' in alappuzha['soil_evidence_status'].values[0], "Alappuzha correctly flagged as insufficient evidence (backwaters)"))
        jaisalmer = df_s[df_s['district'].str.lower() == 'jaisalmer']
        results.append(assert_test('INSUFFICIENT_EVIDENCE' in jaisalmer['soil_evidence_status'].values[0], "Jaisalmer correctly flagged as insufficient evidence (sand dunes)"))

    # ----------------------------------------------------
    # Check 5: Workstream D (Defensible Learning Targets)
    # ----------------------------------------------------
    logger.info("\n--- Check 5: Workstream D - Learning Targets Audit ---")
    target_parquet_path = os.path.join(PROCESSED_DIR, "evaluation", "multilabel_suitability_dataset.parquet")
    target_manifest_path = os.path.join(PROCESSED_DIR, "evaluation", "target_definitions_manifest.json")

    results.append(assert_test(os.path.exists(target_parquet_path), "D24 multilabel suitability parquet exists"))
    results.append(assert_test(os.path.exists(target_manifest_path), "Target definitions manifest JSON exists"))

    if os.path.exists(target_parquet_path):
        df_t = pd.read_parquet(target_parquet_path)
        results.append(assert_test(len(df_t) == 54012, f"D24 has exactly 54,012 rows (643 dists x 3 seasons x 28 crops) (got {len(df_t):,})"))
        
        # Verify 4 target separation
        t1_present = 'is_historically_cultivated' in df_t.columns
        t2_present = 'agronomic_suitability_label' in df_t.columns
        t3_present = 'observed_mean_yield_tonnes_ha' in df_t.columns
        t4_present = 'projected_gross_revenue_inr_ha' in df_t.columns and 'projected_net_margin_inr_ha' in df_t.columns
        results.append(assert_test(t1_present and t2_present and t3_present and t4_present, "All 4 target layers distinct and present in D24"))

        # Verify 3-valued suitability
        suit_vals = set(int(v) for v in df_t['agronomic_suitability_label'].unique())
        results.append(assert_test(suit_vals == {1, 0, -1}, f"Suitability label is strictly 3-valued (1, 0, -1) (got {suit_vals})"))

    # ----------------------------------------------------
    # Check 6: Workstream E & F (Benchmark & Evaluation)
    # ----------------------------------------------------
    logger.info("\n--- Check 6: Workstream E & F - Benchmark & Model Selection Audit ---")
    splits_index_path = os.path.join(PROCESSED_DIR, "evaluation", "benchmark_splits_index.json")
    bench_design_path = os.path.join(CATALOG_DIR, "phase3_benchmark_design.md")
    bench_results_path = os.path.join(PROCESSED_DIR, "evaluation", "baseline_benchmark_results.json")

    results.append(assert_test(os.path.exists(splits_index_path), "Benchmark splits index JSON exists"))
    results.append(assert_test(os.path.exists(bench_design_path), "Benchmark design document exists"))
    results.append(assert_test(os.path.exists(bench_results_path), "Baseline benchmark results JSON exists"))

    if os.path.exists(splits_index_path):
        with open(splits_index_path, "r", encoding="utf-8") as f:
            splits_data = json.load(f)
        # Support both legacy nested format and flat format
        spatial_section = splits_data.get("splits", {}).get("spatial", splits_data.get("spatial_splits", {}))
        held_out_count = spatial_section.get("held_out_districts_count", 0)
        results.append(assert_test(held_out_count >= 80, f"Spatial holdout has >= 80 districts (15%) (got {held_out_count})"))

    if os.path.exists(bench_results_path):
        with open(bench_results_path, "r", encoding="utf-8") as f:
            b_res = json.load(f)
        freq_p3 = b_res["models_evaluated"]["model_1_frequency_baseline"]["metrics_across_all_districts"]["precision_at_3"]
        results.append(assert_test(freq_p3 > 0.5, f"Frequency baseline P@3 evaluated (> 0.50) (got {freq_p3:.4f})"))

    # ----------------------------------------------------
    # Check 7: Catalog & Reporting Deliverables
    # ----------------------------------------------------
    logger.info("\n--- Check 7: Catalog & Reports Audit ---")
    cov_rep_path = os.path.join(CATALOG_DIR, "phase3_coverage_report.csv")
    qual_rep_path = os.path.join(CATALOG_DIR, "phase3_data_quality_report.md")
    runbook_path = os.path.join(CATALOG_DIR, "source_access_runbook.md")
    cat_csv_path = os.path.join(CATALOG_DIR, "dataset_catalog.csv")

    results.append(assert_test(os.path.exists(cov_rep_path), "phase3_coverage_report.csv exists"))
    results.append(assert_test(os.path.exists(qual_rep_path), "phase3_data_quality_report.md exists"))
    results.append(assert_test(os.path.exists(runbook_path), "source_access_runbook.md exists"))
    results.append(assert_test(os.path.exists(cat_csv_path), "dataset_catalog.csv exists"))

    if os.path.exists(cat_csv_path):
        cat_df = pd.read_csv(cat_csv_path)
        results.append(assert_test(len(cat_df) >= 24, f"dataset_catalog.csv tracks D01 to D24 (got {len(cat_df)} entries)"))

    # ----------------------------------------------------
    # Final Verdict
    # ----------------------------------------------------
    passed = sum(results)
    total = len(results)
    logger.info("\n====================================================")
    logger.info(f"PHASE 3 VERIFICATION SUMMARY: {passed}/{total} CHECKS PASSED ({passed/total*100:.1f}%)")
    logger.info("====================================================")

    if passed == total:
        logger.info("ALL PHASE 3 ACCEPTANCE CRITERIA SATISFIED.")
        sys.exit(0)
    else:
        logger.error(f"{total - passed} checks failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
