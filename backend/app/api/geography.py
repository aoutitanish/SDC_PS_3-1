"""
Geography API Endpoints for KrishiMitra AI.
Provides complete list of Indian States, Districts, and Coordinates.
"""

import os
import logging
import pandas as pd
from fastapi import APIRouter, Query
from typing import Optional

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/geography", tags=["Geography"])

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "data", "processed")


def load_geo_df():
    path = os.path.join(DATA_DIR, "clean_geography.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame()


@router.get("/states")
async def get_states():
    df = load_geo_df()
    if df.empty:
        return {"states": []}
    states = sorted(df["State_Name"].dropna().unique().tolist())
    return {"success": True, "count": len(states), "states": states}


@router.get("/districts")
async def get_districts(state: Optional[str] = Query(None)):
    df = load_geo_df()
    if df.empty:
        return {"districts": []}

    if state:
        df = df[df["State_Name"].str.lower() == state.lower().strip()]

    districts = df[["State_Name", "District_Name", "latitude", "longitude"]].to_dict(orient="records")
    return {"success": True, "count": len(districts), "districts": districts}
