"""
Data Quality Hardening Validation Test Suite for Phase 1 Economic Data Foundation.
Verifies:
1. MSP year consistency (explicit 2024-25 year tags, no mislabeling as current or fake future years)
2. Cost metric clarity (explicit metric: "A2+FL", unit: "INR/acre")
3. Historical yield labeling (data_type: "historical", 1997-2015 historical district records)
4. Profit calculation safety disclaimer presence
5. Source traceability (source, source_url, year, unit, data_type)
6. Null MSP handling for non-MSP crops (no guessed fallback prices)
7. Crop alias uniqueness & no duplicate/ambiguous mappings
8. Database table creation
"""

import pytest
import os
import json
from backend.app.services.economic_service import economic_service, EconomicService


def test_crop_economics_dataset_exists_and_loads():
    """Verify crop_economics.json exists and contains 28 supported crops."""
    path = os.path.join("data", "processed", "crop_economics.json")
    assert os.path.exists(path), f"File {path} does not exist"
    
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    assert len(data) >= 28, f"Expected at least 28 crops, found {len(data)}"


def test_crop_name_normalization_and_aliases():
    """Test crop-name crosswalk normalization from commodity aliases to canonical crop names."""
    # Test Arhar/Tur aliases
    assert economic_service.normalize_crop_name("Arhar") == "Arhar/Tur (Pigeon Pea)"
    assert economic_service.normalize_crop_name("Tur") == "Arhar/Tur (Pigeon Pea)"
    assert economic_service.normalize_crop_name("Red Gram") == "Arhar/Tur (Pigeon Pea)"
    assert economic_service.normalize_crop_name("Arhar (Tur/Red Gram)") == "Arhar/Tur (Pigeon Pea)"

    # Test Cotton & Wheat & Paddy & Gram
    assert economic_service.normalize_crop_name("Kapas") == "Cotton"
    assert economic_service.normalize_crop_name("Gehun") == "Wheat"
    assert economic_service.normalize_crop_name("Paddy (Dhan)") == "Rice"
    assert economic_service.normalize_crop_name("Chana") == "Gram (Chickpea)"


def test_alias_uniqueness_and_no_conflicts():
    """Verify every commodity alias maps to exactly ONE canonical crop name without ambiguity."""
    all_recs = economic_service.get_all_records()
    alias_map = {}
    conflicts = []

    for crop_name, rec in all_recs.items():
        aliases = rec.get("commodity_aliases", [])
        for alias in aliases:
            a_clean = alias.lower().strip()
            if a_clean in alias_map and alias_map[a_clean] != crop_name:
                conflicts.append((alias, alias_map[a_clean], crop_name))
            else:
                alias_map[a_clean] = crop_name

    assert len(conflicts) == 0, f"Found conflicting commodity aliases: {conflicts}"


def test_msp_year_consistency_and_validity():
    """Verify MSP records explicitly state year '2024-25' and do not fabricate unnotified future years."""
    all_recs = economic_service.get_all_records()
    
    for crop_name, rec in all_recs.items():
        msp = rec.get("msp_information")
        if msp is not None:
            assert msp["year"] == "2024-25", f"MSP year for {crop_name} must be 2024-25, found {msp['year']}"
            assert msp["data_type"] == "official"
            assert "source" in msp and msp["source"]
            assert "source_url" in msp and msp["source_url"]
            assert msp["unit"] == "INR/quintal"
            assert isinstance(msp["value"], (int, float))


def test_cost_metric_clarity_a2_fl():
    """Verify cost of cultivation explicitly stores metric 'A2+FL' and unit 'INR/acre'."""
    all_recs = economic_service.get_all_records()
    
    for crop_name, rec in all_recs.items():
        cost = rec.get("cost_of_cultivation")
        assert cost is not None, f"Cost of cultivation missing for {crop_name}"
        assert cost["metric"] == "A2+FL", f"Cost metric for {crop_name} must be A2+FL"
        assert cost["unit"] == "INR/acre"
        assert cost["year"] == "2024-25"
        assert cost["data_type"] == "official"
        assert "source" in cost and cost["source"]
        assert "source_url" in cost and cost["source_url"]


def test_historical_yield_labeling_and_disclaimer():
    """Verify historical yield benchmarks are explicitly tagged data_type='historical' with district records year."""
    all_recs = economic_service.get_all_records()
    
    for crop_name, rec in all_recs.items():
        yb = rec.get("yield_benchmark_reference")
        assert yb is not None, f"Yield benchmark reference missing for {crop_name}"
        assert yb["data_type"] == "historical"
        assert yb["year"] == "1997-2015 historical district records"
        assert "disclaimer" in yb


def test_profit_calculation_disclaimer_present():
    """Verify profit calculation disclaimer is attached to every economic record to prevent misleading claims."""
    all_recs = economic_service.get_all_records()
    
    for crop_name, rec in all_recs.items():
        assert "profit_calculation_disclaimer" in rec
        assert "illustrative estimates" in rec["profit_calculation_disclaimer"]


def test_unknown_crop_handling():
    """Test that querying an unknown crop returns None without inventing fake data."""
    unknown = economic_service.get_crop_economics("DragonFruitX")
    assert unknown is None, "Unknown crop must return None"

    norm_unknown = economic_service.normalize_crop_name("NonExistentCrop123")
    assert norm_unknown is None, "Unknown crop normalization must return None"


def test_missing_economic_data_handling():
    """Test that non-MSP crops explicitly have None for msp_information (no fake MSP prices)."""
    non_msp_crops = [
        "Onion", "Potato", "Dry chillies", "Turmeric", "Sweet potato",
        "Linseed", "Horse-gram", "Small millets", "Peas & beans (Pulses)", "Other Kharif pulses"
    ]

    for c in non_msp_crops:
        rec = economic_service.get_crop_economics(c)
        assert rec is not None, f"Record for non-MSP crop {c} must exist"
        assert rec["msp_information"] is None, f"{c} has no MSP and msp_information must be None"


def test_database_tables_exist():
    """Verify market_price_cache and crop_economic_benchmarks tables exist in krishimitra.db."""
    from backend.app.core.database import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='market_price_cache'")
    assert cursor.fetchone() is not None, "market_price_cache table must exist"

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='crop_economic_benchmarks'")
    assert cursor.fetchone() is not None, "crop_economic_benchmarks table must exist"
    
    conn.close()
