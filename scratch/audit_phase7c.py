import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding='utf-8')

from backend.app.ml.predict import recommender
from backend.app.ml.economic_engine import economic_engine
from backend.app.services.economic_service import economic_service
from backend.app.services.intent_service import intent_service

print("=== AUDIT SECTION 2: PALAKKAD CASE ===")

palakkad_context = {
    "state": "Kerala",
    "district": "Palakkad",
    "soil_type": "Laterite Soil / Red Soil",
    "irrigation_type": "Rainfed",
    "water_source": "Rainwater / River",
    "water_availability": "Moderate",
    "season": "Kharif",
    "farm_size_acres": 5.0
}

# 1. Recommendation
rec_res = recommender.recommend(palakkad_context, top_k=6)
primary = rec_res["primary_recommendation"]
alternatives = rec_res["alternative_crops"]

ranked_candidates = [primary["crop"]] + [a["crop"] for a in alternatives]
print(f"Palakkad Recommended Ranked Candidates ({len(ranked_candidates)}): {ranked_candidates}")

# 2. Test Economics for candidates
print("\n=== ECONOMIC CALCULATIONS FOR PALAKKAD CANDIDATES ===")
candidate_econ_batch = []
price_provenance_map = {}

for c_name in ranked_candidates:
    econ_ref = economic_service.get_crop_economics(c_name) or {}
    p_info = econ_ref.get("msp_information") or {}
    c_info = econ_ref.get("cost_of_cultivation") or {}
    y_info = econ_ref.get("yield_benchmark_reference") or {}
    
    p_val = p_info.get("value")
    c_val = c_info.get("value")
    y_val = y_info.get("equivalent_quintals_per_acre")

    p_type = "UNAVAILABLE"
    if p_val is not None:
        p_type = "OFFICIAL MSP REFERENCE"

    price_provenance_map[c_name] = {
        "price": p_val,
        "type": p_type,
        "cost": c_val,
        "yield": y_val
    }

    candidate_econ_batch.append({
        "crop": c_name,
        "price_inr_per_quintal": p_val,
        "yield_quintals_per_acre": y_val,
        "cultivation_cost_inr_per_acre": c_val,
        "price_data_type": p_type,
        "price_basis": "MSP reference" if p_val else "Unavailable"
    })

econ_results = economic_engine.calculate_multiple_crops(candidate_econ_batch, farm_size_acres=5.0)

for res in econ_results:
    c_name = res["crop"]
    prov = price_provenance_map.get(c_name, {})
    m = res.get("economic_metrics") or {}
    status = res.get("status")
    print(f"Crop: {c_name:<25} | Status: {status:<18} | Price Type: {prov['type']:<22} | Est Prod: {m.get('production_quintals')} q | Gross Rev: ₹{m.get('gross_revenue_inr')} | Cost: ₹{m.get('total_cultivation_cost_inr')} | Net Return: ₹{m.get('estimated_net_return_inr')} | Margin: {m.get('gross_margin_pct')}% | ROI: {m.get('roi_pct')}%")

print("\n=== AUDIT SECTION 6: CHAT INTENT ROUTING ===")
queries_to_test = [
    ("Which crop should I grow?", "crop_recommendation"),
    ("What is the best crop for my farm?", "crop_recommendation"),
    ("Which crop is most profitable?", "economic_recommendation / crop_recommendation"),
    ("Among the suitable crops, which gives the highest estimated return?", "economic_recommendation"),
    ("Which crop has the highest profit this season?", "economic_recommendation"),
    ("Compare the profits of rice, maize and ragi.", "crop_comparison"),
    ("Why was rice recommended?", "crop_explanation"),
    ("What is the current mandi price of rice?", "market_price"),
    ("Should I sell rice now or store it?", "post_harvest_storage")
]

for q, expected in queries_to_test:
    detected = intent_service.detect_intent(q)
    print(f"Query: '{q}'\n  -> Detected Intent: {detected:<25} | Expected: {expected}")
