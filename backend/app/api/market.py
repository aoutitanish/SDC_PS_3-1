"""
Market Prices API Router for KrishiMitra AI.
Provides GET /api/market/prices endpoint for live & cached Mandi telemetry.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Query
from backend.app.services.market_service import market_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/market", tags=["Market Telemetry"])


@router.get("/prices")
async def get_market_prices_endpoint(
    crop: str = Query(..., description="Crop name or commodity alias"),
    state: Optional[str] = Query(None, description="State name"),
    district: Optional[str] = Query(None, description="District name")
):
    """
    Retrieves live or cached Mandi market price telemetry for a given crop and location.
    Returns safe structured 'unavailable' status when live API and cache have no records.
    NEVER invents prices or substitutes MSP for live mandi prices.
    """
    res = await market_service.get_market_prices(crop=crop, state=state, district=district)
    return res


@router.post("/economics")
async def calculate_economics_endpoint(payload: dict):
    """
    Calculates deterministic economic metrics using EconomicEngine.
    If explicit price/yield/cost are not passed, retrieves official reference benchmarks from EconomicService.
    Supports single crop or multi-crop batch array in 'crops' field.
    """
    from backend.app.ml.economic_engine import economic_engine
    from backend.app.services.economic_service import economic_service

    crops_list = payload.get("crops")
    farm_size_acres = float(payload.get("farm_size_acres", 1.0) or 1.0)

    if crops_list and isinstance(crops_list, list):
        # Batch multi-crop economics
        prepared_crops = []
        for item in crops_list:
            c_name = item.get("crop", "Unknown")
            econ_ref = economic_service.get_crop_economics(c_name) or {}
            
            # Extract defaults if not supplied
            p_val = item.get("price_inr_per_quintal")
            if p_val is None and "msp_information" in econ_ref:
                p_val = econ_ref["msp_information"].get("value")

            c_val = item.get("cultivation_cost_inr_per_acre")
            if c_val is None and "cost_of_cultivation" in econ_ref:
                c_val = econ_ref["cost_of_cultivation"].get("value")

            y_val = item.get("yield_quintals_per_acre")
            if y_val is None and "yield_benchmark_reference" in econ_ref:
                y_val = econ_ref["yield_benchmark_reference"].get("equivalent_quintals_per_acre")

            prepared_crops.append({
                "crop": c_name,
                "agronomic_score": item.get("agronomic_score"),
                "yield_quintals_per_acre": y_val,
                "price_inr_per_quintal": p_val,
                "cultivation_cost_inr_per_acre": c_val,
                "price_data_type": item.get("price_data_type", "official"),
                "price_basis": item.get("price_basis", "MSP reference")
            })

        results = economic_engine.calculate_multiple_crops(prepared_crops, farm_size_acres=farm_size_acres)
        return {"status": "success", "results": results}

    # Single crop economics
    crop = payload.get("crop", "")
    econ_ref = economic_service.get_crop_economics(crop) or {}

    price_inr = payload.get("price_inr_per_quintal")
    price_dt = payload.get("price_data_type", "official")
    price_basis = payload.get("price_basis")
    price_source = payload.get("price_source", "Unspecified")

    if price_inr is None and "msp_information" in econ_ref:
        price_inr = econ_ref["msp_information"].get("value")
        price_dt = "official"
        price_basis = "MSP reference"
        price_source = econ_ref["msp_information"].get("source", "CACP Government Reference")

    cost_inr = payload.get("cultivation_cost_inr_per_acre")
    cost_source = payload.get("cost_source", "DES / CACP Govt Reports")
    if cost_inr is None and "cost_of_cultivation" in econ_ref:
        cost_inr = econ_ref["cost_of_cultivation"].get("value")
        cost_source = econ_ref["cost_of_cultivation"].get("source", "DES / CACP Govt Reports")

    yield_q_acre = payload.get("yield_quintals_per_acre")
    yield_t_ha = payload.get("yield_tonnes_per_ha")
    yield_source = payload.get("yield_source", "Historical District Dataset")
    if yield_q_acre is None and yield_t_ha is None and "yield_benchmark_reference" in econ_ref:
        yield_q_acre = econ_ref["yield_benchmark_reference"].get("equivalent_quintals_per_acre")
        yield_t_ha = econ_ref["yield_benchmark_reference"].get("mean_yield_tonnes_ha")
        yield_source = econ_ref["yield_benchmark_reference"].get("source", "Historical District Dataset")

    res = economic_engine.calculate_crop_economics(
        crop=crop,
        farm_size_acres=farm_size_acres,
        yield_tonnes_per_ha=yield_t_ha,
        yield_quintals_per_acre=yield_q_acre,
        price_inr_per_quintal=price_inr,
        cultivation_cost_inr_per_acre=cost_inr,
        price_source=price_source,
        price_data_type=price_dt,
        price_basis=price_basis,
        yield_source=yield_source,
        cost_source=cost_source,
        agronomic_score=payload.get("agronomic_score")
    )
    return res


@router.get("/post-harvest")
async def get_post_harvest_endpoint(
    crop: str = Query(..., description="Crop name"),
    farm_size_acres: Optional[float] = Query(None, description="Farm size in acres"),
    harvest_quantity_quintals: Optional[float] = Query(None, description="Harvest quantity in quintals"),
    current_price: Optional[float] = Query(None, description="Current market price per quintal"),
    farmer_goal: Optional[str] = Query(None, description="Farmer goal: sell_now, store, process, compare_options"),
    state: Optional[str] = Query(None, description="State name"),
    district: Optional[str] = Query(None, description="District name")
):
    """
    Retrieves post-harvest storage guidance, Sell Now values, Store information,
    and Seasonal Price Analysis limitation using PostHarvestEngine and SeasonalPriceEngine.
    """
    from backend.app.ml.post_harvest_engine import post_harvest_engine
    from backend.app.ml.seasonal_price_engine import seasonal_price_engine

    res = post_harvest_engine.get_post_harvest_advisory(
        crop=crop,
        farm_size_acres=farm_size_acres,
        harvest_quantity_quintals=harvest_quantity_quintals,
        current_price=current_price,
        farmer_goal=farmer_goal
    )
    
    # Attach isolated SeasonalPriceEngine response
    res["seasonal_price_analysis"] = seasonal_price_engine.get_seasonal_analysis(
        crop=crop,
        state=state,
        district=district,
        current_price=current_price,
        harvest_quantity_quintals=harvest_quantity_quintals
    )
    return res

