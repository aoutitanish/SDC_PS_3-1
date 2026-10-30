"""
Admin & System Health Diagnostic Endpoints for KrishiMitra AI.
"""

import os
import json
import logging
from fastapi import APIRouter
from backend.app.core.config import settings
from backend.app.data_engine.vector_store import vector_store

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Admin & Health"])

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "ml", "models")
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "data", "processed")


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "llm_provider": settings.LLM_PROVIDER,
        "vector_store_ready": vector_store.matrix is not None
    }


@router.get("/admin/status")
async def admin_status():
    # 1. Load ML Model Metadata
    meta_path = os.path.join(MODELS_DIR, "model_metadata.json")
    ml_metadata = {}
    if os.path.exists(meta_path):
        with open(meta_path, "r", encoding="utf-8") as fp:
            ml_metadata = json.load(fp)

    # 2. Validation report
    val_path = os.path.join(DATA_DIR, "validation_report.json")
    val_report = {}
    if os.path.exists(val_path):
        with open(val_path, "r", encoding="utf-8") as fp:
            val_report = json.load(fp)

    # 3. Vector DB stats
    vector_stats = {
        "documents_indexed": len(vector_store.documents),
        "feature_dimensions": vector_store.matrix.shape[1] if vector_store.matrix is not None else 0,
        "status": "Online & Ready"
    }

    return {
        "success": True,
        "app_info": {
            "name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "environment": "Production Ready"
        },
        "llm_status": {
            "configured_provider": settings.LLM_PROVIDER,
            "api_key_configured": bool(settings.LLM_API_KEY or settings.GEMINI_API_KEY or settings.OPENAI_API_KEY),
            "fallback_engine": "Active (Deterministic Agricultural Reasoning Engine)"
        },
        "ml_model_status": ml_metadata,
        "vector_database_status": vector_stats,
        "datasets_status": val_report.get("datasets", {})
    }
