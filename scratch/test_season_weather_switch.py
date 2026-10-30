import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding='utf-8')

from starlette.testclient import TestClient
from backend.main import app

client = TestClient(app)

print("=== SEASON & WEATHER SWITCHING AUDIT ===")

# Test 1: Kharif vs Rabi in Kurnool
session_id = "season_switch_session_3"
base_profile = {
    "farm_name": "Kurnool Test Farm",
    "state": "Andhra Pradesh",
    "district": "Kurnool",
    "soil_type": "Black Soil (Regur/Vertisol)",
    "farm_size_acres": 5.0,
    "irrigation_type": "Drip Irrigation",
    "water_source": "Borewell",
    "water_availability": "Moderate",
    "season": "Kharif",
    "preferred_language": "en"
}

# Query in Kharif
res_kharif = client.post("/api/chat", json={
    "message": "What crops are suitable for Kharif season?",
    "language": "en",
    "session_id": session_id,
    "farm_profile": base_profile
})
assert res_kharif.status_code == 200
data_kharif = res_kharif.json()
crop_kharif = (data_kharif.get("simple_summary") or {}).get("main_crop") or (data_kharif.get("detailed_analysis") or {}).get("crop")
print(f"Kharif Crop: {crop_kharif}")

# Switch to Rabi season
rabi_profile = dict(base_profile)
rabi_profile["season"] = "Rabi"

res_rabi = client.post("/api/chat", json={
    "message": "What crops are suitable for Rabi season?",
    "language": "en",
    "session_id": session_id,
    "farm_profile": rabi_profile
})
assert res_rabi.status_code == 200
data_rabi = res_rabi.json()
crop_rabi = (data_rabi.get("simple_summary") or {}).get("main_crop") or (data_rabi.get("detailed_analysis") or {}).get("crop")
print(f"Rabi Crop: {crop_rabi}")

assert crop_rabi is not None, "Rabi crop returned None"
print("Season switching verified successfully!")

# Test 2: Market Page States
print("\n--- Testing Market API States ---")
res_mkt = client.get("/api/market/prices?district=Kurnool&state=Andhra%20Pradesh&crop=Cotton")
assert res_mkt.status_code == 200
mkt_data = res_mkt.json()
print(f"Market Telemetry Status: {mkt_data.get('status')} | Source: {mkt_data.get('source')}")
assert (mkt_data.get("status") or "").upper() in ["LIVE", "CACHED", "UNAVAILABLE"]

res_mkt_unavail = client.get("/api/market/prices?district=Kurnool&state=Andhra%20Pradesh&crop=NonExistentCrop123")
assert res_mkt_unavail.status_code == 200
mkt_unavail_data = res_mkt_unavail.json()
print(f"Unavailable Market Status: {mkt_unavail_data.get('status')} | State: {mkt_unavail_data.get('telemetry', {}).get('price_state')}")
assert (mkt_unavail_data.get("status") or "").upper() == "UNAVAILABLE"

# Economic calculations endpoint (POST)
res_econ = client.post("/api/market/economics", json={
    "crops": [{"crop": "Cotton", "price_inr_per_quintal": 6500, "yield_quintals_per_acre": 12, "cultivation_cost_inr_per_acre": 25000}],
    "farm_size_acres": 5
})
assert res_econ.status_code == 200
econ_data = res_econ.json()
metrics = econ_data.get("results", [{}])[0]
print(f"Economic Analysis Result: {metrics.get('crop')} -> Net Profit: ₹{metrics.get('net_profit')}")

# Post-harvest Sell-vs-Store limitation check
res_ph = client.get("/api/market/post-harvest?crop=Cotton")
assert res_ph.status_code == 200
ph_data = res_ph.json()
spa = ph_data.get("seasonal_price_analysis", {})
print(f"Seasonal Price Analysis Available: {spa.get('available')}")
print(f"Limitation Reason: {spa.get('reason')}")
assert spa.get('available') is False
assert "historical monthly wholesale-price data is required" in spa.get('reason')

print("\nSeason & Market API verification complete!")
