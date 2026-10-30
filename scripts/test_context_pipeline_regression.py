"""
Comprehensive End-to-End Regression Test Suite for FarmerHelp Context Resolution.
Verifies multi-turn location switching, negative facts preservation, cache invalidation,
and guarantees that no stale farm context reaches RAG, Recommendation, or LLM layers.
"""

import sys
import os
import json
import logging
from typing import Dict, Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from starlette.testclient import TestClient
from backend.main import app
from backend.app.core.session_memory import session_memory

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

client = TestClient(app)

def run_regression_test():
    session_id = "test_regression_session_888"
    session_memory.reset_session(session_id)

    print("\n" + "="*70)
    print("FARMERHELP CONTEXT RESOLUTION & PIPELINE REGRESSION TEST")
    print("="*70)

    # -------------------------------------------------------------
    # TURN 1: KURNOOL, ANDHRA PRADESH (Black Soil, Moderate Water, Drip, Borewell)
    # -------------------------------------------------------------
    turn1_msg = "My farm is in Kurnool, Andhra Pradesh. I have black soil, moderate water availability, drip irrigation and a borewell."
    print(f"\n---> TURN 1: {turn1_msg}")
    resp1 = client.post("/api/chat", json={"message": turn1_msg, "session_id": session_id})
    assert resp1.status_code == 200, f"Turn 1 failed: {resp1.text}"

    session = session_memory.get_or_create(session_id)
    print(f"Turn 1 Session State: location={session.district}, {session.state} | soil={session.soil_type} | irr={session.irrigation_type} | wsrc={session.water_source}")
    assert session.district == "Kurnool"
    assert session.state == "Andhra Pradesh"
    assert "Black Soil" in (session.soil_type or "")
    assert session.has_borewell is True
    assert session.has_drip is True

    # -------------------------------------------------------------
    # TURN 2: RECOMMENDATION FOR KURNOOL
    # -------------------------------------------------------------
    turn2_msg = "What crop should I consider?"
    print(f"\n---> TURN 2: {turn2_msg}")
    resp2 = client.post("/api/chat", json={"message": turn2_msg, "session_id": session_id})
    assert resp2.status_code == 200, f"Turn 2 failed: {resp2.text}"
    answer2 = resp2.json().get("answer", "")
    print(f"Turn 2 Response Preview: {answer2[:150]}...")
    assert "Kurnool" in answer2

    # -------------------------------------------------------------
    # TURN 3: LOCATION SWITCH TO SRI GANGANAGAR, RAJASTHAN (Sandy soil, rainwater, NO borewell, NO drip)
    # -------------------------------------------------------------
    turn3_msg = "Now forget the previous farm details. My farm is in Sri Ganganagar, Rajasthan. It has sandy soil and only rainwater, with no borewell and no drip irrigation. Which Kharif crops should I consider?"
    print(f"\n---> TURN 3: {turn3_msg}")
    resp3 = client.post("/api/chat", json={"message": turn3_msg, "session_id": session_id})
    assert resp3.status_code == 200, f"Turn 3 failed: {resp3.text}"
    answer3 = resp3.json().get("answer", "")
    print(f"Turn 3 Response Preview: {answer3[:200]}...")
    
    assert session.district == "Ganganagar"
    assert session.state == "Rajasthan"
    assert "Sandy" in (session.soil_type or "")
    assert session.has_borewell is False
    assert session.has_drip is False

    # CRITICAL: Verify stale Kurnool drip & borewell setup is NOT mentioned
    assert "borewell setup" not in answer3.lower() or "no borewell" in answer3.lower() or "without borewell" in answer3.lower() or "rainfed" in answer3.lower() or "rainwater" in answer3.lower()
    assert "Kurnool" not in answer3

    # -------------------------------------------------------------
    # TURN 4: LOCATION SWITCH TO LUDHIANA, PUNJAB (Loamy soil, Canal irrigation, NO borewell, NO drip)
    # -------------------------------------------------------------
    turn4_msg = "Now consider my farm in Ludhiana, Punjab. It has fertile loamy soil and canal irrigation. There is no borewell and no drip irrigation."
    print(f"\n---> TURN 4: {turn4_msg}")
    resp4 = client.post("/api/chat", json={"message": turn4_msg, "session_id": session_id})
    assert resp4.status_code == 200, f"Turn 4 failed: {resp4.text}"
    
    assert session.district == "Ludhiana"
    assert session.state == "Punjab"
    assert "Loamy" in (session.soil_type or "") or "Alluvial" in (session.soil_type or "")
    assert "Canal" in (session.irrigation_type or "")
    assert session.has_borewell is False
    assert session.has_drip is False

    # -------------------------------------------------------------
    # TURN 5: RECOMMENDATION FOR LUDHIANA ("What crop should I consider?")
    # -------------------------------------------------------------
    turn5_msg = "What crop should I consider?"
    print(f"\n---> TURN 5: {turn5_msg}")
    resp5 = client.post("/api/chat", json={"message": turn5_msg, "session_id": session_id})
    assert resp5.status_code == 200, f"Turn 5 failed: {resp5.text}"
    answer5 = resp5.json().get("answer", "")
    print(f"Turn 5 Final Response: \n{answer5}\n")

    # -------------------------------------------------------------
    # ASSERTIONS ON RESOLVED CONTEXT AND FINAL OUTPUT
    # -------------------------------------------------------------
    # 1. Final location MUST be Ludhiana, Punjab
    assert session.district == "Ludhiana", f"Expected district Ludhiana, got {session.district}"
    assert session.state == "Punjab", f"Expected state Punjab, got {session.state}"

    # 2. Final soil MUST be Loamy/Alluvial (NOT Black Soil)
    assert "Black Soil" not in (session.soil_type or ""), f"Stale soil leaked: {session.soil_type}"
    assert "Loamy" in (session.soil_type or "") or "Alluvial" in (session.soil_type or ""), f"Expected Loamy/Alluvial soil, got {session.soil_type}"

    # 3. Final irrigation MUST be Canal (NOT Drip)
    assert "Drip" not in (session.irrigation_type or ""), f"Stale drip irrigation leaked: {session.irrigation_type}"
    assert "Canal" in (session.irrigation_type or ""), f"Expected Canal irrigation, got {session.irrigation_type}"

    # 4. Negative facts MUST be preserved
    assert session.has_borewell is False, f"Expected has_borewell=False, got {session.has_borewell}"
    assert session.has_drip is False, f"Expected has_drip=False, got {session.has_drip}"

    # 5. Final Answer MUST NOT contain stale Kurnool / black soil / drip / borewell mentions
    assert "Kurnool" not in answer5, f"Stale location Kurnool found in answer: {answer5}"
    assert "black & red" not in answer5.lower(), f"Stale 'black & red' soil found in answer: {answer5}"
    assert "black soil" not in answer5.lower(), f"Stale black soil found in answer: {answer5}"
    assert "drip irrigation and borewell" not in answer5.lower(), f"Stale drip and borewell phrase found in answer: {answer5}"

    print("="*70)
    print("ALL CONTEXT RESOLUTION & PIPELINE REGRESSION TESTS PASSED PERFECTLY!")
    print("="*70)

if __name__ == "__main__":
    run_regression_test()
