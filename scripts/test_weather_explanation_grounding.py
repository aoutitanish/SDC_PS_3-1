"""
Regression Test Suite for Weather-Aware Recommendation & Explanation Grounding
Verifies that recommendation and explanation text dynamically incorporate actual weather conditions:
1. Drought / low rainfall reasoning
2. Heavy rainfall / excess water reasoning
3. Normal rainfall baseline (no false drought/heavy claims)
"""

import os
import sys
import logging
from fastapi.testclient import TestClient

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.main import app

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

client = TestClient(app)


def run_weather_explanation_tests():
    test_scenarios = [
        {
            "name": "Test 1: Bangalore Rural + Severe Drought + Hot/Dry",
            "query": "My farm is in Bangalore Rural, Karnataka. It has red soil, drip irrigation and borewell. It is summer season with severe drought, very low rainfall and hot dry weather. Which crop should I consider?",
            "exp_query": "Why was that crop recommended? Explain the factors that caused the existing recommendation. Do not make a new recommendation.",
            "required_terms": ["drought", "low rainfall"],
            "forbidden_terms": ["heavy rainfall", "excess water"]
        },
        {
            "name": "Test 2: Bangalore Rural + Heavy Rainfall + Excess Water",
            "query": "My farm is in Bangalore Rural, Karnataka. It has red soil, drip irrigation and borewell. It is monsoon season with heavy rainfall and excess water. Which crop should I consider?",
            "exp_query": "Why was that crop recommended? Explain the factors that caused the existing recommendation. Do not make a new recommendation.",
            "required_terms": ["heavy rainfall", "excess water"],
            "forbidden_terms": ["drought", "low rainfall"]
        },
        {
            "name": "Test 3: Bangalore Rural + Normal Rainfall + Moderate Temperature",
            "query": "My farm is in Bangalore Rural, Karnataka. It has red soil, drip irrigation and borewell. It is Kharif season with normal rainfall and moderate temperature. Which crop should I consider?",
            "exp_query": "Why was that crop recommended? Explain the factors that caused the existing recommendation. Do not make a new recommendation.",
            "required_terms": [],
            "forbidden_terms": ["severe drought", "heavy rainfall"]
        }
    ]

    print("\n" + "="*80)
    print("FARMERHELP WEATHER-AWARE EXPLANATION GROUNDING REGRESSION TEST")
    print("="*80 + "\n")

    passed_count = 0
    total_count = len(test_scenarios)

    for i, sc in enumerate(test_scenarios, 1):
        session_id = f"test_weather_exp_{i}"

        # Turn 1: Recommendation request under weather condition
        resp1 = client.post("/api/chat", json={
            "message": sc["query"],
            "session_id": session_id
        })
        assert resp1.status_code == 200, f"Turn 1 failed: {resp1.text}"
        ans1 = resp1.json().get("answer", "").lower()

        # Turn 2: Explanation request
        resp2 = client.post("/api/chat", json={
            "message": sc["exp_query"],
            "session_id": session_id
        })
        assert resp2.status_code == 200, f"Turn 2 failed: {resp2.text}"
        ans2 = resp2.json().get("answer", "").lower()

        combined_text = ans1 + "\n" + ans2

        forbidden_found = [term for term in sc["forbidden_terms"] if term in combined_text]
        required_missing = [term for term in sc["required_terms"] if term not in combined_text]

        is_pass = (len(forbidden_found) == 0) and (len(required_missing) == 0)
        status = "PASSED" if is_pass else "FAILED"

        if is_pass:
            passed_count += 1

        print(f"[{status}] Test {i}: {sc['name']}")
        print(f"  Query: \"{sc['query']}\"")
        print(f"  Forbidden terms found: {forbidden_found}")
        print(f"  Required terms missing: {required_missing}")
        safe_preview = ans2[:300].encode('ascii', 'ignore').decode('ascii')
        print(f"  Explanation Preview:\n{safe_preview}...\n")

    print("="*80)
    print(f"SUMMARY: {passed_count}/{total_count} WEATHER EXPLANATION TESTS PASSED")
    print("="*80 + "\n")

    if passed_count != total_count:
        sys.exit(1)


if __name__ == "__main__":
    run_weather_explanation_tests()
