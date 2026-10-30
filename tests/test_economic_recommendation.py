"""
Unit and Integration Test Suite for Phase 7C Economic Crop Recommendation.
Verifies economic intent detection, Palakkad end-to-end recommendation flow,
price provenance preservation, missing price handling, and multilingual output.
"""

import pytest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from starlette.testclient import TestClient
from backend.main import app
from backend.app.services.intent_service import intent_service
from backend.app.services.translation_service import translation_service
from backend.app.ml.economic_engine import economic_engine

client = TestClient(app)

PALAKKAD_PROFILE = {
    "farm_name": "Palakkad Test Farm",
    "state": "Kerala",
    "district": "Palakkad",
    "soil_type": "Laterite Soil / Red Soil",
    "farm_size_acres": 5.0,
    "irrigation_type": "Rainfed",
    "water_source": "Rainwater / River",
    "water_availability": "Moderate",
    "season": "Kharif",
    "preferred_language": "en"
}


def test_economic_intent_detection():
    """Verifies that economic queries map to economic_recommendation while preserving standard intents."""
    assert intent_service.detect_intent("Which crop is most profitable?") == "economic_recommendation"
    assert intent_service.detect_intent("Among the suitable crops, which gives the highest estimated return?") == "economic_recommendation"
    assert intent_service.detect_intent("Which crop has the highest profit this season?") == "economic_recommendation"
    
    # Standard intent preservation
    assert intent_service.detect_intent("Which crop should I grow?") == "crop_recommendation"
    assert intent_service.detect_intent("What is the best crop for my farm?") == "crop_recommendation"
    assert intent_service.detect_intent("Compare the profits of rice, maize and ragi.") == "crop_comparison"
    assert intent_service.detect_intent("Why was rice recommended?") == "crop_explanation"


def test_palakkad_economic_recommendation_flow():
    """Verifies end-to-end Palakkad economic recommendation via POST /api/chat."""
    res = client.post("/api/chat", json={
        "message": "Among the suitable crops for my farm, which gives the highest estimated return?",
        "language": "en",
        "session_id": "test_palakkad_econ_session",
        "farm_profile": PALAKKAD_PROFILE
    })
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["intent"] == "economic_recommendation"
    
    answer = data["answer"]
    assert "Highest Estimated Economic Return" in answer or "Cotton" in answer
    assert "Cotton" in answer
    assert "Official MSP reference" in answer or "Price Basis" in answer
    assert "These figures are estimated returns" in answer or "not guaranteed" in answer
    
    # Check recommendation_data payload
    rec_data = data.get("recommendation_data") or {}
    econ_payload = rec_data.get("economic_payload") or {}
    top_crop = econ_payload.get("top_crop") or {}
    assert top_crop.get("crop") == "Cotton"
    assert top_crop.get("net_return_inr") > 100000
    assert "Small millets" in econ_payload.get("unavailable_crops", [])


def test_missing_price_handling():
    """Verifies that missing prices are not fabricated and return unavailable status."""
    batch_input = [
        {
            "crop": "Small millets",
            "price_inr_per_quintal": None,
            "yield_quintals_per_acre": None,
            "cultivation_cost_inr_per_acre": None
        }
    ]
    results = economic_engine.calculate_multiple_crops(batch_input, farm_size_acres=5.0)
    assert len(results) == 1
    res = results[0]
    assert res["status"] in ["partially_available", "unavailable"]
    assert res["economic_metrics"] is None
    assert "price" in res["missing_fields"]


def test_multilingual_economic_formatting():
    """Verifies format_economic_recommendation_response across English, Telugu, and Hindi."""
    payload = {
        "district": "Palakkad",
        "state": "Kerala",
        "top_crop": {
            "crop": "Cotton",
            "net_return_inr": 143369.90,
            "roi_pct": 92.50,
            "gross_revenue_inr": 298369.90,
            "total_cost_inr": 155000.0,
            "price_basis": "Official MSP reference"
        },
        "other_crops": [
            {"crop": "Ragi (Finger Millet)", "net_return_inr": 23389.0, "price_basis": "Official MSP reference"}
        ],
        "unavailable_crops": ["Small millets"]
    }

    # English
    en_resp = translation_service.format_economic_recommendation_response(payload, "en")
    assert "Highest Estimated Economic Return" in en_resp
    assert "₹143,369.90" in en_resp
    assert "Small millets" in en_resp

    # Telugu
    te_resp = translation_service.format_economic_recommendation_response(payload, "te")
    assert "అత్యధిక అంచనా ఆదాయం" in te_resp
    assert "143,369.90" in te_resp

    # Hindi
    hi_resp = translation_service.format_economic_recommendation_response(payload, "hi")
    assert "उच्चतम अनुमानित आय" in hi_resp
    assert "143,369.90" in hi_resp
