"""
Crop Recommendation API Endpoint for KrishiMitra AI.
"""

from fastapi import APIRouter
from backend.app.data_engine.schemas import CropRecommendRequest
from backend.app.ml.predict import recommender
from backend.app.core.config import settings
from backend.app.services.rag_pipeline import rag_pipeline

router = APIRouter(prefix="/recommend", tags=["Recommendation"])


@router.post("")
async def get_crop_recommendation(req: CropRecommendRequest):
    features = req.model_dump(exclude_none=True)
    if settings.RAG_LLM_MODE:
        state = features.get("state")
        season = features.get("season")
        district = features.get("district")
        query = f"Crop recommendation for {district} {state} in {season}"
        res = rag_pipeline.retrieve(query, state_filter=state, season_filter=season)
        return {
            "mode": "rag_llm",
            "message": "Direct model inference bypassed in RAG_LLM_MODE. Recommendations are delivered via /api/chat with full agronomic provenance.",
            "retrieved_documents": res.get("retrieved_documents", [])[:4],
            "sources": res.get("sources", [])
        }
    result = recommender.recommend(features, top_k=4)
    return result

