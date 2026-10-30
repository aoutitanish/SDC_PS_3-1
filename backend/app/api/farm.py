"""
Farm Profile API Endpoints for KrishiMitra AI.
Allows farmers to manage personalized farm profiles and receive tailored summaries.
"""

import json
import logging
from fastapi import APIRouter
from backend.app.data_engine.schemas import FarmProfileModel
from backend.app.core.database import get_db_connection
from backend.app.ml.predict import recommender

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/farm", tags=["My Farm"])


@router.get("")
async def get_farm_profile(user_id: str = "guest"):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM farm_profiles WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        crops = json.loads(row["primary_crops"]) if row["primary_crops"] else []
        return {
            "success": True,
            "profile": {
                "farm_name": row["farm_name"],
                "state": row["state"],
                "district": row["district"],
                "soil_type": row["soil_type"],
                "farm_size_acres": row["farm_size_acres"],
                "irrigation_type": row["irrigation_type"],
                "primary_crops": crops,
                "preferred_language": row["preferred_language"]
            }
        }

    # Default initial profile: Kurnool, Andhra Pradesh, 5.0 Acres, Black Soil, Drip + Borewell
    return {
        "success": True,
        "profile": {
            "farm_name": "Kurnool Farm",
            "state": "Andhra Pradesh",
            "district": "Kurnool",
            "soil_type": "Black Soil (Regur/Vertisol)",
            "farm_size_acres": 5.0,
            "irrigation_type": "Drip Irrigation & Borewell",
            "primary_crops": ["Arhar/Tur (Pigeon Pea)", "Cotton", "Chilli"],
            "preferred_language": "en"
        }
    }


@router.post("")
async def save_farm_profile(profile: FarmProfileModel, user_id: str = "guest"):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO farm_profiles (user_id, farm_name, state, district, soil_type, farm_size_acres, irrigation_type, primary_crops, preferred_language)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        profile.farm_name,
        profile.state,
        profile.district,
        profile.soil_type,
        profile.farm_size_acres,
        profile.irrigation_type,
        json.dumps(profile.primary_crops),
        profile.preferred_language
    ))
    conn.commit()
    conn.close()

    # Generate personalized recommendations for this saved farm
    rec = recommender.recommend({
        "state": profile.state,
        "district": profile.district,
        "soil_type": profile.soil_type
    }, top_k=3)

    return {
        "success": True,
        "message": "Farm profile saved successfully.",
        "profile": profile.model_dump(),
        "personalized_recommendations": rec
    }
