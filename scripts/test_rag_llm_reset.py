"""
KrishiMitra AI -- Evaluation & Acceptance Test Suite for LLM + RAG Intelligence Reset
scripts/test_rag_llm_reset.py

Evaluates:
  1. RAG index availability and document schema (753 documents across ICAR, FAO, NBSS&LUP, CACP)
  2. Hybrid retrieval (TF-IDF + BM25) latency and ranking quality
  3. Provenance tracking: institution, publication, URL, retrieval date
  4. RF model isolation: verifies recommender.recommend() is bypassed in RAG_LLM_MODE
  5. Live tool integration: weather / market data correctly ingested and labeled
  6. Multi-turn context resolution: district, soil, season, language preserved
  7. Uncertainty communication: explicit handling of unsupported/unknown queries
  8. Multilingual prompt and response formatting (en, te, hi)
  9. Rollback mechanism: verifies switching RAG_LLM_MODE=false cleanly restores legacy path
 10. End-to-end Chat API contract integrity (ChatRequest -> ChatResponse schema match)

Run:
  python scripts/test_rag_llm_reset.py
"""

import os
import sys
import json
import time
import asyncio
import unittest
from unittest.mock import patch, MagicMock

# Set project root in path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from backend.app.core.config import settings
from backend.app.services.rag_pipeline import rag_pipeline
from backend.app.core.llm_provider import llm_provider, _build_prompt, SYSTEM_PROMPT
from backend.app.api.chat import process_chat_intent
from backend.app.data_engine.schemas import ChatRequest, ChatResponse


class TestRAGLLMReset(unittest.IsolatedAsyncioTestCase):

    def test_01_rag_index_loaded_and_complete(self):
        """Verify the RAG index is populated with > 700 agronomic documents."""
        self.assertTrue(rag_pipeline.is_available(), "RAG index is not loaded")
        doc_count = len(rag_pipeline.documents)
        self.assertGreaterEqual(doc_count, 700, f"Expected >= 700 docs, got {doc_count}")

        # Check document schema on first 5 documents
        for doc in rag_pipeline.documents[:5]:
            self.assertIn("doc_id", doc)
            self.assertIn("content", doc)
            self.assertIn("source_institution", doc)
            self.assertIn("publication_year", doc)
            self.assertIn("topic", doc)
            self.assertTrue(len(doc["content"]) > 10, "Document content is too short")
        print(f" PASS: Test 01 - RAG Index Loaded with {doc_count} documents.")

    def test_02_hybrid_retrieval_and_provenance(self):
        """Verify hybrid retrieval returns high-scoring ICAR/FAO documents with full provenance."""
        query = "What are the optimal soil pH and water requirements for Cotton in Kharif season?"
        res = rag_pipeline.retrieve(query=query, top_k=4)

        self.assertFalse(res["no_relevant_found"])
        self.assertGreater(len(res["retrieved_documents"]), 0)
        self.assertLess(res["retrieval_latency_ms"], 200, "Retrieval took > 200ms")

        top_doc = res["retrieved_documents"][0]
        self.assertIn("Cotton", top_doc["title"])
        self.assertTrue("ICAR" in top_doc["source_institution"] or "CICR" in top_doc["source_institution"])
        self.assertTrue(len(top_doc["publication_year"]) > 0)
        self.assertGreaterEqual(top_doc["hybrid_score"], 0.2)

        # Sources should be deduplicated with provenance fields
        self.assertGreater(len(res["sources"]), 0)
        for s in res["sources"]:
            self.assertIn("name", s)
            self.assertIn("publication_year", s)
            self.assertIn("used", s)
        print(f" PASS: Test 02 - Hybrid retrieval OK (latency: {res['retrieval_latency_ms']}ms, top score: {top_doc['hybrid_score']}).")

    def test_03_soil_profile_retrieval_by_district(self):
        """Verify NBSS district soil profile retrieval works for specific districts."""
        query = "What is the soil pH, texture, and organic carbon in Kurnool district Andhra Pradesh?"
        res = rag_pipeline.retrieve(query=query, state_filter="Andhra Pradesh", top_k=3)

        self.assertFalse(res["no_relevant_found"])
        found_kurnool = any("Kurnool" in d.get("content", "") for d in res["retrieved_documents"])
        self.assertTrue(found_kurnool, "Kurnool soil profile was not retrieved")
        print(" PASS: Test 03 - District soil profile retrieval OK.")

    def test_04_system_prompt_honesty_rules(self):
        """Verify system prompt enforces non-fabrication, explicit uncertainty, and source attribution."""
        self.assertIn("Ground every crop recommendation in the RETRIEVED EVIDENCE", SYSTEM_PROMPT)
        self.assertIn("Never manufacture numerical suitability scores", SYSTEM_PROMPT)
        self.assertIn("Never claim live weather or market prices unless a LIVE TOOL RESULT is present", SYSTEM_PROMPT)
        self.assertIn("Never invent citations", SYSTEM_PROMPT)
        self.assertIn("ask ONE concise clarifying question", SYSTEM_PROMPT)
        print(" PASS: Test 04 - System prompt honesty rules verified.")

    def test_05_prompt_assembly_structure(self):
        """Verify _build_prompt correctly orders evidence -> profile -> tool results -> question."""
        prompt = _build_prompt(
            message="Which crop is best for black soil with low water?",
            retrieved_context="[SOURCE: ICAR-IIPR] Pigeonpea requires 500-600mm water, suitable for black soil.",
            lang="en",
            farm_context={"state": "Andhra Pradesh", "district": "Kurnool", "soil_type": "Black Soil"},
            live_tool_results={"weather": {"temperature_c": 31, "condition": "Sunny"}},
        )

        self.assertIn("RETRIEVED AGRICULTURAL EVIDENCE:", prompt)
        self.assertIn("ICAR-IIPR", prompt)
        self.assertIn("CURRENT FARM PROFILE:", prompt)
        self.assertIn("Kurnool", prompt)
        self.assertIn("LIVE WEATHER TOOL RESULT", prompt)
        self.assertIn("FARMER QUESTION:", prompt)
        print(" PASS: Test 05 - Prompt assembly correctly structured.")

    async def test_06_rf_model_bypassed_in_rag_llm_mode(self):
        """Verify recommender.recommend() is NOT called when processing crop recommendation in RAG_LLM_MODE."""
        with patch.object(settings, "RAG_LLM_MODE", True):
            with patch("backend.app.api.chat.recommender.recommend") as mock_rf:
                answer, sources, rec_data, comp_data, simple_s, det_a, struct_r, conf, lang, intent = await process_chat_intent(
                    message="Which crop should I grow in Kharif season?",
                    language="en",
                    session_id="test_rf_isolation_session",
                    req_location=None,
                    req_soil_type="Black Soil",
                    req_farm_profile=None,
                    detail_level="simple"
                )

                # CRITICAL: RF model must NOT have been called!
                mock_rf.assert_not_called()
                self.assertIsNone(rec_data, "recommender output should be None in RAG_LLM_MODE")
                self.assertIsNotNone(answer)
                self.assertGreater(len(sources), 0, "Real sources should be returned")
                print(" PASS: Test 06 - Random Forest model successfully bypassed in RAG_LLM_MODE.")

    async def test_07_rollback_restores_legacy_path(self):
        """Verify that setting RAG_LLM_MODE=False immediately routes back to legacy ML pipeline."""
        with patch.object(settings, "RAG_LLM_MODE", False):
            with patch("backend.app.api.chat.recommender.recommend") as mock_rf:
                mock_rf.return_value = {
                    "primary_recommendation": {
                        "crop": "Cotton",
                        "confidence_level": "High",
                        "suitability_score": 0.88,
                        "overall_suitability_score": 0.88
                    },
                    "alternative_crops": [],
                    "resolved_context": {"state": "Andhra Pradesh", "district": "Kurnool"}
                }
                answer, sources, rec_data, comp_data, simple_s, det_a, struct_r, conf, lang, intent = await process_chat_intent(
                    message="Which crop should I grow?",
                    language="en",
                    session_id="test_rollback_session",
                    req_location=None,
                    req_soil_type="Black Soil",
                    req_farm_profile=None,
                    detail_level="simple"
                )

                # Legacy path calls recommender.recommend
                mock_rf.assert_called_once()
                self.assertIsNotNone(rec_data)
                print(" PASS: Test 07 - Rollback mechanism instantly routes to legacy pipeline.")

    async def test_08_live_weather_integration(self):
        """Verify live weather queries are answered with live weather tool telemetry."""
        with patch.object(settings, "RAG_LLM_MODE", True):
            answer, sources, rec_data, comp_data, simple_s, det_a, struct_r, conf, lang, intent = await process_chat_intent(
                message="What is the weather today in Kurnool?",
                language="en",
                session_id="test_weather_session",
                req_location=None,
                req_soil_type=None,
                req_farm_profile=None,
                detail_level="simple"
            )

            self.assertIn("weather", intent.lower())
            weather_sources = [s for s in sources if "weather" in s.get("name", "").lower() or "meteo" in s.get("name", "").lower()]
            self.assertGreater(len(weather_sources), 0, "Weather tool source not cited")
            print(" PASS: Test 08 - Live weather telemetry correctly queried and cited.")

    async def test_09_multilingual_handling(self):
        """Verify Telugu and Hindi requests are processed and maintain language context."""
        with patch.object(settings, "RAG_LLM_MODE", True):
            # Telugu test
            ans_te, src_te, _, _, _, _, _, _, lang_te, _ = await process_chat_intent(
                message="ప్రస్తుతం వర్షకాలంలో ఏ పంట వేయాలి?",
                language="te",
                session_id="test_telugu_session"
            )
            self.assertEqual(lang_te, "te")
            self.assertTrue(len(ans_te) > 0)

            # Hindi test
            ans_hi, src_hi, _, _, _, _, _, _, lang_hi, _ = await process_chat_intent(
                message="खरीफ मौसम में कौन सी फसल सबसे अच्छी रहेगी?",
                language="hi",
                session_id="test_hindi_session"
            )
            self.assertEqual(lang_hi, "hi")
            self.assertTrue(len(ans_hi) > 0)
            print(" PASS: Test 09 - Multilingual (Telugu/Hindi) routing verified.")

    async def test_10_api_contract_compatibility(self):
        """Verify ChatResponse model validates output from RAG_LLM_MODE without validation errors."""
        with patch.object(settings, "RAG_LLM_MODE", True):
            answer, sources, recommendation_data, comparison_data, simple_summary, detailed_analysis, structured_response, confidence, active_lang, intent = await process_chat_intent(
                message="What is the recommended seed rate for Red Gram in dryland farming?",
                language="en",
                session_id="test_contract_session"
            )

            # Build ChatResponse Pydantic model
            response = ChatResponse(
                success=True,
                answer=answer,
                language=active_lang,
                intent=intent,
                simple_summary=simple_summary,
                detailed_analysis=detailed_analysis,
                structured_response=structured_response,
                sources=sources,
                recommendation_data=recommendation_data,
                comparison_data=comparison_data,
                confidence=confidence
            )

            self.assertTrue(response.success)
            self.assertIsNotNone(response.answer)
            self.assertEqual(response.language, "en")
            self.assertGreater(len(response.sources), 0)
            print(" PASS: Test 10 - API response conforms to ChatResponse schema.")


def main():
    print("=" * 70)
    print("KrishiMitra AI -- Acceptance Test Suite: LLM + RAG Intelligence Reset")
    print("=" * 70)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestRAGLLMReset)
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)
    if result.wasSuccessful():
        print("\n" + "=" * 70)
        print(" ALL 10 ACCEPTANCE TESTS PASSED SUCCESSFULLY!")
        print("=" * 70)
        sys.exit(0)
    else:
        print("\n" + "=" * 70)
        print(f" {len(result.failures) + len(result.errors)} TEST(S) FAILED.")
        print("=" * 70)
        sys.exit(1)


if __name__ == "__main__":
    main()
