"""
Configuration settings for KrishiMitra AI.
Loads settings from environment variables with sensible defaults.
"""

import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseModel):
    PROJECT_NAME: str = "KrishiMitra AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"

    # LLM Settings
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "ollama")  # options: bionic, gemini, openai, ollama, rule_engine
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "http://localhost:1234/v1")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "qwen/qwen3.5-9b")
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "750"))
    LLM_TIMEOUT_S: float = float(os.getenv("LLM_TIMEOUT_S", "60.0"))
    LLM_MAX_RETRIES: int = int(os.getenv("LLM_MAX_RETRIES", "2"))
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen3.5:9b")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    # ---------------------------------------------------------------
    # RAG + LLM Reset Configuration
    # Set RAG_LLM_MODE=true to bypass Random Forest / AgriculturalEngine.
    # Set RAG_LLM_MODE=false (default) to keep the legacy RF pipeline active.
    # Rollback: flip this back to false and restart uvicorn — no code change needed.
    # ---------------------------------------------------------------
    RAG_LLM_MODE: bool = os.getenv("RAG_LLM_MODE", "false").lower() in ("true", "1", "yes")

    # Retrieval settings (used when RAG_LLM_MODE=true)
    RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "6"))
    RAG_HYBRID_ALPHA: float = float(os.getenv("RAG_HYBRID_ALPHA", "0.5"))  # 0 = pure BM25, 1 = pure TF-IDF cosine
    RAG_RERANK_ENABLED: bool = os.getenv("RAG_RERANK_ENABLED", "false").lower() in ("true", "1", "yes")

    # Embedding / knowledge base path
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "tfidf")  # "tfidf" uses local TF-IDF; future: sentence-transformers
    KNOWLEDGE_BASE_DIR: str = os.getenv(
        "KNOWLEDGE_BASE_DIR",
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "data", "knowledge_base", "rag_documents")
    )

    # Weather API Settings
    WEATHER_API_KEY: str = os.getenv("WEATHER_API_KEY", "")

    # Database & Storage
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./krishimitra.db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "krishimitra-secure-farming-key-2026")

    # CORS
    CORS_ORIGINS: list = ["*"]


settings = Settings()
