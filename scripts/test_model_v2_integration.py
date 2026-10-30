"""
Integration Verification Test for Model V1 and Model V2 Staging Modes in KrishiMitra AI.
Verifies loading, feature building, probability calculations, score fusion, and weather/season rules.
"""

import sys
import os
import json
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from backend.app.ml.predict import recommender


def test_v1_and_v2_integration():
    print("==================================================")
    print("   MODEL V1 AND V2 INTEGRATION STAGING TEST       ")
    print("==================================================")

    sample_farm_kurnool = {
        "state": "Andhra Pradesh",
        "district": "Kurnool",
        "soil_type": "Black Soil (Regur/Vertisol)",
        "season": "Kharif",
        "water_availability": "Moderate",
        "irrigation_type": "Drip Irrigation",
        "water_source": "Borewell"
    }

    sample_farm_ludhiana_rabi = {
        "state": "Punjab",
        "district": "Ludhiana",
        "soil_type": "Alluvial Soil",
        "season": "Rabi",
        "water_availability": "Moderate",
        "irrigation_type": "Canal / Flood Irrigation",
        "water_source": "Borewell"
    }

    sample_farm_drought = {
        "state": "Rajasthan",
        "district": "Sri Ganganagar",
        "soil_type": "Desert / Arid Soil",
        "season": "Kharif",
        "water_availability": "Limited",
        "rainfall_condition": "drought"
    }

    # 1. VERIFY V1 LOADING & PREDICTION
    print("\n[TEST 1] Testing MODEL_V1 Loading & Probabilities...")
    recommender.set_model_version("v1")
    assert recommender.model_version == "v1", "Failed to set model version to v1"
    assert recommender.model is not None, "Model V1 is None"

    defaults_v1 = recommender.get_district_defaults("Andhra Pradesh", "Kurnool")
    merged_v1 = {
        "ph": 7.1, "clay_pct": 31.2, "sand_pct": 41.6, "silt_pct": 27.2,
        "nitrogen_cg_kg": 165.0, "soc_dg_kg": 170.0, "cec": 340.0, "bulk_density": 1.58,
        "annual_rainfall_mm": 927.0, "kharif_rainfall_mm": 820.0, "rabi_rainfall_mm": 85.0,
        "mean_temperature_c": 27.2, "max_temperature_c": 36.5, "min_temperature_c": 18.5,
        "relative_humidity_pct": 58.5, "wind_speed_ms": 2.2
    }
    probs_v1 = recommender.get_model_probabilities(merged_v1, "Kharif", "Black Soil (Regur/Vertisol)", defaults_v1)
    
    assert len(probs_v1) == 28, f"V1 probabilities length expected 28, got {len(probs_v1)}"
    sum_p1 = sum(probs_v1.values())
    assert np.isclose(sum_p1, 1.0, atol=1e-3), f"V1 probabilities sum error: {sum_p1}"
    print(f"  ✅ V1 Loaded successfully. Target classes: {len(probs_v1)}, Probability sum = {sum_p1:.4f}")

    res_v1 = recommender.recommend(sample_farm_kurnool)
    assert res_v1["success"] is True
    print(f"  ✅ V1 Recommendation: Primary = '{res_v1['primary_recommendation']['crop']}' (Score: {res_v1['primary_recommendation']['agronomic_suitability_score']})")

    # 2. VERIFY V2 LOADING & PREDICTION
    print("\n[TEST 2] Testing MODEL_V2 Candidate Loading & Probabilities...")
    recommender.set_model_version("v2")
    assert recommender.model_version == "v2", "Failed to set model version to v2"
    assert recommender.pipeline is not None, "Model V2 Pipeline is None"
    assert "Season" in recommender.feature_cols, "Model V2 missing 'Season' feature"
    assert "indian_soil_group" in recommender.feature_cols, "Model V2 missing 'indian_soil_group' feature"

    probs_v2 = recommender.get_model_probabilities(merged_v1, "Kharif", "Black Soil (Regur/Vertisol)", defaults_v1)
    assert len(probs_v2) == 28, f"V2 probabilities length expected 28, got {len(probs_v2)}"
    sum_p2 = sum(probs_v2.values())
    assert np.isclose(sum_p2, 1.0, atol=1e-3), f"V2 probabilities sum error: {sum_p2}"
    print(f"  ✅ V2 Candidate Loaded successfully. Features: {len(recommender.feature_cols)}, Probability sum = {sum_p2:.4f}")

    res_v2 = recommender.recommend(sample_farm_kurnool)
    assert res_v2["success"] is True
    print(f"  ✅ V2 Recommendation: Primary = '{res_v2['primary_recommendation']['crop']}' (Score: {res_v2['primary_recommendation']['agronomic_suitability_score']})")

    # 3. VERIFY V2 CATEGORICAL FEATURE PASSTHROUGH (Season & Soil Group)
    print("\n[TEST 3] Verifying V2 Feature Passthrough (Season & Soil Group)...")
    probs_v2_rabi = recommender.get_model_probabilities(merged_v1, "Rabi", "Alluvial Soil", defaults_v1)
    top_crop_rabi = sorted(probs_v2_rabi.items(), key=lambda x: x[1], reverse=True)[0]
    print(f"  ✅ V2 Rabi Season prediction shift: Top predicted crop = '{top_crop_rabi[0]}' ({top_crop_rabi[1]*100:.2f}%)")

    # 4. VERIFY EXISTING WEATHER & SEASON RULES
    print("\n[TEST 4] Verifying Weather & Season Rule Integrity in V2 Mode...")
    res_rabi = recommender.recommend(sample_farm_ludhiana_rabi)
    rabi_crop = res_rabi["primary_recommendation"]["crop"]
    print(f"  ✅ Rabi Ludhiana recommendation: '{rabi_crop}'")
    assert any(c in rabi_crop.lower() for c in ["wheat", "gram", "barley", "mustard"]), f"Rabi rule failure, got {rabi_crop}"

    res_drought = recommender.recommend(sample_farm_drought)
    drought_crop = res_drought["primary_recommendation"]["crop"]
    print(f"  ✅ Drought Ganganagar recommendation: '{drought_crop}'")
    assert not any(c in drought_crop.lower() for c in ["rice", "sugarcane"]), f"Drought rule failure, got {drought_crop}"

    # 5. RESET BACK TO V1 PRODUCTION DEFAULT
    print("\n[TEST 5] Resetting to V1 Production Default...")
    recommender.set_model_version("v1")
    assert recommender.model_version == "v1", "Failed to reset model version to v1"
    print("  ✅ Recommender successfully reset to V1 production default.")

    print("\n==================================================")
    print("  ✅ ALL INTEGRATION VERIFICATION TESTS PASSED!    ")
    print("==================================================")


if __name__ == "__main__":
    test_v1_and_v2_integration()
