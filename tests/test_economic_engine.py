"""
Unit Test Suite for Phase 3 Economic Engine (EconomicEngine).
Verifies deterministic economic metrics calculation, unit conversions, missing data handling,
provenance metadata integrity, MSP & Mandi price labeling, no guaranteed profit wording,
AgriculturalEngine score pass-through, and multi-crop calculations.
"""

import pytest
import json
from backend.app.ml.economic_engine import economic_engine, EconomicEngine


def test_1_production_calculation():
    """1: Verify production_quintals = yield_quintals_per_acre * farm_size_acres."""
    res = economic_engine.calculate_crop_economics(
        crop="Cotton",
        farm_size_acres=5.0,
        yield_quintals_per_acre=8.0,
        price_inr_per_quintal=7000.0,
        cultivation_cost_inr_per_acre=25000.0
    )
    assert res["status"] == "success"
    # 8.0 q/acre * 5.0 acres = 40.0 quintals
    assert res["economic_metrics"]["production_quintals"] == 40.0


def test_2_revenue_calculation():
    """2: Verify gross_revenue = production_quintals * price_inr_per_quintal."""
    res = economic_engine.calculate_crop_economics(
        crop="Wheat",
        farm_size_acres=2.0,
        yield_quintals_per_acre=15.0,
        price_inr_per_quintal=2275.0,
        cultivation_cost_inr_per_acre=18000.0
    )
    # Production = 30 quintals; Gross revenue = 30 * 2275 = 68250.0
    assert res["economic_metrics"]["gross_revenue_inr"] == 68250.0


def test_3_cost_calculation():
    """3: Verify total_cost = cultivation_cost_inr_per_acre * farm_size_acres."""
    res = economic_engine.calculate_crop_economics(
        crop="Rice",
        farm_size_acres=4.0,
        yield_quintals_per_acre=18.0,
        price_inr_per_quintal=2300.0,
        cultivation_cost_inr_per_acre=22000.0
    )
    # Total cost = 4.0 * 22000 = 88000.0
    assert res["economic_metrics"]["total_cultivation_cost_inr"] == 88000.0


def test_4_net_estimate_calculation():
    """4: Verify net_estimate = gross_revenue - total_cost."""
    res = economic_engine.calculate_crop_economics(
        crop="Gram (Chickpea)",
        farm_size_acres=3.0,
        yield_quintals_per_acre=6.0,
        price_inr_per_quintal=5440.0,
        cultivation_cost_inr_per_acre=15000.0
    )
    # Prod = 18 q; Rev = 18 * 5440 = 97920; Cost = 3 * 15000 = 45000; Net = 52920
    assert res["economic_metrics"]["estimated_net_return_inr"] == 52920.0


def test_5_gross_margin_calculation():
    """5: Verify gross_margin_pct = ((gross_revenue - total_cost) / gross_revenue) * 100."""
    res = economic_engine.calculate_crop_economics(
        crop="Groundnut",
        farm_size_acres=2.0,
        yield_quintals_per_acre=10.0,
        price_inr_per_quintal=6783.0,
        cultivation_cost_inr_per_acre=25000.0
    )
    # Prod = 20 q; Rev = 135660; Cost = 50000; Net = 85660; GM% = 85660 / 135660 * 100 = 63.14%
    assert res["economic_metrics"]["gross_margin_pct"] == 63.14


def test_6_break_even_price_calculation():
    """6: Verify break_even_price = total_cost / production_quintals."""
    res = economic_engine.calculate_crop_economics(
        crop="Maize",
        farm_size_acres=2.5,
        yield_quintals_per_acre=12.0,
        price_inr_per_quintal=2225.0,
        cultivation_cost_inr_per_acre=18000.0
    )
    # Cost = 45000; Prod = 30; Break-even price = 45000 / 30 = 1500.0
    assert res["economic_metrics"]["break_even_price_inr_per_quintal"] == 1500.0


def test_7_roi_calculation():
    """7: Verify ROI = (net_estimate / total_cost) * 100."""
    res = economic_engine.calculate_crop_economics(
        crop="Mustard",
        farm_size_acres=2.0,
        yield_quintals_per_acre=7.0,
        price_inr_per_quintal=5650.0,
        cultivation_cost_inr_per_acre=16000.0
    )
    # Cost = 32000; Rev = 79100; Net = 47100; ROI% = 47100 / 32000 * 100 = 147.19%
    assert res["economic_metrics"]["roi_pct"] == 147.19


def test_8_hectare_to_acre_conversion():
    """8: Verify hectare/acre unit conversion constant."""
    # 1 hectare = 2.47105 acres
    q_per_acre = EconomicEngine.convert_yield_to_quintals_per_acre(yield_tonnes_per_ha=1.0)
    # 1 tonne/ha = 10 quintals / 2.47105 acres ≈ 4.04686 quintals/acre
    assert pytest.approx(q_per_acre, 0.001) == 4.04686


def test_9_tonne_to_quintal_conversion():
    """9: Verify yield conversion from tonnes/ha to quintals/acre in calculation."""
    res = economic_engine.calculate_crop_economics(
        crop="Sugarcane",
        farm_size_acres=1.0,
        yield_tonnes_per_ha=70.0,
        price_inr_per_quintal=315.0,
        cultivation_cost_inr_per_acre=45000.0
    )
    # 70 t/ha * 4.04686 = 283.28 quintals/acre
    assert res["status"] == "success"
    assert pytest.approx(res["provenance"]["yield"]["value"], 0.1) == 283.28


def test_10_missing_yield_handling():
    """10: Test handling when yield is missing."""
    res = economic_engine.calculate_crop_economics(
        crop="Cotton",
        farm_size_acres=3.0,
        yield_quintals_per_acre=None,
        price_inr_per_quintal=7000.0,
        cultivation_cost_inr_per_acre=25000.0
    )
    assert res["status"] == "partially_available"
    assert "yield" in res["missing_fields"]
    assert res["economic_metrics"] is None


def test_11_missing_price_handling():
    """11: Test handling when price is missing."""
    res = economic_engine.calculate_crop_economics(
        crop="Jute",
        farm_size_acres=2.0,
        yield_quintals_per_acre=10.0,
        price_inr_per_quintal=None,
        cultivation_cost_inr_per_acre=20000.0
    )
    assert res["status"] == "partially_available"
    assert "price" in res["missing_fields"]
    assert res["economic_metrics"] is None


def test_12_missing_cost_handling():
    """12: Test handling when cost is missing."""
    res = economic_engine.calculate_crop_economics(
        crop="Soyabean",
        farm_size_acres=4.0,
        yield_quintals_per_acre=6.0,
        price_inr_per_quintal=4892.0,
        cultivation_cost_inr_per_acre=None
    )
    assert res["status"] == "partially_available"
    assert "cost" in res["missing_fields"]
    assert res["economic_metrics"] is None


def test_13_zero_acreage_handling():
    """13: Test zero acreage handling."""
    res = economic_engine.calculate_crop_economics(
        crop="Wheat",
        farm_size_acres=0.0,
        yield_quintals_per_acre=15.0,
        price_inr_per_quintal=2275.0,
        cultivation_cost_inr_per_acre=18000.0
    )
    assert res["status"] == "invalid_input"
    assert res["economic_metrics"] is None
    assert "greater than zero" in res["error"]


def test_14_negative_input_rejection():
    """14: Test rejection of negative inputs."""
    res_neg_acre = economic_engine.calculate_crop_economics(
        crop="Wheat",
        farm_size_acres=-2.0,
        yield_quintals_per_acre=15.0,
        price_inr_per_quintal=2275.0,
        cultivation_cost_inr_per_acre=18000.0
    )
    assert res_neg_acre["status"] == "invalid_input"

    res_neg_price = economic_engine.calculate_crop_economics(
        crop="Wheat",
        farm_size_acres=2.0,
        yield_quintals_per_acre=15.0,
        price_inr_per_quintal=-500.0,
        cultivation_cost_inr_per_acre=18000.0
    )
    assert res_neg_price["status"] == "invalid_input"


def test_15_historical_yield_provenance():
    """15: Test that historical yield provenance data_type remains 'historical'."""
    res = economic_engine.calculate_crop_economics(
        crop="Pigeon Pea",
        farm_size_acres=2.0,
        yield_quintals_per_acre=5.0,
        price_inr_per_quintal=7550.0,
        cultivation_cost_inr_per_acre=20000.0,
        yield_data_type="historical"
    )
    assert res["provenance"]["yield"]["data_type"] == "historical"
    assert "predicted" not in res["provenance"]["yield"]["data_type"]
    assert "expected current" not in res["provenance"]["yield"]["data_type"]


def test_16_msp_price_basis_labeling():
    """16: Test MSP price-basis labeling."""
    res = economic_engine.calculate_crop_economics(
        crop="Pigeon Pea",
        farm_size_acres=2.0,
        yield_quintals_per_acre=5.0,
        price_inr_per_quintal=7550.0,
        cultivation_cost_inr_per_acre=20000.0,
        price_data_type="official"
    )
    assert res["provenance"]["price"]["price_basis"] == "MSP reference"
    assert res["provenance"]["price"]["data_type"] == "official"


def test_17_live_mandi_price_basis_labeling():
    """17: Test Live Mandi price-basis labeling."""
    res = economic_engine.calculate_crop_economics(
        crop="Cotton",
        farm_size_acres=3.0,
        yield_quintals_per_acre=8.0,
        price_inr_per_quintal=7200.0,
        cultivation_cost_inr_per_acre=25000.0,
        price_data_type="live"
    )
    assert res["provenance"]["price"]["price_basis"] == "Mandi modal price"
    assert res["provenance"]["price"]["data_type"] == "live"


def test_18_cached_mandi_price_basis_labeling():
    """18: Test Cached Mandi price-basis labeling."""
    res = economic_engine.calculate_crop_economics(
        crop="Cotton",
        farm_size_acres=3.0,
        yield_quintals_per_acre=8.0,
        price_inr_per_quintal=7150.0,
        cultivation_cost_inr_per_acre=25000.0,
        price_data_type="cached"
    )
    assert res["provenance"]["price"]["price_basis"] == "Mandi modal price"
    assert res["provenance"]["price"]["data_type"] == "cached"


def test_19_no_guaranteed_profit_wording():
    """19: Test that no 'guaranteed profit' wording exists in returned schemas or disclaimer."""
    res = economic_engine.calculate_crop_economics(
        crop="Maize",
        farm_size_acres=2.0,
        yield_quintals_per_acre=12.0,
        price_inr_per_quintal=2225.0,
        cultivation_cost_inr_per_acre=18000.0
    )
    raw_str = json.dumps(res).lower()
    assert "guaranteed profit" not in raw_str
    assert "guaranteed return" not in raw_str
    assert "estimated net return" in raw_str


def test_20_agricultural_engine_score_remains_unchanged():
    """20: Test that pass-through agronomic_score is preserved without modification."""
    ag_score = 88.75
    res = economic_engine.calculate_crop_economics(
        crop="Rice",
        farm_size_acres=2.0,
        yield_quintals_per_acre=16.0,
        price_inr_per_quintal=2300.0,
        cultivation_cost_inr_per_acre=22000.0,
        agronomic_score=ag_score
    )
    assert res["agronomic_score"] == 88.75


def test_21_multi_crop_economic_calculation():
    """21: Test calculating economics for multiple crops independently without ranking alteration."""
    crop_list = [
        {
            "crop": "Cotton",
            "agronomic_score": 85.0,
            "yield_quintals_per_acre": 8.0,
            "price_inr_per_quintal": 7100.0,
            "cultivation_cost_inr_per_acre": 25000.0
        },
        {
            "crop": "Gram (Chickpea)",
            "agronomic_score": 92.0,
            "yield_quintals_per_acre": 6.0,
            "price_inr_per_quintal": 5440.0,
            "cultivation_cost_inr_per_acre": 15000.0
        }
    ]

    res = economic_engine.calculate_multiple_crops(crop_list, farm_size_acres=3.0)
    assert len(res) == 2
    assert res[0]["crop"] == "Cotton"
    assert res[0]["agronomic_score"] == 85.0
    assert res[0]["economic_metrics"]["estimated_net_return_inr"] == 95400.0

    assert res[1]["crop"] == "Gram (Chickpea)"
    assert res[1]["agronomic_score"] == 92.0
    assert res[1]["economic_metrics"]["estimated_net_return_inr"] == 52920.0
