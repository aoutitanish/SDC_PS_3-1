"""
Comprehensive Multilingual and Agricultural Response Generator for KrishiMitra AI.
Generates farmer-friendly Level 1 primary answers and Level 2 scientific details
in English, Telugu (తెలుగు), and Hindi (हिंदी).
"""

import re
import logging
from typing import Dict, Any, List, Optional
from backend.app.data_engine.schemas import (
    SimpleFarmerSummary,
    DetailedAgronomicAnalysis,
    FactorItem,
    RecommendationItem,
    StructuredCropResponse
)

logger = logging.getLogger(__name__)


class TranslationService:
    @staticmethod
    def detect_language(text: str, fallback_lang: str = "en") -> str:
        """Detects whether text is in Telugu, Hindi, or English."""
        if not text or not isinstance(text, str):
            return fallback_lang

        # Telugu Unicode range: \u0C00-\u0C7F
        if re.search(r"[\u0C00-\u0C7F]", text):
            return "te"

        # Devanagari (Hindi) Unicode range: \u0900-\u097F
        if re.search(r"[\u0900-\u097F]", text):
            return "hi"

        return fallback_lang

    @staticmethod
    def _translate_crop_name(crop: str, lang: str) -> str:
        """Provides natural localized crop name with English in brackets where helpful."""
        crop_lower = crop.lower()
        if lang == "te":
            if "pigeon" in crop_lower or "arhar" in crop_lower or "tur" in crop_lower or "red gram" in crop_lower:
                return "కంది (Arhar/Tur)"
            elif "cotton" in crop_lower:
                return "పత్తి (Cotton)"
            elif "chilli" in crop_lower:
                return "మిర్చి (Chilli)"
            elif "maize" in crop_lower:
                return "మొక్కజొన్న (Maize)"
            elif "groundnut" in crop_lower or "peanut" in crop_lower:
                return "వేరుశనగ (Groundnut)"
            elif "rice" in crop_lower or "paddy" in crop_lower:
                return "వరి (Paddy)"
            elif "soybean" in crop_lower:
                return "సోయాబీన్ (Soybean)"
            elif "sugarcane" in crop_lower:
                return "చెరకు (Sugarcane)"
            elif "sunflower" in crop_lower:
                return "పొద్దుతిరుగుడు (Sunflower)"
            elif "black gram" in crop_lower or "urad" in crop_lower:
                return "మినుము (Black Gram)"
            elif "green gram" in crop_lower or "moong" in crop_lower:
                return "పెసర (Green Gram)"
            elif "bengal gram" in crop_lower or "chana" in crop_lower or "chickpea" in crop_lower:
                return "శనగ (Bengal Gram)"
            elif "tomato" in crop_lower:
                return "టమాటా (Tomato)"
            return crop
        elif lang == "hi":
            if "pigeon" in crop_lower or "arhar" in crop_lower or "tur" in crop_lower or "red gram" in crop_lower:
                return "अरहर/तूर (Pigeon Pea)"
            elif "cotton" in crop_lower:
                return "कपास (Cotton)"
            elif "chilli" in crop_lower:
                return "मिर्च (Chilli)"
            elif "maize" in crop_lower:
                return "मक्का (Maize)"
            elif "groundnut" in crop_lower or "peanut" in crop_lower:
                return "मूंगफली (Groundnut)"
            elif "rice" in crop_lower or "paddy" in crop_lower:
                return "धान (Paddy)"
            elif "soybean" in crop_lower:
                return "सोयाबीन (Soybean)"
            elif "sugarcane" in crop_lower:
                return "गन्ना (Sugarcane)"
            elif "sunflower" in crop_lower:
                return "सूरजमुखी (Sunflower)"
            elif "black gram" in crop_lower or "urad" in crop_lower:
                return "उड़द (Black Gram)"
            elif "green gram" in crop_lower or "moong" in crop_lower:
                return "मूंग (Green Gram)"
            elif "bengal gram" in crop_lower or "chana" in crop_lower or "chickpea" in crop_lower:
                return "चना (Bengal Gram)"
            elif "tomato" in crop_lower:
                return "टमाटर (Tomato)"
            return crop
        return crop

    @staticmethod
    def _translate_soil_name(soil: str, lang: str) -> str:
        s_lower = (soil or "").lower()
        if lang == "te":
            if "black" in s_lower or "regur" in s_lower or "vertisol" in s_lower:
                return "నల్ల నేల"
            elif "red" in s_lower or "alfisol" in s_lower:
                return "ఎర్ర నేల"
            elif "alluvial" in s_lower or "inceptisol" in s_lower:
                return "ఒండ్రు నేల"
            elif "laterite" in s_lower:
                return "లేటరైట్ నేల"
            return soil or "నేల"
        elif lang == "hi":
            if "black" in s_lower or "regur" in s_lower or "vertisol" in s_lower:
                return "काली मिट्टी"
            elif "red" in s_lower or "alfisol" in s_lower:
                return "लाल मिट्टी"
            elif "alluvial" in s_lower or "inceptisol" in s_lower:
                return "जलोढ़ मिट्टी"
            elif "laterite" in s_lower:
                return "लैटेराइट मिट्टी"
            return soil or "मिट्टी"
        return soil or "soil"

    @staticmethod
    def _translate_season(season: str, lang: str) -> str:
        s_lower = (season or "kharif").lower()
        if lang == "te":
            if "kharif" in s_lower:
                return "ఖరీఫ్ (వర్షాకాలం)"
            elif "rabi" in s_lower:
                return "రబీ (శీతాకాలం)"
            elif "summer" in s_lower or "zaid" in s_lower:
                return "వేసవి / జాయెద్"
            return season
        elif lang == "hi":
            if "kharif" in s_lower:
                return "खरीफ (मानसून)"
            elif "rabi" in s_lower:
                return "रबी (सर्दियों का मौसम)"
            elif "summer" in s_lower or "zaid" in s_lower:
                return "जायद / ग्रीष्मकालीन"
            return season
        return season

    @staticmethod
    def format_live_weather_statement(live_weather: Optional[Dict[str, Any]], lang: str = "en") -> str:
        """Formats concise live weather telemetry statement according to requested language."""
        if not live_weather or not isinstance(live_weather, dict):
            return ""

        parts = []
        temp = live_weather.get("temperature_c")
        if temp is not None:
            parts.append(f"{temp:.1f}°C" if isinstance(temp, float) else f"{temp}°C")

        rh = live_weather.get("relative_humidity_pct")
        if rh is not None:
            if lang == "te":
                parts.append(f"{rh:.0f}% తేమ" if isinstance(rh, float) else f"{rh}% తేమ")
            elif lang == "hi":
                parts.append(f"{rh:.0f}% आर्द्रता" if isinstance(rh, float) else f"{rh}% आर्द्रता")
            else:
                parts.append(f"{rh:.0f}% humidity" if isinstance(rh, float) else f"{rh}% humidity")

        precip = live_weather.get("rainfall_mm")
        if precip is not None:
            if lang == "te":
                parts.append(f"{precip} mm వర్షపాతం")
            elif lang == "hi":
                parts.append(f"{precip} mm वर्षा")
            else:
                parts.append(f"{precip} mm rainfall")

        wind = live_weather.get("wind_speed_ms")
        if wind is not None:
            if lang == "te":
                parts.append(f"గాలి {wind} m/s")
            elif lang == "hi":
                parts.append(f"हवा {wind} m/s")
            else:
                parts.append(f"wind {wind} m/s")

        if not parts:
            return ""

        details_str = ", ".join(parts)
        if lang == "te":
            return f"ప్రస్తుత వాతావరణం: {details_str}."
        elif lang == "hi":
            return f"वर्तमान मौसम: {details_str}."
        else:
            return f"Current weather: {details_str}."

    @staticmethod
    def format_recommendation_response(
        rec_data: Dict[str, Any],
        lang: str = "en",
        detail_level: str = "simple"
    ) -> str:
        """
        Formats farmer-facing recommendation.
        Default (Simple Level 1):
        - What to do
        - Why (3-4 simple bullets including live weather statement if present)
        - Water & Season
        - What to watch out for
        """
        prim = rec_data.get("primary_recommendation", {})
        raw_crop = prim.get("crop", "Arhar/Tur (Pigeon Pea)")
        crop_display = TranslationService._translate_crop_name(raw_crop, lang)
        loc = rec_data.get("location_context", {})
        district = loc.get("district", "Kurnool")
        state = loc.get("state", "Andhra Pradesh")
        raw_soil = loc.get("soil_group", "Black Soil")
        soil_display = TranslationService._translate_soil_name(raw_soil, lang)
        irrigation = loc.get("irrigation_type", "Drip Irrigation")
        season = loc.get("season", "Kharif")
        season_display = TranslationService._translate_season(season, lang)
        water_info = prim.get("water_assessment", {})
        water_demand = water_info.get("water_demand", "Low to Moderate")
        alts = [TranslationService._translate_crop_name(a["crop"], lang) for a in rec_data.get("alternative_crops", [])[:2]]

        res_ctx = rec_data.get("resolved_context") or {}
        live_weather = res_ctx.get("live_weather") or loc.get("live_weather") or rec_data.get("live_weather")
        weather_stmt = TranslationService.format_live_weather_statement(live_weather, lang)

        rain_cond = res_ctx.get("rainfall_condition") or loc.get("rainfall_condition")
        temp_cond = res_ctx.get("temperature_condition") or loc.get("temperature_condition")

        if rain_cond == "drought":
            climate_bullet_en = "Severe drought and low rainfall increase the importance of drought tolerance and efficient water use."
            climate_bullet_te = "తీవ్రమైన కరువు మరియు తక్కువ వర్షపాతం వల్ల కరువును తట్టుకునే పంటలకు ప్రాధాన్యత ఇవ్వబడింది."
            climate_bullet_hi = "गंभीर सूखा और कम वर्षा के कारण सूखा-सहनशील और कुशल जल उपयोग वाली फसलों को प्राथमिकता दी गई है।"
        elif rain_cond == "heavy":
            climate_bullet_en = "Heavy rainfall and excess water favor crops that can tolerate higher moisture availability, while drainage remains important."
            climate_bullet_te = "అధిక వర్షపాతం మరియు ఎక్కువ నీటి లభ్యత ఉన్నందున ఎక్కువ తేమను తట్టుకోగల పంటలకు ప్రాధాన్యత ఇవ్వబడింది."
            climate_bullet_hi = "भारी बारिश और अत्यधिक पानी की उपलब्धता अधिक नमी सहन करने वाली फसलों के अनुकूल है।"
        elif temp_cond == "hot":
            climate_bullet_en = "Hot conditions increase thermal stress and favor crops suited to higher temperatures."
            climate_bullet_te = "ఎక్కువ ఉష్ణోగ్రత మరియు వేడి పరిస్థితులను తట్టుకోగల పంటలకు ప్రాధాన్యత ఇవ్వబడింది."
            climate_bullet_hi = "उच्च तापमान और गर्म मौसम की स्थिति अधिक गर्मी सहन करने वाली फसलों के अनुकूल है।"
        elif temp_cond == "cold":
            climate_bullet_en = "Cold conditions favor crops suited to cooler Rabi conditions."
            climate_bullet_te = "చలి పరిస్థితులు మరియు రబీ వాతావరణానికి అనుకూలమైన పంట."
            climate_bullet_hi = "ठंड की स्थिति रबी के मौसम के अनुकूल फसलों के लिए उपयुक्त है।"
        else:
            climate_bullet_en = "The local rainfall and temperature conditions are suitable for crop development."
            climate_bullet_te = "స్థానిక వర్షపాతం మరియు ఉష్ణోగ్రత పరిస్థితులు పంటకు అనుకూలంగా ఉన్నాయి."
            climate_bullet_hi = "स्थानीय वर्षा और तापमान की परिस्थितियां फसल के अनुकूल हैं।"

        irr_lower = (irrigation or "").lower()
        wsrc_lower = (loc.get("water_source") or "").lower()

        if lang == "te":
            water_demand_te = "తక్కువ నుండి మితమైనది" if "low" in water_demand.lower() or "mod" in water_demand.lower() else "మితం / ఎక్కువ"
            
            if "drip" in irr_lower and "borewell" in wsrc_lower:
                irr_bullet_te = "• మీ డ్రిప్ ఇరిగేషన్ మరియు బోర్వెల్ ద్వారా అవసరమైనప్పుడు నీటి తడులు అందించవచ్చు."
            elif "drip" in irr_lower:
                irr_bullet_te = "• మీ డ్రిప్ ఇరిగేషన్ ద్వారా నీటి సదుపాయం అందించవచ్చు."
            elif "canal" in irr_lower or "canal" in wsrc_lower:
                irr_bullet_te = "• మీ కాలువ నీటిపారుదల ద్వారా పంటకు అవసరమైన నీటిని అందించవచ్చు."
            elif "rainfed" in irr_lower or "rainwater" in wsrc_lower:
                irr_bullet_te = "• వర్షాధార పద్ధతిలో కాలానికి అనుగుణంగా వర్షపాతంపై ఆధారపడి సాగు చేయవచ్చు."
            else:
                irr_bullet_te = f"• మీ నీటిపారుదల పద్ధతి ({irrigation}) ద్వారా పంటకు తగిన నీరు అందించబడుతుంది."

            why_bullets_te = [
                f"• మీ {soil_display} ఈ పంట పెరుగుదలకు బాగా సరిపోతుంది.",
                f"• {climate_bullet_te}",
            ]
            if weather_stmt:
                why_bullets_te.append(f"• {weather_stmt}")
            why_bullets_te.extend([
                irr_bullet_te,
                f"• ఈ పంటకు నీటి అవసరం {water_demand_te}."
            ])

            lines = [
                "🌾 **పంట సిఫార్సు**",
                "",
                f"మీ {district} పొలం వివరాలను బట్టి, **{crop_display}** ప్రస్తుత సమాచారం ఆధారంగా అనుకూలమైన పంటగా ఉంది.",
                "",
                "**ఎందుకు?**",
            ] + why_bullets_te + [
                "",
                f"💧 **నీటి అవసరం:** {water_demand_te}",
                f"📅 **సీజన్:** {season_display}",
            ]
            if alts:
                lines.extend(["", f"🔄 **ఇతర అనుకూల పంటలు:** {', '.join(alts)}"])

            lines.extend([
                "",
                "⚠️ **గమనించవలసిన అంశాలు:**",
                "వాస్తవ పంట దిగుబడి మరియు ఎంపిక నేల పరీక్ష ఫలితాలు, నీటి లభ్యత, విత్తే సమయం మరియు ప్రస్తుత వాతావరణ పరిస్థితులపై ఆధారపడి ఉంటుంది."
            ])
            return "\n".join(lines)

        elif lang == "hi":
            water_demand_hi = "कम से मध्यम" if "low" in water_demand.lower() or "mod" in water_demand.lower() else "मध्यम से अधिक"
            
            if "drip" in irr_lower and "borewell" in wsrc_lower:
                irr_bullet_hi = "• ड्रिप सिंचाई और बोरवेल से जरूरत पड़ने पर पूरक सिंचाई दी जा सकती है।"
            elif "drip" in irr_lower:
                irr_bullet_hi = "• ड्रिप सिंचाई व्यवस्था से पौधों को आवश्यक पानी दिया जा सकता है।"
            elif "canal" in irr_lower or "canal" in wsrc_lower:
                irr_bullet_hi = "• नहर सिंचाई व्यवस्था से फसल को आवश्यक पानी उपलब्ध कराया जा सकता है।"
            elif "rainfed" in irr_lower or "rainwater" in wsrc_lower:
                irr_bullet_hi = "• वर्षा आधारित खेती में मौसमी वर्षा के अनुसार फसल प्रबंधन किया जा सकता है।"
            else:
                irr_bullet_hi = f"• आपकी सिंचाई व्यवस्था ({irrigation}) से फसल की पानी की आवश्यकता पूरी होगी।"

            why_bullets_hi = [
                f"• आपकी {soil_display} इस फसल की प्रकृति के पूर्णतः अनुकूल है।",
                f"• {climate_bullet_hi}",
            ]
            if weather_stmt:
                why_bullets_hi.append(f"• {weather_stmt}")
            why_bullets_hi.extend([
                irr_bullet_hi,
                f"• इस फसल की पानी की आवश्यकता {water_demand_hi} है।"
            ])

            lines = [
                "🌾 **फसल सिफारिश**",
                "",
                f"{district} में आपके खेत के विवरण के आधार पर, **{crop_display}** उपलब्ध जानकारी के अनुसार एक उपयुक्त विकल्प है।",
                "",
                "**सिफारिश के मुख्य कारण:**",
            ] + why_bullets_hi + [
                "",
                f"💧 **जल आवश्यकता:** {water_demand_hi}",
                f"📅 **मौसम (सीजन):** {season_display}",
            ]
            if alts:
                lines.extend(["", f"🔄 **अन्य उपयुक्त विकल्प:** {', '.join(alts)}"])

            lines.extend([
                "",
                "⚠️ **ध्यान रखने योग्य बातें:**",
                "फसल का वास्तविक प्रदर्शन और चयन मिट्टी की जांच रिपोर्ट, पानी की उपलब्धता, बुवाई के समय और वर्तमान मौसम पर भी निर्भर करेगा।"
            ])
            return "\n".join(lines)

        else:
            if "drip" in irr_lower and "borewell" in wsrc_lower:
                irr_bullet_en = "• Your drip irrigation and borewell setup can provide supplementary water during dry periods."
            elif "drip" in irr_lower:
                irr_bullet_en = "• Your drip irrigation setup provides targeted water management during key growth stages."
            elif "canal" in irr_lower or "canal" in wsrc_lower:
                irr_bullet_en = "• Your canal irrigation setup provides surface water supply during crop growth stages."
            elif "rainfed" in irr_lower or "rainwater" in wsrc_lower:
                irr_bullet_en = "• Rainfed crop management aligns with seasonal precipitation without requiring micro-irrigation."
            else:
                irr_bullet_en = f"• Your irrigation setup ({irrigation}) supports moisture requirements during key growth stages."

            why_bullets_en = [
                f"• Your {raw_soil.lower() if 'soil' in raw_soil.lower() else raw_soil.lower() + ' soil'} is compatible with this crop.",
                f"• {climate_bullet_en}",
            ]
            if weather_stmt:
                why_bullets_en.append(f"• {weather_stmt}")
            why_bullets_en.extend([
                irr_bullet_en,
                f"• The crop has relatively {water_demand.lower()} water requirements."
            ])

            lines = [
                "🌾 **Crop Recommendation**",
                "",
                f"For your farm in {district}, **{raw_crop}** is a suitable option based on the information currently available.",
                "",
                "**Why?**",
            ] + why_bullets_en + [
                "",
                f"💧 **Water:** {water_demand}",
                f"📅 **Season:** {season}",
            ]
            if alts:
                lines.extend(["", f"🔄 **Alternative Suitable Crops:** {', '.join(alts)}"])

            lines.extend([
                "",
                "⚠️ **Keep in mind:**",
                "Actual crop performance will also depend on recent soil test results, water discharge/availability, sowing window, and current local weather."
            ])
            return "\n".join(lines)

    @staticmethod
    def build_structured_summary_and_analysis(
        rec_data: Dict[str, Any],
        lang: str = "en"
    ) -> Dict[str, Any]:
        """Builds typed SimpleFarmerSummary and DetailedAgronomicAnalysis objects."""
        prim = rec_data.get("primary_recommendation", {})
        crop = prim.get("crop", "Arhar/Tur (Pigeon Pea)")
        scores = prim.get("factor_scores", {})
        actuals = prim.get("actual_values", {})
        opt = prim.get("optimal_ranges", {})
        water_info = prim.get("water_assessment", {})
        loc = rec_data.get("location_context", {})
        district = loc.get("district", "Kurnool")
        state = loc.get("state", "Andhra Pradesh")
        soil = loc.get("soil_group", "Black Soil")
        irrigation = loc.get("irrigation_type", "Drip Irrigation")
        season = loc.get("season", "Kharif")

        # Simple Summary
        simple_summary = SimpleFarmerSummary(
            title="Crop Recommendation",
            main_crop=crop,
            simple_reason=[
                f"Compatible with your {soil}",
                f"Matches {district} regional rainfall and temperature patterns",
                f"{irrigation} provides timely supplemental moisture",
                f"Water demand: {water_info.get('water_demand', 'Low to Moderate')}"
            ],
            water_requirement=water_info.get("water_demand", "Low to Moderate"),
            season=season,
            warning="Actual suitability depends on soil testing, water discharge, and sowing window.",
            next_steps=[
                "Verify soil pH and organic carbon with a recent test if available.",
                "Check borewell yield before finalizing the sowing acreage.",
                "Procure certified high-germination seed varieties suited for your agro-climatic zone.",
                "Confirm local APMC market prices and procurement centers."
            ]
        )

        # Detailed Analysis
        detailed_analysis = DetailedAgronomicAnalysis(
            crop=crop,
            agronomic_suitability_score=prim.get("agronomic_suitability_score"),
            model_confidence=prim.get("confidence_level", "High"),
            soil_parameters={
                "measured_clay_pct": actuals.get("soil_clay_pct", 31.2),
                "optimal_clay_range": f"{opt.get('clay_pct_optimal', [20, 45])[0]}–{opt.get('clay_pct_optimal', [20, 45])[1]}%",
                "measured_ph": actuals.get("ph", 7.1),
                "optimal_ph_range": f"{opt.get('ph_optimal', [5.5, 7.8])[0]}–{opt.get('ph_optimal', [5.5, 7.8])[1]}",
                "soil_suitability_score": scores.get("soil_suitability", 95)
            },
            climate_parameters={
                "regional_rainfall_mm": actuals.get("rainfall_mm", 927.0),
                "crop_rainfall_optimal_mm": f"{opt.get('rainfall_optimal_mm', [500, 1100])[0]}–{opt.get('rainfall_optimal_mm', [500, 1100])[1]} mm",
                "mean_temperature_c": actuals.get("mean_temp_c", 27.2),
                "crop_temp_optimal_c": f"{opt.get('temp_optimal_c', [20, 35])[0]}–{opt.get('temp_optimal_c', [20, 35])[1]}°C",
                "climate_suitability_score": scores.get("rainfall_suitability", 92)
            },
            water_analysis={
                "farm_irrigation": irrigation,
                "water_source": actuals.get("water_source", "Borewell"),
                "crop_water_requirement": water_info.get("water_demand", "Low to Moderate (400–650 mm)"),
                "water_compatibility": water_info.get("compatibility", "High Water Efficiency")
            },
            explainability_factors=[
                {"factor": "Soil Compatibility", "status": "Optimal", "impact": "+28%"},
                {"factor": "Rainfall & Thermal Suitability", "status": "Optimal", "impact": "+25%"},
                {"factor": "Irrigation Efficiency", "status": "Favorable", "impact": "+22%"},
                {"factor": "Historical Regional Yield", "status": "Normal", "impact": "+15%"}
            ],
            sources=[
                {"name": "Crop Expert Dataset", "why_used": "Crop agronomic thresholds and regional yield benchmarks"},
                {"name": "Soil Expert Dataset", "why_used": "SoilGrids clay composition and pH calibration"},
                {"name": "Weather Expert Dataset", "why_used": "IMD regional climate normals and precipitation"},
                {"name": "Master Geography Dataset", "why_used": "District administrative and agro-climatic boundaries"}
            ],
            limitations=[
                "Extreme dry spells during pod development may require supplemental irrigation.",
                "Ensure proper drainage to prevent temporary water stagnation in heavy clay soil."
            ]
        )

        # Structured Response Object
        structured_crop_response = StructuredCropResponse(
            intent="crop_recommendation",
            language=lang,
            summary=simple_summary,
            recommendation=RecommendationItem(
                crop=crop,
                suitability_score=prim.get("agronomic_suitability_score"),
                confidence=prim.get("confidence_level", "High")
            ),
            factors=[
                FactorItem(name="Soil", status="Suitable", value=soil),
                FactorItem(name="Rainfall", status="Suitable", value=f"{actuals.get('rainfall_mm', 927.0):.0f} mm"),
                FactorItem(name="Temperature", status="Suitable", value=f"{actuals.get('mean_temp_c', 27.2):.1f}°C"),
                FactorItem(name="Water", status="Suitable", value=irrigation)
            ],
            alternatives=[a["crop"] for a in rec_data.get("alternative_crops", [])],
            warnings=[simple_summary.warning] if simple_summary.warning else [],
            next_steps=simple_summary.next_steps,
            detailed_analysis=detailed_analysis,
            sources=detailed_analysis.sources
        )

        return {
            "simple_summary": simple_summary,
            "detailed_analysis": detailed_analysis,
            "structured_response": structured_crop_response
        }

    @staticmethod
    def format_explanation_response(
        rec_data: Dict[str, Any],
        lang: str = "en"
    ) -> str:
        """Formats an explainability answer answering why this recommendation was made."""
        prim = rec_data.get("primary_recommendation", {})
        crop = prim.get("crop", "Arhar/Tur (Pigeon Pea)")
        crop_display = TranslationService._translate_crop_name(crop, lang)
        
        res_ctx = rec_data.get("resolved_context") or {}
        loc = rec_data.get("location_context", {})
        district = res_ctx.get("district") or loc.get("district", "Kurnool")
        soil = res_ctx.get("soil_type") or loc.get("soil_group", "Black Soil")
        soil_display = TranslationService._translate_soil_name(soil, lang)

        irrigation = res_ctx.get("irrigation_type") or loc.get("irrigation_type", "")
        water_src = res_ctx.get("water_source") or loc.get("water_source", "")
        has_drip = res_ctx.get("has_drip") if res_ctx.get("has_drip") is not None else ("drip" in (irrigation or "").lower())
        has_borewell = res_ctx.get("has_borewell") if res_ctx.get("has_borewell") is not None else ("borewell" in (water_src or "").lower() or "borewell" in (irrigation or "").lower())

        irr_lower = (irrigation or "").lower()
        wsrc_lower = (water_src or "").lower()

        # Dynamic Water Management bullets based strictly on resolved context
        if has_drip and has_borewell:
            water_bullet_en = "Your drip irrigation and borewell setup can provide targeted supplemental watering during critical growth stages."
            water_bullet_te = "మీ డ్రిప్ ఇరిగేషన్ మరియు బోర్వెల్ ద్వారా అవసరమైనప్పుడు నీటి తడులు అందించవచ్చు."
            water_bullet_hi = "आपकी ड्रिप सिंचाई और बोरवेल व्यवस्था से सूखे की स्थिति में पूरक सिंचाई दी जा सकती है।"
        elif has_drip:
            water_bullet_en = "Your drip irrigation can provide targeted supplemental watering during critical growth stages."
            water_bullet_te = "మీ డ్రిప్ ఇరిగేషన్ ద్వారా తక్కువ నీటితో సమర్థవంతంగా తడులు అందించవచ్చు."
            water_bullet_hi = "आपकी ड्रिप सिंचाई प्रणाली द्वारा कम पानी में भी पौधों को आवश्यकतानुसार नियमित नमी मिलती रहती है।"
        elif "canal" in irr_lower or "canal" in wsrc_lower or "flood" in irr_lower:
            if has_borewell:
                water_bullet_en = "Your canal/flood irrigation and borewell setup provide surface and groundwater supply during crop growth."
                water_bullet_te = "మీ కాలువ నీటిపారుదల మరియు బోర్వెల్ ద్వారా పంట పెరుగుదల దశలలో నీటిని అందించవచ్చు."
                water_bullet_hi = "आपकी नहर/बाढ़ सिंचाई और बोरवेल व्यवस्था फसल की वृद्धि के दौरान जल की आपूर्ति प्रदान करती है।"
            else:
                water_bullet_en = "Your canal/flood irrigation provides surface water during crop growth."
                water_bullet_te = "మీ కాలువ నీటిపారుదల ద్వారా పంట పెరుగుదల దశలలో ఉపరితల నీటిని అందించవచ్చు."
                water_bullet_hi = "आपकी नहर/बाढ़ सिंचाई व्यवस्था फसल की वृद्धि के दौरान सतही जल की आपूर्ति प्रदान करती है।"
        elif "rainfed" in irr_lower or "rainwater" in wsrc_lower:
            water_bullet_en = "Rainfed conditions make seasonal rainfall availability important for crop growth."
            water_bullet_te = "వర్షాధార పరిస్థితులలో కాలానికి అనుగుణంగా వర్షపాతంపై ఆధారపడి సాగు చేయవచ్చు."
            water_bullet_hi = "वर्षा आधारित स्थिति में मौसमी वर्षा के अनुसार फसल को नमी प्राप्त होती है।"
        else:
            water_bullet_en = f"Your current irrigation setup ({irrigation or 'Standard'}) supports required moisture during crop growth."
            water_bullet_te = f"మీ నీటిపారుదల వ్యవస్థ ({irrigation or 'సాధారణ'}) ద్వారా పంటకు అవసరమైన నీరు అందించబడుతుంది."
            water_bullet_hi = f"आपकी वर्तमान सिंचाई व्यवस्था ({irrigation or 'सामान्य'}) फसल की आवश्यकतानुसार नमी सहायता प्रदान करती है।"

        rain_cond = res_ctx.get("rainfall_condition") or loc.get("rainfall_condition")
        temp_cond = res_ctx.get("temperature_condition") or loc.get("temperature_condition")

        if rain_cond == "drought":
            climate_exp_en = "Severe drought and low rainfall increase the importance of drought tolerance and efficient water use."
            climate_exp_te = "తీవ్రమైన కరువు మరియు తక్కువ వర్షపాతం వల్ల కరువును తట్టుకునే పంటలకు ప్రాధాన్యత ఇవ్వబడింది."
            climate_exp_hi = "गंभीर सूखा और कम वर्षा के कारण सूखा-सहनशील और कुशल जल उपयोग वाली फसलों को प्राथमिकता दी गई है।"
        elif rain_cond == "heavy":
            climate_exp_en = "Heavy rainfall and excess water favor crops that can tolerate higher moisture availability, while drainage remains important."
            climate_exp_te = "అధిక వర్షపాతం మరియు ఎక్కువ నీటి లభ్యత ఉన్నందున ఎక్కువ తేమను తట్టుకోగల పంటలకు ప్రాధాన్యత ఇవ్వబడింది."
            climate_exp_hi = "भारी बारिश और अत्यधिक पानी की उपलब्धता अधिक नमी सहन करने वाली फसलों के अनुकूल है।"
        elif temp_cond == "hot":
            climate_exp_en = "Hot conditions increase thermal stress and favor crops suited to higher temperatures."
            climate_exp_te = "ఎక్కువ ఉష్ణోగ్రత మరియు వేడి పరిస్థితులను తట్టుకోగల పంటలకు ప్రాధాన్యత ఇవ్వబడింది."
            climate_exp_hi = "उच्च तापमान और गर्म मौसम की स्थिति अधिक गर्मी सहन करने वाली फसलों के अनुकूल है।"
        elif temp_cond == "cold":
            climate_exp_en = "Cold conditions favor crops suited to cooler Rabi conditions."
            climate_exp_te = "చలి పరిస్థితులు మరియు రబీ వాతావరణానికి అనుకూలమైన పంట."
            climate_exp_hi = "ठंड की स्थिति रबी के मौसम के अनुकूल फसलों के लिए उपयुक्त है।"
        else:
            climate_exp_en = f"Historical climate and temperature in {district} match the optimal growth requirements of this crop."
            climate_exp_te = f"{district} ప్రాంతంలోని సహజ ఉష్ణోగ్రత మరియు వర్షపాతం పంట పెరుగుదలకు సరిగ్గా సరిపోతాయి."
            climate_exp_hi = f"{district} क्षेत्र का तापमान और वर्षा इस फसल की बढ़वार के लिए पूरी तरह अनुकूल है।"

        if lang == "te":
            return (
                f"🔍 **{crop_display} సిఫార్సు చేయడానికి ప్రధాన కారణాలు:**\n\n"
                f"1. **నేల అనుకూలత:** మీ పొలంలోని {soil_display} ఈ పంట పెరుగుదలకు సరిగ్గా సరిపోతుంది.\n"
                f"2. **వాతావరణం:** {climate_exp_te}\n"
                f"3. **నీటి నిర్వహణ:** {water_bullet_te}\n\n"
                f"⚠️ **గమనిక:** సంపూర్ణ శాస్త్రీయ వివరాలు (pH, క్లే శాతం, ఉష్ణోగ్రత పరిధులు) క్రింది **పూర్తి విశ్లేషణ** బటన్ ద్వారా చూడవచ్చు."
            )
        elif lang == "hi":
            return (
                f"🔍 **{crop_display} की सिफारिश के मुख्य कारण:**\n\n"
                f"1. **मिट्टी की अनुकूलता:** आपके खेत की {soil_display} इस फसल की बढ़वार के लिए पूरी तरह अनुकूल है।\n"
                f"2. **जलवायु:** {climate_exp_hi}\n"
                f"3. **सिंचाई प्रबंधन:** {water_bullet_hi}\n\n"
                f"⚠️ **नोट:** विस्तृत वैज्ञानिक विश्लेषण (pH, क्ले %, तापमान सीमा) देखने के लिए नीचे दिए गए **पूर्ण विश्लेषण** बटन पर क्लिक करें।"
            )
        else:
            clean_soil = soil.lower() if "soil" in soil.lower() else soil.lower() + " soil"
            return (
                f"🔍 **Why was {crop} recommended?**\n\n"
                f"1. **Soil Match:** Your {clean_soil} supports healthy root establishment for {crop}.\n"
                f"2. **Climate Fit:** {climate_exp_en}\n"
                f"3. **Water Management:** {water_bullet_en}\n\n"
                f"⚠️ **Note:** To inspect precise soil pH, clay percentages, temperature ranges, and data provenance, click **View Full Analysis** below."
            )

    @staticmethod
    def format_comparison_response(
        comp_data: Dict[str, Any],
        farm_context: Dict[str, Any],
        lang: str = "en"
    ) -> str:
        """Formats a comparison response tailored to the active farm profile."""
        matrix = comp_data.get("comparison_matrix", [])
        district = farm_context.get("district", "Kurnool")
        state = farm_context.get("state", "Andhra Pradesh")
        soil = farm_context.get("soil_type", "Black Soil")
        irrigation = farm_context.get("irrigation_type", "Drip Irrigation")

        if lang == "te":
            lines = [
                "📊 **పంటల తులనాత్మక పరిశీలన (Crop Comparison)**",
                "",
                f"మీ ప్రస్తుత పొలం వివరాల ఆధారంగా ({district}, {state} | {soil} | {irrigation}):",
                ""
            ]
            for c in matrix:
                c_name = TranslationService._translate_crop_name(c['crop'], 'te')
                lines.extend([
                    f"🌱 **{c_name}**",
                    f"• నీటి అవసరం: {c['water_demand']}",
                    f"• ప్రధాన ప్రయోజనం: {c['advantage']}",
                    f"• జాగ్రత్త: {c['limitation']}",
                    ""
                ])
            lines.append("💡 శాస్త్రీయ పట్టిక మరియు స్కోర్ల కోసం [పూర్తి విశ్లేషణ] చూడండి.")
            return "\n".join(lines)

        elif lang == "hi":
            lines = [
                "📊 **फसलों का तुलनात्मक विश्लेषण (Crop Comparison)**",
                "",
                f"आपके खेत के वर्तमान विवरण के आधार पर ({district}, {state} | {soil} | {irrigation}):",
                ""
            ]
            for c in matrix:
                c_name = TranslationService._translate_crop_name(c['crop'], 'hi')
                lines.extend([
                    f"🌱 **{c_name}**",
                    f"• जल आवश्यकता: {c['water_demand']}",
                    f"• मुख्य लाभ: {c['advantage']}",
                    f"• सावधानी: {c['limitation']}",
                    ""
                ])
            lines.append("💡 विस्तृत वैज्ञानिक तुलना के लिए [पूर्ण विश्लेषण] देखें।")
            return "\n".join(lines)

        else:
            lines = [
                "📊 **Crop Comparison Analysis**",
                "",
                f"Based on your active farm profile ({district}, {state} • {soil} • {irrigation}):",
                ""
            ]
            for c in matrix:
                lines.extend([
                    f"🌱 **{c['crop']}**",
                    f"• **Water Need:** {c['water_demand']}",
                    f"• **Main Advantage:** {c['advantage']}",
                    f"• **Key Caution:** {c['limitation']}",
                    ""
                ])
            lines.append("💡 *Open Full Analysis below to view the detailed agronomic suitability metrics.*")
            return "\n".join(lines)

    @staticmethod
    def format_economic_recommendation_response(
        payload: Dict[str, Any],
        lang: str = "en"
    ) -> str:
        """
        Formats a grounded economic return comparison for agronomically suitable crops.
        Does NOT alter numbers or guess future market prices.
        """
        district = payload.get("district", "Your district")
        state = payload.get("state", "Your state")
        top_crop = payload.get("top_crop")
        other_crops = payload.get("other_crops", [])
        unavail_crops = payload.get("unavailable_crops", [])

        if not top_crop:
            if lang == "te":
                return f"⚠️ **{district}, {state}** పొలానికి అనుకూలమైన పంటల ఆర్థిక వివరాలు ప్రస్తుతం అందుబాటులో లేవు. ధరల డేటా లభించలేదు."
            elif lang == "hi":
                return f"⚠️ **{district}, {state}** के लिए उपयुक्त फसलों के आर्थिक विवरण वर्तमान में उपलब्ध नहीं हैं।"
            else:
                return f"⚠️ Economic financial estimates are currently unavailable for suitable crops in **{district}, {state}** because verified price data is missing."

        c_name_raw = top_crop.get("crop", "Unknown")
        top_net = top_crop.get("net_return_inr")
        top_roi = top_crop.get("roi_pct")
        top_rev = top_crop.get("gross_revenue_inr")
        top_cost = top_crop.get("total_cost_inr")
        top_basis = top_crop.get("price_basis", "Official MSP reference")

        if lang == "te":
            c_name = TranslationService._translate_crop_name(c_name_raw, "te")
            lines = [
                f"💰 **వ్యవసాయపరంగా అనుకూలమైన పంటలలో అత్యధిక అంచనా ఆదాయం:**",
                "",
                f"మీ **{district}, {state}** పొలానికి అనుకూలమైన పంటలలో, లభ్యమైన ధరల డేటా ఆధారంగా **{c_name}** అత్యధిక అంచనా ఆదాయం నమోదు చేసింది.",
                "",
                f"🌱 **{c_name}**",
                f"• అంచనా నికర ఆదాయం (Estimated Net Return): **₹{top_net:,.2f}**" if top_net is not None else f"• అంచనా నికర ఆదాయం: డేటా లేదు",
                f"• ROI (లాభదాయకత శాతం): **{top_roi}%**" if top_roi is not None else "",
                f"• అంచనా మొత్తం రాబడి: **₹{top_rev:,.2f}**" if top_rev is not None else "",
                f"• అంచనా సాగు ఖర్చు: **₹{top_cost:,.2f}**" if top_cost is not None else "",
                f"• ధర మూలం (Price Basis): **{top_basis}**",
                ""
            ]
            if other_crops:
                lines.append("📊 **అందుబాటులో ఉన్న ఇతర అనుకూల పంటల అంచనాలు:**")
                for oc in other_crops:
                    oc_name = TranslationService._translate_crop_name(oc.get("crop", ""), "te")
                    oc_net = oc.get("net_return_inr")
                    net_str = f"₹{oc_net:,.2f}" if oc_net is not None else "డేటా లేదు"
                    lines.append(f"• **{oc_name}**: అంచనా నికర ఆదాయం {net_str} ({oc.get('price_basis', 'MSP reference')})")
                lines.append("")

            if unavail_crops:
                lines.append(f"⚠️ **అంచనా లభించని పంటలు:** {', '.join([TranslationService._translate_crop_name(uc, 'te') for uc in unavail_crops])} (ధర బెంచ్మార్క్ అందుబాటులో లేదు).")
                lines.append("")

            lines.append("💡 *గమనిక: ఇవి అందుబాటులో ఉన్న దిగుబడి, సాగు ఖర్చు మరియు ప్రారంభ ధరల డేటా ఆధారంగా లెక్కించిన అంచనాలు మాత్రమే. ఇవి గ్యారెంటీ మార్కెట్ లాభాలు కావు.*")
            return "\n".join([l for l in lines if l != ""])

        elif lang == "hi":
            c_name = TranslationService._translate_crop_name(c_name_raw, "hi")
            lines = [
                f"💰 **कृषि रूप से उपयुक्त फसलों में उच्चतम अनुमानित आय:**",
                "",
                f"आपके **{district}, {state}** खेत के लिए उपयुक्त फसलों में, उपलब्ध मूल्य डेटा के आधार पर **{c_name}** की अनुमानित आय सबसे अधिक है।",
                "",
                f"🌱 **{c_name}**",
                f"• अनुमानित शुद्ध आय (Estimated Net Return): **₹{top_net:,.2f}**" if top_net is not None else f"• अनुमानित शुद्ध आय: डेटा अनुपलब्ध",
                f"• ROI (रिटर्न ऑन इन्वेस्टमेंट): **{top_roi}%**" if top_roi is not None else "",
                f"• अनुमानित कुल राजस्व: **₹{top_rev:,.2f}**" if top_rev is not None else "",
                f"• अनुमानित खेती की लागत: **₹{top_cost:,.2f}**" if top_cost is not None else "",
                f"• मूल्य आधार (Price Basis): **{top_basis}**",
                ""
            ]
            if other_crops:
                lines.append("📊 **उपलब्ध अन्य उपयुक्त फसलों का अनुमान:**")
                for oc in other_crops:
                    oc_name = TranslationService._translate_crop_name(oc.get("crop", ""), "hi")
                    oc_net = oc.get("net_return_inr")
                    net_str = f"₹{oc_net:,.2f}" if oc_net is not None else "डेटा अनुपलब्ध"
                    lines.append(f"• **{oc_name}**: अनुमानित शुद्ध आय {net_str} ({oc.get('price_basis', 'MSP reference')})")
                lines.append("")

            if unavail_crops:
                lines.append(f"⚠️ **अनुमान अनुपलब्ध फसलें:** {', '.join([TranslationService._translate_crop_name(uc, 'hi') for uc in unavail_crops])} (मूल्य मानक उपलब्ध नहीं)।")
                lines.append("")

            lines.append("💡 *ध्यान दें: ये अनुमान उपलब्ध उपज, खेती की लागत और आधिकारिक संदर्भ मूल्यों पर आधारित हैं। ये गारंटीकृत बाजार लाभ नहीं हैं।*")
            return "\n".join([l for l in lines if l != ""])

        else:
            lines = [
                f"💰 **Highest Estimated Economic Return (Agronomically Suitable Crops)**",
                "",
                f"Among the agronomically suitable crops for your **{district}, {state}** farm, **{c_name_raw}** has the highest estimated return based on available market and reference data.",
                "",
                f"🌱 **{c_name_raw}**",
                f"• **Estimated Net Return:** **₹{top_net:,.2f}**" if top_net is not None else f"• **Estimated Net Return:** Unavailable",
                f"• **ROI:** **{top_roi}%**" if top_roi is not None else "",
                f"• **Gross Revenue Estimate:** **₹{top_rev:,.2f}**" if top_rev is not None else "",
                f"• **Cultivation Cost:** **₹{top_cost:,.2f}**" if top_cost is not None else "",
                f"• **Price Basis:** **{top_basis}**",
                ""
            ]
            if other_crops:
                lines.append("📊 **Other Suitable Crops with Available Estimates:**")
                for oc in other_crops:
                    oc_net = oc.get("net_return_inr")
                    net_str = f"₹{oc_net:,.2f}" if oc_net is not None else "Unavailable"
                    lines.append(f"• **{oc.get('crop')}**: Estimated Net Return {net_str} ({oc.get('price_basis', 'MSP reference')})")
                lines.append("")

            if unavail_crops:
                lines.append(f"⚠️ **Economic Estimate Unavailable:** {', '.join(unavail_crops)} (verified price benchmark unrecorded).")
                lines.append("")

            lines.append("💡 *Note: These figures are estimated returns calculated from historical yield benchmarks, A2+FL cultivation costs, and available price references. They are not guaranteed market profits.*")
            return "\n".join([l for l in lines if l != ""])


# Singleton instance
translation_service = TranslationService()

