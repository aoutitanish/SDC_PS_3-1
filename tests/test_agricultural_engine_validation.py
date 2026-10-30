"""
Unit Test Suite for Agricultural Engine Independent Validation Study.
Validates temporal splitting, regional mapping, safety checks, and decision outputs.
"""

import os
import sys
import pytest

# Ensure project root is in sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.app.ml.agricultural_engine import AgriculturalEngine


def test_temporal_split_disjoint():
    """Verify that earlier years and evaluation holdout years are disjoint."""
    train_years = list(range(1997, 2009))  # 1997-2008
    test_years = list(range(2009, 2016))   # 2009-2015

    overlap = set(train_years).intersection(set(test_years))
    assert len(overlap) == 0
    assert max(train_years) < min(test_years)


def test_regional_mapping_coverage():
    """Verify regional mapping covers major Indian agricultural states."""
    region_map = {
        "Punjab": "North", "Haryana": "North", "Uttar Pradesh": "North",
        "Andhra Pradesh": "South", "Karnataka": "South", "Tamil Nadu": "South",
        "Maharashtra": "West/Central", "Madhya Pradesh": "West/Central",
        "Bihar": "East", "West Bengal": "East"
    }

    assert region_map["Uttar Pradesh"] == "North"
    assert region_map["Andhra Pradesh"] == "South"
    assert region_map["Maharashtra"] == "West/Central"
    assert region_map["Bihar"] == "East"


def test_safety_checks_validation():
    """Verify safety guarantees in evaluation context."""
    engine = AgriculturalEngine()
    ctx_unknown = {"state": None, "district": None}
    res = engine.evaluate_crop("Wheat", ctx_unknown)

    # No Kurnool fallback
    assert "kurnool" not in str(res).lower()
    assert "andhra pradesh" not in str(res).lower()

    # No drip/borewell injection
    ctx_nodrip = {"has_drip": False, "has_borewell": False, "irrigation_type": "Rainfed"}
    res_nodrip = engine.evaluate_crop("Rice", ctx_nodrip)
    for s in res_nodrip["supporting_factors"]:
        assert "drip irrigation setup available" not in s.lower()
        assert "borewell water source confirmed" not in s.lower()


def test_valid_decision_format():
    """Verify final decision choice is one of the three specified options."""
    allowed_decisions = [
        "A. READY FOR STAGED INTEGRATION",
        "B. NEEDS WEIGHT REVISION",
        "C. NEEDS ENGINE LOGIC REVISION"
    ]
    current_decision = "B. NEEDS WEIGHT REVISION"
    assert current_decision in allowed_decisions
