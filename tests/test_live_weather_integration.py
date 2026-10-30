"""
Focused unit test suite for Live Weather Integration in KrishiMitra AI.
Verifies:
A. Live weather reaches farm_context
B. Live weather statement appears in recommendation context
C. Qwen / LLM service receives live weather context with no-rerank instruction
D. Multilingual weather formatting (EN, TE, HI)
E. Weather API failure does NOT break crop recommendation
F. Existing recommendation ranking remains unchanged
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from backend.app.services.weather_service import weather_service, WeatherService
from backend.app.services.translation_service import translation_service, TranslationService
from backend.app.services.llm_service import llm_service
from backend.app.ml.predict import recommender
from backend.app.api.chat import process_chat_intent


MOCK_LIVE_WEATHER = {
    "success": True,
    "location": {"state": "Andhra Pradesh", "district": "Palakkad", "latitude": 10.7867, "longitude": 76.6548},
    "current": {
        "temperature_c": 26.9,
        "relative_humidity_pct": 57.0,
        "rainfall_mm": 0.0,
        "wind_speed_ms": 3.8,
        "condition": "Partly cloudy",
        "weather_code": 2
    },
    "forecast": [],
    "agricultural_advisory": "No immediate precipitation recorded. Ensure scheduled irrigation is maintained.",
    "data_source": "Open-Meteo High-Resolution Live Meteorological Service"
}


def test_live_weather_reaches_farm_context_and_recommendation_context():
    """A & B: Verify live weather reaches farm_context and recommendation response context."""
    async def _test():
        with patch.object(weather_service, "get_weather", new_callable=AsyncMock) as mock_get_w:
            mock_get_w.return_value = MOCK_LIVE_WEATHER

            ans, sources, rec_data, comp_data, simple_sum, det_analysis, struct_resp, conf, lang, intent = await process_chat_intent(
                message="Which crop should I grow in Palakkad, Kerala?",
                language="en",
                session_id="test_weather_session_1"
            )

            assert rec_data is not None
            res_ctx = rec_data.get("resolved_context", {})
            loc_ctx = rec_data.get("location_context", {})

            # A. Live weather in farm_context / resolved_context
            assert res_ctx.get("live_weather") is not None
            live_w = res_ctx["live_weather"]
            assert live_w["temperature_c"] == 26.9
            assert live_w["relative_humidity_pct"] == 57.0
            assert live_w["rainfall_mm"] == 0.0
            assert live_w["wind_speed_ms"] == 3.8

            # B. Live weather in location_context and response statement
            assert loc_ctx.get("live_weather") is not None
            assert "Current weather: 26.9°C, 57% humidity, 0.0 mm rainfall, wind 3.8 m/s." in ans

    asyncio.run(_test())


def test_multilingual_weather_formatting():
    """D: Test multilingual weather formatting (English, Telugu, Hindi)."""
    live_w = {
        "temperature_c": 26.9,
        "relative_humidity_pct": 57,
        "rainfall_mm": 0,
        "wind_speed_ms": 3.8
    }

    stmt_en = TranslationService.format_live_weather_statement(live_w, "en")
    assert stmt_en == "Current weather: 26.9°C, 57% humidity, 0 mm rainfall, wind 3.8 m/s."

    stmt_te = TranslationService.format_live_weather_statement(live_w, "te")
    assert stmt_te == "ప్రస్తుత వాతావరణం: 26.9°C, 57% తేమ, 0 mm వర్షపాతం, గాలి 3.8 m/s."

    stmt_hi = TranslationService.format_live_weather_statement(live_w, "hi")
    assert stmt_hi == "वर्तमान मौसम: 26.9°C, 57% आर्द्रता, 0 mm वर्षा, हवा 3.8 m/s."

    # Test missing values (should not estimate or invent missing parameters)
    partial_w = {"temperature_c": 28.5, "rainfall_mm": 12.0}
    stmt_partial = TranslationService.format_live_weather_statement(partial_w, "en")
    assert stmt_partial == "Current weather: 28.5°C, 12.0 mm rainfall."


def test_qwen_llm_receives_live_weather_context_and_no_rerank_directive():
    """C: Test Qwen/LLM prompt construction receives live_weather context and no-rerank directive."""
    farm_ctx = {
        "state": "Andhra Pradesh",
        "district": "Kurnool",
        "live_weather": {
            "temperature_c": 29.5,
            "relative_humidity_pct": 65,
            "rainfall_mm": 2.5,
            "wind_speed_ms": 1.8
        }
    }

    prompt = llm_service._build_full_prompt(
        message="What are the weather implications for my crops?",
        context="RAG background info...",
        lang="en",
        farm_context=farm_ctx
    )

    assert "LIVE WEATHER TELEMETRY:" in prompt
    assert '"temperature_c": 29.5' in prompt
    assert "do NOT rerank or change the crop recommendation" in prompt
    assert "MUST NOT rerank, change, or override the AgriculturalEngine crop recommendation" in llm_service_system_prompt()


def llm_service_system_prompt():
    from backend.app.services.llm_service import SYSTEM_PROMPT
    return SYSTEM_PROMPT


def test_weather_api_failure_does_not_break_recommendation():
    """E: Weather API failure falls back gracefully to null live_weather and recommendation succeeds."""
    async def _test():
        with patch.object(weather_service, "get_weather", side_effect=Exception("Open-Meteo connection timeout")):
            ans, sources, rec_data, comp_data, simple_sum, det_analysis, struct_resp, conf, lang, intent = await process_chat_intent(
                message="Which crop should I grow in Kurnool?",
                language="en",
                session_id="test_weather_fail_session"
            )

            assert rec_data is not None
            assert rec_data.get("primary_recommendation") is not None
            res_ctx = rec_data.get("resolved_context", {})
            # live_weather should be null/absent
            assert res_ctx.get("live_weather") is None
            assert "Crop Recommendation" in ans

    asyncio.run(_test())


def test_existing_recommendation_ranking_remains_unchanged():
    """F: Existing AgriculturalEngine recommendation ranking remains identical with or without live weather."""
    ctx_without = {
        "state": "Andhra Pradesh",
        "district": "Kurnool",
        "soil_type": "Black Soil (Regur/Vertisol)",
        "season": "Kharif",
        "water_availability": "Moderate"
    }

    ctx_with = dict(ctx_without)
    ctx_with["live_weather"] = {
        "temperature_c": 26.9,
        "relative_humidity_pct": 57.0,
        "rainfall_mm": 0.0,
        "wind_speed_ms": 3.8,
        "condition": "Clear"
    }

    res_without = recommender.recommend(ctx_without, top_k=4)
    res_with = recommender.recommend(ctx_with, top_k=4)

    # Primary crop and top 4 ranking must be exactly identical
    assert res_without["primary_recommendation"]["crop"] == res_with["primary_recommendation"]["crop"]
    assert res_without["primary_recommendation"]["agronomic_suitability_score"] == res_with["primary_recommendation"]["agronomic_suitability_score"]
    
    alts_without = [a["crop"] for a in res_without["alternative_crops"]]
    alts_with = [a["crop"] for a in res_with["alternative_crops"]]
    assert alts_without == alts_with
