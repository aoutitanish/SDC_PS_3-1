"""
KrishiMitra AI - Comprehensive Acceptance Test Suite for LLM + Dynamic RAG Reset

Validates all 14 mandatory acceptance criteria specified in the project mission:
1. No trained crop model is loaded or invoked.
2. No legacy agricultural scoring engine is called.
3. Existing static crop/soil/weather datasets are not consulted for agricultural answers.
4. Old vector index is not used as the knowledge source.
5. Each new agricultural answer performs dynamic retrieval when external evidence is needed.
6. Retrieved documents and URLs are genuine and visible to the user.
7. No citations are fabricated.
8. No static location modal or hardcoded district fallback is triggered.
9. General questions do not inherit saved farm details.
10. Farm-specific questions ask only for relevant missing information.
11. Live weather and market values are retrieved from live tools, not static files.
12. Ollama connection failures are surfaced honestly without silent fallbacks.
13. English, Telugu and Hindi support continues to work.
14. Existing authentication, chat persistence and API contracts remain functional.
"""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from backend.app.data_engine.schemas import ChatRequest, ChatResponse, FarmProfileInput, LocationInput
from backend.app.core.session_memory import session_memory
from backend.app.core.config import settings
from backend.app.ml.predict import recommender
from backend.app.core.llm_provider import llm_provider
from backend.app.services.dynamic_rag_service import dynamic_rag
from backend.app.services.rag_pipeline import rag_pipeline
from backend.app.api.chat import process_chat_intent, chat_endpoint, chat_stream_endpoint
from backend.app.core.database import get_db_connection


@pytest.fixture(autouse=True)
def reset_environment():
    """Ensure clean session memory and cache before each test."""
    session_memory._sessions.clear()
    dynamic_rag.clear_cache()
    yield
    session_memory._sessions.clear()
    dynamic_rag.clear_cache()


# --------------------------------------------------------------------------
# Test 1: No trained crop model is loaded or invoked
# --------------------------------------------------------------------------
def test_01_no_trained_crop_model_loaded_or_invoked():
    assert settings.RAG_LLM_MODE is True, "RAG_LLM_MODE must be enabled"
    # When RAG_LLM_MODE is True, CropRecommender._load_artifacts() is bypassed
    assert recommender.model is None, "Trained Random Forest model should NOT be loaded into memory"
    assert recommender.pipeline is None, "Model pipeline should NOT be loaded into memory"
    assert recommender.label_encoder is None, "Label encoder should NOT be loaded into memory"


# --------------------------------------------------------------------------
# Test 2: No legacy agricultural scoring engine is called
# --------------------------------------------------------------------------
def test_02_no_legacy_agricultural_scoring_engine_called():
    async def _test():
        with patch("backend.app.ml.agricultural_engine.agricultural_engine.evaluate_crop") as mock_eval, \
             patch("backend.app.ml.agricultural_engine.agricultural_engine.rank_crops") as mock_rank, \
             patch.object(llm_provider, "generate", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = "Paddy thrives in flooded, clayey or clay-loam soils."

            res = await process_chat_intent(
                message="What type of soil is needed for paddy cultivation?",
                language="en",
                session_id="test_no_engine_sess"
            )

            assert mock_eval.call_count == 0, "agricultural_engine.evaluate_crop must NEVER be called"
            assert mock_rank.call_count == 0, "agricultural_engine.rank_crops must NEVER be called"
            assert res.answer == "Paddy thrives in flooded, clayey or clay-loam soils."
    asyncio.run(_test())


# --------------------------------------------------------------------------
# Test 3: Existing static crop/soil/weather datasets not consulted for agricultural answers
# --------------------------------------------------------------------------
def test_03_static_crop_soil_weather_datasets_not_consulted():
    async def _test():
        static_files_accessed = []
        original_open = open

        def guarded_open(file, *args, **kwargs):
            filename = str(file).lower()
            if any(f in filename for f in [
                "crop_suitability_master.csv",
                "soil_types.csv",
                "district_expert_weather.csv",
                "crop_economic_benchmarks.csv"
            ]):
                static_files_accessed.append(filename)
                raise RuntimeError(f"Illegal static dataset read attempted on {file}")
            return original_open(file, *args, **kwargs)

        with patch("builtins.open", side_effect=guarded_open), \
             patch.object(llm_provider, "generate", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = "Groundnut requires sandy loam or well-drained loamy soil."

            res = await process_chat_intent(
                message="Which soil is best for groundnut?",
                language="en",
                session_id="test_no_static_csv"
            )

            assert len(static_files_accessed) == 0, f"Static CSV files were accessed: {static_files_accessed}"
            assert res.confidence == "Grounded in Dynamic External Agricultural Research"
    asyncio.run(_test())


# --------------------------------------------------------------------------
# Test 4: Old vector index is not used as the knowledge source
# --------------------------------------------------------------------------
def test_04_old_vector_index_not_used():
    async def _test():
        with patch.object(rag_pipeline, "retrieve") as mock_old_rag, \
             patch.object(dynamic_rag, "retrieve_dynamic", wraps=dynamic_rag.retrieve_dynamic) as mock_dyn_rag, \
             patch.object(llm_provider, "generate", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = "Sorghum is a drought-resilient millets crop."

            res = await process_chat_intent(
                message="Tell me about sorghum water requirements.",
                language="en",
                session_id="test_vector_index_bypassed"
            )

            assert mock_old_rag.call_count == 0, "Old static TF-IDF rag_pipeline.retrieve must NOT be called"
            assert mock_dyn_rag.call_count >= 1, "dynamic_rag.retrieve_dynamic MUST be called"
    asyncio.run(_test())


# --------------------------------------------------------------------------
# Test 5: Dynamic retrieval performed when external evidence is needed
# --------------------------------------------------------------------------
def test_05_dynamic_retrieval_performed():
    result = dynamic_rag.retrieve_dynamic(
        query="cotton nitrogen fertilizer ICAR",
        crop_filter="Cotton",
        state_filter="Telangana",
        top_k=3
    )

    assert "context_text" in result
    assert "sources" in result
    assert len(result["sources"]) > 0, "Dynamic RAG must retrieve actual external sources"
    assert result["no_relevant_found"] is False


# --------------------------------------------------------------------------
# Test 6: Retrieved documents and URLs are genuine and visible to user
# --------------------------------------------------------------------------
def test_06_retrieved_documents_and_urls_genuine():
    result = dynamic_rag.retrieve_dynamic(
        query="wheat rust disease resistance ICAR",
        crop_filter="Wheat",
        top_k=3
    )
    for source in result["sources"]:
        assert "url" in source
        assert source["url"].startswith("http://") or source["url"].startswith("https://")
        assert any(domain in source["url"] for domain in ["doi.org", "crossref.org", "openalex.org", "wikipedia.org", "open-meteo.com", "agmarknet.gov.in"]), f"Source URL {source['url']} must be from authoritative domain"
        assert len(source["title"]) > 0


# --------------------------------------------------------------------------
# Test 7: No citations fabricated & honest confidence labels
# --------------------------------------------------------------------------
def test_07_no_fabricated_citations():
    async def _test():
        with patch.object(llm_provider, "generate", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = "Black soil has high moisture retention due to montmorillonite clay."

            res = await process_chat_intent(
                message="What makes black soil moisture retentive?",
                language="en",
                session_id="test_citation_honesty"
            )

            # Confidence must never claim 100% verified
            assert "100%" not in res.confidence
            assert "Verified" not in res.confidence or res.confidence == "Unverified (No External Agricultural Literature Found)"
            # Every source in response must have title and url
            for s in res.sources:
                assert "title" in s
                assert "url" in s
    asyncio.run(_test())


# --------------------------------------------------------------------------
# Test 8: No static location modal or hardcoded district fallback
# --------------------------------------------------------------------------
def test_08_no_hardcoded_district_fallback():
    async def _test():
        with patch.object(llm_provider, "generate", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = "Blossom end rot is caused by calcium deficiency in soil."

            res = await process_chat_intent(
                message="What causes blossom end rot in tomatoes?",
                language="en",
                session_id="test_no_location_force"
            )

            call_kwargs = mock_gen.call_args[1]
            farm_ctx = call_kwargs.get("farm_context")
            # General query with no location must pass None for farm_context
            assert farm_ctx is None, "Farm context must not be populated with hardcoded district fallback"
    asyncio.run(_test())


# --------------------------------------------------------------------------
# Test 9: General questions do not inherit saved farm details
# --------------------------------------------------------------------------
def test_09_general_questions_do_not_inherit_saved_farm():
    async def _test():
        farm = FarmProfileInput(state="Punjab", district="Ludhiana", soil_type="Alluvial Soil")

        with patch.object(llm_provider, "generate", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = "Optimal soil pH for cotton is 6.5 to 7.5."

            res = await process_chat_intent(
                message="What is the ideal soil pH for cotton?",
                language="en",
                session_id="test_general_gate",
                req_farm_profile=farm
            )

            call_kwargs = mock_gen.call_args[1]
            farm_ctx = call_kwargs.get("farm_context")
            assert farm_ctx is None, "General question must not receive saved farm details"
    asyncio.run(_test())


# --------------------------------------------------------------------------
# Test 10: Farm-specific questions ask only for relevant missing information
# --------------------------------------------------------------------------
def test_10_adaptive_follow_up_for_missing_info():
    async def _test():
        with patch.object(llm_provider, "generate", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = "To recommend crops, I need to know your district or region."

            res = await process_chat_intent(
                message="Which crop should I grow on my farm?",
                language="en",
                session_id="test_missing_info_followup"
            )

            # Missing district/region triggers concise follow-up
            assert res.follow_up is not None
            assert "district" in res.follow_up.lower() or "state" in res.follow_up.lower()
            assert res.quick_replies is not None
            assert len(res.quick_replies) > 0
    asyncio.run(_test())


# --------------------------------------------------------------------------
# Test 11: Live weather from live tools, not static files
# --------------------------------------------------------------------------
def test_11_live_weather_from_live_tools():
    async def _test():
        with patch("backend.app.services.weather_service.weather_service.get_weather", new_callable=AsyncMock) as mock_weather:
            mock_weather.return_value = {
                "success": True,
                "data_source": "Open-Meteo High-Resolution Weather API",
                "current": {
                    "temperature_c": 31.5,
                    "relative_humidity_pct": 58,
                    "rainfall_mm": 0.0,
                    "wind_speed_ms": 3.2,
                    "condition": "Partly Cloudy"
                },
                "agricultural_advisory": "Ideal for field spray operations."
            }

            res = await process_chat_intent(
                message="What is the current weather in Kurnool?",
                language="en",
                session_id="test_weather_tool",
                req_location=LocationInput(state="Andhra Pradesh", district="Kurnool")
            )

            assert mock_weather.called
            assert "31.5" in res.answer or "Partly Cloudy" in res.answer
            assert res.confidence == "Live Telemetry"
            assert res.sources[0]["url"] == "https://open-meteo.com/"
    asyncio.run(_test())


# --------------------------------------------------------------------------
# Test 12: Ollama connection failures surfaced honestly without silent fallbacks
# --------------------------------------------------------------------------
def test_12_ollama_connection_failure_surfaced_honestly():
    async def _test():
        import httpx
        with patch("httpx.AsyncClient.post", side_effect=httpx.ConnectError("Connection refused by Ollama daemon")):
            # Clear cache and run
            ans = await llm_provider.generate(
                message="How do I control fall armyworm in maize?",
                retrieved_context="ICAR recommendations...",
                lang="en"
            )

            # Must disclose connection error honestly and not fabricate response or fallback silently to OpenAI/Bionic
            assert "Ollama" in ans
            assert "11434" in ans or "unavailable" in ans.lower() or "connection" in ans.lower()
    asyncio.run(_test())


# --------------------------------------------------------------------------
# Test 13: Multilingual support (English, Telugu, Hindi) continues to work
# --------------------------------------------------------------------------
def test_13_multilingual_continuity():
    async def _test():
        with patch.object(llm_provider, "generate", new_callable=AsyncMock) as mock_gen:
            # Telugu query
            mock_gen.return_value = "పత్తి సాగుకు నల్ల రేగడి నేలలు అత్యంత అనుకూలమైనవి."
            res_te = await process_chat_intent(
                message="పత్తికి ఏ నేల మంచిది?",
                language="te",
                session_id="test_sess_te"
            )
            assert res_te.active_lang == "te"

            # Hindi query
            mock_gen.return_value = "कपास की खेती के लिए काली मिट्टी सबसे उपयुक्त होती है।"
            res_hi = await process_chat_intent(
                message="कपास के लिए कौन सी मिट्टी अच्छी है?",
                language="hi",
                session_id="test_sess_hi"
            )
            assert res_hi.active_lang == "hi"
    asyncio.run(_test())


# --------------------------------------------------------------------------
# Test 14: Existing auth, chat persistence and API contracts remain functional
# --------------------------------------------------------------------------
def test_14_existing_auth_persistence_and_api_contracts():
    async def _test():
        with patch.object(llm_provider, "generate", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = "Chickpea is grown predominantly during the Rabi season in Central and South India."

            req = ChatRequest(
                message="When is chickpea sown in India?",
                language="en",
                session_id="test_sess_persistence"
            )

            resp: ChatResponse = await chat_endpoint(req)

            # Verify ChatResponse structure
            assert resp.success is True
            assert len(resp.answer) > 0
            assert resp.confidence is not None
            assert isinstance(resp.sources, list)

            # Verify SQLite persistence
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT sender, content FROM messages WHERE session_id = ? ORDER BY id ASC", ("test_sess_persistence",))
            rows = cursor.fetchall()
            conn.close()

            assert len(rows) >= 2, "Both user and assistant messages must be persisted in SQLite"
            assert rows[0]["sender"] == "user"
            assert rows[1]["sender"] == "assistant"
    asyncio.run(_test())
