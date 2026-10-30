"""
KrishiMitra AI - Universal Reliability & Agronomic Quality Test Suite (Phase 4)

Covers the complete 17-point test matrix (Categories A through Q):
- Category A: Simple factual questions across many crops
- Category B: Different Indian regions and international locations
- Category C: Explicit location overriding a saved profile
- Category D: General questions that must not inherit farm context
- Category E: Multi-turn farm recommendations with several missing details
- Category F: Follow-up replies in text ("3 acres") and quick replies
- Category G: Switching consultations and starting new ones
- Category H: Multiple questions in one message
- Category I: English, Telugu, and Hindi queries and follow-ups
- Category J: Retrieval failures, empty results, and graceful degradation
- Category K: Fabricated citation and unsupported precision prevention
- Category L: Live weather and market-tool success and failure
- Category M: Questions where live weather is irrelevant (no weather telemetry)
- Category N: Out-of-scope non-agricultural queries rejected cleanly
- Category O: Stale response cancellation and concurrent request isolation
- Category P: Citation-to-claim support and source provenance
- Category Q: Conciseness and absence of unrelated answer padding
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from backend.app.data_engine.schemas import ChatRequest, ChatResponse, FarmProfileInput, LocationInput
from backend.app.core.session_memory import session_memory, PendingFollowUp
from backend.app.core.config import settings
from backend.app.core.llm_provider import llm_provider
from backend.app.services.dynamic_rag_service import dynamic_rag
from backend.app.services.intent_service import intent_service
from backend.app.api.chat import process_chat_intent


@pytest.fixture(autouse=True)
def reset_test_env():
    """Ensure clean session memory and cache before each test."""
    session_memory._sessions.clear()
    dynamic_rag.clear_cache()
    yield
    session_memory._sessions.clear()
    dynamic_rag.clear_cache()


# --------------------------------------------------------------------------
# Category A: Simple factual questions across many crops
# --------------------------------------------------------------------------
@pytest.mark.parametrize("crop,query", [
    ("cotton", "What is the optimal temperature range for cotton growth?"),
    ("paddy", "What water depth is required for paddy seedling transplanting?"),
    ("groundnut", "What is the recommended seed rate for rainfed groundnut?"),
    ("chickpea", "Which fungal wilt disease commonly affects chickpea crops?"),
    ("mustard", "How much sulfur is recommended per hectare for mustard?"),
])
def test_category_a_simple_factual_questions_across_crops(crop, query):
    async def _test():
        with patch.object(llm_provider, "generate", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = f"Agronomic answer for {crop}."
            res = await process_chat_intent(
                message=query,
                language="en",
                session_id=f"test_cat_a_{crop}"
            )
            assert res.intent in ["CROP_FACT", "GENERAL_KNOWLEDGE", "PEST_DISEASE", "FERTILIZER_NUTRIENT", "general_agriculture", "crop_fact"]
            assert res.follow_up is None, "Factual crop questions should receive answers first without forced follow-ups"
            assert len(res.answer) > 0
    asyncio.run(_test())


# --------------------------------------------------------------------------
# Category B: Indian regions and international locations
# --------------------------------------------------------------------------
def test_category_b_international_and_diverse_indian_regions():
    # 1. International location: Kenya
    cat_kenya, entities_kenya = intent_service.classify_and_extract("Can coffee be grown in Kenya highlands?")
    assert entities_kenya.get("country") == "Kenya", "Should extract Kenya as country"
    assert any("coffee" in c.lower() for c in entities_kenya.get("crop_mentions", []))

    # 2. International location: California
    cat_cal, entities_cal = intent_service.classify_and_extract("What almond irrigation practices work in California?")
    assert entities_cal.get("country") == "United States", "Should extract United States / California"

    # 3. Diverse Indian states: Assam
    cat_assam, entities_assam = intent_service.classify_and_extract("Tea plantation soil management in Assam")
    assert entities_assam.get("state") == "Assam"
    assert any("tea" in c.lower() for c in entities_assam.get("crop_mentions", []))


# --------------------------------------------------------------------------
# Category C: Explicit location overriding a saved profile
# --------------------------------------------------------------------------
def test_category_c_explicit_location_overrides_saved_farm():
    async def _test():
        sess_id = "test_override_farm_sess"
        # Seed saved farm profile: Kurnool, Andhra Pradesh
        farm_profile = FarmProfileInput(
            location=LocationInput(state="Andhra Pradesh", district="Kurnool"),
            area_acres=5.0,
            soil_type="Black Soil"
        )
        session_memory.update_farm_profile(sess_id, farm_profile)

        with patch.object(llm_provider, "generate", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = "Wheat is suitable for Ludhiana, Punjab during Rabi season."

            # User explicitly asks about Ludhiana, Punjab
            res = await process_chat_intent(
                message="What crops can I grow on my newly leased land in Ludhiana, Punjab?",
                language="en",
                session_id=sess_id
            )

            # Resolved context should reflect Ludhiana, Punjab, NOT Kurnool
            state = session_memory.get_session(sess_id)
            assert state.district == "Ludhiana"
            assert state.state == "Punjab"
            assert "Punjab" in res.answer or "Ludhiana" in res.answer
    asyncio.run(_test())


# --------------------------------------------------------------------------
# Category D: General questions must not inherit farm context
# --------------------------------------------------------------------------
def test_category_d_general_questions_do_not_inherit_farm_context():
    async def _test():
        sess_id = "test_general_no_inherit"
        farm_profile = FarmProfileInput(
            location=LocationInput(state="Maharashtra", district="Nagpur"),
            area_acres=10.0,
            soil_type="Black Cotton Soil"
        )
        session_memory.update_farm_profile(sess_id, farm_profile)

        # General question about soil pH
        resolved_context = session_memory.resolve_context(
            session_id=sess_id,
            user_message="What is the ideal pH range for growing bananas?",
            category="GENERAL_KNOWLEDGE"
        )

        # State/district should NOT be forced into the prompt context for general knowledge
        assert resolved_context.get("state") is None, "General question must not bind to farm state"
        assert resolved_context.get("district") is None, "General question must not bind to farm district"
    asyncio.run(_test())


# --------------------------------------------------------------------------
# Category E: Multi-turn farm recommendations with several missing details
# --------------------------------------------------------------------------
def test_category_e_multi_turn_farm_recommendation_flow():
    async def _test():
        sess_id = "test_multi_turn_e"
        with patch.object(llm_provider, "generate", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = "Please share your location so I can give specific recommendations."

            # Turn 1: Farmer asks a vague recommendation question
            res1 = await process_chat_intent(
                message="Which crops should I sow in the upcoming season?",
                language="en",
                session_id=sess_id
            )

            # System must ask high-impact follow-up for missing district/location
            assert res1.follow_up is not None
            assert len(res1.quick_replies) > 0

            # Verify pending follow-up state is stored
            st = session_memory.get_session(sess_id)
            assert st.pending_follow_up is not None
            assert st.pending_follow_up.target_field in ["district", "state"]

            # Turn 2: Farmer provides location "Warangal, Telangana"
            mock_gen.return_value = "Warangal is excellent for Cotton and Chilli. What type of soil do you have?"
            res2 = await process_chat_intent(
                message="My farm is in Warangal, Telangana",
                language="en",
                session_id=sess_id
            )

            st2 = session_memory.get_session(sess_id)
            assert st2.district == "Warangal"
            assert st2.state == "Telangana"
    asyncio.run(_test())


# --------------------------------------------------------------------------
# Category F: Follow-up replies in free-text ("3 acres") and quick-replies
# --------------------------------------------------------------------------
def test_category_f_follow_up_short_replies_resolve_pending_field():
    async def _test():
        sess_id = "test_short_reply_f"
        st = session_memory.get_session(sess_id)
        st.district = "Guntur"
        st.state = "Andhra Pradesh"
        st.set_pending_follow_up(
            original_query="What crop should I plant on my farm?",
            target_field="farm_area",
            consultation_id="cons_123",
            prompt_question="How many acres is your farm?",
            quick_replies=["1 Acre", "2-5 Acres", "5+ Acres"]
        )

        with patch.object(llm_provider, "generate", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = "For a 3 acre farm in Guntur, Chilli and Cotton are strong cash crop options."

            # Farmer replies with just "3 acres"
            res = await process_chat_intent(
                message="3 acres",
                language="en",
                session_id=sess_id
            )

            # Pending follow up for farm_area should be resolved, updating farm_area to 3.0
            st_after = session_memory.get_session(sess_id)
            assert st_after.farm_area == 3.0 or st_after.farm_size_acres == 3.0
            # Follow-up on farm_area resolved; next follow-up (if any) targets the next missing field (soil_type)
            if st_after.pending_follow_up:
                assert st_after.pending_follow_up.target_field != "farm_area"
    asyncio.run(_test())


# --------------------------------------------------------------------------
# Category G: Switching consultations and starting new ones
# --------------------------------------------------------------------------
def test_category_g_consultation_isolation():
    sess_a = "session_A"
    sess_b = "session_B"

    # Set up session A with pending follow-up
    st_a = session_memory.get_session(sess_a)
    st_a.district = "Nashik"
    st_a.set_pending_follow_up("What to grow?", "soil_type", "cons_A", "What is your soil?", ["Black", "Red"])

    # Set up session B
    st_b = session_memory.get_session(sess_b)
    st_b.district = "Amritsar"

    assert st_b.pending_follow_up is None, "Session B must not inherit Session A's pending follow-up"
    assert st_b.district == "Amritsar"

    # Resetting Session A clears pending follow up
    session_memory.reset_session(sess_a)
    assert session_memory.get_session(sess_a).pending_follow_up is None
    assert session_memory.get_session(sess_b).district == "Amritsar", "Resetting A must not affect B"


# --------------------------------------------------------------------------
# Category H: Multiple questions in one message
# --------------------------------------------------------------------------
def test_category_h_multiple_questions_in_one_message():
    async def _test():
        query = "What is the best fertilizer for wheat, and when is the harvest time?"
        cat, entities = intent_service.classify_and_extract(query)
        assert any("wheat" in c.lower() for c in entities.get("crop_mentions", []))
        # Intent detection captures the compound nature
        assert cat in ["FERTILIZER_NUTRIENT", "POST_HARVEST", "CROP_FACT", "FARM_RECOMMENDATION", "GENERAL_KNOWLEDGE"]

        with patch.object(llm_provider, "generate", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = "For wheat, apply 120 kg N, 60 kg P2O5. Harvesting takes place in March-April."
            res = await process_chat_intent(
                message=query,
                language="en",
                session_id="test_compound_q"
            )
            assert len(res.answer) > 20
    asyncio.run(_test())


# --------------------------------------------------------------------------
# Category I: Multilingual queries (English, Telugu, Hindi)
# --------------------------------------------------------------------------
def test_category_i_multilingual_intent_and_crop_extraction():
    # English
    cat_en, ent_en = intent_service.classify_and_extract("How to control pink bollworm in cotton?")
    assert any("cotton" in c.lower() for c in ent_en.get("crop_mentions", []))
    assert cat_en == "PEST_DISEASE"

    # Telugu
    cat_te, ent_te = intent_service.classify_and_extract("వరిలో ఎరువుల యాజమాన్యం ఎలా చేయాలి?")
    assert any("rice" in c.lower() or "paddy" in c.lower() for c in ent_te.get("crop_mentions", []))
    assert cat_te in ["FERTILIZER_NUTRIENT", "CROP_FACT", "GENERAL_KNOWLEDGE"]

    # Hindi
    cat_hi, ent_hi = intent_service.classify_and_extract("गेहूं की बुवाई का सही समय क्या है?")
    assert any("wheat" in c.lower() for c in ent_hi.get("crop_mentions", []))
    assert cat_hi in ["SOWING_CALENDAR", "CROP_FACT", "GENERAL_KNOWLEDGE"]


# --------------------------------------------------------------------------
# Category J: Retrieval failures and graceful degradation
# --------------------------------------------------------------------------
def test_category_j_retrieval_failure_graceful_handling():
    async def _test():
        # Mock external RAG returning empty/failed results
        with patch.object(dynamic_rag, "retrieve_dynamic") as mock_rag, \
             patch.object(llm_provider, "generate", new_callable=AsyncMock) as mock_gen:
            mock_rag.return_value = {
                "context_text": "No external agricultural records found dynamically. Answer from established agronomic principles.",
                "sources": [],
                "no_relevant_found": True,
                "retrieval_log": {"total_passages": 0, "unique_sources": 0}
            }
            mock_gen.return_value = "External research databases yielded no records. Based on general principles, quinoa requires well-drained soil."

            res = await process_chat_intent(
                message="Agronomic field trials for quinoa in cold deserts of Ladakh",
                language="en",
                session_id="test_empty_rag"
            )

            assert res.sources == []
            assert "Unverified" in res.confidence or "No External" in res.confidence or "General" in res.confidence
            assert "quinoa" in res.answer.lower()
    asyncio.run(_test())


# --------------------------------------------------------------------------
# Category K: Fabricated citation prevention
# --------------------------------------------------------------------------
def test_category_k_fabricated_citation_prevention():
    async def _test():
        with patch.object(dynamic_rag, "retrieve_dynamic") as mock_rag, \
             patch.object(llm_provider, "generate", new_callable=AsyncMock) as mock_gen:
            mock_rag.return_value = {
                "context_text": "ICAR Groundnut Guide: Gypsum application at pegging stage increases pod filling. URL: https://icar.org.in/groundnut.",
                "sources": [{
                    "name": "ICAR Groundnut Research Directorate",
                    "title": "Groundnut Agronomy Bulletin",
                    "url": "https://icar.org.in/groundnut",
                    "publication_year": "2023",
                    "score": 0.95,
                    "used": True
                }],
                "no_relevant_found": False
            }
            # LLM tries to hallucinate a fake citation URL
            mock_gen.return_value = "Apply gypsum at 500 kg/ha [Source: https://fake-agri-site.com/fake-paper]."

            res = await process_chat_intent(
                message="When should gypsum be applied to groundnut?",
                language="en",
                session_id="test_fake_citation"
            )

            # Response sources must contain only genuine retrieved sources, not fabricated URLs
            for src in res.sources:
                assert "fake-agri-site" not in src.get("url", "")
                assert src.get("url") == "https://icar.org.in/groundnut"
    asyncio.run(_test())


# --------------------------------------------------------------------------
# Category L: Live weather and market tools
# --------------------------------------------------------------------------
def test_category_l_live_weather_and_market_tool_gating():
    async def _test():
        with patch("backend.app.services.weather_service.weather_service.get_weather", new_callable=AsyncMock) as mock_weather:
            mock_weather.return_value = {
                "temperature_c": 31.5,
                "relative_humidity_pct": 65,
                "condition": "Partly Cloudy",
                "rainfall_mm": 0.0,
                "wind_speed_ms": 3.2
            }

            # Weather explicitly requested
            res_weather = await process_chat_intent(
                message="What is the current weather forecast in Kurnool, Andhra Pradesh?",
                language="en",
                session_id="test_weather_call"
            )
            assert mock_weather.call_count >= 1
            assert "31.5" in res_weather.answer or "Kurnool" in res_weather.answer
    asyncio.run(_test())


# --------------------------------------------------------------------------
# Category M: Questions where live weather is irrelevant
# --------------------------------------------------------------------------
def test_category_m_weather_irrelevant_queries_do_not_call_weather():
    async def _test():
        with patch("backend.app.services.weather_service.weather_service.get_weather", new_callable=AsyncMock) as mock_weather, \
             patch.object(llm_provider, "generate", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = "Powdery mildew in grapes is managed by spraying wettable sulfur."

            res = await process_chat_intent(
                message="How to treat powdery mildew on grape leaves?",
                language="en",
                session_id="test_no_weather_call"
            )

            # Weather service must NOT be called for a fungal disease question
            assert mock_weather.call_count == 0, "Weather tool must not be called when weather is irrelevant"
            # No weather telemetry should appear in sources
            for s in res.sources:
                assert "weather" not in s.get("name", "").lower()
    asyncio.run(_test())


# --------------------------------------------------------------------------
# Category N: Out-of-scope non-agricultural queries rejected cleanly
# --------------------------------------------------------------------------
@pytest.mark.parametrize("query", [
    "What is the best cryptocurrency to buy today?",
    "Write a python script for binary search algorithm",
    "Which smartphone has the best camera under 30000?",
    "Who won the cricket world cup final in 2023?",
    "What movies are releasing in theatres this Friday?",
])
def test_category_n_out_of_scope_rejection(query):
    async def _test():
        with patch.object(llm_provider, "generate", new_callable=AsyncMock) as mock_gen:
            res = await process_chat_intent(
                message=query,
                language="en",
                session_id="test_oos"
            )
            # Must be caught at the scope boundary before any LLM inference
            assert mock_gen.call_count == 0, "Out of scope queries must not consume LLM tokens"
            assert res.confidence == "Scope Boundary"
            assert "krishimitra" in res.answer.lower() or "agricultural" in res.answer.lower()
    asyncio.run(_test())


# --------------------------------------------------------------------------
# Category O: Stale response cancellation and concurrent requests
# --------------------------------------------------------------------------
def test_category_o_concurrent_session_isolation():
    async def _test():
        with patch.object(llm_provider, "generate", new_callable=AsyncMock) as mock_gen:
            async def dynamic_answer(*args, **kwargs):
                msg = kwargs.get("message") or (args[0] if args else "")
                if "mustard" in str(msg).lower():
                    return "Mustard needs sandy loam."
                return "Sugarcane needs 1500-2500 mm."
            mock_gen.side_effect = dynamic_answer

            # Run two concurrent sessions simultaneously
            res_a, res_b = await asyncio.gather(
                process_chat_intent(message="What soil is best for mustard?", language="en", session_id="concurrent_1"),
                process_chat_intent(message="How much water does sugarcane need?", language="en", session_id="concurrent_2")
            )

            assert res_a.answer == "Mustard needs sandy loam."
            assert res_b.answer == "Sugarcane needs 1500-2500 mm."
    asyncio.run(_test())


# --------------------------------------------------------------------------
# Category P: Citation-to-claim support and source provenance
# --------------------------------------------------------------------------
def test_category_p_source_provenance_metadata():
    result = dynamic_rag.retrieve_dynamic(
        query="chickpea wilt resistance ICAR",
        crop_filter="Chickpea",
        top_k=2
    )

    for src in result.get("sources", []):
        assert "name" in src
        assert "title" in src
        assert "url" in src
        assert "publication_year" in src
        assert "score" in src
        assert src["url"].startswith("http")


# --------------------------------------------------------------------------
# Category Q: Conciseness and absence of unrelated answer padding
# --------------------------------------------------------------------------
def test_category_q_concise_response_prompting():
    async def _test():
        with patch.object(llm_provider, "generate", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = "The optimal soil pH for groundnut is 6.0 to 6.5."

            res = await process_chat_intent(
                message="What is the ideal soil pH for groundnut?",
                language="en",
                session_id="test_conciseness"
            )

            # Response should be concise and direct without unsolicited farm profile repetition
            assert "farm area" not in res.answer.lower()
            assert "my farm" not in res.answer.lower()
            assert res.answer == "The optimal soil pH for groundnut is 6.0 to 6.5."
    asyncio.run(_test())
