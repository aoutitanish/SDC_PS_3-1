"""
Crop Encyclopedia API Endpoints for KrishiMitra AI.
"""

import os
import json
import logging
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/crops", tags=["Crops"])

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "data", "processed")
MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "ml", "models")


def load_crop_data():
    summary_path = os.path.join(DATA_DIR, "crop_summary.json")
    profiles_path = os.path.join(MODELS_DIR, "crop_agronomic_profiles.json")

    crops = []
    if os.path.exists(summary_path):
        with open(summary_path, "r", encoding="utf-8") as fp:
            crops = json.load(fp)

    profiles = {}
    if os.path.exists(profiles_path):
        with open(profiles_path, "r", encoding="utf-8") as fp:
            profiles = json.load(fp)

    return crops, profiles


@router.get("")
async def list_crops(
    search: Optional[str] = Query(None),
    season: Optional[str] = Query(None),
    state: Optional[str] = Query(None)
):
    crops, profiles = load_crop_data()

    results = []
    for c in crops:
        name = c.get("Crop", "")
        if search and search.lower() not in name.lower():
            continue
        if season and season != "All" and season not in c.get("top_seasons", []):
            continue
        if state and state != "All" and state not in c.get("top_states", []):
            continue

        prof = profiles.get(name, {})
        results.append({
            "crop": name,
            "mean_yield_tonnes_ha": round(float(c.get("mean_yield", 0.0)), 2),
            "total_records": c.get("total_records", 0),
            "top_seasons": c.get("top_seasons", []),
            "top_states": c.get("top_states", []),
            "has_agronomic_profile": name in profiles
        })

    return {
        "success": True,
        "total_count": len(results),
        "crops": results
    }


@router.get("/{crop_name}")
async def get_crop_detail(crop_name: str):
    crops, profiles = load_crop_data()

    matched_crop = next((c for c in crops if c.get("Crop", "").lower() == crop_name.lower().strip()), None)
    prof = profiles.get(crop_name)

    if not matched_crop and not prof:
        raise HTTPException(status_code=404, detail=f"Crop '{crop_name}' not found in knowledge base.")

    return {
        "success": True,
        "crop": crop_name,
        "summary": matched_crop or {},
        "agronomic_requirements": prof or {
            "note": "Information not fully detailed in the current knowledge base profile."
        },
        "sources": [
            "Crop Expert Dataset (1997-2015 historical district records)",
            "ICAR Package of Practices",
            "Soil & Weather Expert Multi-year Normals"
        ]
    }
