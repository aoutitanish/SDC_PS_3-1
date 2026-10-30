"""
Comprehensive Test Suite for KrishiMitra AI.
Tests ML Recommendation, Explainability, RAG Vector Search, Multilingual Detection, and FastAPI Endpoints.
"""

import pytest
import os
import sys

# Ensure root path is included
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.ml.predict import recommender
from backend.app.services.rag_service import rag_service
from backend.app.services.translation_service import translation_service
from starlette.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_ml_recommendation_telangana_black_soil():
    """Test ML recommendation for Telangana Black Soil."""
    input_data = {
        "state": "Telangana",
        "district": "Warangal",
        "soil_type": "Black Soil",
        "ph": 7.2
    }
    res = recommender.recommend(input_data)
    assert res["success"] is True
    assert "primary_recommendation" in res
    assert "crop" in res["primary_recommendation"]
    assert "factor_scores" in res["primary_recommendation"]
    assert "soil_suitability" in res["primary_recommendation"]["factor_scores"]
    assert len(res["alternative_crops"]) > 0
    assert len(res["primary_recommendation"]["sources"]) > 0


def test_explainability_scoring_bounds():
    """Verify that explainability factor scores stay within 0-100% and provide reasoning."""
    res = recommender.recommend({"state": "Punjab", "district": "Ludhiana", "ph": 7.0})
    prim = res["primary_recommendation"]
    scores = prim["factor_scores"]
    for k, v in scores.items():
        assert 0.0 <= v <= 100.0, f"Score {k} was {v}, out of range"
    assert len(prim["supporting_factors"]) > 0


def test_rag_retrieval_and_entities():
    """Test entity extraction and vector context retrieval."""
    query = "What crop can I grow in Telangana with black soil?"
    res = rag_service.retrieve_context(query)
    assert res["entities_detected"]["state"] == "Telangana"
    assert res["entities_detected"]["soil_type"] == "black soil"
    assert len(res["retrieved_documents"]) > 0
    assert len(res["sources"]) > 0


def test_language_detection():
    """Test detection for Telugu, Hindi, and English."""
    assert translation_service.detect_language("నల్ల నేలలో ఏ పంట వేయాలి?") == "te"
    assert translation_service.detect_language("काली मिट्टी में कौन सी फसल उगानी चाहिए?") == "hi"
    assert translation_service.detect_language("What crop is best for black soil?") == "en"


def test_api_health_endpoint():
    """Test /api/health endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_api_recommend_endpoint():
    """Test /api/recommend endpoint."""
    response = client.post("/api/recommend", json={
        "state": "Telangana",
        "district": "Warangal",
        "soil_type": "Black Soil",
        "ph": 7.2
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "primary_recommendation" in data


def test_api_soil_analyze_endpoint():
    """Test /api/soil/analyze endpoint."""
    response = client.post("/api/soil/analyze", json={
        "clay_pct": 40.0,
        "sand_pct": 30.0,
        "silt_pct": 30.0,
        "ph": 7.2
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "soil_profile" in data
    assert data["soil_profile"]["usda_texture"] in ["Clay", "Clay Loam"]


def test_api_crops_list():
    """Test /api/crops listing."""
    response = client.get("/api/crops")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["total_count"] > 0


def test_api_geography_states():
    """Test /api/geography/states listing."""
    response = client.get("/api/geography/states")
    assert response.status_code == 200
    data = response.json()
    assert "Telangana" in data["states"]
    assert "Maharashtra" in data["states"]


def test_api_chat_telugu_flow():
    """Test /api/chat with Telugu query."""
    response = client.post("/api/chat", json={
        "message": "నల్ల నేలలో ఏ పంట వేయాలి?",
        "language": "te",
        "session_id": "test_telugu_sess"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["language"] == "te"
    assert len(data["answer"]) > 0
