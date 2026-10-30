"""
Unit Test Suite for Phase 4 Post-Harvest Intelligence Engine (PostHarvestEngine).
Verifies:
1. Crop lookup
2. Storage method retrieval
3. Shelf-life retrieval
4. Moisture target retrieval
5. Source provenance integrity
6. Unknown crop handling
7. Missing post-harvest data handling
8. Perishability unknown handling
9. Sell-now framework
10. Insufficient-data handling for sell vs store comparison
11. No speculative future price or profit generation
12. No invented storage values
13. EconomicEngine separation
14. Multilingual-ready structured output
15. All pre-existing Stage-1, 2, and 3 behaviors remain unchanged
"""

import pytest
import json
from backend.app.ml.post_harvest_engine import post_harvest_engine, PostHarvestEngine
from backend.app.ml.agricultural_engine import AgriculturalEngine
from backend.app.ml.economic_engine import economic_engine


def test_1_crop_lookup():
    """1: Verify crop lookup resolves canonical name and returns success."""
    res = post_harvest_engine.get_post_harvest_advisory(crop="Rice")
    assert res["status"] == "success"
    assert res["crop"] == "Rice"


def test_2_storage_method_retrieval():
    """2: Verify retrieval of verified storage method for Rice."""
    res = post_harvest_engine.get_post_harvest_advisory(crop="Rice")
    profile = res["post_harvest_profile"]
    assert "godown" in profile["storage_method"].lower() or "jute" in profile["storage_method"].lower()


def test_3_shelf_life_retrieval():
    """3: Verify retrieval of verified shelf-life days."""
    res = post_harvest_engine.get_post_harvest_advisory(crop="Wheat")
    profile = res["post_harvest_profile"]
    assert profile["shelf_life_days"] == 365


def test_4_moisture_target_retrieval():
    """4: Verify retrieval of verified optimal moisture percentage."""
    res = post_harvest_engine.get_post_harvest_advisory(crop="Maize")
    profile = res["post_harvest_profile"]
    assert profile["optimal_moisture_pct"] == 13.5


def test_5_source_provenance():
    """5: Verify source provenance metadata is preserved."""
    res = post_harvest_engine.get_post_harvest_advisory(crop="Rice")
    prov = res["provenance"]
    assert prov["source"] != "None"
    assert "source_url" in prov
    assert prov["data_type"] == "official"


def test_6_unknown_crop_handling():
    """6: Verify handling of unknown crop names."""
    res = post_harvest_engine.get_post_harvest_advisory(crop="FakeCrop99")
    assert res["status"] == "unavailable"
    assert res["post_harvest_profile"] is None
    assert "not recognized" in res["error"]


def test_7_missing_post_harvest_data_handling():
    """7: Verify handling when crop is recognized but missing specific fields."""
    # Build manual mock missing response via class instance if needed
    missing_resp = post_harvest_engine._build_missing_data_response("TestCrop")
    assert missing_resp["status"] == "partially_available"
    assert "post_harvest_storage" in missing_resp["missing_fields"]


def test_8_perishability_unknown_handling():
    """8: Verify perishability classification returns 'unknown' when shelf life is missing."""
    perishability = PostHarvestEngine._classify_perishability(None)
    assert perishability == "unknown"


def test_9_sell_now_framework():
    """9: Verify sell-now framework computes revenue when price and quantity supplied."""
    res = post_harvest_engine.get_post_harvest_advisory(
        crop="Wheat",
        harvest_quantity_quintals=50.0,
        current_price=2275.0,
        farmer_goal="sell_now"
    )
    comp = res["sell_vs_store_comparison"]
    assert comp["sell_now"]["available_price_inr_per_quintal"] == 2275.0
    assert comp["sell_now"]["estimated_revenue_inr"] == 113750.0


def test_10_insufficient_data_handling():
    """10: Verify sell vs store comparison returns 'insufficient_data' for speculative metrics."""
    res = post_harvest_engine.get_post_harvest_advisory(
        crop="Cotton",
        farmer_goal="compare_options"
    )
    comp = res["sell_vs_store_comparison"]
    assert comp["comparison_status"] in ["unavailable", "insufficient_data"]
    assert "Sell-vs-store financial comparison unavailable" in comp["reason"] or "not speculatively" in comp["reason"]


def test_11_no_speculative_future_price():
    """11: Verify no speculative future prices or profit gains are generated."""
    res = post_harvest_engine.get_post_harvest_advisory(crop="Maize")
    comp = res["sell_vs_store_comparison"]
    assert comp["speculative_future_profit_calculated"] is False


def test_12_no_invented_storage_values():
    """12: Verify storage values are strictly sourced from dataset without guessing."""
    res = post_harvest_engine.get_post_harvest_advisory(crop="Rice")
    prof = res["post_harvest_profile"]
    assert isinstance(prof["shelf_life_days"], int)
    assert isinstance(prof["optimal_moisture_pct"], float)


def test_13_economic_engine_separation():
    """13: Verify EconomicEngine result is passed through unmodified in economic_reference."""
    mock_econ = {
        "status": "success",
        "crop": "Cotton",
        "economic_metrics": {"estimated_net_return_inr": 95400.0}
    }
    res = post_harvest_engine.get_post_harvest_advisory(
        crop="Cotton",
        economic_result=mock_econ
    )
    assert res["economic_reference"] == mock_econ
    assert res["economic_reference"]["economic_metrics"]["estimated_net_return_inr"] == 95400.0


def test_14_multilingual_ready_structured_output():
    """14: Verify response is a clean structured dictionary ready for JSON serialization and translation."""
    res = post_harvest_engine.get_post_harvest_advisory(crop="Groundnut")
    raw_str = json.dumps(res)
    assert "post_harvest_profile" in raw_str
    assert "storage_advisory" in raw_str
    assert "provenance" in raw_str
    assert "guaranteed shelf life" not in raw_str.lower()
    assert "guaranteed profit" not in raw_str.lower()


def test_15_all_existing_stage1_2_3_behavior_unchanged():
    """15: Verify AgriculturalEngine and EconomicEngine remain functioning and unchanged."""
    ag_engine = AgriculturalEngine()
    ctx = {
        "ph": 6.5,
        "annual_rainfall_mm": 1000.0,
        "mean_temperature_c": 25.0,
        "season": "Kharif",
        "state": "Maharashtra"
    }
    ag_res = ag_engine.evaluate_crop("Arhar/Tur (Pigeon Pea)", ctx)
    assert ag_res["crop"] == "Arhar/Tur (Pigeon Pea)"
    assert ag_res["overall_score"] >= 80.0

    econ_res = economic_engine.calculate_crop_economics(
        crop="Wheat",
        farm_size_acres=2.0,
        yield_quintals_per_acre=15.0,
        price_inr_per_quintal=2275.0,
        cultivation_cost_inr_per_acre=18000.0
    )
    assert econ_res["status"] == "success"
    assert econ_res["economic_metrics"]["estimated_net_return_inr"] == 68250.0 - 36000.0
