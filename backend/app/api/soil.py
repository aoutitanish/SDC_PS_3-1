"""
Soil Analysis API Endpoint for KrishiMitra AI.
Provides soil health assessment, USDA texture calculation, nutrient ratings, and amendment advisories.
"""

from fastapi import APIRouter
from backend.app.data_engine.schemas import SoilAnalysisRequest
from scripts.clean_data import determine_usda_texture, determine_indian_soil_group
from backend.app.ml.predict import recommender

router = APIRouter(prefix="/soil", tags=["Soil Analysis"])


@router.post("/analyze")
async def analyze_soil(req: SoilAnalysisRequest):
    sand = float(req.sand_pct or 35.0)
    silt = float(req.silt_pct or 35.0)
    clay = float(req.clay_pct or 30.0)
    ph = float(req.ph or 6.8)
    n_val = float(req.nitrogen_cg_kg or 180.0)
    soc_val = float(req.soc_dg_kg or 200.0)
    state = req.state or "All India"

    # Normalize texture percentages to sum to 100
    total_tex = sand + silt + clay
    if total_tex > 0 and abs(total_tex - 100.0) > 0.5:
        sand = round((sand / total_tex) * 100.0, 1)
        silt = round((silt / total_tex) * 100.0, 1)
        clay = round((clay / total_tex) * 100.0, 1)

    usda_tex = determine_usda_texture(sand, silt, clay)
    indian_group = req.soil_type or determine_indian_soil_group(usda_tex, ph, soc_val, state)

    # pH category and amendment advice
    if ph < 5.8:
        ph_cat = "Strongly Acidic"
        ph_status = "Sub-optimal"
        ph_advice = "Apply Agricultural Lime (Calcium Carbonate) or Dolomite @ 2-4 tonnes/ha to neutralize soil acidity and improve phosphate uptake."
    elif 5.8 <= ph < 6.5:
        ph_cat = "Slightly Acidic"
        ph_status = "Moderately Good"
        ph_advice = "Suitable for most pulses and cereals. Apply well-rotted farmyard manure (FYM) to buffer soil acidity."
    elif 6.5 <= ph <= 7.8:
        ph_cat = "Neutral / Optimal"
        ph_status = "Optimal"
        ph_advice = "Ideal pH range for maximum availability of macronutrients (N, P, K) and micronutrients (Zn, Fe, Mn)."
    elif 7.8 < ph <= 8.5:
        ph_cat = "Moderately Alkaline"
        ph_status = "Moderate"
        ph_advice = "Apply Gypsum (Calcium Sulfate) @ 1-2 tonnes/ha and incorporate green manuring crops (Dhaincha/Sunn hemp) to lower pH."
    else:
        ph_cat = "Saline / Alkaline"
        ph_status = "Challenging"
        ph_advice = "Ensure deep leaching with good quality irrigation water. Apply elemental sulfur or gypsum alongside organic compost."

    # Nitrogen status
    if n_val < 150.0:
        n_status = "Low"
        n_advice = "Nitrogen is deficient. Incorporate legume cover crops (Moong/Cowpea) and apply balanced split doses of Urea/DAP."
    elif 150.0 <= n_val <= 250.0:
        n_status = "Medium"
        n_advice = "Adequate nitrogen reserves. Maintain with standard recommended fertilizer doses and crop rotation."
    else:
        n_status = "High"
        n_advice = "Rich nitrogen content. Avoid excessive nitrogenous fertilizers to prevent vegetative lodging and pest susceptibility."

    # Organic Carbon status
    if soc_val < 150.0:
        oc_status = "Low"
    elif 150.0 <= soc_val <= 280.0:
        oc_status = "Medium"
    else:
        oc_status = "High"

    # Get recommended crops for this soil profile
    rec_res = recommender.recommend({
        "state": state,
        "district": req.district,
        "soil_type": indian_group,
        "ph": ph,
        "clay_pct": clay,
        "sand_pct": sand,
        "silt_pct": silt,
        "nitrogen_cg_kg": n_val,
        "soc_dg_kg": soc_val
    }, top_k=4)

    return {
        "success": True,
        "soil_profile": {
            "usda_texture": usda_tex,
            "indian_soil_group": indian_group,
            "ph": ph,
            "ph_category": ph_cat,
            "ph_status": ph_status,
            "ph_amendment_advice": ph_advice,
            "nitrogen_cg_kg": n_val,
            "nitrogen_status": n_status,
            "nitrogen_advice": n_advice,
            "organic_carbon_status": oc_status,
            "texture_composition": {
                "sand_pct": sand,
                "silt_pct": silt,
                "clay_pct": clay
            }
        },
        "recommendations": rec_res
    }
