"""
Regional Context Resolution & Dynamic Precedence Benchmark Test Script for KrishiMitra AI.
Verifies all 6 regional state/district test cases and same-location attribute update test.
"""

import sys
import os
import json
import logging
import asyncio

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from starlette.testclient import TestClient
from backend.main import app
from backend.app.core.session_memory import session_memory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = TestClient(app)

def run_regional_benchmarks():
    print("=" * 70)
    print("REGIONAL CONTEXT RESOLUTION & DYNAMIC PRECEDENCE TEST SUITE")
    print("=" * 70)

    session_id = "test_regional_session_999"
    session_memory.reset_session(session_id)

    # -------------------------------------------------------------
    # TEST 1 — ANDHRA PRADESH
    # -------------------------------------------------------------
    print("\n--- TEST 1: ANDHRA PRADESH (Kurnool) ---")
    r1 = client.post("/api/chat", json={
        "message": "My farm is in Kurnool, Andhra Pradesh. I have black soil and moderate water availability.",
        "session_id": session_id
    })
    print(f"Turn 1 Statement Status: {r1.status_code}")
    print(f"Turn 1 Response: {r1.json().get('answer')[:120]}...")

    r1_followup = client.post("/api/chat", json={
        "message": "What crop should I consider?",
        "session_id": session_id
    })
    ans1 = r1_followup.json().get("answer", "")
    print(f"Turn 2 Recommendation Status: {r1_followup.status_code}")
    print(f"Turn 2 Answer Preview: {ans1[:180]}...")
    
    sess = session_memory.get_or_create(session_id)
    print(f"Session Memory State after Test 1: state={sess.state}, district={sess.district}, soil={sess.soil_type}, water={sess.water_availability}")
    
    assert sess.state == "Andhra Pradesh", f"Expected Andhra Pradesh, got {sess.state}"
    assert sess.district == "Kurnool", f"Expected Kurnool, got {sess.district}"

    # -------------------------------------------------------------
    # TEST 2 — PUNJAB
    # -------------------------------------------------------------
    print("\n--- TEST 2: PUNJAB (Ludhiana) ---")
    r2 = client.post("/api/chat", json={
        "message": "My farm is in Ludhiana, Punjab. I have fertile loamy soil and good irrigation availability. Which Kharif crops should I consider?",
        "session_id": session_id
    })
    ans2 = r2.json().get("answer", "")
    print(f"Test 2 Status: {r2.status_code}")
    print(f"Test 2 Answer Preview: {ans2[:200]}...")

    sess = session_memory.get_or_create(session_id)
    print(f"Session Memory State after Test 2: state={sess.state}, district={sess.district}, soil={sess.soil_type}, water={sess.water_availability}")

    assert sess.state == "Punjab", f"Expected Punjab, got {sess.state}"
    assert sess.district == "Ludhiana", f"Expected Ludhiana, got {sess.district}"
    assert "Kurnool" not in ans2, "ERROR: Stale Kurnool location leaked into Punjab answer!"
    assert "Black Soil" not in str(sess.soil_type), "ERROR: Stale Black Soil leaked into Punjab context!"

    # -------------------------------------------------------------
    # TEST 3 — RAJASTHAN
    # -------------------------------------------------------------
    print("\n--- TEST 3: RAJASTHAN (Sri Ganganagar) ---")
    r3 = client.post("/api/chat", json={
        "message": "My farm is in Sri Ganganagar, Rajasthan. I have sandy/loamy soil and limited water availability. Which Kharif crops should I consider?",
        "session_id": session_id
    })
    ans3 = r3.json().get("answer", "")
    print(f"Test 3 Status: {r3.status_code}")
    print(f"Test 3 Answer Preview: {ans3[:200]}...")

    sess = session_memory.get_or_create(session_id)
    print(f"Session Memory State after Test 3: state={sess.state}, district={sess.district}, soil={sess.soil_type}, water={sess.water_availability}")

    assert sess.state == "Rajasthan", f"Expected Rajasthan, got {sess.state}"
    assert sess.district == "Ganganagar", f"Expected Ganganagar, got {sess.district}"
    assert "Ludhiana" not in ans3 and "Kurnool" not in ans3, "ERROR: Stale previous locations leaked into Rajasthan answer!"

    # -------------------------------------------------------------
    # TEST 4 — MAHARASHTRA
    # -------------------------------------------------------------
    print("\n--- TEST 4: MAHARASHTRA (Vidarbha) ---")
    r4 = client.post("/api/chat", json={
        "message": "My farm is in Vidarbha, Maharashtra. I have black cotton soil and rainfed farming. Which Kharif crops should I consider?",
        "session_id": session_id
    })
    ans4 = r4.json().get("answer", "")
    print(f"Test 4 Status: {r4.status_code}")
    print(f"Test 4 Answer Preview: {ans4[:200]}...")

    sess = session_memory.get_or_create(session_id)
    print(f"Session Memory State after Test 4: state={sess.state}, district={sess.district}, soil={sess.soil_type}, irrigation={sess.irrigation_type}")

    assert sess.state == "Maharashtra", f"Expected Maharashtra, got {sess.state}"
    assert "Ganganagar" not in ans4 and "Punjab" not in ans4, "ERROR: Stale locations leaked into Maharashtra answer!"

    # -------------------------------------------------------------
    # TEST 5 — KERALA
    # -------------------------------------------------------------
    print("\n--- TEST 5: KERALA (Palakkad) ---")
    r5 = client.post("/api/chat", json={
        "message": "My farm is in Palakkad, Kerala. I have laterite soil and high rainfall. Which monsoon crops should I consider?",
        "session_id": session_id
    })
    ans5 = r5.json().get("answer", "")
    print(f"Test 5 Status: {r5.status_code}")
    print(f"Test 5 Answer Preview: {ans5[:200]}...")

    sess = session_memory.get_or_create(session_id)
    print(f"Session Memory State after Test 5: state={sess.state}, district={sess.district}, soil={sess.soil_type}")

    assert sess.state == "Kerala", f"Expected Kerala, got {sess.state}"
    assert sess.district == "Palakkad", f"Expected Palakkad, got {sess.district}"

    # -------------------------------------------------------------
    # TEST 6 — TELANGANA
    # -------------------------------------------------------------
    print("\n--- TEST 6: TELANGANA (Warangal) ---")
    r6 = client.post("/api/chat", json={
        "message": "My farm is in Warangal, Telangana. I have red soil and limited irrigation. Which Kharif crops should I consider?",
        "session_id": session_id
    })
    ans6 = r6.json().get("answer", "")
    print(f"Test 6 Status: {r6.status_code}")
    print(f"Test 6 Answer Preview: {ans6[:200]}...")

    sess = session_memory.get_or_create(session_id)
    print(f"Session Memory State after Test 6: state={sess.state}, district={sess.district}, soil={sess.soil_type}, water={sess.water_availability}")

    assert sess.state == "Telangana", f"Expected Telangana, got {sess.state}"
    assert sess.district == "Warangal", f"Expected Warangal, got {sess.district}"

    # -------------------------------------------------------------
    # SAME LOCATION, CHANGING ONE ATTRIBUTE TEST
    # -------------------------------------------------------------
    print("\n--- SAME LOCATION ATTRIBUTE UPDATE TEST ---")
    same_sess_id = "test_same_loc_session"
    session_memory.reset_session(same_sess_id)

    # Step 1: Kurnool + Black Soil + Moderate Water
    client.post("/api/chat", json={
        "message": "My farm is in Kurnool, Andhra Pradesh. I have black soil and moderate water availability.",
        "session_id": same_sess_id
    })
    s_obj = session_memory.get_or_create(same_sess_id)
    print(f"Step 1 Context: location={s_obj.district}, {s_obj.state} | soil={s_obj.soil_type} | water={s_obj.water_availability}")
    assert s_obj.district == "Kurnool" and s_obj.water_availability == "Moderate"

    # Step 2: Update water only ("My Kurnool farm now has very limited water.")
    client.post("/api/chat", json={
        "message": "My Kurnool farm now has very limited water.",
        "session_id": same_sess_id
    })
    s_obj = session_memory.get_or_create(same_sess_id)
    print(f"Step 2 Context: location={s_obj.district}, {s_obj.state} | soil={s_obj.soil_type} | water={s_obj.water_availability}")
    assert s_obj.district == "Kurnool", "Location should remain Kurnool"
    assert "Black Soil" in s_obj.soil_type, "Soil type should remain Black Soil"
    assert s_obj.water_availability == "Limited", f"Water availability should be updated to Limited, got {s_obj.water_availability}"

    # Step 3: Add irrigation ("I have installed drip irrigation.")
    client.post("/api/chat", json={
        "message": "I have installed drip irrigation.",
        "session_id": same_sess_id
    })
    s_obj = session_memory.get_or_create(same_sess_id)
    print(f"Step 3 Context: location={s_obj.district}, {s_obj.state} | soil={s_obj.soil_type} | water={s_obj.water_availability} | irrigation={s_obj.irrigation_type}")
    assert s_obj.district == "Kurnool", "Location should remain Kurnool"
    assert s_obj.water_availability == "Limited", "Water availability should remain Limited"
    assert s_obj.irrigation_type == "Drip Irrigation", f"Irrigation should be Drip Irrigation, got {s_obj.irrigation_type}"

    print("\n" + "=" * 70)
    print("ALL 6 REGIONAL TESTS AND SAME-LOCATION ATTRIBUTE TESTS PASSED PERFECTLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_regional_benchmarks()
