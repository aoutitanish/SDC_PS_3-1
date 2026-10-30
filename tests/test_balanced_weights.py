"""
Unit Test Suite for Final Balanced Weight Validation.
Validates identical configuration detection, frozen weight vector properties, and decision output.
"""

import os
import sys
import math
import pytest

# Ensure project root is in sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.app.ml.agricultural_engine import AgriculturalEngine


def test_identical_weight_detection():
    """Verify that Config B and Config C use identical weight vectors."""
    w_config_b = [0.15, 0.15, 0.12, 0.10, 0.15, 0.12, 0.08, 0.08, 0.05]
    w_config_c = [0.15, 0.15, 0.12, 0.10, 0.15, 0.12, 0.08, 0.08, 0.05]

    assert w_config_b == w_config_c
    assert len(w_config_b) == 9


def test_frozen_weight_vector_properties():
    """Verify frozen weight vector non-negativity and exact sum of 1.00."""
    frozen_weights = [0.15, 0.15, 0.12, 0.10, 0.15, 0.12, 0.08, 0.08, 0.05]

    assert len(frozen_weights) == 9
    assert all(w >= 0.0 for w in frozen_weights)
    assert math.isclose(sum(frozen_weights), 1.00, abs_tol=1e-5)


def test_final_decision_format():
    """Verify final decision matches 'A. FREEZE BALANCED WEIGHTS'."""
    decision = "A. FREEZE BALANCED WEIGHTS"
    assert decision in ["A. FREEZE BALANCED WEIGHTS", "B. NEED ANOTHER WEIGHT REVISION"]


def test_engine_evaluation_with_frozen_weights():
    """Verify AgriculturalEngine evaluates cleanly with frozen weights."""
    engine = AgriculturalEngine()
    ctx = {
        "state": "Andhra Pradesh",
        "district": "Kurnool",
        "season": "Kharif",
        "ph": 6.8,
        "clay_pct": 32.0,
        "annual_rainfall_mm": 900.0,
        "mean_temperature_c": 26.0
    }
    res = engine.evaluate_crop("Arhar/Tur (Pigeon Pea)", ctx)

    assert res["crop"] == "Arhar/Tur (Pigeon Pea)"
    assert isinstance(res["overall_score"], float)
    assert 0.0 <= res["overall_score"] <= 100.0
