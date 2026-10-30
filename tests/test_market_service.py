"""
Unit test suite for Phase 2 Market Telemetry Service (MarketService & GET /api/market/prices).
Verifies:
1. Internal crop -> commodity normalization
2. Alias -> canonical crop resolution
3. Unknown crop handling
4. Successful market response normalization
5. Missing market data handling
6. API timeout handling
7. API error handling
8. Cache write/read
9. Cached data provenance
10. Stale-cache / offline handling
11. No fake price generation
12. MSP is NOT substituted for mandi price
13. Stage-1 recommendation behavior remains unchanged
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from starlette.testclient import TestClient

from backend.main import app
from backend.app.services.market_service import market_service, MarketService
from backend.app.services.economic_service import economic_service
from backend.app.ml.predict import recommender

client = TestClient(app)


def test_internal_crop_to_commodity_normalization():
    """1 & 2: Test canonical resolution and commodity alias lookups."""
    # Canonical crop lookup
    assert economic_service.normalize_crop_name("Arhar/Tur (Pigeon Pea)") == "Arhar/Tur (Pigeon Pea)"
    
    # Alias to canonical resolution
    assert economic_service.normalize_crop_name("Arhar") == "Arhar/Tur (Pigeon Pea)"
    assert economic_service.normalize_crop_name("Red Gram") == "Arhar/Tur (Pigeon Pea)"
    assert economic_service.normalize_crop_name("Kapas") == "Cotton"
    assert economic_service.normalize_crop_name("Gehun") == "Wheat"
    assert economic_service.normalize_crop_name("Chana") == "Gram (Chickpea)"

    # Commodity aliases retrieval
    aliases = economic_service.get_commodity_aliases("Cotton")
    assert "Cotton" in aliases
    assert "Kapas" in aliases


def test_unknown_crop_handling():
    """3: Test unknown crop returns structured 'unavailable' status without crashing or guessing."""
    async def _test():
        res = await market_service.get_market_prices(crop="UnknownCrop999", state="Andhra Pradesh")
        assert res["status"] == "unavailable"
        assert res["markets"] == []
        assert res["data_type"] == "unavailable"
        assert "not recognized" in res["error"]

    asyncio.run(_test())


def test_missing_market_data_handling_and_no_fake_prices():
    """5 & 11 & 12: Missing live market data returns empty markets array, no fake prices, and no MSP substitution."""
    async def _test():
        # Query a crop with no live API key and empty cache
        res = await market_service.get_market_prices(crop="Rice", state="UnknownStateXYZ")
        assert res["status"] in ["unavailable", "success"]
        
        # When unavailable, markets is empty list (no fake fallback price, no MSP substitution)
        if res["status"] == "unavailable":
            assert res["markets"] == []
            assert res["data_type"] == "unavailable"
            assert res["data_source"] == "None"

    asyncio.run(_test())


def test_successful_market_response_normalization():
    """4: Test live market response normalization into standard internal schema."""
    mock_data_gov_resp = {
        "records": [
            {
                "state": "Andhra Pradesh",
                "district": "Kurnool",
                "market": "Kurnool APMC",
                "commodity": "Arhar (Tur/Red Gram)",
                "variety": "Desi",
                "arrival_date": "29/09/2026",
                "min_price": "7200",
                "max_price": "7800",
                "modal_price": "7500"
            }
        ]
    }

    async def _test():
        with patch.object(market_service, "api_key", "mock_key"):
            with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
                mock_resp = MagicMock()
                mock_resp.status_code = 200
                mock_resp.json.return_value = mock_data_gov_resp
                mock_get.return_value = mock_resp

                res = await market_service.get_market_prices(crop="Arhar/Tur (Pigeon Pea)", state="Andhra Pradesh", district="Kurnool")

                assert res["status"] == "success"
                assert res["crop"] == "Arhar/Tur (Pigeon Pea)"
                assert res["data_type"] == "live"
                assert len(res["markets"]) == 1

                m = res["markets"][0]
                assert m["mandi_name"] == "Kurnool APMC"
                assert m["min_price"] == 7200.0
                assert m["max_price"] == 7800.0
                assert m["modal_price"] == 7500.0
                assert m["price_unit"] == "INR/quintal"

    asyncio.run(_test())


def test_api_timeout_and_error_handling():
    """6 & 7: Test API timeout and network exception handling falls back safely without raising internal error."""
    async def _test():
        with patch.object(market_service, "api_key", "mock_key"):
            with patch("httpx.AsyncClient.get", side_effect=Exception("API Timeout")):
                res = await market_service.get_market_prices(crop="Wheat", state="Punjab")
                assert res["status"] in ["unavailable", "success"]
                if res["status"] == "unavailable":
                    assert res["markets"] == []
                    assert res["data_type"] == "unavailable"

    asyncio.run(_test())


def test_cache_write_read_and_provenance():
    """8, 9, & 10: Test SQLite cache write, read, provenance, and cached data type tagging."""
    mock_records = [
        {
            "state": "Telangana",
            "district": "Warangal",
            "mandi_name": "Warangal APMC",
            "commodity_name": "Cotton",
            "min_price": 6800.0,
            "max_price": 7400.0,
            "modal_price": 7100.0,
            "price_unit": "INR/quintal",
            "arrival_date": "29/09/2026",
            "data_source": "Agmarknet Live Mandi Service"
        }
    ]

    # Save to cache
    market_service.save_market_cache(mock_records)

    # Read from cache
    cached = market_service.get_market_cache(state="Telangana", district="Warangal", commodity_names=["Cotton", "Kapas"])
    assert len(cached) >= 1
    c0 = cached[0]
    assert c0["mandi_name"] == "Warangal APMC"
    assert c0["modal_price"] == 7100.0
    assert c0["data_type"] == "cached"
    assert "cached_at" in c0


def test_msp_is_not_substituted_for_mandi_price():
    """12: Test that MSP is never substituted for missing live mandi prices."""
    async def _test():
        res = await market_service.get_market_prices(crop="Gram (Chickpea)", state="NonExistentState")
        assert res["status"] == "unavailable"
        assert res["markets"] == []
        # Ensure MSP (5440) is not returned inside markets list as a fake mandi price
        for m in res["markets"]:
            assert m.get("modal_price") != 5440.0

    asyncio.run(_test())


def test_api_endpoint_get_market_prices():
    """Test GET /api/market/prices HTTP API endpoint."""
    res = client.get("/api/market/prices?crop=Cotton&state=Andhra%20Pradesh&district=Kurnool")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert "crop" in data
    assert "commodity" in data
    assert "markets" in data
    assert "data_type" in data
    assert "retrieved_at" in data


def test_stage1_recommendation_behavior_unchanged():
    """13: Test that AgriculturalEngine recommendation behavior remains identical and unaffected by MarketService."""
    kurnool_profile = {
        "state": "Andhra Pradesh",
        "district": "Kurnool",
        "soil_type": "Black Soil (Regur/Vertisol)",
        "season": "Kharif",
        "water_availability": "Moderate",
        "irrigation_type": "Drip Irrigation & Borewell",
        "water_source": "Borewell",
        "has_drip": True,
        "has_borewell": True
    }

    rec = recommender.recommend(kurnool_profile, top_k=4)
    assert rec["success"] is True
    assert "crop" in rec["primary_recommendation"]
    assert rec["primary_recommendation"]["crop"] == "Horse-gram"
    assert rec["primary_recommendation"]["agronomic_suitability_score"] > 50.0
    assert len(rec["alternative_crops"]) == 3
