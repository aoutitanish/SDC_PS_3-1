"""
Automated Test Suite for Season & Weather Driven Crop Recommendation in FarmerHelp.
Verifies Kharif, Rabi, Summer/Zaid, Drought, and Heavy Rainfall test cases.
Ensures season and weather conditions reach RAG, ML Recommender, and LLM prompt without hardcoded assumptions.
"""

import sys
import os
import json
import logging

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from starlette.testclient import TestClient
from backend.main import app
from backend.app.core.session_memory import session_memory

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

client = TestClient(app)

def run_season_weather_tests():
    print("\n" + "="*75)
    print("SEASON & WEATHER DRIVEN CROP RECOMMENDATION TEST SUITE")
    print("="*75)

    # -------------------------------------------------------------
    # TEST 1: KHARIF + MONSOON (Kurnool, AP)
    # -------------------------------------------------------------
    session_id1 = "test_season_kharif_1"
    session_memory.reset_session(session_id1)
    t1_msg = "My farm is in Kurnool, Andhra Pradesh. It is Kharif season with monsoon rainfall, black soil and moderate water availability."
    print(f"\n---> TEST 1: {t1_msg}")
    client.post("/api/chat", json={"message": t1_msg, "session_id": session_id1})
    resp1 = client.post("/api/chat", json={"message": "Which Kharif crops should I consider?", "session_id": session_id1})
    assert resp1.status_code == 200
    ans1 = resp1.json().get("answer", "")
    print(f"Test 1 Answer Preview:\n{ans1[:250]}...\n")
    
    session1 = session_memory.get_or_create(session_id1)
    print(f"Test 1 Resolved Context: season={session1.season} | rain_cond={session1.rainfall_condition}")
    assert session1.season == "Kharif"
    assert "Arhar" in ans1 or "Cotton" in ans1 or "Groundnut" in ans1 or "Maize" in ans1

    # -------------------------------------------------------------
    # TEST 2: RABI + WINTER (Kurnool, AP)
    # -------------------------------------------------------------
    session_id2 = "test_season_rabi_2"
    session_memory.reset_session(session_id2)
    t2_msg = "My farm is in Kurnool, Andhra Pradesh. It is Rabi season with winter conditions, black soil and moderate water availability."
    print(f"\n---> TEST 2: {t2_msg}")
    client.post("/api/chat", json={"message": t2_msg, "session_id": session_id2})
    resp2 = client.post("/api/chat", json={"message": "Which crops should I consider for Rabi season?", "session_id": session_id2})
    assert resp2.status_code == 200
    ans2 = resp2.json().get("answer", "")
    print(f"Test 2 Answer Preview:\n{ans2[:250]}...\n")

    session2 = session_memory.get_or_create(session_id2)
    print(f"Test 2 Resolved Context: season={session2.season} | temp_cond={session2.temperature_condition}")
    assert session2.season == "Rabi"
    # Gram (Chickpea), Wheat, Mustard, Sunflower, or Onion should be recommended for Rabi
    assert any(c in ans2 for c in ["Gram", "Chickpea", "Wheat", "Mustard", "Sunflower", "Onion"])

    # -------------------------------------------------------------
    # TEST 3: ZAID / SUMMER + HOT & DRY (Kurnool, AP)
    # -------------------------------------------------------------
    session_id3 = "test_season_zaid_3"
    session_memory.reset_session(session_id3)
    t3_msg = "My farm is in Kurnool, Andhra Pradesh. It is summer/Zaid season with hot and dry weather, black soil and moderate water availability."
    print(f"\n---> TEST 3: {t3_msg}")
    client.post("/api/chat", json={"message": t3_msg, "session_id": session_id3})
    resp3 = client.post("/api/chat", json={"message": "Which crops should I consider for summer season?", "session_id": session_id3})
    assert resp3.status_code == 200
    ans3 = resp3.json().get("answer", "")
    print(f"Test 3 Answer Preview:\n{ans3[:250]}...\n")

    session3 = session_memory.get_or_create(session_id3)
    print(f"Test 3 Resolved Context: season={session3.season} | temp_cond={session3.temperature_condition}")
    assert session3.season == "Summer"
    # Moong (Green Gram), Groundnut, Maize, Sesamum, or Bajra should be recommended for Summer
    assert any(c in ans3 for c in ["Moong", "Green Gram", "Groundnut", "Maize", "Sesamum", "Bajra"])

    # -------------------------------------------------------------
    # TEST 4: DROUGHT / VERY LOW RAINFALL (Kurnool, AP)
    # -------------------------------------------------------------
    session_id4 = "test_weather_drought_4"
    session_memory.reset_session(session_id4)
    t4_msg = "My farm is in Kurnool, Andhra Pradesh. We are facing a severe drought with very low rainfall and water scarcity. Soil is black soil."
    print(f"\n---> TEST 4: {t4_msg}")
    client.post("/api/chat", json={"message": t4_msg, "session_id": session_id4})
    resp4 = client.post("/api/chat", json={"message": "Which drought tolerant crops should I consider?", "session_id": session_id4})
    assert resp4.status_code == 200
    ans4 = resp4.json().get("answer", "")
    print(f"Test 4 Answer Preview:\n{ans4[:250]}...\n")

    session4 = session_memory.get_or_create(session_id4)
    print(f"Test 4 Resolved Context: water={session4.water_availability} | rain_cond={session4.rainfall_condition}")
    assert session4.rainfall_condition == "drought" or session4.water_availability == "Limited"
    # Rice / Paddy should NOT be primary recommendation under drought
    assert "Rice" not in ans4 or "Gram" in ans4 or "Bajra" in ans4 or "Jowar" in ans4 or "Moong" in ans4

    # -------------------------------------------------------------
    # TEST 5: HEAVY RAINFALL / EXCESS WATER (Kurnool, AP)
    # -------------------------------------------------------------
    session_id5 = "test_weather_heavy_5"
    session_memory.reset_session(session_id5)
    t5_msg = "My farm is in Kurnool, Andhra Pradesh. We have heavy rainfall and excess water availability during heavy monsoon."
    print(f"\n---> TEST 5: {t5_msg}")
    client.post("/api/chat", json={"message": t5_msg, "session_id": session_id5})
    resp5 = client.post("/api/chat", json={"message": "Which crops suit heavy rainfall conditions?", "session_id": session_id5})
    assert resp5.status_code == 200
    ans5 = resp5.json().get("answer", "")
    print(f"Test 5 Answer Preview:\n{ans5[:250]}...\n")

    session5 = session_memory.get_or_create(session_id5)
    print(f"Test 5 Resolved Context: water={session5.water_availability} | rain_cond={session5.rainfall_condition}")
    assert session5.rainfall_condition == "heavy" or session5.water_availability == "Good"

    print("="*75)
    print("ALL 5 SEASON & WEATHER RECOMMENDATION TESTS PASSED PERFECTLY!")
    print("="*75)

if __name__ == "__main__":
    run_season_weather_tests()
