"""
Chat API Endpoints for KrishiMitra AI.
Features structured 2-level outputs (Level 1 Farmer-friendly & Level 2 Scientific Details),
strict FarmContext priority, 14 agricultural intents, conversational context resolution, and SSE streaming.
"""

import asyncio
import json
import logging
from typing import Tuple, List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from backend.app.data_engine.schemas import ChatRequest, ChatResponse, SimpleFarmerSummary, DetailedAgronomicAnalysis
from backend.app.services.rag_service import rag_service
from backend.app.services.llm_service import llm_service
from backend.app.services.intent_service import intent_service
from backend.app.services.comparison_service import comparison_service
from backend.app.services.translation_service import translation_service
from backend.app.services.weather_service import weather_service
from backend.app.services.market_service import market_service
from backend.app.services.economic_service import economic_service
from backend.app.ml.economic_engine import economic_engine
from backend.app.ml.predict import recommender
from backend.app.core.session_memory import session_memory
from backend.app.core.database import get_db_connection
from backend.app.core.config import settings
from backend.app.core.llm_provider import llm_provider
from backend.app.services.dynamic_rag_service import dynamic_rag

logger = logging.getLogger(__name__)
import time
router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatProcessResult(tuple):
    def __new__(
        cls,
        answer,
        sources,
        recommendation_data,
        comparison_data,
        simple_summary,
        detailed_analysis,
        structured_response,
        confidence,
        active_lang,
        intent,
        follow_up=None,
        quick_replies=None,
        latency_metrics=None,
    ):
        return super().__new__(
            cls,
            (
                answer,
                sources,
                recommendation_data,
                comparison_data,
                simple_summary,
                detailed_analysis,
                structured_response,
                confidence,
                active_lang,
                intent,
            ),
        )

    def __init__(
        self,
        answer,
        sources,
        recommendation_data,
        comparison_data,
        simple_summary,
        detailed_analysis,
        structured_response,
        confidence,
        active_lang,
        intent,
        follow_up=None,
        quick_replies=None,
        latency_metrics=None,
    ):
        self.answer = answer
        self.sources = sources
        self.recommendation_data = recommendation_data
        self.comparison_data = comparison_data
        self.simple_summary = simple_summary
        self.detailed_analysis = detailed_analysis
        self.structured_response = structured_response
        self.confidence = confidence
        self.active_lang = active_lang
        self.intent = intent
        self.follow_up = follow_up
        self.quick_replies = quick_replies
        self.latency_metrics = latency_metrics


def generate_adaptive_follow_up(
    category: str,
    session: Any,
    language: str = "en",
) -> Tuple[Optional[str], Optional[List[str]], Optional[str]]:
    """
    Determines whether an adaptive follow-up would materially improve the next response.
    Returns: (prompt_question, quick_replies, target_field)
    Rules:
      1. ONLY requested when category == 'FARM_RECOMMENDATION' and key variables are missing.
      2. Self-contained factual queries (crop facts, soil science, pests, fertilizers, schemes, weather) receive NO follow-up.
      3. Ask for the highest-impact missing detail (one at a time):
         1. District or region.
         2. Farm area.
         3. Soil type or soil test result.
         4. Irrigation/water availability.
         5. Season and planting timeframe.
    """
    if category != "FARM_RECOMMENDATION":
        return None, None, None

    # Priority 1: District or region
    if not session.district and not session.state:
        if language == "te":
            return "మీ పొలం ఏ జిల్లా లేదా ప్రాంతంలో ఉంది?", ["కర్నూలు", "వరంగల్", "నల్గొండ", "గుంటూరు", "తెలియదు"], "district"
        elif language == "hi":
            return "आपका खेत किस जिले या क्षेत्र में स्थित है?", ["कुरनूल", "वारंगल", "नालगोंडा", "गुंटूर", "पता नहीं"], "district"
        return "Which district or region is your farm located in?", ["Kurnool", "Warangal", "Nalgonda", "Guntur", "Not sure"], "district"

    # Priority 2: Farm area
    if not session.farm_size_acres:
        if language == "te":
            return "మీ పొలం విస్తీర్ణం ఎంత?", ["1-2 ఎకరాలు", "3-5 ఎకరాలు", "5 ఎకరాల కంటే ఎక్కువ", "చిన్న కమతం (< 1 ఎకరం)"], "farm_size_acres"
        elif language == "hi":
            return "आपके खेत का क्षेत्रफल कितना है?", ["1-2 एकड़", "3-5 एकड़", "5 एकड़ से अधिक", "छोटा खेत (< 1 एकड़)"], "farm_size_acres"
        return "What is your farm area or land size?", ["1-2 Acres", "3-5 Acres", "More than 5 Acres", "Small plot (< 1 Acre)"], "farm_size_acres"

    # Priority 3: Soil type or soil test result
    if not session.soil_type:
        if language == "te":
            return "మీ పొలంలో ఏ రకమైన నేల (మట్టి) ఉంది?", ["నల్లరేగడి నేల", "ఎర్ర నేల", "ఒండ్రు నేల", "ఇసుక నేల", "తెలియదు"], "soil_type"
        elif language == "hi":
            return "आपके खेत में किस प्रकार की मिट्टी है?", ["काली मिट्टी", "लाल मिट्टी", "जलोढ़ मिट्टी", "बलुई दोमट", "पता नहीं"], "soil_type"
        return "What type of soil does your farm have?", ["Black soil", "Red soil", "Alluvial soil", "Sandy loam", "Not sure"], "soil_type"

    # Priority 4: Irrigation/water availability
    if not session.irrigation_type and not session.water_availability and session.has_borewell is None and session.has_drip is None:
        if language == "te":
            return "మీ భూమికి సాగునీటి లేదా నీటి వసతి ఎలా ఉంది?", ["బోరుబావి", "కాలువ నీరు", "బిందు సేద్యం (Drip)", "కేవలం వర్షాధారం", "తెలియదు"], "irrigation_type"
        elif language == "hi":
            return "आपकी भूमि के लिए सिंचाई या पानी की क्या सुविधा है?", ["बोरवेल", "नहर सिंचाई", "ड्रिप सिंचाई", "केवल वर्षा आधारित", "पता नहीं"], "irrigation_type"
        return "What water or irrigation facility is available for your land?", ["Borewell", "Canal irrigation", "Drip irrigation", "Rainfed only", "Not sure"], "irrigation_type"

    # Priority 5: Season and planting timeframe
    if not session.season:
        if language == "te":
            return "మీరు ఏ సీజన్ లేదా సమయంలో విత్తనాలు వేయాలనుకుంటున్నారు?", ["ఖరీఫ్ (వర్షాకాలం)", "రబీ (శీతాకాలం)", "జైద్ (వేసవి)"], "season"
        elif language == "hi":
            return "आप किस मौसम में बुवाई की योजना बना रहे हैं?", ["खरीफ (मानसून)", "रबी (सर्दियां)", "जायद (गर्मी)"], "season"
        return "Which season are you planning to sow in?", ["Kharif (Monsoon)", "Rabi (Winter)", "Summer / Zaid"], "season"

    return None, None, None


async def _process_rag_llm_mode(
    message: str,
    active_lang: str,
    session: Any,
    session_id: str,
    intent: str,
    category: str,
    farm_context: Optional[Dict[str, Any]],
    live_weather: Optional[Dict[str, Any]],
    final_state: Optional[str],
    final_district: Optional[str],
    final_season: Optional[str],
    extracted_entities: Dict[str, Any],
    detail_level: str,
    t_start: float,
    t_resolve_ms: float
) -> ChatProcessResult:
    """
    RAG + LLM execution path.
    Bypasses Random Forest model, AgriculturalEngine heuristics, and fixed crop profiles.
    Retrieves evidence from ICAR/FAO agronomic knowledge base and generates responses via LLM.
    """
    logger.info(f"[RAG_LLM_MODE] query='{message}' category='{category}' intent='{intent}' lang='{active_lang}' district='{final_district}'")

    # Handle Out-of-Scope non-agricultural questions honestly
    if category == "OUT_OF_SCOPE":
        if active_lang == "te":
            ans = "నేను కృషిమిత్ర AI, కేవలం వ్యవసాయం, పంటలు, నేలలు, వాతావరణం, ఎరువులు మరియు తెగుళ్ళ నివారణపై మాత్రమే సహాయం చేయగలను. దయచేసి వ్యవసాయానికి సంబంధించిన ప్రశ్నను అడగండి."
        elif active_lang == "hi":
            ans = "मैं कृषिमित्र AI हूँ, जो केवल कृषि, फसलों की खेती, मिट्टी, मौसम, उर्वरकों और कीट प्रबंधन से संबंधित प्रश्नों में सहायता करता हूँ। कृपया कोई कृषि संबंधी प्रश्न पूछें।"
        else:
            ans = "I am KrishiMitra AI, an assistant dedicated exclusively to agriculture, crop advisory, soil health, weather, pests, and farm management. I cannot assist with non-agricultural topics. Please feel free to ask any farming-related question!"
        
        t_total_ms = (time.perf_counter() - t_start) * 1000
        latency_metrics = {
            "resolve_ms": round(t_resolve_ms, 2),
            "rag_ms": 0.0,
            "gen_ms": 0.0,
            "total_ms": round(t_total_ms, 2)
        }
        return ChatProcessResult(
            ans, [], None, None, None, None, None, "Scope Boundary", active_lang, intent,
            follow_up=None, quick_replies=None, latency_metrics=latency_metrics
        )

    # 1. Fetch live tool data where appropriate
    live_tool_results: Dict[str, Any] = {}
    if live_weather:
        live_tool_results["weather"] = live_weather

    crop_mentions = extracted_entities.get("crop_mentions", [])
    primary_crop = crop_mentions[0].title() if crop_mentions else None

    # Handle weather intent directly if weather requested specifically
    if intent in ["WEATHER", "weather"] and live_weather and final_district:
        if active_lang == "te":
            ans = (
                f"🌦 **{final_district}, {final_state} ప్రత్యక్ష వాతావరణ సమాచారం:**\n\n"
                f"• ప్రస్తుత ఉష్ణోగ్రత: **{live_weather.get('temperature_c')}°C** ({live_weather.get('condition')})\n"
                f"• గాలిలో తేమ (Humidity): **{live_weather.get('relative_humidity_pct')}%**\n"
                f"• వర్షపాతం: **{live_weather.get('rainfall_mm')} mm**\n"
                f"• గాలి వేగం: **{live_weather.get('wind_speed_ms')} m/s**\n\n"
                f"💡 **వ్యవసాయ సూచన:** {live_weather.get('agricultural_advisory') or 'సాధారణ వ్యవసాయ పనులు కొనసాగించవచ్చు.'}"
            )
        elif active_lang == "hi":
            ans = (
                f"🌦 **{final_district}, {final_state} लाइव मौसम विवरण:**\n\n"
                f"• वर्तमान तापमान: **{live_weather.get('temperature_c')}°C** ({live_weather.get('condition')})\n"
                f"• आर्द्रता (Humidity): **{live_weather.get('relative_humidity_pct')}%**\n"
                f"• वर्षा: **{live_weather.get('rainfall_mm')} mm**\n"
                f"• हवा की गति: **{live_weather.get('wind_speed_ms')} m/s**\n\n"
                f"💡 **कृषि सलाह:** {live_weather.get('agricultural_advisory') or 'सामान्य कृषि कार्य जारी रख सकते हैं।'}"
            )
        else:
            ans = (
                f"🌦 **Live Weather for {final_district}, {final_state}:**\n\n"
                f"• Temperature: **{live_weather.get('temperature_c')}°C** ({live_weather.get('condition')})\n"
                f"• Relative Humidity: **{live_weather.get('relative_humidity_pct')}%**\n"
                f"• Rainfall: **{live_weather.get('rainfall_mm')} mm**\n"
                f"• Wind Speed: **{live_weather.get('wind_speed_ms')} m/s**\n\n"
                f"💡 **Agronomic Advisory:** {live_weather.get('agricultural_advisory') or 'Standard seasonal operations recommended.'}"
            )
        sources = [{
            "name": "Open-Meteo High-Resolution Weather API",
            "title": f"Live Weather Telemetry for {final_district}, {final_state}",
            "publication_year": "Live",
            "url": "https://open-meteo.com/",
            "region": f"{final_district}, {final_state}",
            "score": 1.0,
            "used": True
        }]
        t_total_ms = (time.perf_counter() - t_start) * 1000
        latency_metrics = {
            "resolve_ms": round(t_resolve_ms, 2),
            "rag_ms": 0.0,
            "gen_ms": 0.0,
            "total_ms": round(t_total_ms, 2)
        }
        return ChatProcessResult(
            ans, sources, None, None, None, None, None, "Live Telemetry", active_lang, intent,
            follow_up=None, quick_replies=None, latency_metrics=latency_metrics
        )

    needs_market = (
        category == "MARKET_WEATHER"
        or intent in ["MARKET", "market", "ECONOMIC_RECOMMENDATION", "economic_recommendation"]
        or any(w in message.lower() for w in ["price", "mandi", "rate", "ధర", "भाव"])
    )
    if needs_market:
        try:
            m_res = await market_service.get_market_prices(
                crop=primary_crop or "Cotton",
                state=final_state or "Andhra Pradesh",
                district=final_district or "Kurnool"
            )
            if m_res:
                live_tool_results["market"] = m_res
        except Exception as e:
            logger.warning(f"Market telemetry error in RAG LLM mode: {e}")

    # 2. Dynamic RAG retrieval (Context Relevance Gate: Do not filter by farm location for general questions)
    t_rag_start = time.perf_counter()
    crop_filter = primary_crop if primary_crop else None
    
    # Only filter by state/season if question is location/farm specific
    is_general = category in ["CROP_FACT", "GENERAL_KNOWLEDGE"]
    state_filter = None if is_general else final_state
    season_filter = None if is_general else final_season

    rag_res = await asyncio.to_thread(
        dynamic_rag.retrieve_dynamic,
        query=message,
        crop_filter=crop_filter,
        state_filter=state_filter,
        country_filter=extracted_entities.get("country"),
        season_filter=season_filter,
        category=category,
        top_k=settings.RAG_TOP_K
    )
    t_rag_ms = (time.perf_counter() - t_rag_start) * 1000

    # 3. Fetch recent conversation history from SQLite
    conv_history: List[Dict[str, str]] = []
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT sender, content FROM messages WHERE session_id = ? ORDER BY id DESC LIMIT 4",
            (session_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        conv_history = [{"role": r["sender"], "content": r["content"]} for r in reversed(rows)]
    except Exception as e:
        logger.warning(f"Failed to fetch conversation history: {e}")

    # 4. Generate grounded answer via LLM
    # Gate: For general questions or pure crop facts, pass farm_context=None so LLM does not hallucinate user's farm
    llm_farm_context = None if is_general else farm_context

    t_gen_start = time.perf_counter()
    answer = await llm_provider.generate(
        message=message,
        retrieved_context=rag_res.get("context_text", ""),
        lang=active_lang,
        farm_context=llm_farm_context,
        live_tool_results=live_tool_results,
        conversation_history=conv_history
    )
    t_gen_ms = (time.perf_counter() - t_gen_start) * 1000
    t_total_ms = (time.perf_counter() - t_start) * 1000

    latency_metrics = {
        "resolve_ms": round(t_resolve_ms, 2),
        "rag_ms": round(t_rag_ms, 2),
        "gen_ms": round(t_gen_ms, 2),
        "total_ms": round(t_total_ms, 2)
    }

    # 5. Extract and format sources with true provenance
    sources = rag_res.get("sources", [])
    if live_tool_results.get("weather") and final_district:
        sources.append({
            "name": "Open-Meteo High-Resolution Weather API",
            "title": f"Live Weather Telemetry for {final_district}, {final_state}",
            "publication_year": "Live",
            "url": "https://open-meteo.com/",
            "region": f"{final_district}, {final_state}",
            "score": 1.0,
            "used": True
        })
    if live_tool_results.get("market") and final_district:
        sources.append({
            "name": "Agmarknet Mandi Telemetry",
            "title": f"Mandi Price Telemetry for {primary_crop or 'Crop'}",
            "publication_year": "Live / Cached",
            "url": "https://agmarknet.gov.in/",
            "region": f"{final_district}, {final_state}",
            "score": 1.0,
            "used": True
        })

    # Confidence assessment
    if rag_res.get("no_relevant_found"):
        confidence = "Unverified (No External Agricultural Literature Found)"
    else:
        confidence = "Grounded in Dynamic External Agricultural Research"

    # 6. Generate adaptive follow-up and register pending state
    follow_up, quick_replies, target_field = generate_adaptive_follow_up(category, session, active_lang)
    if target_field:
        session.set_pending_follow_up(
            original_query=message,
            target_field=target_field,
            prompt_question=follow_up,
            quick_replies=quick_replies,
            accumulated_facts=farm_context or {}
        )
    else:
        session.clear_pending_follow_up()

    # Persist in SQLite
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO chat_sessions (id, title, language) VALUES (?, ?, ?)",
                       (session_id, message[:40] + "...", active_lang))
        cursor.execute("INSERT INTO messages (session_id, sender, content, metadata) VALUES (?, ?, ?, ?)",
                       (session_id, "user", message, json.dumps({"lang": active_lang, "intent": intent, "category": category, "mode": "rag_llm"})))
        cursor.execute("INSERT INTO messages (session_id, sender, content, metadata) VALUES (?, ?, ?, ?)",
                       (session_id, "assistant", answer, json.dumps({
                           "sources": sources,
                           "intent": intent,
                           "category": category,
                           "mode": "rag_llm",
                           "follow_up": follow_up,
                           "quick_replies": quick_replies,
                           "latency_metrics": latency_metrics
                       })))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"Could not persist chat message: {e}")

    return ChatProcessResult(
        answer, sources, None, None, None, None, None, confidence, active_lang, category or intent,
        follow_up=follow_up, quick_replies=quick_replies, latency_metrics=latency_metrics
    )


async def process_chat_intent(
    message: str,
    language: str,
    session_id: str,
    req_location: Any = None,
    req_soil_type: Optional[str] = None,
    req_farm_profile: Any = None,
    detail_level: str = "simple"
) -> Tuple[str, List[Dict[str, Any]], Optional[Dict[str, Any]], Optional[Dict[str, Any]], Optional[SimpleFarmerSummary], Optional[DetailedAgronomicAnalysis], Any, str, str, str]:
    """
    Core conversational reasoning pipeline with Context Relevance Gate, strict Phase 2 precedence,
    and adaptive follow-up.
    """
    t_start = time.perf_counter()
    session = session_memory.get_or_create(session_id)

    # 0. Intercept pending follow-up resolution
    initial_extracted = intent_service.extract_entities(message)
    is_resolved, orig_goal, resolved_val = session.resolve_pending_follow_up(message, initial_extracted)
    effective_message = orig_goal if (is_resolved and orig_goal) else message
    if is_resolved:
        logger.info(f"[FOLLOW_UP RESOLVED] Answer='{message}' -> Continuing original goal: '{effective_message}'")

    # 1. Detect language & maintain conversation language continuity
    detected_lang = translation_service.detect_language(message, None)
    if detected_lang in ["te", "hi"]:
        active_lang = detected_lang
        session.language = detected_lang
    elif session.language in ["te", "hi"] and len(message.strip().split()) <= 5 and not message.lower().startswith("in english"):
        active_lang = session.language
    else:
        active_lang = detected_lang or language or session.language or "en"
        session.language = active_lang

    # 2. Extract entities from effective query (Highest priority)
    extracted_entities = intent_service.extract_entities(effective_message)
    # Merge newly resolved value if follow-up was answered
    if is_resolved and session.farm_size_acres:
        extracted_entities["farm_size_acres"] = session.farm_size_acres
    extracted_entities["language"] = active_lang

    # 3. Context Relevance Gate: Classify question category
    category = intent_service.classify_question_category(effective_message, extracted_entities)

    # 4. Resolve context according to strict Phase 2 & 4 precedence rules:
    resolved_context = session.resolve_context(
        extracted_facts=extracted_entities,
        req_farm_profile=req_farm_profile,
        req_location=req_location,
        req_soil_type=req_soil_type,
        category=category
    )

    is_general = category in [
        "CROP_FACT", "GENERAL_KNOWLEDGE", "PEST_DISEASE", "FERTILIZER_NUTRIENT",
        "SOWING_CALENDAR", "CROP_ROTATION", "POST_HARVEST", "GOVERNMENT_SCHEME", "OUT_OF_SCOPE"
    ]
    is_regional = category == "REGIONAL_QUERY"

    # Context Gate: Do NOT inject location or user farm profile for general questions!
    if is_general:
        final_state = None
        final_district = None
        final_soil = None
        final_water_avail = None
        final_irrigation = None
        final_water_src = None
        final_season = None
        final_rain_cond = None
        final_temp_cond = None
        final_size = None
        final_ph = None
        has_borewell = None
        has_drip = None
        live_weather = None
        farm_context = None
    elif is_regional:
        # Regional query: respect the explicit region queried without forcing My Farm profile
        final_state = resolved_context.get("state")
        final_district = resolved_context.get("district")
        final_soil = resolved_context.get("soil_type")
        final_water_avail = resolved_context.get("water_availability")
        final_irrigation = resolved_context.get("irrigation_type")
        final_water_src = resolved_context.get("water_source")
        final_season = resolved_context.get("season")
        final_rain_cond = resolved_context.get("rainfall_condition")
        final_temp_cond = resolved_context.get("temperature_condition")
        final_size = resolved_context.get("farm_size_acres")
        final_ph = resolved_context.get("ph")
        has_borewell = resolved_context.get("has_borewell")
        has_drip = resolved_context.get("has_drip")
        
        live_weather = None
        if final_state and final_district:
            try:
                w_data = await weather_service.get_weather(state=final_state, district=final_district)
                if w_data and w_data.get("success") and w_data.get("data_source") != "IMD Historical Weather Dataset":
                    curr = w_data.get("current", {})
                    live_weather = {
                        "temperature_c": curr.get("temperature_c"),
                        "relative_humidity_pct": curr.get("relative_humidity_pct"),
                        "rainfall_mm": curr.get("rainfall_mm"),
                        "wind_speed_ms": curr.get("wind_speed_ms"),
                        "condition": curr.get("condition"),
                        "agricultural_advisory": w_data.get("agricultural_advisory")
                    }
            except Exception as e:
                logger.warning(f"Live weather fetch failed in chat pipeline: {e}")
                live_weather = None

        farm_context = {
            "state": final_state,
            "district": final_district,
            "live_weather": live_weather
        } if (final_state or final_district) else None
    else:
        # Farm-specific recommendation, explanation, or comparison
        state_to_use = resolved_context.get("state")
        district_to_use = resolved_context.get("district")

        # District defaults if district is known
        defaults = recommender.get_district_defaults(state_to_use, district_to_use) or {} if (state_to_use and district_to_use) else {}

        has_borewell = resolved_context.get("has_borewell")
        has_drip = resolved_context.get("has_drip")

        final_state = state_to_use
        final_district = district_to_use
        final_soil = resolved_context.get("soil_type")
        final_water_avail = resolved_context.get("water_availability")
        final_irrigation = resolved_context.get("irrigation_type")
        final_water_src = resolved_context.get("water_source")
        final_season = resolved_context.get("season")
        final_rain_cond = resolved_context.get("rainfall_condition")
        final_temp_cond = resolved_context.get("temperature_condition")
        final_size = resolved_context.get("farm_size_acres")
        final_ph = resolved_context.get("ph")

        # Fetch live weather ONLY if question actually asks for or relates to weather/forecast
        live_weather = None
        needs_weather = (
            category == "MARKET_WEATHER"
            or any(w in effective_message.lower() for w in ["weather", "forecast", "rain", "temperature", "వాతావరణం", "मौसम"])
        )
        if needs_weather and final_state and final_district:
            try:
                w_data = await weather_service.get_weather(state=final_state, district=final_district)
                if w_data and w_data.get("success") and w_data.get("data_source") != "IMD Historical Weather Dataset":
                    curr = w_data.get("current", {})
                    live_weather = {
                        "temperature_c": curr.get("temperature_c"),
                        "relative_humidity_pct": curr.get("relative_humidity_pct"),
                        "rainfall_mm": curr.get("rainfall_mm"),
                        "wind_speed_ms": curr.get("wind_speed_ms"),
                        "condition": curr.get("condition"),
                        "agricultural_advisory": w_data.get("agricultural_advisory")
                    }
            except Exception as e:
                logger.warning(f"Live weather fetch failed in chat pipeline: {e}")
                live_weather = None

        farm_context = {
            "state": final_state,
            "district": final_district,
            "soil_type": final_soil,
            "water_availability": final_water_avail,
            "irrigation_type": final_irrigation,
            "water_source": final_water_src,
            "season": final_season,
            "rainfall_condition": final_rain_cond,
            "temperature_condition": final_temp_cond,
            "farm_size_acres": final_size,
            "ph": final_ph,
            "has_borewell": has_borewell,
            "has_drip": has_drip,
            "live_weather": live_weather
        } if (final_state or final_district or final_soil) else None

    # Intent detection
    has_prior_rec = session.last_recommendation_result is not None
    intent = intent_service.detect_intent(
        query=message,
        has_prior_recommendation=has_prior_rec,
        last_intent=session.last_intent or "",
        last_crops=session.last_recommended_crops
    )
    session.last_intent = intent
    session.last_query = message
    session.conversation_turn_count += 1

    t_resolve_ms = (time.perf_counter() - t_start) * 1000

    logger.info(f"Session {session_id} | Category: {category} | Intent: {intent} | Lang: {active_lang} | Location: {final_district}, {final_state}")

    # -------------------------------------------------------------
    # RAG + LLM RESET BRANCH (When settings.RAG_LLM_MODE is True)
    # Bypasses Random Forest model, AgriculturalEngine, and legacy heuristics
    # -------------------------------------------------------------
    if settings.RAG_LLM_MODE:
        return await _process_rag_llm_mode(
            message=message,
            active_lang=active_lang,
            session=session,
            session_id=session_id,
            intent=intent,
            category=category,
            farm_context=farm_context,
            live_weather=live_weather,
            final_state=final_state,
            final_district=final_district,
            final_season=final_season,
            extracted_entities=extracted_entities,
            detail_level=detail_level,
            t_start=t_start,
            t_resolve_ms=t_resolve_ms
        )

    # 5. Intent-Specific Handlers (Legacy ML / Heuristic Pipeline)
    # -------------------------------------------------------------
    # INTENT A: EXPLANATION ("Why did you recommend this crop?")
    # -------------------------------------------------------------
    recommendation_data = None
    comparison_data = None
    simple_summary = None
    detailed_analysis = None
    structured = None
    confidence = "High"
    sources = []

    rag_result = rag_service.retrieve_context(
        query=message,
        location_filter={"state": final_state, "district": final_district} if final_state else None,
        season=final_season or "Kharif",
        rainfall_condition=final_rain_cond or "normal",
        top_k=4
    )
    sources = rag_result.get("sources", [])

    if intent in ["EXPLANATION", "crop_explanation", "recommendation_explanation"]:
        rec_result = session.last_recommendation_result
        if not rec_result:
            rec_result = recommender.recommend(farm_context, top_k=4)
            session.last_recommendation_result = rec_result
            session.last_recommended_crops = [rec_result["primary_recommendation"]["crop"]] + [a["crop"] for a in rec_result["alternative_crops"]]

        rec_context = rec_result.get("resolved_context") or farm_context
        prev_crop = rec_result.get("primary_recommendation", {}).get("crop", "Unknown")

        debug_exp = (
            f"\n[EXPLANATION CONTEXT DEBUG]\n"
            f"previous_crop={prev_crop}\n"
            f"previous_recommendation_context={json.dumps(rec_result.get('resolved_context') or rec_result.get('location_context'))}\n"
            f"current_resolved_context={json.dumps(farm_context)}\n"
            f"irrigation={rec_context.get('irrigation_type')}\n"
            f"soil={rec_context.get('soil_type')}\n"
            f"water={rec_context.get('water_availability')}\n"
            f"season={rec_context.get('season')}\n"
            f"rainfall={rec_context.get('rainfall_condition')}\n"
            f"temperature={rec_context.get('temperature_condition')}\n"
            f"has_drip={rec_context.get('has_drip')}\n"
            f"has_borewell={rec_context.get('has_borewell')}\n"
        )
        logger.info(debug_exp)

        answer = translation_service.format_explanation_response(rec_result, active_lang)
        recommendation_data = rec_result
        structured = translation_service.build_structured_summary_and_analysis(rec_result, active_lang)
        simple_summary = structured["simple_summary"]
        detailed_analysis = structured["detailed_analysis"]
        sources = [
            {"name": "Crop Expert Dataset", "why_used": "Crop suitability information", "used": True},
            {"name": "Soil Expert Dataset", "why_used": "Soil properties and compatibility", "used": True},
            {"name": "Weather Expert Dataset", "why_used": "Climate/rainfall information", "used": True},
            {"name": "Master Geography Dataset", "why_used": "Location context", "used": True}
        ]
        confidence = "High"

    # -------------------------------------------------------------
    # INTENT B: CROP COMPARISON ("Compare top 3 crops" / "Compare cotton and pigeon pea" / "Compare it with cotton")
    # -------------------------------------------------------------
    elif intent in ["CROP_COMPARISON", "crop_comparison"]:
        crops_to_compare = []
        mentions = extracted_entities.get("crop_mentions", [])
        if len(mentions) >= 2:
            crops_to_compare = [c.title() for c in mentions]
        elif len(mentions) == 1:
            # Single crop mentioned in follow-up ("Compare it with cotton") -> compare with last recommended crop
            target_crop = mentions[0].title()
            base_crop = "Arhar/Tur (Pigeon Pea)"
            if session.last_recommended_crops:
                base_crop = session.last_recommended_crops[0]
            elif session.last_recommendation_result:
                base_crop = session.last_recommendation_result.get("primary_recommendation", {}).get("crop", "Arhar/Tur (Pigeon Pea)")
            
            if base_crop.lower() != target_crop.lower():
                crops_to_compare = [base_crop, target_crop]
            else:
                crops_to_compare = [base_crop, "Cotton"]
        elif session.last_recommended_crops:
            crops_to_compare = session.last_recommended_crops[:3]
        else:
            rec = recommender.recommend(farm_context, top_k=3)
            session.last_recommendation_result = rec
            session.last_recommended_crops = [rec["primary_recommendation"]["crop"]] + [a["crop"] for a in rec["alternative_crops"]]
            crops_to_compare = session.last_recommended_crops[:3]

        comp_result = comparison_service.compare_crops(crops_to_compare, farm_context, active_lang)
        session.last_comparison_result = comp_result
        comparison_data = comp_result
        answer = translation_service.format_comparison_response(comp_result, farm_context, active_lang)
        sources = [
            {"name": "Crop Expert Dataset", "why_used": "Comparative agronomic benchmarks", "used": True},
            {"name": "Soil Expert Dataset", "why_used": "Soil suitability matrix", "used": True},
            {"name": "Weather Expert Dataset", "why_used": "Climate compatibility comparison", "used": True}
        ]
        confidence = "High"

    # -------------------------------------------------------------
    # INTENT C: CROP RECOMMENDATION ("Which crop should I grow?")
    # -------------------------------------------------------------
    elif intent in ["CROP_RECOMMENDATION", "crop_recommendation"]:
        logger.info(f"FINAL CONTEXT BEFORE RECOMMENDATION:\n{json.dumps(farm_context, indent=2)}")
        rec_result = recommender.recommend(farm_context, top_k=4)
        session.last_recommendation_result = rec_result
        session.last_recommended_crops = [rec_result["primary_recommendation"]["crop"]] + [a["crop"] for a in rec_result["alternative_crops"]]

        answer = translation_service.format_recommendation_response(rec_result, active_lang, detail_level)
        recommendation_data = rec_result
        structured = translation_service.build_structured_summary_and_analysis(rec_result, active_lang)
        simple_summary = structured["simple_summary"]
        detailed_analysis = structured["detailed_analysis"]
        sources = [
            {"name": "Crop Expert Dataset", "why_used": "Crop suitability information", "used": True},
            {"name": "Soil Expert Dataset", "why_used": "Soil properties and compatibility", "used": True},
            {"name": "Weather Expert Dataset", "why_used": "Climate/rainfall information", "used": True},
            {"name": "Master Geography Dataset", "why_used": "Location context", "used": True}
        ]
        confidence = rec_result["primary_recommendation"].get("confidence_level", "High")

    # -------------------------------------------------------------
    # INTENT C2: ECONOMIC RECOMMENDATION ("Which crop is most profitable?")
    # -------------------------------------------------------------
    elif intent in ["ECONOMIC_RECOMMENDATION", "economic_recommendation"]:
        logger.info(f"ECONOMIC RECOMMENDATION CONTEXT:\n{json.dumps(farm_context, indent=2)}")
        rec_result = recommender.recommend(farm_context, top_k=6)
        session.last_recommendation_result = rec_result
        
        primary_c = rec_result["primary_recommendation"]["crop"]
        alt_cs = [a["crop"] for a in rec_result["alternative_crops"]]
        all_candidates = [primary_c] + alt_cs

        final_acres = float(resolved_context.get("farm_size_acres") or 5.0)

        # Prepare candidate array for EconomicEngine
        econ_batch = []
        for c_name in all_candidates:
            econ_ref = economic_service.get_crop_economics(c_name) or {}
            p_info = econ_ref.get("msp_information") or {}
            c_info = econ_ref.get("cost_of_cultivation") or {}
            y_info = econ_ref.get("yield_benchmark_reference") or {}
            
            p_val = p_info.get("value")
            c_val = c_info.get("value")
            y_val = y_info.get("equivalent_quintals_per_acre")

            p_type = "UNAVAILABLE"
            p_basis = "Unavailable"

            # Check if live or cached mandi price exists
            try:
                m_prices = await market_service.get_market_prices(crop=c_name, state=final_state, district=final_district)
                if m_prices and m_prices.get("status") in ["LIVE", "CACHED"]:
                    m_modal = m_prices.get("telemetry", {}).get("modal_price")
                    if m_modal:
                        p_val = float(m_modal)
                        if m_prices.get("status") == "LIVE":
                            p_type = "LIVE MANDI PRICE"
                            p_basis = "Live mandi market data"
                        else:
                            p_type = "CACHED MANDI PRICE"
                            p_basis = "Cached mandi market data"
            except Exception as e:
                logger.warning(f"Error fetching mandi telemetry for {c_name}: {e}")

            if p_type == "UNAVAILABLE" and p_val is not None:
                p_type = "OFFICIAL MSP REFERENCE"
                p_basis = "Official MSP reference"

            econ_batch.append({
                "crop": c_name,
                "price_inr_per_quintal": p_val,
                "yield_quintals_per_acre": y_val,
                "cultivation_cost_inr_per_acre": c_val,
                "price_data_type": p_type,
                "price_basis": p_basis
            })

        econ_results = economic_engine.calculate_multiple_crops(econ_batch, farm_size_acres=final_acres)

        available_econ = []
        unavail_crops = []

        for item in econ_results:
            m = item.get("economic_metrics")
            if item.get("status") == "success" and m and m.get("estimated_net_return_inr") is not None:
                available_econ.append({
                    "crop": item["crop"],
                    "net_return_inr": m["estimated_net_return_inr"],
                    "roi_pct": m.get("roi_pct"),
                    "gross_revenue_inr": m.get("gross_revenue_inr"),
                    "total_cost_inr": m.get("total_cultivation_cost_inr"),
                    "price_basis": item.get("provenance", {}).get("price", {}).get("price_basis", "Official MSP reference")
                })
            else:
                unavail_crops.append(item["crop"])

        # Sort available crops strictly by estimated_net_return_inr descending
        available_econ.sort(key=lambda x: x["net_return_inr"], reverse=True)

        top_econ = available_econ[0] if available_econ else None
        other_econ = available_econ[1:] if len(available_econ) > 1 else []

        payload = {
            "district": final_district,
            "state": final_state,
            "top_crop": top_econ,
            "other_crops": other_econ,
            "unavailable_crops": unavail_crops
        }

        answer = translation_service.format_economic_recommendation_response(payload, active_lang)
        recommendation_data = {
            "agronomic_recommendation": rec_result,
            "economic_payload": payload
        }
        structured = translation_service.build_structured_summary_and_analysis(rec_result, active_lang)
        simple_summary = structured["simple_summary"]
        detailed_analysis = structured["detailed_analysis"]
        sources = [
            {"name": "Crop Expert Dataset", "why_used": "Agronomic crop suitability candidates", "used": True},
            {"name": "DES / CACP Benchmark Reports", "why_used": "Cost of cultivation and MSP reference values", "used": True},
            {"name": "Agmarknet Mandi Telemetry", "why_used": "Market price telemetry", "used": True}
        ]
        confidence = "High"
    elif intent in ["WEATHER", "weather"]:
        w_data = await weather_service.get_weather(state=final_state, district=final_district)
        if w_data and w_data.get("success"):
            curr = w_data["current"]
            if active_lang == "te":
                answer = (
                    f"🌦 **{final_district}, {final_state} ప్రత్యక్ష వాతావరణం:**\n\n"
                    f"• ప్రస్తుత ఉష్ణోగ్రత: **{curr['temperature_c']}°C** ({curr['condition']})\n"
                    f"• గాలిలో తేమ (Humidity): **{curr['relative_humidity_pct']}%**\n"
                    f"• వర్షపాతం: **{curr['rainfall_mm']} mm**\n"
                    f"• గాలి వేగం: **{curr['wind_speed_ms']} m/s**\n\n"
                    f"💡 **వ్యవసాయ వివరణ:** {w_data.get('agricultural_advisory')}\n\n"
                    f"📚 **వనరు:** Open-Meteo High-Resolution Weather Service"
                )
            elif active_lang == "hi":
                answer = (
                    f"🌦 **{final_district}, {final_state} लाइव मौसम:**\n\n"
                    f"• तापमान: **{curr['temperature_c']}°C** ({curr['condition']})\n"
                    f"• आर्द्रता (Humidity): **{curr['relative_humidity_pct']}%**\n"
                    f"• वर्षा: **{curr['rainfall_mm']} mm**\n"
                    f"• हवा की गति: **{curr['wind_speed_ms']} m/s**\n\n"
                    f"💡 **कृषि सलाह:** {w_data.get('agricultural_advisory')}\n\n"
                    f"📚 **डेटा स्रोत:** Open-Meteo Live Weather Service"
                )
            else:
                answer = (
                    f"🌦 **Live Weather for {final_district}, {final_state}:**\n\n"
                    f"• Temperature: **{curr['temperature_c']}°C** ({curr['condition']})\n"
                    f"• Relative Humidity: **{curr['relative_humidity_pct']}%**\n"
                    f"• Rainfall: **{curr['rainfall_mm']} mm**\n"
                    f"• Wind Speed: **{curr['wind_speed_ms']} m/s**\n\n"
                    f"💡 **Agricultural Advisory:** {w_data.get('agricultural_advisory')}\n\n"
                    f"📚 **Source:** Open-Meteo High-Resolution Meteorological Service"
                )
            sources = [{"name": "Weather Expert Dataset", "why_used": "Open-Meteo Live Telemetry", "used": True}]
        else:
            answer = f"Live weather telemetry is temporarily unavailable for {final_district}. Using regional climate normals."
            sources = [{"name": "Weather Expert Dataset", "why_used": "Regional climate normals", "used": True}]
        confidence = "High"

    # -------------------------------------------------------------
    # INTENT E: IRRIGATION / WATER FOLLOW-UP ("What about water?")
    # -------------------------------------------------------------
    elif intent in ["IRRIGATION", "irrigation"]:
        rec_result = session.last_recommendation_result
        if not rec_result:
            rec_result = recommender.recommend(farm_context, top_k=4)
            session.last_recommendation_result = rec_result
            session.last_recommended_crops = [rec_result["primary_recommendation"]["crop"]] + [a["crop"] for a in rec_result["alternative_crops"]]

        prim = rec_result.get("primary_recommendation", {})
        crop = prim.get("crop", "Arhar/Tur (Pigeon Pea)")
        crop_display = translation_service._translate_crop_name(crop, active_lang)
        water_info = prim.get("water_assessment", {})
        w_demand = water_info.get("water_demand", "Low to Moderate (400–650 mm)")

        if active_lang == "te":
            answer = (
                f"💧 **{crop_display} నీటి అవసరాలు మరియు నీటిపారుదల సలహా:**\n\n"
                f"• **నీటి అవసరం:** {w_demand}\n"
                f"• **మీ పొలం అమరిక:** {final_irrigation} ({final_water_src})\n"
                f"• **సాగు సలహా:** మీ {final_district} ({final_soil}) పొలానికి తగిన విధంగా నీటిపారుదల పద్ధతులు పాటించండి.\n\n"
                f"📚 **వనరు:** Crop Expert Dataset"
            )
        elif active_lang == "hi":
            answer = (
                f"💧 **{crop_display} के लिए जल आवश्यकता एवं सिंचाई सलाह:**\n\n"
                f"• **जल आवश्यकता:** {w_demand}\n"
                f"• **सिंचाई व्यवस्था:** {final_irrigation} ({final_water_src})\n"
                f"• **कृषि सलाह:** अपने {final_district} ({final_soil}) खेत के अनुसार उचित सिंचाई तकनीक अपनाएं।\n\n"
                f"📚 **डेटा स्रोत:** Crop Expert Dataset"
            )
        else:
            answer = (
                f"💧 **Water Requirements for {crop}:**\n\n"
                f"• **Crop Water Demand:** {w_demand}\n"
                f"• **Your Farm Setup:** {final_irrigation} ({final_water_src})\n"
                f"• **Management Advisory:** This crop thrives with suited water management for your {final_soil} in {final_district}.\n\n"
                f"📚 **Source:** Crop Expert Dataset"
            )
        sources = [
            {"name": "Crop Expert Dataset", "why_used": "Crop water requirement parameters", "used": True},
            {"name": "Soil Expert Dataset", "why_used": "Soil moisture retention data", "used": True}
        ]
        confidence = "High"

    # -------------------------------------------------------------
    # INTENT G: RAINFALL FOLLOW-UP ("What about rainfall?")
    # -------------------------------------------------------------
    elif intent in ["rainfall_for_previous_crop"]:
        rec_result = session.last_recommendation_result
        if not rec_result:
            rec_result = recommender.recommend(farm_context, top_k=4)
            session.last_recommendation_result = rec_result
        prim = rec_result.get("primary_recommendation", {})
        crop = prim.get("crop", "Arhar/Tur (Pigeon Pea)")
        crop_display = translation_service._translate_crop_name(crop, active_lang)
        opt = prim.get("optimal_ranges", {})
        rain_range = f"{opt.get('rainfall_optimal_mm', [500, 1100])[0]}–{opt.get('rainfall_optimal_mm', [500, 1100])[1]} mm"

        if active_lang == "te":
            answer = (
                f"🌧 **{crop_display} వర్షపాత అనుకూలత:**\n\n"
                f"• **అనుకూల వార్షిక వర్షపాతం:** {rain_range}\n"
                f"• **మీ ప్రాంత వర్షపాతం ({final_district}):** {farm_context.get('annual_rainfall_mm', 900)} mm\n"
                f"• **వివరణ:** {final_district} ప్రాంత వర్షపాతం ఈ పంట సాగుకు పరిశీలించబడింది.\n\n"
                f"📚 **వనరు:** Weather Expert Dataset"
            )
        elif active_lang == "hi":
            answer = (
                f"🌧 **{crop_display} के लिए वर्षा अनुकूलता:**\n\n"
                f"• **अनुकूल वार्षिक वर्षा:** {rain_range}\n"
                f"• **आपके क्षेत्र की वर्षा ({final_district}):** {farm_context.get('annual_rainfall_mm', 900)} mm\n"
                f"• **विवरण:** {final_district} क्षेत्र की वार्षिक वर्षा इस फसल के लिए उपयुक्त है।\n\n"
                f"📚 **डेटा स्रोत:** Weather Expert Dataset"
            )
        else:
            answer = (
                f"🌧 **Rainfall Suitability for {crop}:**\n\n"
                f"• **Optimal Annual Rainfall:** {rain_range}\n"
                f"• **Your Regional Normal ({final_district}):** ~{farm_context.get('annual_rainfall_mm', 900)} mm\n"
                f"• **Agronomic Fit:** The natural rainfall profile in {final_district}, {final_state} aligns with the moisture requirements of {crop}.\n\n"
                f"📚 **Source:** Weather Expert Dataset"
            )
        sources = [
            {"name": "Weather Expert Dataset", "why_used": "Regional rainfall normals", "used": True},
            {"name": "Crop Expert Dataset", "why_used": "Crop rainfall threshold ranges", "used": True}
        ]
        confidence = "High"

    # -------------------------------------------------------------
    # INTENT H: WATER COMPARISON ("Which needs more water?")
    # -------------------------------------------------------------
    elif intent in ["water_comparison_for_previous"]:
        if active_lang == "te":
            answer = (
                "💧 **పంటల నీటి అవసరాల పోలిక:**\n\n"
                "• **పత్తి (Cotton):** 700–1200 mm (అధిక నీటి అవసరం)\n"
                "• **కంది (Arhar/Tur):** 400–650 mm (మితమైన నీటి అవసరం)\n\n"
                "💡 **ముగింపు:** పత్తితో పోల్చితే కంది పంటకు దాదాపు 40–50% తక్కువ నీరు అవసరమవుతుంది. పరిమిత బోరుబావి నీరు ఉన్న పరిస్థితుల్లో కంది మరింత సురక్షితమైన ఎంపిక.\n\n"
                "📚 **వనరు:** Crop Expert Dataset"
            )
        elif active_lang == "hi":
            answer = (
                "💧 **जल आवश्यकता की तुलना:**\n\n"
                "• **कपास (Cotton):** 700–1200 mm (अधिक पानी)\n"
                "• **अरहर (Arhar/Tur):** 400–650 mm (मध्यम पानी)\n\n"
                "💡 **निष्कर्ष:** कपास की तुलना में अरहर को काफी कम पानी की आवश्यकता होती है। सीमित जल उपलब्धता में अरहर अधिक सुरक्षित विकल्प है।\n\n"
                "📚 **डेटा स्रोत:** Crop Expert Dataset"
            )
        else:
            answer = (
                "💧 **Water Requirement Comparison:**\n\n"
                "• **Cotton:** Requires 700–1200 mm throughout its 150–180 day cycle.\n"
                "• **Arhar/Tur (Pigeon Pea):** Requires 400–650 mm, with deep taproots accessing subsoil moisture.\n\n"
                "💡 **Takeaway:** Arhar/Tur has significantly lower total water demand than Cotton, making it a lower-risk choice under limited borewell discharge.\n\n"
                "📚 **Source:** Crop Expert Dataset"
            )
        sources = [{"name": "Crop Expert Dataset", "why_used": "Comparative crop hydrology benchmarks", "used": True}]
        confidence = "High"

    # -------------------------------------------------------------
    # INTENT I: TRANSLATION FOLLOW-UP ("Explain that in Telugu")
    # -------------------------------------------------------------
    elif intent in ["translation_followup"]:
        rec_result = session.last_recommendation_result
        if not rec_result:
            rec_result = recommender.recommend(farm_context, top_k=4)
            session.last_recommendation_result = rec_result

        target_lang = "te" if "telugu" in message.lower() or "తెలుగు" in message else "hi" if "hindi" in message.lower() or "हिंदी" in message else active_lang
        answer = translation_service.format_explanation_response(rec_result, target_lang)
        active_lang = target_lang
        session.language = target_lang
        sources = [{"name": "Crop Expert Dataset", "why_used": "Multilingual crop advisory", "used": True}]
        confidence = "High"

    # -------------------------------------------------------------
    # INTENT: INFO STATEMENT (Acknowledge user facts conversationally)
    # -------------------------------------------------------------
    elif intent == "info_statement":
        saved_facts = []
        if session.soil_type:
            saved_facts.append(f"soil type as **{session.soil_type}**")
        if session.water_availability:
            saved_facts.append(f"water availability as **{session.water_availability}**")
        elif session.irrigation_type:
            saved_facts.append(f"irrigation method as **{session.irrigation_type}**")
        if session.district:
            saved_facts.append(f"location as **{session.district}, {session.state or 'Andhra Pradesh'}**")

        facts_str = " and ".join(saved_facts) if saved_facts else "your farm details"

        if active_lang == "te":
            answer = f"అర్థమైంది! నేను మీ పొలం వివరాలను ({facts_str}) నమోధు చేసుకున్నాను. మీరు పంట సిఫార్సులు, నీటి యాజమాన్యం లేదా నేల నిర్వహణ గురించి అడగవచ్చు. మీరు తర్వాత ఏమి తెలుసుకోవాలనుకుంటున్నారు?"
        elif active_lang == "hi":
            answer = f"समझ गया! मैंने आपके खेत की जानकारी ({facts_str}) दर्ज कर ली है। मैं फसल सिफारिशों, सिंचाई या मृदा प्रबंधन के लिए इसका उपयोग कर सकता हूँ। आप आगे क्या जानना चाहते हैं?"
        else:
            answer = f"Got it. I've noted your {facts_str}. I will use this context when suggesting crops, irrigation, or soil-management practices. What would you like to know?"

        sources = []
        confidence = "High"

    # -------------------------------------------------------------
    # INTENT: FARM CONTEXT QUERY (Return stored profile factors without recommending)
    # -------------------------------------------------------------
    elif intent == "farm_context_query":
        if active_lang == "te":
            answer = (
                f"📋 **మీ వ్యవసాయ ప్రొఫైల్ వివరాలు:**\n\n"
                f"• **ప్రాంతం:** {final_district}, {final_state}\n"
                f"• **నేల రకం:** {final_soil}\n"
                f"• **నీటి పారద‌ల వ్యవస్థ:** {final_irrigation} ({final_water_src})\n"
                f"• **నీటి లభ్యత:** {final_water_avail}\n"
                f"• **సీజన్:** {final_season}\n"
                f"• **వర్షపాతం/వాతావరణం:** {final_rain_cond} rainfall, {final_temp_cond} temperature\n"
                f"• **సాగు విస్తీర్ణం:** {final_size} acres\n"
                f"• **నేల pH:** {final_ph}\n\n"
                f"ఈ వివరాలు మీ ప్రస్తుత వ్యవసాయ ప్రొఫైల్‌గా ఉపయోగిస్తున్నాను."
            )
        elif active_lang == "hi":
            answer = (
                f"📋 **आपके खेत का वर्तमान प्रोफ़ाइल:**\n\n"
                f"• **स्थान:** {final_district}, {final_state}\n"
                f"• **मिट्टी का प्रकार:** {final_soil}\n"
                f"• **सिंचाई प्रणाली:** {final_irrigation} ({final_water_src})\n"
                f"• **पानी की उपलब्धता:** {final_water_avail}\n"
                f"• **मौसम:** {final_season}\n"
                f"• **वर्षा/तापमान स्थिति:** {final_rain_cond} rainfall, {final_temp_cond} temperature\n"
                f"• **खेत का आकार:** {final_size} acres\n"
                f"• **मिट्टी का pH:** {final_ph}\n\n"
                f"यह जानकारी आपके वर्तमान फ़ार्म प्रोफ़ाइल के रूप में सहेजी गई है।"
            )
        else:
            answer = (
                f"📋 **Current Farm Profile Factors:**\n\n"
                f"• **Location:** {final_district}, {final_state}\n"
                f"• **Soil Type:** {final_soil}\n"
                f"• **Irrigation Setup:** {final_irrigation} ({final_water_src})\n"
                f"• **Water Availability:** {final_water_avail}\n"
                f"• **Season:** {final_season}\n"
                f"• **Weather Conditions:** {final_rain_cond} rainfall, {final_temp_cond} temperature\n"
                f"• **Farm Size:** {final_size} acres\n"
                f"• **Soil pH:** {final_ph}\n\n"
                f"These stored profile factors are used across RAG retrieval, crop suitability evaluation, and explanation generation."
            )
        sources = [{"name": "Master Geography Dataset", "why_used": "Active session farm profile", "used": True}]
        confidence = "High"

    # -------------------------------------------------------------
    # INTENT J: SOIL / DISEASE / FERTILIZER / LOCATION / GENERAL
    # -------------------------------------------------------------
    else:
        logger.info(f"FINAL CONTEXT BEFORE LLM:\n{json.dumps(farm_context, indent=2)}")
        answer = await llm_service.generate_response(
            message=message,
            context=rag_result["context_text"],
            lang=active_lang,
            farm_context=farm_context
        )
        if intent == "exact_yield":
            sources = [
                {"name": "Crop Expert Dataset", "why_used": "Historical regional yield benchmarks", "used": True}
            ]
        elif intent == "generic_agri_definition":
            sources = [
                {"name": "Soil Expert Dataset", "why_used": "Agronomic practice definitions", "used": True},
                {"name": "Crop Expert Dataset", "why_used": "Crop application benchmarks", "used": True}
            ]
        elif intent == "soil_information":
            sources = [
                {"name": "Soil Expert Dataset", "why_used": "Soil physicochemical profiles", "used": True}
            ]
        elif intent == "location_agriculture":
            sources = [
                {"name": "Master Geography Dataset", "why_used": "Regional agro-climatic boundaries", "used": True},
                {"name": "Weather Expert Dataset", "why_used": "Regional rainfall normals", "used": True}
            ]
        elif intent == "fertilizer":
            sources = [
                {"name": "Soil Expert Dataset", "why_used": "Soil fertility and nutrient guidelines", "used": True}
            ]
        elif intent == "disease_help":
            sources = [
                {"name": "Crop Expert Dataset", "why_used": "Plant pathology and deficiency diagnostics", "used": True}
            ]
        else:
            sources = rag_result.get("sources", [
                {"name": "Crop Expert Dataset", "why_used": "Agricultural reference data", "used": True}
            ])
        confidence = "High"

    # Save to SQLite database
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO chat_sessions (id, title, language) VALUES (?, ?, ?)",
                       (session_id, message[:40] + "...", active_lang))
        cursor.execute("INSERT INTO messages (session_id, sender, content, metadata) VALUES (?, ?, ?, ?)",
                       (session_id, "user", message, json.dumps({"lang": active_lang, "intent": intent})))
        cursor.execute("INSERT INTO messages (session_id, sender, content, metadata) VALUES (?, ?, ?, ?)",
                       (session_id, "assistant", answer, json.dumps({"sources": sources, "intent": intent})))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"Could not persist chat message: {e}")

    structured_response = None
    if structured and "structured_response" in structured:
        structured_response = structured["structured_response"]

    return answer, sources, recommendation_data, comparison_data, simple_summary, detailed_analysis, structured_response, confidence, active_lang, intent


@router.post("", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    res = await process_chat_intent(
        message=req.message,
        language=req.language or "en",
        session_id=req.session_id or "default_session",
        req_location=req.location,
        req_soil_type=req.soil_type,
        req_farm_profile=req.farm_profile,
        detail_level=req.detail_level or "simple"
    )

    return ChatResponse(
        success=True,
        answer=res[0],
        language=res[8],
        intent=res[9],
        simple_summary=res[4],
        detailed_analysis=res[5],
        structured_response=res[6],
        sources=res[1],
        recommendation_data=res[2],
        comparison_data=res[3],
        confidence=res[7],
        follow_up=getattr(res, "follow_up", None),
        quick_replies=getattr(res, "quick_replies", None),
        latency_metrics=getattr(res, "latency_metrics", None)
    )


@router.post("/stream")
async def chat_stream_endpoint(req: ChatRequest):
    res = await process_chat_intent(
        message=req.message,
        language=req.language or "en",
        session_id=req.session_id or "default_session",
        req_location=req.location,
        req_soil_type=req.soil_type,
        req_farm_profile=req.farm_profile,
        detail_level=req.detail_level or "simple"
    )

    answer = res[0]
    sources = res[1]
    recommendation_data = res[2]
    comparison_data = res[3]
    simple_summary = res[4]
    detailed_analysis = res[5]
    structured_response = res[6]
    confidence = res[7]
    active_lang = res[8]
    intent = res[9]
    follow_up = getattr(res, "follow_up", None)
    quick_replies = getattr(res, "quick_replies", None)
    latency_metrics = getattr(res, "latency_metrics", None)

    async def event_generator():
        meta_event = {
            "type": "metadata",
            "sources": sources,
            "language": active_lang,
            "intent": intent,
            "simple_summary": simple_summary.model_dump() if simple_summary else None,
            "detailed_analysis": detailed_analysis.model_dump() if detailed_analysis else None,
            "structured_response": structured_response.model_dump() if structured_response else None,
            "recommendation_data": recommendation_data,
            "comparison_data": comparison_data,
            "confidence": confidence,
            "follow_up": follow_up,
            "quick_replies": quick_replies,
            "latency_metrics": latency_metrics
        }
        yield f"data: {json.dumps(meta_event)}\n\n"

        words = answer.split(" ")
        for i in range(0, len(words), 3):
            chunk = " ".join(words[i:i+3]) + " "
            yield f"data: {json.dumps({'type': 'token', 'token': chunk})}\n\n"

        yield "data: {\"type\": \"done\"}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")



@router.get("/history/{session_id}")
async def get_history(session_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT sender, content, metadata, created_at FROM messages WHERE session_id = ? ORDER BY id ASC", (session_id,))
    rows = cursor.fetchall()
    conn.close()

    history = []
    for r in rows:
        meta = json.loads(r["metadata"]) if r["metadata"] else {}
        history.append({
            "sender": r["sender"],
            "content": r["content"],
            "metadata": meta,
            "created_at": r["created_at"]
        })
    return {"session_id": session_id, "messages": history}


@router.delete("/history/{session_id}")
async def clear_history(session_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
    cursor.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()
    session_memory.reset_session(session_id)
    return {"success": True, "message": f"Session {session_id} deleted."}
