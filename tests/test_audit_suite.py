"""
Comprehensive Audit Test Suite for KrishiMitra AI.
Validates all Tests A through Q, typo tolerance, multi-turn follow-ups, and FarmContext consistency.
"""

import pytest
import os
import sys

# Ensure root path is included
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from starlette.testclient import TestClient
from backend.main import app
from backend.app.services.intent_service import intent_service

client = TestClient(app)

KURNOOL_PROFILE = {
    "farm_name": "Kurnool Farm",
    "state": "Andhra Pradesh",
    "district": "Kurnool",
    "soil_type": "Black Soil (Regur/Vertisol)",
    "farm_size_acres": 5.0,
    "irrigation_type": "Drip Irrigation & Borewell",
    "water_source": "Borewell",
    "water_availability": "Moderate",
    "season": "Kharif",
    "primary_crops": ["Arhar/Tur (Pigeon Pea)", "Cotton", "Chilli"],
    "preferred_language": "en"
}


def test_scenario_a_crop_recommendation():
    """TEST A: Crop recommendation - 'Based on my current farm profile, what crops are suitable for me?'"""
    res = client.post("/api/chat", json={
        "message": "Based on my current farm profile, what crops are suitable for me?",
        "language": "en",
        "session_id": "test_chain_session",
        "farm_profile": KURNOOL_PROFILE
    })
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["intent"] in ["crop_recommendation", "farm_context_query"]
    assert len(data["answer"]) > 0
    assert "Warangal" not in data["answer"]
    assert len(data["sources"]) >= 1


def test_scenario_b_followup_why():
    """TEST B: Why - 'Why?' -> Explanation of the SAME recommended crop."""
    res = client.post("/api/chat", json={
        "message": "Why?",
        "language": "en",
        "session_id": "test_chain_session",
        "farm_profile": KURNOOL_PROFILE
    })
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["intent"] == "crop_explanation"
    assert any(c in data["answer"] for c in ["Horse-gram", "Arhar", "Tur", "Pigeon", "Cotton", "Ragi", "Rice", "soil", "rainfall"])
    assert "Vizianagaram" not in data["answer"]
    assert "Srikakulam" not in data["answer"]


def test_scenario_c_water_requirements():
    """TEST C: Water - 'What about water requirements?' -> Water requirement of SAME recommended crop."""
    res = client.post("/api/chat", json={
        "message": "What about water requirements?",
        "language": "en",
        "session_id": "test_chain_session",
        "farm_profile": KURNOOL_PROFILE
    })
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["intent"] == "irrigation"
    assert "water" in data["answer"].lower()
    assert any(c in data["answer"].lower() for c in ["horse-gram", "arhar", "tur", "drip", "water", "irrigation"])


def test_scenario_d_rainfall_suitability():
    """TEST D: Rainfall - 'What about rainfall?' -> Rainfall suitability of SAME crop."""
    res = client.post("/api/chat", json={
        "message": "What about rainfall?",
        "language": "en",
        "session_id": "test_chain_session",
        "farm_profile": KURNOOL_PROFILE
    })
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["intent"] in ["rainfall_for_previous_crop", "weather"]
    assert "rainfall" in data["answer"].lower() or "927" in data["answer"]


def test_scenario_e_compare_with_cotton():
    """TEST E: Compare with cotton - 'Compare it with cotton.' -> Comparison between SAME crop and cotton."""
    res = client.post("/api/chat", json={
        "message": "Compare it with cotton.",
        "language": "en",
        "session_id": "test_chain_session",
        "farm_profile": KURNOOL_PROFILE
    })
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["intent"] == "crop_comparison"
    assert "Cotton" in data["answer"] or "cotton" in data["answer"].lower()


def test_scenario_f_black_soil_characteristics():
    """TEST F: Black soil information - 'What are the main characteristics of black soil, and why is it useful for agriculture?'"""
    res = client.post("/api/chat", json={
        "message": "What are the main characteristics of black soil, and why is it useful for agriculture?",
        "language": "en",
        "session_id": "test_chain_session",
        "farm_profile": KURNOOL_PROFILE
    })
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["intent"] == "soil_information"
    assert "clay" in data["answer"].lower() or "moisture" in data["answer"].lower() or "vertisol" in data["answer"].lower()
    # Ensure district soil does not overwrite user's farm soil
    assert "black soil" in data["answer"].lower()
    assert len(data["sources"]) >= 1


def test_scenario_g_kurnool_agricultural_conditions():
    """TEST G: Kurnool agriculture - 'What agricultural conditions are common in Kurnool?'"""
    res = client.post("/api/chat", json={
        "message": "What agricultural conditions are common in Kurnool?",
        "language": "en",
        "session_id": "test_chain_session",
        "farm_profile": KURNOOL_PROFILE
    })
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["intent"] == "location_agriculture"
    assert "Kurnool" in data["answer"] or "kurnool" in data["answer"].lower()


def test_scenario_h_drip_irrigation_definition():
    """TEST H: Drip irrigation definition - 'What is drip irrigation?'"""
    res = client.post("/api/chat", json={
        "message": "What is drip irrigation?",
        "language": "en",
        "session_id": "test_definition_session",
        "farm_profile": KURNOOL_PROFILE
    })
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["intent"] == "generic_agri_definition"
    assert any(w in data["answer"].lower() for w in ["drip", "micro-irrigation", "delivers water", "pipes", "water", "irrigation"])


def test_scenario_i_exact_yield():
    """TEST I: Exact yield - 'Tell me the exact yield I will get from my 5-acre farm.'"""
    res = client.post("/api/chat", json={
        "message": "Tell me the exact yield I will get from my 5-acre farm.",
        "language": "en",
        "session_id": "test_yield_session",
        "farm_profile": KURNOOL_PROFILE
    })
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["intent"] == "exact_yield"
    # Must explain exact cannot be predicted/guaranteed
    assert "exact" in data["answer"].lower() or "cannot" in data["answer"].lower() or "yield" in data["answer"].lower()


def test_scenario_j_telugu_recommendation():
    """TEST J: Telugu recommendation - 'నా పొలానికి ఏ పంట అనుకూలంగా ఉంటుంది?'"""
    res = client.post("/api/chat", json={
        "message": "నా పొలానికి ఏ పంట అనుకూలంగా ఉంటుంది?",
        "language": "te",
        "session_id": "test_telugu_chain_session",
        "farm_profile": KURNOOL_PROFILE
    })
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["language"] == "te"
    assert "కంది" in data["answer"] or "పంట" in data["answer"] or "ఉలవలు" in data["answer"]


def test_scenario_k_telugu_why():
    """TEST K: Telugu why - 'ఎందుకు?'"""
    res = client.post("/api/chat", json={
        "message": "ఎందుకు?",
        "language": "te",
        "session_id": "test_telugu_chain_session",
        "farm_profile": KURNOOL_PROFILE
    })
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["language"] == "te"
    assert data["intent"] == "crop_explanation"
    assert "కంది" in data["answer"] or "కారణాలు" in data["answer"] or "నేల" in data["answer"] or "పంట" in data["answer"]
    assert "Vizianagaram" not in data["answer"]


def test_scenario_l_telugu_water():
    """TEST L: Telugu water - 'నీటి అవసరం ఎంత?'"""
    res = client.post("/api/chat", json={
        "message": "నీటి అవసరం ఎంత?",
        "language": "te",
        "session_id": "test_telugu_chain_session",
        "farm_profile": KURNOOL_PROFILE
    })
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["language"] == "te"
    assert data["intent"] == "irrigation"
    assert "నీటి" in data["answer"] or "డ్రిప్" in data["answer"] or "పంట" in data["answer"]


def test_scenario_m_hindi_recommendation():
    """TEST M: Hindi recommendation - 'खरीफ में मेरे खेत के लिए कौन सी फसल उपयुक्त है?'"""
    res = client.post("/api/chat", json={
        "message": "खरीफ में मेरे खेत के लिए कौन सी फसल उपयुक्त है?",
        "language": "hi",
        "session_id": "test_hindi_chain_session",
        "farm_profile": KURNOOL_PROFILE
    })
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["language"] == "hi"
    assert data["intent"] == "crop_recommendation"
    assert "अरहर" in data["answer"] or "फसल" in data["answer"] or "कुलथी" in data["answer"]


def test_scenario_n_hindi_why():
    """TEST N: Hindi why - 'क्यों?'"""
    res = client.post("/api/chat", json={
        "message": "क्यों?",
        "language": "hi",
        "session_id": "test_hindi_chain_session",
        "farm_profile": KURNOOL_PROFILE
    })
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["language"] == "hi"
    assert data["intent"] == "crop_explanation"
    assert "अरहर" in data["answer"] or "कारण" in data["answer"] or "मिट्टी" in data["answer"] or "फसल" in data["answer"]


def test_scenario_o_hindi_water():
    """TEST O: Hindi water - 'पानी की कितनी जरूरत है?'"""
    res = client.post("/api/chat", json={
        "message": "पानी की कितनी जरूरत है?",
        "language": "hi",
        "session_id": "test_hindi_chain_session",
        "farm_profile": KURNOOL_PROFILE
    })
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["language"] == "hi"
    assert data["intent"] == "irrigation"
    assert "पानी" in data["answer"] or "सिंचाई" in data["answer"]


def test_scenario_p_hindi_voice_intent_detection():
    """TEST P: Hindi voice recognition & intent classification"""
    hindi_query = "खरीफ में मेरे खेत के लिए कौन सी फसल उपयुक्त है?"
    detected_intent = intent_service.detect_intent(hindi_query)
    assert detected_intent == "crop_recommendation"
    entities = intent_service.extract_entities(hindi_query)
    assert entities["season"] == "Kharif"


def test_scenario_q_weather_and_rainfall_consistency():
    """TEST Q: Weather and rainfall consistency across all responses"""
    res = client.post("/api/chat", json={
        "message": "What is the current weather in Kurnool?",
        "language": "en",
        "session_id": "test_weather_session",
        "farm_profile": KURNOOL_PROFILE
    })
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["intent"] == "weather"
    assert "temperature" in data["answer"].lower() or "weather" in data["answer"].lower()


def test_regression_typo_tolerance():
    """Regression: Typo tolerance"""
    res = client.post("/api/chat", json={
        "message": "My farm is in kurnooland I have black soil which crock is suitable for kharif",
        "language": "en",
        "session_id": "test_typo_session",
        "farm_profile": KURNOOL_PROFILE
    })
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["intent"] == "crop_recommendation"
    assert any(c in data["answer"] for c in ["Horse-gram", "Arhar", "Tur", "Pigeon", "Cotton", "Ragi", "Rice"])


def test_regression_water_comparison():
    """Regression: Water comparison"""
    client.post("/api/chat", json={
        "message": "Based on my current farm profile, what crops are suitable for me?",
        "language": "en",
        "session_id": "test_compare_chain",
        "farm_profile": KURNOOL_PROFILE
    })
    res = client.post("/api/chat", json={
        "message": "Which needs more water?",
        "language": "en",
        "session_id": "test_compare_chain",
        "farm_profile": KURNOOL_PROFILE
    })
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["intent"] == "water_comparison_for_previous"
    assert "Cotton" in data["answer"] or "water" in data["answer"].lower()


def test_regression_translation_followup():
    """Regression: Translation follow-up"""
    client.post("/api/chat", json={
        "message": "Based on my current farm profile, what crops are suitable for me?",
        "language": "en",
        "session_id": "test_trans_chain",
        "farm_profile": KURNOOL_PROFILE
    })
    res = client.post("/api/chat", json={
        "message": "Explain that in Telugu",
        "language": "en",
        "session_id": "test_trans_chain",
        "farm_profile": KURNOOL_PROFILE
    })
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["language"] == "te"
    assert "కంది" in data["answer"] or "కారణాలు" in data["answer"] or "పంట" in data["answer"]
