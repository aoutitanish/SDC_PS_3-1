"""
Unit Test Suite for Agricultural Engine.
Validates isolated crop suitability scoring across 12 distinct test scenarios.
"""

import pytest
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.ml.agricultural_engine import AgriculturalEngine


@pytest.fixture
def engine():
    return AgriculturalEngine()


def test_1_crop_strongly_compatible(engine):
    """Scenario 1: Crop strongly compatible with soil, climate, and season."""
    farm_context = {
        "ph": 6.5,
        "clay_pct": 30.0,
        "annual_rainfall_mm": 1000.0,
        "mean_temperature_c": 25.0,
        "nitrogen_cg_kg": 180.0,
        "season": "Kharif",
        "water_availability": "Moderate",
        "state": "Maharashtra"
    }
    res = engine.evaluate_crop("Arhar/Tur (Pigeon Pea)", farm_context)

    assert res["crop"] == "Arhar/Tur (Pigeon Pea)"
    assert res["overall_score"] >= 80.0
    assert res["factor_scores"]["soil"] == 100.0
    assert res["factor_scores"]["climate"] == 100.0
    assert res["factor_scores"]["season"] == 100.0
    assert len(res["supporting_factors"]) >= 3
    assert len(res["hard_constraints"]) == 0


def test_2_clearly_wrong_season(engine):
    """Scenario 2: Clearly wrong season penalty."""
    farm_context_kharif = {
        "season": "Kharif",
        "ph": 6.5,
        "annual_rainfall_mm": 1000.0,
        "mean_temperature_c": 25.0
    }
    farm_context_rabi = {
        "season": "Rabi",
        "ph": 6.5,
        "annual_rainfall_mm": 1000.0,
        "mean_temperature_c": 25.0
    }

    res_kharif = engine.evaluate_crop("Arhar/Tur (Pigeon Pea)", farm_context_kharif)
    res_rabi = engine.evaluate_crop("Arhar/Tur (Pigeon Pea)", farm_context_rabi)

    assert res_kharif["factor_scores"]["season"] == 100.0
    assert res_rabi["factor_scores"]["season"] <= 30.0
    assert res_rabi["overall_score"] < res_kharif["overall_score"]
    assert any("out-of-season" in c.lower() for c in res_rabi["hard_constraints"]) or any("not historically grown" in l.lower() for l in res_rabi["limitations"])


def test_3_limited_water_vs_water_intensive(engine):
    """Scenario 3: Limited water vs water-intensive crop."""
    farm_context = {
        "water_availability": "Limited",
        "irrigation_type": "Rainfed",
        "has_drip": False,
        "has_borewell": False
    }
    res_rice = engine.evaluate_crop("Rice", farm_context)
    res_gram = engine.evaluate_crop("Gram (Chickpea)", farm_context)

    assert res_rice["factor_scores"]["water"] <= 35.0
    assert res_gram["factor_scores"]["water"] >= 80.0
    assert any("high water" in l.lower() or "risk" in l.lower() for l in res_rice["limitations"])
    assert any("drought-tolerant" in s.lower() or "limited water" in s.lower() for s in res_gram["supporting_factors"])


def test_4_drought_condition(engine):
    """Scenario 4: Drought weather stress."""
    farm_context = {
        "weather_condition": "drought"
    }
    res_rice = engine.evaluate_crop("Rice", farm_context)
    res_bajra = engine.evaluate_crop("Bajra (Pearl Millet)", farm_context)

    assert res_bajra["factor_scores"]["weather"] >= 85.0
    assert res_rice["factor_scores"]["weather"] <= 35.0
    assert any("drought" in s.lower() for s in res_bajra["supporting_factors"])
    assert any("vulnerable" in l.lower() or "drought" in l.lower() for l in res_rice["limitations"])


def test_5_heavy_rainfall_condition(engine):
    """Scenario 5: Heavy rainfall condition."""
    farm_context = {
        "weather_condition": "heavy"
    }
    res_rice = engine.evaluate_crop("Rice", farm_context)
    res_gram = engine.evaluate_crop("Gram (Chickpea)", farm_context)

    assert res_rice["factor_scores"]["weather"] >= 85.0
    assert res_gram["factor_scores"]["weather"] <= 40.0
    assert any("waterlogging" in l.lower() for l in res_gram["limitations"])


def test_6_hot_condition(engine):
    """Scenario 6: Hot weather stress."""
    farm_context = {
        "weather_condition": "hot"
    }
    res_cotton = engine.evaluate_crop("Cotton", farm_context)
    res_wheat = engine.evaluate_crop("Wheat", farm_context)

    assert res_cotton["factor_scores"]["weather"] >= 85.0
    assert res_wheat["factor_scores"]["weather"] <= 40.0
    assert any("temperature stress" in l.lower() or "cool-season" in l.lower() for l in res_wheat["limitations"])


def test_7_cold_condition(engine):
    """Scenario 7: Cold weather stress."""
    farm_context = {
        "weather_condition": "cold"
    }
    res_wheat = engine.evaluate_crop("Wheat", farm_context)
    res_cotton = engine.evaluate_crop("Cotton", farm_context)

    assert res_wheat["factor_scores"]["weather"] >= 85.0
    assert res_cotton["factor_scores"]["weather"] <= 50.0


def test_8_explicit_no_drip_no_borewell(engine):
    """Scenario 8: Explicit no-drip/no-borewell must not become drip/borewell."""
    farm_context = {
        "has_drip": False,
        "has_borewell": False,
        "irrigation_type": "Rainfed",
        "water_source": "Rainwater"
    }
    res = engine.evaluate_crop("Gram (Chickpea)", farm_context)

    for factor in res["supporting_factors"]:
        assert "drip irrigation setup available" not in factor.lower()
        assert "borewell water source confirmed" not in factor.lower()

    for item in res["evidence"]:
        assert "drip irrigation" not in item.lower()
        assert "borewell" not in item.lower()


def test_9_regional_evidence(engine):
    """Scenario 9: Regional historical evidence."""
    farm_context_mh = {"state": "Maharashtra"}
    farm_context_kl = {"state": "Kerala"}

    res_mh = engine.evaluate_crop("Arhar/Tur (Pigeon Pea)", farm_context_mh)
    res_kl = engine.evaluate_crop("Arhar/Tur (Pigeon Pea)", farm_context_kl)

    assert res_mh["factor_scores"]["regional"] > res_kl["factor_scores"]["regional"]
    assert any("Maharashtra" in s for s in res_mh["supporting_factors"])
    assert any("historical evidence" in e.lower() for e in res_mh["evidence"])


def test_10_ml_probability_affects_ranking(engine):
    """Scenario 10: ML probability affects ranking but does not completely dominate agronomy."""
    farm_context = {
        "season": "Rabi",
        "water_availability": "Limited",
        "irrigation_type": "Rainfed",
        "has_drip": False,
        "has_borewell": False,
        "ph": 7.0,
        "mean_temperature_c": 20.0
    }
    # Give Rice a high ML probability (0.80) and Gram a low ML probability (0.10)
    ml_probs = {
        "Rice": 0.80,
        "Gram (Chickpea)": 0.10
    }

    ranked = engine.rank_crops(farm_context, candidate_crops=["Rice", "Gram (Chickpea)"], ml_probabilities=ml_probs, top_k=2)

    # Gram (Chickpea) is Rabi-suited and drought-tolerant; Rice is out-of-season and water-intensive.
    # Gram should still rank #1 despite lower raw ML probability.
    assert ranked[0]["crop"] == "Gram (Chickpea)"
    assert ranked[1]["crop"] == "Rice"


def test_11_missing_optional_data(engine):
    """Scenario 11: Missing optional data does not crash."""
    farm_context_empty = {}
    res_empty = engine.evaluate_crop("Maize", farm_context_empty)

    assert res_empty["crop"] == "Maize"
    assert isinstance(res_empty["overall_score"], float)
    assert 0.0 <= res_empty["overall_score"] <= 100.0

    ranked = engine.rank_crops({})
    assert len(ranked) > 0


def test_12_unknown_location_no_kurnool(engine):
    """Scenario 12: Unknown location does not silently become Kurnool."""
    farm_context = {
        "state": None,
        "district": None,
        "ph": 6.8
    }
    res = engine.evaluate_crop("Wheat", farm_context)

    all_text = str(res).lower()
    assert "kurnool" not in all_text
    assert "andhra pradesh" not in all_text
    assert res["factor_scores"]["regional"] == 50.0
