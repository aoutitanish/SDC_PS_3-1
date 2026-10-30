"""
Weather API Endpoints for KrishiMitra AI.
"""

from fastapi import APIRouter, Query
from typing import Optional
from backend.app.services.weather_service import weather_service

router = APIRouter(prefix="/weather", tags=["Weather"])


@router.get("")
async def get_weather(
    state: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    lat: Optional[float] = Query(None),
    lon: Optional[float] = Query(None)
):
    result = await weather_service.get_weather(state=state, district=district, lat=lat, lon=lon)
    return result
