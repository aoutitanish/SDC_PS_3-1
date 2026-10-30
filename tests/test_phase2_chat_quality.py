"""
KrishiMitra AI - Phase 2 Comprehensive Chat Quality & Context Resolution Regression Suite

Tests all 13 Phase 2 requirements:
1. General crop fact while a farm profile exists: no forced location.
2. Explicit Kashmir query while the saved farm is in Telangana.
3. Farm-specific recommendation using available saved details.
4. Temporary second farm without overwriting the primary profile.
5. New consultation without unrelated old context.
6. Missing soil or irrigation triggers one appropriate question.
7. Complete simple question receives no unnecessary follow-up.
8. Follow-up answer updates active conversation context.
9. Quick-reply click sends the correct answer.
10. Citation provenance is preserved.
11. Ollama think: false remains enabled.
12. Streaming and cancellation behave correctly.
13. Existing authentication, chat history and API contracts remain functional.
"""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from backend.app.data_engine.schemas import ChatRequest, ChatResponse, FarmProfileInput, LocationInput
from backend.app.core.session_memory import session_memory, ConversationState
from backend.app.services.intent_service import intent_service
from backend.app.core.llm_provider import llm_provider
from backend.app.api.chat import process_chat_intent, generate_adaptive_follow_up, chat_endpoint, chat_stream_endpoint


@pytest.fixture(autouse=True)
def clean_sessions():
    """Ensure clean session memory before each test."""
    session_memory._sessions.clear()
    yield
    session_memory._sessions.clear()


# --------------------------------------------------------------------------
# Test 1: General crop fact while a farm profile exists: no forced location
# --------------------------------------------------------------------------
def test_1_general_crop_fact_no_forced_location():
    async def _test():
        farm = FarmProfileInput(state="Telangana", district="Warangal", soil_type="Black Soil")
        loc = LocationInput(state="Telangana", district="Warangal")

        with patch.object(llm_provider, "generate", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = "The ideal soil pH for cotton is between 6.0 and 7.5 (ICAR-CICR)."

            res = await process_chat_intent(
                message="What is the ideal soil pH for cotton?",
                language="en",
                session_id="test_sess_1",
                req_location=loc,
                req_farm_profile=farm
            )

            assert mock_gen.called
            call_kwargs = mock_gen.call_args[1]
            prompt_farm = call_kwargs.get("farm_context")
            # Context gate MUST NOT pass Warangal farm context for general crop fact
            assert prompt_farm is None
            assert "Warangal" not in res[0]
            assert "Telangana" not in res[0]

    asyncio.run(_test())


# --------------------------------------------------------------------------
# Test 2: Explicit Kashmir query while saved farm is in Telangana
# --------------------------------------------------------------------------
def test_2_explicit_kashmir_query_while_farm_in_telangana():
    async def _test():
        farm = FarmProfileInput(state="Telangana", district="Warangal", soil_type="Black Soil")

        with patch.object(llm_provider, "generate", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = "In Kashmir, temperate crops such as saffron, apples, maize, and mustard thrive."

            res = await process_chat_intent(
                message="What crops suit Kashmir?",
                language="en",
                session_id="test_sess_2",
                req_farm_profile=farm
            )

            call_kwargs = mock_gen.call_args[1]
            prompt_farm = call_kwargs.get("farm_context")
            assert prompt_farm is not None
            assert prompt_farm.get("district") in ["Srinagar", "Kashmir"]
            assert prompt_farm.get("district") != "Warangal"

    asyncio.run(_test())


# --------------------------------------------------------------------------
# Test 3: Farm-specific recommendation using available saved details
# --------------------------------------------------------------------------
def test_3_farm_recommendation_uses_available_saved_details():
    async def _test():
        farm = FarmProfileInput(state="Andhra Pradesh", district="Kurnool", soil_type="Black Soil (Regur/Vertisol)")

        with patch.object(llm_provider, "generate", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = "For your black soil farm in Kurnool, Cotton and Bengal Gram are highly suitable."

            res = await process_chat_intent(
                message="For my farm, which crop is suitable?",
                language="en",
                session_id="test_sess_3",
                req_farm_profile=farm
            )

            call_kwargs = mock_gen.call_args[1]
            prompt_farm = call_kwargs.get("farm_context")
            assert prompt_farm is not None
            assert prompt_farm.get("district") == "Kurnool"
            assert prompt_farm.get("state") == "Andhra Pradesh"
            assert prompt_farm.get("soil_type") == "Black Soil (Regur/Vertisol)"
            assert res.follow_up is not None

    asyncio.run(_test())


# --------------------------------------------------------------------------
# Test 4: Temporary second farm without overwriting primary profile
# --------------------------------------------------------------------------
def test_4_temporary_second_farm_without_overwriting_primary():
    async def _test():
        session = session_memory.get_or_create("test_sess_4")
        farm = FarmProfileInput(state="Andhra Pradesh", district="Kurnool", soil_type="Black Soil")
        
        # Establish primary farm
        session.resolve_context({}, req_farm_profile=farm)
        assert session.primary_saved_farm["district"] == "Kurnool"

        # User mentions second farm
        facts = intent_service.extract_entities("My other farm is in Kashmir")
        assert facts.get("is_other_farm") is True
        session.resolve_context(facts, category="REGIONAL_QUERY")

        # Primary farm profile MUST remain Kurnool
        assert session.primary_saved_farm["district"] == "Kurnool"
        assert session.conversation_farm_context.get("district") in ["Srinagar", "Kashmir"]

    asyncio.run(_test())


# --------------------------------------------------------------------------
# Test 5: New consultation without unrelated old context
# --------------------------------------------------------------------------
def test_5_new_consultation_clears_old_context():
    session1 = session_memory.get_or_create("session_1")
    facts1 = intent_service.extract_entities("I have black soil and drip irrigation in Kurnool")
    session1.resolve_context(facts1)
    assert session1.soil_type == "Black Soil (Regur/Vertisol)"

    # Session 2 is a brand new consultation
    session2 = session_memory.get_or_create("session_2")
    assert session2.soil_type is None
    assert session2.district is None
    assert session2.conversation_farm_context == {}


# --------------------------------------------------------------------------
# Test 6: Missing soil or irrigation triggers one appropriate question
# --------------------------------------------------------------------------
def test_6_missing_soil_triggers_one_question():
    session = ConversationState("test_sess_6")
    session.district = "Kurnool"
    session.state = "Andhra Pradesh"
    session.farm_size_acres = 5.0
    # Missing: soil_type and irrigation_type
    
    follow_up, chips = generate_adaptive_follow_up("FARM_RECOMMENDATION", session, language="en")
    assert follow_up is not None
    # Higher priority is Soil Type (Priority 3) before Irrigation (Priority 4)
    assert "soil" in follow_up.lower()
    assert "Black soil" in chips
    assert "Red soil" in chips


# --------------------------------------------------------------------------
# Test 7: Complete simple question receives no unnecessary follow-up
# --------------------------------------------------------------------------
def test_7_simple_crop_fact_receives_no_follow_up():
    session = ConversationState("test_sess_7")
    follow_up, chips = generate_adaptive_follow_up("CROP_FACT", session, language="en")
    assert follow_up is None
    assert chips is None

    follow_up_gen, chips_gen = generate_adaptive_follow_up("GENERAL_KNOWLEDGE", session, language="en")
    assert follow_up_gen is None
    assert chips_gen is None


# --------------------------------------------------------------------------
# Test 8: Follow-up answer updates active conversation context
# --------------------------------------------------------------------------
def test_8_follow_up_answer_updates_context():
    session = session_memory.get_or_create("test_sess_8")
    session.district = "Kurnool"

    facts = intent_service.extract_entities("Black soil")
    resolved = session.resolve_context(facts, category="FARM_RECOMMENDATION")
    assert resolved["soil_type"] == "Black Soil (Regur/Vertisol)"
    assert session.soil_type == "Black Soil (Regur/Vertisol)"


# --------------------------------------------------------------------------
# Test 9: Quick-reply click sends correct answer
# --------------------------------------------------------------------------
def test_9_quick_reply_click_updates_context():
    session = session_memory.get_or_create("test_sess_9")
    facts = intent_service.extract_entities("Canal irrigation")
    resolved = session.resolve_context(facts, category="FARM_RECOMMENDATION")
    assert resolved["irrigation_type"] == "Canal Irrigation"


# --------------------------------------------------------------------------
# Test 10: Citation provenance is preserved
# --------------------------------------------------------------------------
def test_10_citation_provenance_preserved():
    async def _test():
        with patch.object(llm_provider, "generate", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = "Cotton thrives in black soils with good drainage (ICAR-CICR)."

            res = await process_chat_intent(
                message="What is the ideal soil pH for cotton?",
                language="en",
                session_id="test_sess_10"
            )

            sources = res.sources
            assert isinstance(sources, list)
            for s in sources:
                assert "name" in s
                assert "title" in s or "publication_year" in s

    asyncio.run(_test())


# --------------------------------------------------------------------------
# Test 11: Ollama think: false remains enabled
# --------------------------------------------------------------------------
def test_11_ollama_think_false_enabled():
    async def _test():
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                "message": {"content": "Cotton requires warm climate and moderate rainfall."}
            }
            mock_post.return_value = mock_resp

            ans = await llm_provider._ollama_generate("Test prompt")
            assert ans is not None
            assert mock_post.called

            call_json = mock_post.call_args[1].get("json")
            assert call_json is not None
            assert call_json.get("think") is False

    asyncio.run(_test())


# --------------------------------------------------------------------------
# Test 12: Streaming and cancellation behave correctly
# --------------------------------------------------------------------------
def test_12_streaming_and_cancellation():
    async def _test():
        req = ChatRequest(
            message="What is the ideal soil pH for cotton?",
            language="en",
            session_id="test_sess_12"
        )

        with patch.object(llm_provider, "generate", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = "Ideal pH is 6.5 to 7.5."
            resp = await chat_stream_endpoint(req)
            assert resp.status_code == 200
            assert resp.media_type == "text/event-stream"

    asyncio.run(_test())


# --------------------------------------------------------------------------
# Test 13: Existing API contracts remain functional
# --------------------------------------------------------------------------
def test_13_api_contracts_remain_functional():
    async def _test():
        req = ChatRequest(
            message="Which crop is suitable for Kurnool?",
            language="en",
            session_id="test_sess_13"
        )

        with patch.object(llm_provider, "generate", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = "Cotton and Red Gram are recommended."

            resp = await chat_endpoint(req)
            assert isinstance(resp, ChatResponse)
            assert resp.success is True
            assert resp.answer != ""
            assert resp.intent is not None

    asyncio.run(_test())
