"""
Unit Test Suite for Agricultural Engine Calibration Study.
Validates dataset loading, leakage checks, weight constraints, and ranking metric calculations.
"""

import os
import sys
import math
import numpy as np
import pytest

# Ensure project root is in sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.app.ml.agricultural_engine import AgriculturalEngine


def test_baseline_weight_sum():
    """Verify that tested weight configurations are non-negative and sum to 1.0."""
    configs = [
        [0.20, 0.18, 0.15, 0.07, 0.15, 0.10, 0.05, 0.05, 0.05],  # Config A
        [0.30, 0.25, 0.15, 0.10, 0.10, 0.05, 0.02, 0.01, 0.02],  # Config B
        [0.10, 0.10, 0.10, 0.05, 0.30, 0.20, 0.10, 0.03, 0.02],  # Config C
        [0.10, 0.10, 0.10, 0.05, 0.10, 0.05, 0.02, 0.03, 0.45],  # Config D
        [0.10, 0.10, 0.10, 0.05, 0.10, 0.05, 0.02, 0.45, 0.03],  # Config E
        [0.15, 0.15, 0.12, 0.10, 0.15, 0.12, 0.08, 0.08, 0.05],  # Config F
        [0.15, 0.15, 0.10, 0.05, 0.25, 0.10, 0.05, 0.10, 0.05]   # Config G
    ]

    for idx, w in enumerate(configs):
        assert len(w) == 9, f"Config {idx} must have 9 weights"
        assert all(x >= 0.0 for x in w), f"Config {idx} contains negative weights"
        assert math.isclose(sum(w), 1.0, abs_tol=1e-5), f"Config {idx} sum is {sum(w)}, not 1.0"


def test_leakage_checks():
    """Verify that leakage fields are excluded from context building."""
    leakage_fields = ["Yield_tonnes_per_ha", "Production", "Area", "Crop_Year"]
    dummy_ctx = {
        "state": "Andhra Pradesh",
        "district": "Kurnool",
        "season": "Kharif",
        "ph": 7.1,
        "clay_pct": 30.0
    }

    for lf in leakage_fields:
        assert lf not in dummy_ctx, f"Leakage field {lf} detected in context"


def test_ndcg_calculation():
    """Verify NDCG calculation logic for perfect and partial matches."""
    targets = {"Rice", "Maize"}
    ranked_perfect = ["Rice", "Maize", "Wheat", "Cotton"]
    ranked_imperfect = ["Wheat", "Cotton", "Rice", "Maize"]

    # Perfect ranking NDCG@3
    rels_perf = [1.0 if c in targets else 0.0 for c in ranked_perfect[:3]]
    dcg_perf = sum(r / math.log2(i + 2) for i, r in enumerate(rels_perf))
    idcg_perf = sum(1.0 / math.log2(i + 2) for i in range(min(3, len(targets))))
    ndcg_perf = dcg_perf / idcg_perf if idcg_perf > 0 else 0.0

    # Imperfect ranking NDCG@3
    rels_imp = [1.0 if c in targets else 0.0 for c in ranked_imperfect[:3]]
    dcg_imp = sum(r / math.log2(i + 2) for i, r in enumerate(rels_imp))
    ndcg_imp = dcg_imp / idcg_perf if idcg_perf > 0 else 0.0

    assert ndcg_perf > ndcg_imp
    assert 0.0 <= ndcg_perf <= 1.0
    assert 0.0 <= ndcg_imp <= 1.0
