"""
Pydantic Request & Response Schemas for KrishiMitra AI API.
Strictly typed data contracts separating Level 1 Simple Farmer Answers from Level 2 Scientific Details.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class LocationInput(BaseModel):
    state: Optional[str] = None
    district: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class FarmProfileInput(BaseModel):
    farm_name: Optional[str] = "My Farm"
    state: Optional[str] = None
    district: Optional[str] = None
    soil_type: Optional[str] = None
    farm_size_acres: Optional[float] = None
    irrigation_type: Optional[str] = None
    water_source: Optional[str] = None
    water_availability: Optional[str] = "Moderate"  # Low, Moderate, Adequate, Unknown
    season: Optional[str] = "Kharif"
    preferred_language: Optional[str] = "en"


class ChatRequest(BaseModel):
    message: str
    language: Optional[str] = "en"
    session_id: Optional[str] = "default_session"
    location: Optional[LocationInput] = None
    soil_type: Optional[str] = None
    farm_profile: Optional[FarmProfileInput] = None
    detail_level: Optional[str] = "simple"  # "simple" (Level 1) or "detailed" (Level 2)
    image_data: Optional[str] = None


class SimpleFarmerSummary(BaseModel):
    title: str = "Crop Recommendation"
    main_crop: Optional[str] = None
    simple_reason: List[str] = []
    water_requirement: Optional[str] = None
    season: Optional[str] = None
    warning: Optional[str] = None
    next_steps: List[str] = []


class DetailedAgronomicAnalysis(BaseModel):
    crop: str
    agronomic_suitability_score: Optional[float] = None
    model_confidence: Optional[str] = None
    soil_parameters: Dict[str, Any] = {}
    climate_parameters: Dict[str, Any] = {}
    water_analysis: Dict[str, Any] = {}
    explainability_factors: List[Dict[str, Any]] = []
    sources: List[Dict[str, Any]] = []
    limitations: List[str] = []


class SourceItem(BaseModel):
    name: str
    category: Optional[str] = None
    title: Optional[str] = None
    why_used: Optional[str] = None


class FactorItem(BaseModel):
    name: str
    status: str = "Suitable"
    value: str


class RecommendationItem(BaseModel):
    crop: str
    suitability_score: Optional[float] = None
    confidence: Optional[str] = "High"


class StructuredCropResponse(BaseModel):
    intent: str = "crop_recommendation"
    language: str = "en"
    summary: Optional[SimpleFarmerSummary] = None
    recommendation: Optional[RecommendationItem] = None
    factors: List[FactorItem] = []
    alternatives: List[str] = []
    warnings: List[str] = []
    next_steps: List[str] = []
    detailed_analysis: Optional[DetailedAgronomicAnalysis] = None
    sources: List[Dict[str, Any]] = []


class ChatResponse(BaseModel):
    success: bool = True
    answer: str  # Primary farmer-facing narrative
    language: str = "en"
    intent: Optional[str] = "general_agriculture"
    simple_summary: Optional[SimpleFarmerSummary] = None
    detailed_analysis: Optional[DetailedAgronomicAnalysis] = None
    structured_response: Optional[StructuredCropResponse] = None
    sources: List[Dict[str, Any]] = []
    recommendation_data: Optional[Dict[str, Any]] = None
    comparison_data: Optional[Dict[str, Any]] = None
    confidence: Optional[str] = "High"
    follow_up: Optional[str] = None
    quick_replies: Optional[List[str]] = None
    latency_metrics: Optional[Dict[str, Any]] = None


class CropRecommendRequest(BaseModel):
    state: Optional[str] = None
    district: Optional[str] = None
    soil_type: Optional[str] = None
    ph: Optional[float] = 6.8
    clay_pct: Optional[float] = None
    sand_pct: Optional[float] = None
    silt_pct: Optional[float] = None
    nitrogen_cg_kg: Optional[float] = None
    annual_rainfall_mm: Optional[float] = None
    temperature: Optional[float] = None
    season: Optional[str] = "Kharif"
    irrigation_available: Optional[bool] = True
    irrigation_type: Optional[str] = "Drip Irrigation"
    water_source: Optional[str] = "Borewell"


class SoilAnalysisRequest(BaseModel):
    state: Optional[str] = None
    district: Optional[str] = None
    soil_type: Optional[str] = None
    ph: Optional[float] = 6.8
    clay_pct: Optional[float] = 30.0
    sand_pct: Optional[float] = 35.0
    silt_pct: Optional[float] = 35.0
    nitrogen_cg_kg: Optional[float] = 180.0
    soc_dg_kg: Optional[float] = 200.0


class FarmProfileModel(BaseModel):
    farm_name: str = "My Farm"
    state: str = "Andhra Pradesh"
    district: str = "Kurnool"
    soil_type: str = "Black Soil (Regur/Vertisol)"
    farm_size_acres: float = 5.0
    irrigation_type: str = "Drip Irrigation & Borewell"
    water_source: Optional[str] = "Borewell"
    water_availability: Optional[str] = "Moderate"
    season: Optional[str] = "Kharif"
    primary_crops: List[str] = ["Arhar/Tur (Pigeon Pea)", "Cotton", "Chilli"]
    preferred_language: str = "en"
