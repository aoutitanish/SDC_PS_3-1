"""
Test Suite for Intent Priority Hierarchy & Semantic Phrase-Aware Matching in FarmerHelp
Verifies that intent classification correctly prioritizes:
1. Explicit context/profile queries (farm_context_query)
2. Existing recommendation explanation queries (crop_explanation / recommendation_explanation)
3. Explicit negative recommendation instructions
4. Actual crop recommendation queries (crop_recommendation)
5. Seasonal advice & general agriculture
"""

import os
import sys
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

from backend.app.services.intent_service import intent_service


def run_intent_tests():
    test_cases = [
        (
            "What exact factors from my current farm profile are being used to calculate my crop recommendation?",
            ["farm_context_query"],
            "Explicit context/profile query"
        ),
        (
            "What irrigation system and soil type are currently stored for my farm?",
            ["farm_context_query"],
            "Explicit context/profile query"
        ),
        (
            "Why was Maize recommended?",
            ["crop_explanation", "recommendation_explanation"],
            "Existing recommendation explanation query"
        ),
        (
            "Explain why the system selected Maize instead of Gram.",
            ["crop_explanation", "recommendation_explanation"],
            "Existing recommendation explanation query"
        ),
        (
            "Do not recommend a crop. Tell me the current farm factors.",
            ["farm_context_query"],
            "Explicit negative instruction overriding crop_recommendation"
        ),
        (
            "Which crop should I consider?",
            ["crop_recommendation"],
            "Actual crop recommendation request"
        ),
        (
            "What crop should I plant?",
            ["crop_recommendation"],
            "Actual crop recommendation request"
        ),
        (
            "Recommend a crop for my farm.",
            ["crop_recommendation"],
            "Actual crop recommendation request"
        ),
        (
            "Using only those current farm-profile and weather values, explain why the system selected Maize instead of Gram or Wheat.",
            ["crop_explanation", "recommendation_explanation"],
            "Complex explanation request"
        )
    ]

    print("\n" + "="*80)
    print("FARMERHELP INTENT PRIORITY HIERARCHY REGRESSION TEST")
    print("="*80 + "\n")

    passed_count = 0
    total_count = len(test_cases)

    for i, (query, expected_intents, category) in enumerate(test_cases, 1):
        detected = intent_service.detect_intent(query, has_prior_recommendation=True)
        is_pass = detected in expected_intents
        status = "PASSED" if is_pass else "FAILED"
        
        if is_pass:
            passed_count += 1

        print(f"[{status}] Test {i} ({category}):")
        print(f"  Query: \"{query}\"")
        print(f"  Detected Intent: {detected}")
        print(f"  Expected: {expected_intents}\n")

    print("="*80)
    print(f"SUMMARY: {passed_count}/{total_count} INTENT TESTS PASSED")
    print("="*80 + "\n")

    if passed_count != total_count:
        sys.exit(1)


if __name__ == "__main__":
    run_intent_tests()
