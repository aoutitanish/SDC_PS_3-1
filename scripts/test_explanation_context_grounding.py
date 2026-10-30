"""
Regression Test Suite for Explanation Context Grounding in FarmerHelp
Verifies that recommendation_explanation uses the EXACT context that produced
the stored recommendation result, without leaking stale irrigation terms (e.g. drip vs canal vs rainfed).
"""

import os
import sys
import json
import logging
from fastapi.testclient import TestClient

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.main import app

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

client = TestClient(app)


def run_explanation_grounding_tests():
    test_scenarios = [
        {
            "name": "Scenario 1: Ludhiana + Canal + Borewell + No Drip",
            "setup_query": "My farm is in Ludhiana, Punjab. I have alluvial soil, canal irrigation and a borewell, but no drip irrigation. It is Rabi season.",
            "exp_query": "Why was that crop recommended? Explain the factors that caused the existing recommendation. Do not make a new recommendation.",
            "forbidden_terms": ["drip irrigation", "micro-irrigation"],
            "required_terms": ["canal"]
        },
        {
            "name": "Scenario 2: Ludhiana + Drip + Borewell",
            "setup_query": "My farm is in Ludhiana, Punjab. I have alluvial soil, drip irrigation and a borewell. It is Rabi season.",
            "exp_query": "Why was that crop recommended? Explain the factors that caused the existing recommendation. Do not make a new recommendation.",
            "forbidden_terms": [],
            "required_terms": ["drip"]
        },
        {
            "name": "Scenario 3: Ganganagar + Limited Irrigation + No Borewell + No Drip",
            "setup_query": "My farm is in Sri Ganganagar, Rajasthan. I have sandy soil, limited water availability, no borewell and no drip irrigation.",
            "exp_query": "Why was that crop recommended? Explain the factors that caused the existing recommendation. Do not make a new recommendation.",
            "forbidden_terms": ["drip irrigation", "borewell"],
            "required_terms": []
        },
        {
            "name": "Scenario 4: Kurnool + Drip + Borewell",
            "setup_query": "My farm is in Kurnool, Andhra Pradesh. I have black soil, drip irrigation, a borewell and moderate water availability.",
            "exp_query": "Why was that crop recommended? Explain the factors that caused the existing recommendation. Do not make a new recommendation.",
            "forbidden_terms": [],
            "required_terms": ["drip"]
        }
    ]

    print("\n" + "="*80)
    print("FARMERHELP EXPLANATION CONTEXT GROUNDING REGRESSION TEST")
    print("="*80 + "\n")

    passed_count = 0
    total_count = len(test_scenarios)

    for i, sc in enumerate(test_scenarios, 1):
        session_id = f"test_exp_grounding_{i}"
        
        # Turn 1: Setup farm context & trigger recommendation
        resp1 = client.post("/api/chat", json={
            "message": sc["setup_query"],
            "session_id": session_id
        })
        assert resp1.status_code == 200, f"Turn 1 failed: {resp1.text}"

        # Ask for recommendation explicitly if turn 1 was info statement
        resp1_json = resp1.json()
        if resp1_json.get("intent") != "crop_recommendation":
            resp1_rec = client.post("/api/chat", json={
                "message": "Which crops should I consider?",
                "session_id": session_id
            })
            assert resp1_rec.status_code == 200

        # Turn 2: Request explanation
        resp2 = client.post("/api/chat", json={
            "message": sc["exp_query"],
            "session_id": session_id
        })
        assert resp2.status_code == 200, f"Turn 2 failed: {resp2.text}"

        data2 = resp2.json()
        answer = data2.get("answer", "")
        answer_lower = answer.lower()

        forbidden_found = [term for term in sc["forbidden_terms"] if term in answer_lower]
        required_missing = [term for term in sc["required_terms"] if term not in answer_lower]

        is_pass = (len(forbidden_found) == 0) and (len(required_missing) == 0)
        status = "PASSED" if is_pass else "FAILED"

        if is_pass:
            passed_count += 1

        print(f"[{status}] Test {i}: {sc['name']}")
        print(f"  Setup Query: \"{sc['setup_query']}\"")
        print(f"  Explanation Intent: {data2.get('intent')}")
        print(f"  Forbidden terms found: {forbidden_found}")
        print(f"  Required terms missing: {required_missing}")
        safe_preview = answer[:300].encode('ascii', 'ignore').decode('ascii')
        print(f"  Answer Preview:\n{safe_preview}...\n")

    print("="*80)
    print(f"SUMMARY: {passed_count}/{total_count} EXPLANATION GROUNDING TESTS PASSED")
    print("="*80 + "\n")

    if passed_count != total_count:
        sys.exit(1)


if __name__ == "__main__":
    run_explanation_grounding_tests()
