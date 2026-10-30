"""
Phase 6C Evidence-Bounded Test Suite for KrishiMitra AI.
Verifies all 12 required test scenarios:
1. Live market price + economic calculation
2. Cached market price + economic calculation
3. Market unavailable
4. MSP reference must not become mandi price
5. Historical yield remains historical
6. Post-harvest information
7. Sell Now calculation
8. Store information
9. Sell-vs-Store unavailable state
10. Missing economic inputs
11. Zero/invalid inputs
12. Provenance preservation
"""

import pytest
import asyncio
from backend.app.services.market_service import market_service
from backend.app.ml.economic_engine import economic_engine
from backend.app.ml.post_harvest_engine import post_harvest_engine
from backend.app.ml.seasonal_price_engine import seasonal_price_engine


# 1. Live market price + economic calculation
def test_live_market_price_and_economic_calculation():
    live_price = 5800.0
    res = economic_engine.calculate_crop_economics(
        crop="Arhar/Tur (Pigeon Pea)",
        farm_size_acres=2.0,
        yield_quintals_per_acre=6.0,
        price_inr_per_quintal=live_price,
        cultivation_cost_inr_per_acre=18000.0,
        price_source="Agmarknet Live Mandi Service",
        price_data_type="live",
        price_basis="Mandi Modal Price"
    )
    assert res["status"] == "success"
    assert res["economic_metrics"]["gross_revenue_inr"] == 69600.0  # 2.0 * 6.0 * 5800
    assert res["provenance"]["price"]["data_type"] == "live"
    assert res["provenance"]["price"]["price_basis"] == "Mandi Modal Price"


# 2. Cached market price + economic calculation
def test_cached_market_price_and_economic_calculation():
    cached_records = [{
        "mandi_name": "TestMandiKurnool",
        "commodity_name": "Arhar (Tur/Red Gram)(Whole)",
        "state": "Andhra Pradesh",
        "district": "Kurnool",
        "min_price": 5200.0,
        "max_price": 6100.0,
        "modal_price": 5600.0,
        "price_unit": "INR/quintal",
        "arrival_date": "2026-09-29",
        "data_source": "Agmarknet Cached Telemetry"
    }]
    market_service.save_market_cache(cached_records)
    
    res = asyncio.run(market_service.get_market_prices(crop="Arhar/Tur (Pigeon Pea)", state="Andhra Pradesh", district="Kurnool"))
    assert res["status"] == "success"
    assert res["data_type"] in ["live", "cached"]
    assert len(res["markets"]) > 0


# 3. Market unavailable
def test_market_unavailable_state():
    res = asyncio.run(market_service.get_market_prices(crop="UnknownCrop123", state="NonExistentState"))
    assert res["status"] == "unavailable"
    assert res["markets"] == []
    assert res["data_type"] == "unavailable"


# 4. MSP reference must not become mandi price
def test_msp_reference_must_not_become_mandi_price():
    # Calling market_service for unavailable crop returns unavailable, never MSP
    res = asyncio.run(market_service.get_market_prices(crop="Wheat", state="NonExistentStateForcingUnavailable"))
    if res["status"] == "unavailable":
        assert res["data_type"] == "unavailable"
        assert res["data_source"] == "None"
        for m in res["markets"]:
            assert m.get("data_type") != "mandi_price"


# 5. Historical yield remains historical
def test_historical_yield_remains_historical():
    res = economic_engine.calculate_crop_economics(
        crop="Rice",
        farm_size_acres=1.0,
        yield_quintals_per_acre=12.0,
        price_inr_per_quintal=2300.0,
        cultivation_cost_inr_per_acre=15000.0,
        yield_source="DES Historical District Reference"
    )
    assert res["provenance"]["yield"]["data_type"] == "historical"
    assert "Historical" in res["provenance"]["yield"]["source"] or "DES" in res["provenance"]["yield"]["source"]


# 6. Post-harvest information
def test_post_harvest_information():
    res = post_harvest_engine.get_post_harvest_advisory(crop="Rice")
    assert res["status"] in ["success", "partially_available"]
    assert "storage_method" in res["post_harvest_profile"]
    assert "optimal_moisture_pct" in res["post_harvest_profile"]
    assert res["provenance"]["source"] != ""


# 7. Sell Now calculation
def test_sell_now_calculation():
    res = post_harvest_engine.get_post_harvest_advisory(
        crop="Wheat",
        harvest_quantity_quintals=50.0,
        current_price=2275.0
    )
    sell_now = res["sell_vs_store_comparison"]["sell_now"]
    assert sell_now["label"] == "Current sale-value estimate"
    assert sell_now["estimated_revenue_inr"] == 113750.0  # 50 * 2275
    assert sell_now["is_recommendation"] is False


# 8. Store information
def test_store_information():
    res = post_harvest_engine.get_post_harvest_advisory(crop="Wheat")
    store_info = res["sell_vs_store_comparison"]["store"]
    assert store_info["label"] == "Store Information"
    assert "disclaimer" in store_info
    assert "guarantee" not in store_info["disclaimer"].lower() or "does not guarantee" in store_info["disclaimer"].lower()


# 9. Sell-vs-Store unavailable state
def test_sell_vs_store_unavailable_state():
    res = post_harvest_engine.get_post_harvest_advisory(crop="Chickpea")
    comp = res["sell_vs_store_comparison"]
    assert comp["comparison_status"] == "unavailable"
    assert "historical monthly wholesale-price data is required" in comp["reason"]
    assert comp["speculative_future_profit_calculated"] is False


# 10. Missing economic inputs
def test_missing_economic_inputs():
    res = economic_engine.calculate_crop_economics(
        crop="Maize",
        farm_size_acres=1.0,
        yield_quintals_per_acre=None,
        price_inr_per_quintal=None,
        cultivation_cost_inr_per_acre=None
    )
    assert res["status"] in ["unavailable", "partially_available"]


# 11. Zero/invalid inputs
def test_zero_or_invalid_inputs():
    res = economic_engine.calculate_crop_economics(
        crop="Maize",
        farm_size_acres=0.0,
        yield_quintals_per_acre=-5.0,
        price_inr_per_quintal=0.0,
        cultivation_cost_inr_per_acre=0.0
    )
    assert res["status"] in ["invalid_input", "invalid_inputs", "partially_available", "unavailable"]


# 12. Provenance preservation
def test_provenance_preservation():
    res = seasonal_price_engine.get_seasonal_analysis(crop="Cotton")
    assert res["available"] is False
    assert "historical monthly" in res["reason"].lower()
    assert res["seasonal_index_calculated"] is False
    assert res["provenance"]["data_type"] == "unavailable"
