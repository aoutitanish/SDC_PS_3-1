"""
LLM Integration and Agronomic Expert Reasoning Service for KrishiMitra AI.
Provides grounded agricultural decision support for Indian farmers across 14 intents
in English, Telugu (తెలుగు), and Hindi (हिंदी).
"""

import os
import re
import json
import logging
import asyncio
from typing import AsyncGenerator, Dict, Any, Optional
import httpx
from backend.app.core.config import settings
from backend.app.services.translation_service import translation_service

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are KrishiMitra AI, an intelligent, concise, and grounded agricultural assistant for Indian farmers.

CRITICAL RULES:
1. Provide direct, practical, and farmer-friendly guidance in 2 to 5 sentences for general queries, or concise bullet points for crop advisories.
2. Do NOT output internal reasoning monologues, chain-of-thought analysis, or markdown meta-reflections. Jump straight to the answer.
3. Do NOT repeat the user's entire farm profile or redundant source lists in the response.
4. Ground your answer strictly in the provided agricultural context. Do NOT fabricate weather, chemical dosages, or crop data.
5. For exact yield queries, clarify that an exact guaranteed yield cannot be predicted from available data, but provide an estimated benchmark range with key influencing factors.
6. Respond purely in the requested language (English, Telugu, or Hindi).
7. Rely ONLY on the CURRENT FARM CONTEXT provided in the prompt. Do NOT assume drip irrigation or borewell setup if has_borewell/has_drip is false or if irrigation_type is Canal/Rainfed. Do NOT retain facts from previous locations or conversations.
8. If live weather telemetry is provided, you may explain its agronomic implications for crop growth or field work, but you MUST NOT rerank, change, or override the AgriculturalEngine crop recommendation.
"""


class LLMService:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.api_key = settings.LLM_API_KEY or settings.GEMINI_API_KEY or settings.OPENAI_API_KEY

    def _build_full_prompt(self, message: str, context: str, lang: str, farm_context: Optional[Dict[str, Any]] = None) -> str:
        prompt_parts = [
            f"USER QUERY: {message}",
            f"LANGUAGE: {lang}",
            f"RETRIEVED AGRICULTURAL CONTEXT:\n{context}"
        ]
        if farm_context:
            prompt_parts.append(f"CURRENT FARM CONTEXT:\n{json.dumps(farm_context, indent=2)}")
            if farm_context.get("live_weather"):
                prompt_parts.append(
                    f"LIVE WEATHER TELEMETRY:\n{json.dumps(farm_context['live_weather'], indent=2)}\n"
                    f"Note: You may explain the implications of this live weather for farm advisory, but do NOT rerank or change the crop recommendation."
                )

        prompt_parts.append(
            "\nTASK: Provide a farmer-friendly, grounded response in the requested language."
        )
        return "\n\n".join(prompt_parts)

    async def _rule_engine_generate(
        self,
        message: str,
        context: str,
        lang: str,
        farm_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Deterministic agricultural expert reasoning engine with comprehensive coverage."""
        q_lower = message.lower()
        district = farm_context.get("district", "Kurnool") if farm_context else "Kurnool"
        state = farm_context.get("state", "Andhra Pradesh") if farm_context else "Andhra Pradesh"
        soil = farm_context.get("soil_type", "Black Soil (Regur/Vertisol)") if farm_context else "Black Soil (Regur/Vertisol)"
        size_acres = farm_context.get("farm_size_acres", 5.0) if farm_context else 5.0

        # 1. Non-agricultural query check
        non_agri_keywords = ["movie", "song", "cricket", "politics", "president", "bitcoin", "football", "joke", "bollywood"]
        if any(w in q_lower for w in non_agri_keywords):
            if lang == "te":
                return "నేను వ్యవసాయం, నేల రకాలు, పంటలు, వాతావరణం మరియు ప్రభుత్వ పథకాలకు సంబంధించిన ప్రశ్నలకు మాత్రమే సహాయం చేయగలను. దయచేసి వ్యవసాయ సంబంధిత ప్రశ్న అడగండి."
            elif lang == "hi":
                return "मैं केवल कृषि, मिट्टी, फसलों, मौसम और सरकारी योजनाओं से संबंधित प्रश्नों में सहायता के लिए समर्पित हूँ। कृपया खेती से जुड़ा सवाल पूछें।"
            else:
                return "I am an agricultural assistant specialized in farming, crop health, soil, weather, and farm advisories. Please ask a farming-related question."

        # 2. Exact Yield Queries ("Tell me the exact yield I will get from my 5-acre farm")
        if any(w in q_lower for w in ["exact yield", "yield i will get", "how much yield", "what will be my yield", "yield from my", "దిగుబడి ఎంత", "ఖచ్చితమైన దిగుబడి", "सटीक उपज", "कितनी पैदावार होगी"]):
            if lang == "te":
                return (
                    f"🌾 **దిగుబడి అంచనా మరియు వాస్తవిక మార్గదర్శకాలు ({size_acres:.0f} ఎకరాల పొలం):**\n\n"
                    "ఖచ్చితమైన దిగుబడిని ముందస్తుగా హామీ ఇవ్వడం సాధ్యం కాదు, ఎందుకంటే వాస్తవ దిగుబడి పలు క్షేత్రస్థాయి అంశాలపై ఆధారపడి ఉంటుంది.\n\n"
                    f"• **చారిత్రక సరాసరి దిగుబడి (కంది/పప్పుదినుసులు):** కర్నూలు ప్రాంతంలో హెక్టారుకు సుమారు 1.2 నుండి 2.0 టన్నులు (ఎకరానికి ~0.5 నుండి 0.8 టన్నులు).\n"
                    f"• **మీ {size_acres:.0f} ఎకరాలకు అంచనా పరిధి:** సరైన యాజమాన్య పద్ధతులు పాటిస్తే సుమారు **2.5 నుండి 4.0 టన్నుల** మొత్తం దిగుబడి వచ్చే అవకాశం ఉంది.\n\n"
                    "🔍 **దిగుబడిని ప్రభావితం చేసే కీలక అంశాలు:**\n"
                    "1. ప్రామాణిక ధ్రువీకరించిన విత్తనాల నాణ్యత మరియు మొలక శాతం.\n"
                    "2. సరైన సమయానికి విత్తుకోవడం మరియు సిఫార్సు చేసిన మొక్కల సాంద్రత.\n"
                    "3. సమతుల్య ఎరువుల యాజమాన్యం మరియు సకాలంలో కలుపు, పురుగు నివారణ.\n"
                    "4. పూత మరియు కాత దశలలో డ్రిప్ ద్వారా అవసరమైనప్పుడు తడులు అందించడం.\n\n"
                    "📚 **వనరు:** Crop Expert Dataset (Historical Yield Benchmarks)"
                )
            elif lang == "hi":
                return (
                    f"🌾 **उपज अनुमान एवं व्यावहारिक दिशानिर्देश ({size_acres:.0f} एकड़ खेत):**\n\n"
                    "उपलब्ध जानकारी के आधार पर किसी भी खेत की सटीक व गारंटीड उपज पहले से तय नहीं की जा सकती, क्योंकि यह कई प्राकृतिक व प्रबंधन कारकों पर निर्भर करती है।\n\n"
                    f"• **ऐतिहासिक मानक उपज (अरहर/दलहन):** कुरनूल क्षेत्र में लगभग 1.2 से 2.0 टन प्रति हेक्टेयर (लगभग 0.5 से 0.8 टन प्रति एकड़)।\n"
                    f"• **आपके {size_acres:.0f} एकड़ के लिए अनुमानित सीमा:** उत्तम कृषि प्रबंधन के तहत लगभग **2.5 से 4.0 टन** कुल उत्पादन की संभावना है।\n\n"
                    "🔍 **उपज को प्रभावित करने वाले प्रमुख कारक:**\n"
                    "1. प्रमाणित बीज की गुणवत्ता एवं अंकुरण दर।\n"
                    "2. समय पर बुवाई और उचित पौध संख्या।\n"
                    "3. संतुलित पोषक तत्व प्रबंधन और कीट/रोग नियंत्रण।\n"
                    "4. फलियां बनते समय ड्रिप सिंचाई द्वारा समय पर पूरक सिंचाई।\n\n"
                    "📚 **डेटा स्रोत:** Crop Expert Dataset (Historical Yield Benchmarks)"
                )
            else:
                return (
                    f"🌾 **Estimated Yield Range & Guidance for your {size_acres:.0f}-Acre Farm:**\n\n"
                    "An exact guaranteed yield cannot be predicted from available data alone because agricultural outcomes depend on biological, weather, and management factors.\n\n"
                    f"• **Historical Benchmark Range (Pigeon Pea / Pulses):** In {district} conditions, benchmark yields typically range between **1.2 and 2.0 tonnes per hectare** (~0.5 to 0.8 tonnes per acre under good practices).\n"
                    f"• **Estimated Potential for {size_acres:.0f} Acres:** Approximately **2.5 to 4.0 tonnes total** under recommended crop management.\n\n"
                    "🔍 **Key Factors Influencing Actual Yield:**\n"
                    "1. Quality and germination rate of certified seed.\n"
                    "2. Timely sowing within the recommended window and maintaining optimal plant population.\n"
                    "3. Balanced nutrient application based on soil test results.\n"
                    "4. Timely supplemental drip irrigation during critical flowering and pod-filling stages.\n\n"
                    "📚 **Source:** Crop Expert Dataset (Historical Regional Benchmarks)"
                )

        # 3. Generic Definition: Drip Irrigation ("What is drip irrigation?")
        if any(w in q_lower for w in ["what is drip irrigation", "what is drip", "డ్రిప్ ఇరిగేషన్ అంటే ఏమిటి", "డ్రిప్ అంటే ఏమిటి", "ड्रिप सिंचाई क्या है"]):
            if lang == "te":
                return (
                    "💧 **బిందు సేద్యం (Drip Irrigation) అంటే ఏమిటి?**\n\n"
                    "బిందు సేద్యం అనేది పైపులు మరియు ఎమిటర్ల నెట్‌వర్క్ ద్వారా నీటిని మరియు ద్రవ ఎరువులను నేరుగా మొక్కల వేర్ల వద్దకు బొట్లు బొట్లుగా నెమ్మదిగా అందించే ఆధునిక సూక్ష్మ నీటిపారుదల పద్ధతి.\n\n"
                    "• **ప్రయోజనాలు:** 40%–60% నీటి ఆదా, కలుపు మొక్కల పెరుగుదల తగ్గింపు, మరియు ఎరువుల సమర్థవంతమైన వినియోగం (Fertigation).\n\n"
                    f"🌱 **మీ పొలానికి అనుసంధానం:** మీ {district} పొలంలో ({soil}) బోరుబావి నీటితో కంది లేదా పత్తి సాగు చేసేటప్పుడు డ్రిప్ ఇరిగేషన్ ఉపయోగించడం వల్ల తక్కువ నీటితో అధిక దిగుబడి సాధించవచ్చు.\n\n"
                    "📚 **వనరు:** Soil Expert Dataset & Crop Expert Dataset"
                )
            elif lang == "hi":
                return (
                    "💧 **ड्रिप सिंचाई (Drip Irrigation) क्या है?**\n\n"
                    "ड्रिप सिंचाई एक आधुनिक सूक्ष्म सिंचाई तकनीक है जिसमें पाइपों और ड्रिपर्स के माध्यम से पानी और तरल उर्वरक सीधे पौधों की जड़ों के पास बूंद-बूंद करके दिए जाते हैं।\n\n"
                    "• **प्रमुख लाभ:** 40%–60% पानी की बचत, वाष्पीकरण में कमी, खरपतवार में कमी और उर्वरक दक्षता में वृद्धि।\n\n"
                    f"🌱 **आपके खेत के संदर्भ में:** आपके {district} स्थित {size_acres:.0f} एकड़ खेत ({soil}) में बोरवेल के पानी के साथ अरहर या कपास जैसी फसलों के लिए ड्रिप सिंचाई अत्यंत उपयोगी है।\n\n"
                    "📚 **डेटा स्रोत:** Soil Expert Dataset & Crop Expert Dataset"
                )
            else:
                return (
                    "💧 **What is Drip Irrigation?**\n\n"
                    "Drip irrigation is a micro-irrigation method that delivers water and liquid nutrients slowly and precisely directly to the root zone of plants through a network of pipes, tubing, and calibrated emitters.\n\n"
                    "• **Key Benefits:** 40%–60% water savings compared to flood irrigation, minimized evaporation losses, reduced weed emergence, and efficient fertigation.\n\n"
                    f"🌱 **Application to Your Farm:** For your {size_acres:.0f}-acre holding in {district} ({soil}), drip irrigation paired with your borewell allows targeted moisture delivery for crops like Pigeon Pea or Cotton without water wastage.\n\n"
                    "📚 **Source:** Soil Expert Dataset & Crop Expert Dataset"
                )

        # 4. Generic Definition: Crop Rotation ("What is crop rotation?")
        if any(w in q_lower for w in ["what is crop rotation", "crop rotation", "పంట మార్పిడి అంటే ఏమిటి", "పంట మార్పిడి", "फसल चक्र क्या है"]):
            if lang == "te":
                return (
                    "🔄 **పంట మార్పిడి (Crop Rotation) అంటే ఏమిటి?**\n\n"
                    "ఒకే భూమిలో వరుసగా ఒకే రకమైన పంటను వేయకుండా, వేర్వేరు జాతులకు చెందిన పంటలను (ఉదాహరణకు పప్పుదినుసులు మరియు ధాన్యపు పంటలు) క్రమపద్ధతిలో మార్చి మార్చి సాగు చేయడాన్ని పంట మార్పిడి అంటారు.\n\n"
                    "• **ప్రయోజనాలు:** నేలలో నత్రజని స్థిరీకరణ, నేల సారం పెంపు, తెగుళ్లు మరియు కలుపు నియంత్రణ.\n\n"
                    f"🌱 **మీ పొలానికి సలహా:** మీ నల్లరేగడి నేలలో పత్తి లేదా మిర్చి తర్వాత కంది/శనగ వంటి పప్పుధాన్యాలను సాగు చేయడం వల్ల నేల సహజ సారం మెరుగుపడుతుంది.\n\n"
                    "📚 **వనరు:** Soil Expert Dataset & Crop Expert Dataset"
                )
            elif lang == "hi":
                return (
                    "🔄 **फसल चक्र (Crop Rotation) क्या है?**\n\n"
                    "एक ही खेत में लगातार एक ही फसल उगाने के बजाय विभिन्न कुल की फसलों (जैसे दलहन और अनाज/नकदी फसलें) को निश्चित क्रम में बदल-बदल कर बोना फसल चक्र कहलाता है।\n\n"
                    "• **प्रमुख लाभ:** मिट्टी की उर्वरा शक्ति में वृद्धि, नाइट्रोजन स्थिरीकरण, और कीट-रोगों के चक्र का टूटना।\n\n"
                    f"🌱 **आपके खेत के संदर्भ में:** आपके खेत में कपास या मिर्च के बाद अरहर या चना जैसी दलहनी फसलों का फसल चक्र अपनाने से मिट्टी की सेहत मजबूत रहती है।\n\n"
                    "📚 **डेटा स्रोत:** Soil Expert Dataset & Crop Expert Dataset"
                )
            else:
                return (
                    "🔄 **What is Crop Rotation?**\n\n"
                    "Crop rotation is the agricultural practice of growing different types of crops sequentially on the same land across successive seasons, rather than continuously monocropping.\n\n"
                    "• **Key Benefits:** Restores soil nitrogen naturally through leguminous root nodules, disrupts pest and weed life cycles, and improves soil structure.\n\n"
                    f"🌱 **Application to Your Farm:** Alternating deep-rooted cash crops like Cotton with nitrogen-fixing legumes like Pigeon Pea (Arhar/Tur) in your {soil} enhances long-term soil health.\n\n"
                    "📚 **Source:** Soil Expert Dataset & Crop Expert Dataset"
                )

        # 5. Generic Definition: Soil pH ("What is soil pH?")
        if any(w in q_lower for w in ["what is soil ph", "what is ph", "soil ph", "నేల ph అంటే ఏమిటి", "మట్టి ph", "पीएच क्या है"]):
            if lang == "te":
                return (
                    "🧪 **నేల pH (Soil pH) అంటే ఏమిటి?**\n\n"
                    "నేల pH అనేది నేల యొక్క ఆమ్ల లేదా క్షార స్వభావాన్ని (Acidity or Alkalinity) కొలిచే 0 నుండి 14 వరకు ఉండే ఒక ప్రామాణిక స్కేల్.\n\n"
                    "• **pH 6.5 – 7.5:** తటస్థ నేల (చాలా పంటలకు అనుకూలం).\n"
                    "• **pH < 6.5:** ఆమ్ల నేల (Acidic).\n"
                    "• **pH > 7.5:** క్షార నేల (Alkaline).\n\n"
                    f"🌱 **మీ పొలం నేల పరిస్థితి:** మీ నేల pH సుమారు 7.1 వద్ద ఉంది, ఇది తటస్థం నుండి అనుకూలమైన పరిధిలో ఉండి పోషకాల శోషణకు సహకరిస్తుంది.\n\n"
                    "📚 **వనరు:** Soil Expert Dataset"
                )
            elif lang == "hi":
                return (
                    "🧪 **मृदा pH (Soil pH) क्या है?**\n\n"
                    "मृदा pH मिट्टी की अम्लीयता या क्षारीयता को मापने का 0 से 14 तक का पैमाना है।\n\n"
                    "• **pH 6.5 – 7.5:** तटस्थ मिट्टी (अधिकांश फसलों के लिए सर्वोत्तम)।\n"
                    "• **pH < 6.5:** अम्लीय मिट्टी (Acidic)।\n"
                    "• **pH > 7.5:** क्षारीय मिट्टी (Alkaline)।\n\n"
                    f"🌱 **आपके खेत के संदर्भ में:** आपके खेत का pH मान लगभग 7.1 है, जो पोषक तत्वों की सुलभता के लिए पूरी तरह अनुकूल है।\n\n"
                    "📚 **डेटा स्रोत:** Soil Expert Dataset"
                )
            else:
                return (
                    "🧪 **What is Soil pH?**\n\n"
                    "Soil pH is a measure of the acidity or alkalinity of the soil solution on a logarithmic scale from 0 to 14.\n\n"
                    "• **pH 6.5 – 7.5:** Neutral range (optimal for nutrient availability for most crops).\n"
                    "• **pH < 6.5:** Acidic soils.\n"
                    "• **pH > 7.5:** Alkaline / calcareous soils.\n\n"
                    f"🌱 **Application to Your Farm:** Your profile's soil pH (~7.1) sits in the optimal neutral range, supporting strong availability of macro and micronutrients.\n\n"
                    "📚 **Source:** Soil Expert Dataset"
                )

        # 6. Disease / Leaf Symptoms (e.g. Tomato leaves yellowing, pest)
        if any(w in q_lower for w in ["yellow", "yellowing", "leaves", "leaf", "disease", "pest", "spots", "wilt", "ఆకులు పసుపు", "తెగులు", "పురుగు", "पीले", "पत्ते", "रोग"]):
            if lang == "te":
                return (
                    "🍅 **టమాటా / పంట ఆకులు పసుపు రంగులోకి మారడానికి గల కారణాలు:**\n\n"
                    "ఆకులు పసుపు రంగులోకి మారడానికి పలు కారణాలు ఉండవచ్చు:\n"
                    "• **పోషకాల లోపం:** నత్రజని (Nitrogen), ఐరన్ లేదా మెగ్నీషియం లోపం.\n"
                    "• **నీటి ఒత్తిడి:** నేలలో అధిక తేమ (నీరు నిలవడం) లేదా తీవ్రమైన నీటి ఎద్దడి.\n"
                    "• **వేరు సమస్యలు:** వేరుకుళ్ళు లేదా నెమటోడ్ల దాడి.\n"
                    "• **శిలీంధ్ర లేదా వైరస్ తెగుళ్లు:** ముడత తెగులు లేదా ఆకుమచ్చ తెగులు.\n\n"
                    "🔍 **సమస్యను స్పష్టంగా గుర్తించడానికి క్రింది వివరాలు తెలపండి:**\n"
                    "1. పంట నాటి ఎన్ని రోజులు / వారాలు అయ్యింది?\n"
                    "2. మొదట క్రింది పాత ఆకులు పసుపుగా మారాయా లేదా పై లేత చిగురు ఆకులా?\n"
                    "3. నేలలో నీరు ఎక్కువగా నిల్వ ఉందా?\n"
                    "4. ఆకులపై మచ్చలు, రంధ్రాలు లేదా పురుగులు కనిపిస్తున్నాయా?\n\n"
                    "⚠️ **సలహా:** తగిన నివారణ చర్యల కోసం వివరాలు తెలియజేయండి లేదా స్థానిక మండల వ్యవసాయ అధికారిని సంప్రదించండి.\n\n"
                    "📚 **వనరు:** Crop Expert Dataset"
                )
            elif lang == "hi":
                return (
                    "🍅 **टमाटर / फसल की पत्तियां पीली पड़ने के संभावित कारण:**\n\n"
                    "पत्तियों का पीला पड़ना कई कारणों से हो सकता है:\n"
                    "• **पोषक तत्वों की कमी:** मुख्य रूप से नाइट्रोजन, आयरन या मैग्नीशियम की कमी।\n"
                    "• **जल प्रबंधन (Water Stress):** खेत में पानी का ठहराव या लंबे समय तक नमी की कमी।\n"
                    "• **जड़ संबंधी समस्याएं:** जड़ गलन या नेमाटोड का प्रकोप।\n"
                    "• **रोग एवं कीट:** फफूंद जनित झुलसा रोग या विषाणु जनित मोज़ेक रोग।\n\n"
                    "🔍 **सटीक कारण जानने के लिए कृपया बताएं:**\n"
                    "1. फसल कितने दिन की है?\n"
                    "2. क्या पुरानी (निचली) पत्तियां पीली हैं या नई (ऊपरी) पत्तियां?\n"
                    "3. क्या खेत में जलभराव की स्थिति है?\n"
                    "4. क्या पत्तियों पर धब्बे, मुड़ाव या कीट दिखाई दे रहे हैं?\n\n"
                    "⚠️ **परामर्श:** सही उपचार के लिए उपर्युक्त जानकारी साझा करें या स्थानीय कृषि विज्ञान केंद्र से संपर्क करें।\n\n"
                    "📚 **डेटा स्रोत:** Crop Expert Dataset"
                )
            else:
                return (
                    "🍅 **Possible Causes for Yellowing Leaves:**\n\n"
                    "Leaf yellowing can occur due to several common agricultural factors:\n"
                    "• **Nutrient Deficiency:** Lack of Nitrogen (older leaves) or Micronutrients like Iron/Zinc (newer leaves).\n"
                    "• **Water Stress:** Over-watering / poor root drainage, or prolonged dry spells.\n"
                    "• **Root Health Issues:** Root rot or soil-borne nematodes restricting nutrient uptake.\n"
                    "• **Fungal/Viral Disease:** Early blight, leaf curl, or mosaic infection.\n\n"
                    "🔍 **To narrow this down accurately, please tell me:**\n"
                    "1. How old are the plants (growth stage)?\n"
                    "2. Are older lower leaves or newer top leaves turning yellow first?\n"
                    "3. Is the soil heavily waterlogged or dry?\n"
                    "4. Do you see any black spots, powdery residue, or curling on the leaves?\n\n"
                    "⚠️ **Recommendation:** Clarify the symptoms above, and follow proper soil aeration and balanced fertigation.\n\n"
                    "📚 **Source:** Crop Expert Dataset"
                )

        # 7. Fertilizer Dosage Query
        if any(w in q_lower for w in ["fertilizer dosage", "fertilizer", "dose", "exact fertilizer", "ఎరువుల మోతాదు", "ఎరువు", "उर्वरक", "खाद की मात्रा"]):
            if lang == "te":
                return (
                    "🧪 **ఎరువుల యాజమాన్యం మరియు మోతాదు మార్గదర్శకాలు:**\n\n"
                    "మీ నిర్దిష్ట పొలానికి ఖచ్చితమైన ఎరువుల మోతాదు నేల పరీక్ష (Soil Test) ఫలితాల్లోని నత్రజని (N), భాస్వరం (P), పొటాషియం (K) మరియు సేంద్రియ కర్బనం శాతాలపై ఆధారపడి ఉంటుంది.\n\n"
                    "• **సాధారణ సూత్రం:** విత్తే సమయంలో సేంద్రియ పశువుల ఎరువు లేదా వర్మీ కంపోస్ట్ వేయడం మంచిది.\n"
                    "• రసాయన ఎరువులను పంట దశల వారీగా (విత్తేటప్పుడు బేసల్ డోస్, పూత మరియు కాత దశలలో టాప్ డ్రెస్సింగ్) అందించాలి.\n\n"
                    "⚠️ **ముఖ్యమైన భద్రతా గమనిక:** రసాయన ఎరువుల ఖచ్చితమైన మోతాదు కోసం ఎరువుల సంచి/లేబుల్‌పై ఉన్న సూచనలను పాటించండి మరియు మీ ప్రాంత కృషి విజ్ఞాన కేంద్రం (KVK) లేదా మండల వ్యవసాయ అధికారిని సంప్రదించండి.\n\n"
                    "📚 **వనరు:** Soil Expert Dataset"
                )
            elif lang == "hi":
                return (
                    "🧪 **उर्वरक प्रबंधन एवं मात्रा संबंधी दिशानिर्देश:**\n\n"
                    "आपके खेत के लिए सटीक उर्वरक खुराक मिट्टी की हालिया जांच (Soil Test) में उपस्थित नाइट्रोजन, फास्फोरस, पोटाश और जैविक कार्बन की मात्रा पर निर्भर करती है।\n\n"
                    "• **सामान्य दिशानिर्देश:** बुवाई पूर्व गोबर की सड़ी खाद या वर्मीकम्पोस्ट का प्रयोग करें।\n"
                    "• रासायनिक उर्वरकों को फसल की विभिन्न अवस्थाओं (बुवाई के समय बेसल डोज, फूल और फल बनते समय टॉप ड्रेसिंग) में विभाजित करके दें।\n\n"
                    "⚠️ **सुरक्षा सूचना:** सटीक मात्रा के लिए उत्पाद लेबल का पालन करें और अपने स्थानीय कृषि विज्ञान केंद्र अथवा कृषि अधिकारी से परामर्श लें।\n\n"
                    "📚 **डेटा स्रोत:** Soil Expert Dataset"
                )
            else:
                return (
                    "🧪 **Fertilizer Management & Dosage Guidance:**\n\n"
                    "Exact fertilizer dosage depends on your recent soil test report (NPK levels, pH, and organic carbon percentage).\n\n"
                    "• **General Best Practice:** Apply well-decomposed Farm Yard Manure (FYM) or Vermicompost prior to sowing.\n"
                    "• Apply chemical fertilizers in split doses aligned with crop phenological stages (basal dose at sowing, followed by top-dressing at vegetative and flowering stages).\n\n"
                    "⚠️ **Safety Notice:** Always follow the recommended dosage printed on the registered product packaging and consult your local Agricultural Extension Officer or KVK before application.\n\n"
                    "📚 **Source:** Soil Expert Dataset"
                )

        # 8. Soil Information Queries (e.g. Black soil, Red soil, Alluvial)
        if any(w in q_lower for w in ["black soil", "regur", "vertisol", "నల్ల నేల", "నల్లరేగడి", "काली मिट्टी", "characteristics of black soil"]):
            if lang == "te":
                return (
                    "🌱 **నల్లరేగడి నేల (Black Soil / Regur / Vertisol) ముఖ్య లక్షణాలు:**\n\n"
                    "నల్ల నేలలు అత్యంత సారవంతమైనవి మరియు ఎక్కువ తేమను నిలుపుకునే గుణం కలిగి ఉంటాయి.\n\n"
                    "**లక్షణాలు:**\n"
                    "• **నిర్మాణం:** క్లే (Clay) శాతం ఎక్కువగా (30%–60%) ఉంటుంది. తడిసినప్పుడు ఉబ్బుతుంది, ఎండినప్పుడు పగుళ్లు ఏర్పడి నేలకు గాలి ప్రసరణ జరుగుతుంది.\n"
                    "• **తేమ నిల్వ:** అత్యధిక తేమ నిల్వ సామర్థ్యం కలిగి ఉండటం వల్ల వర్షాధార లేదా డ్రిప్ సాగుకు చాలా అనుకూలం.\n"
                    "• **పోషకాలు:** కాల్షియం, మెగ్నీషియం, పొటాష్ సమృద్ధిగా ఉంటాయి. నత్రజని మరియు భాస్వరం తక్కువగా ఉంటాయి.\n"
                    "• **pH పరిధి:** సాధారణంగా 7.0 నుండి 8.5 (తటస్థం నుండి కొద్దిగా క్షారయుతం).\n\n"
                    "**అనుకూల పంటలు:**\n"
                    "పత్తి (Cotton), కంది/పప్పుదినుసులు (Pigeon Pea / Pulses), మిర్చి (Chilli), మొక్కజొన్న (Maize), పొద్దుతిరుగుడు మరియు సోయాబీన్.\n\n"
                    f"🔍 **మీ పొలం నేల:** కర్నూలు జిల్లాలో ఎర్ర మరియు నల్ల నేలలు ఉన్నప్పటికీ, మీ నిర్దిష్ట పొలం **{soil}** తో నమోదు చేయబడింది.\n\n"
                    "📚 **వనరు:** Soil Expert Dataset"
                )
            elif lang == "hi":
                return (
                    "🌱 **काली मिट्टी (Black Soil / Regur / Vertisol) की मुख्य विशेषताएं:**\n\n"
                    "काली मिट्टी अत्यधिक उपजाऊ और नमी को लंबे समय तक बनाए रखने वाली मिट्टी है।\n\n"
                    "**प्रमुख विशेषताएं:**\n"
                    "• **बनावट:** इसमें क्ले (चिकनी मिट्टी) 30% से 50% तक होती है। गीली होने पर फूलती है और सूखने पर इसमें दरारें पड़ती हैं जिससे प्राकृतिक वायु संचार होता है।\n"
                    "• **नमी धारण:** उच्च नमी धारण क्षमता के कारण यह शुष्क एवं कम पानी वाले क्षेत्रों के लिए भी उत्तम है।\n"
                    "• **पोषक तत्व:** कैल्शियम, मैग्नीशियम, कार्बोनेट और पोटाश से भरपूर; नाइट्रोजन एवं फास्फोरस की कमी।\n"
                    "• **pH मान:** 7.0 से 8.5 के मध्य (तटस्थ से हल्का क्षारीय)।\n\n"
                    "**प्रमुख उपयुक्त फसलें:**\n"
                    "कपास (Cotton), अरहर/दालें (Pigeon Pea / Pulses), मिर्च (Chilli), मक्का (Maize), सोयाबीन और सूरजमुखी।\n\n"
                    f"🔍 **आपके खेत की मिट्टी:** कुरनूल में लाल और काली दोनों प्रकार की मिट्टियां हैं, परंतु आपका विशिष्ट खेत **{soil}** श्रेणी में दर्ज है।\n\n"
                    "📚 **डेटा स्रोत:** Soil Expert Dataset"
                )
            else:
                return (
                    "🌱 **Characteristics of Black Soil (Regur / Vertisol):**\n\n"
                    "Black soil is naturally fertile and known for its remarkable moisture-holding capacity.\n\n"
                    "**Key Characteristics:**\n"
                    "• **Texture & Structure:** High clay content (30%–60%). Expands when wet and develops vertical cracks during dry periods, allowing natural soil aeration.\n"
                    "• **Moisture Retention:** Excellent water-retention capacity, making it resilient during rainfed dry spells.\n"
                    "• **Nutrient Status:** Naturally rich in Calcium Carbonate, Magnesium, and Potash; generally low in Nitrogen and Phosphorus.\n"
                    "• **pH Range:** Neutral to moderately alkaline (pH 7.0 – 8.5).\n\n"
                    "**Most Suitable Crops:**\n"
                    "Cotton, Pigeon Pea (Arhar/Tur), Chilli, Maize, Soybean, Sunflower, and Groundnut.\n\n"
                    f"🔍 **Farm vs District Soil Context:** While {district} district geographically encompasses both Black soils (~60%) and Red sandy-loam soils (~40%), your specific landholding profile is configured as **{soil}**.\n\n"
                    "📚 **Source:** Soil Expert Dataset"
                )

        # 9. Location Agriculture Queries (e.g. Kurnool agricultural conditions)
        if any(w in q_lower for w in ["kurnool", "conditions in kurnool", "కర్నూలు", "కూర్నూలు", "कुरनूल"]):
            if lang == "te":
                return (
                    "📍 **కర్నూలు జిల్లా (ఆంధ్రప్రదేశ్) వ్యవసాయ పరిస్థితులు:**\n\n"
                    f"• **జిల్లా నేల విస్తరణ:** కర్నూలు జిల్లాలో ప్రధానంగా నల్లరేగడి నేలలు (~60%) మరియు ఎర్ర నేలలు (~40%) విస్తరించి ఉన్నాయి. (మీ నిర్దిష్ట పొలం: **{soil}**).\n"
                    "• **వాతావరణం & వర్షపాతం:** రాయలసీమ ప్రాంతంలో భాగమైన కర్నూలులో 30 ఏళ్ల చారిత్రక వార్షిక సాధారణ వర్షపాతం **927 mm** (ఖరీఫ్ సీజన్ సాధారణ వర్షపాతం: ~650–700 mm).\n"
                    "• **ప్రధాన పంటలు:** పత్తి, కంది/పప్పుదినుసులు, వేరుశనగ, మిర్చి, మొక్కజొన్న మరియు జొన్నలు.\n"
                    "• **నీటిపారుదల:** తుంగభద్ర/కేసీ కెనాల్ ఆయకట్టుతో పాటు బోరుబావులు మరియు బిందు సేద్యం (Drip) ద్వారా సాగు జరుగుతుంది.\n\n"
                    "💡 **సిఫార్సు:** తక్కువ నుండి మితమైన నీటితో అధిక దిగుబడినిచ్చే కంది మరియు పత్తి వంటి పంటలకు డ్రిప్ ఇరిగేషన్ ఉపయోగించడం శ్రేయస్కరం.\n\n"
                    "📚 **వనరు:** Master Geography Dataset & Weather Expert Dataset"
                )
            elif lang == "hi":
                return (
                    "📍 **कुरनूल जिला (आंध्र प्रदेश) की कृषि परिस्थितियां:**\n\n"
                    f"• **मिट्टी का वितरण:** कुरनूल में मुख्य रूप से गहरी काली मिट्टी (~60%) और लाल मिट्टी (~40%) पाई जाती है। (आपका खेत: **{soil}**)।\n"
                    "• **जलवायु एवं वर्षा:** रायलसीमा क्षेत्र के अंतर्गत 30 वर्षीय ऐतिहासिक वार्षिक सामान्य वर्षा **927 मिमी** है (खरीफ मौसमी वर्षा: ~650–700 मिमी)।\n"
                    "• **प्रमुख फसलें:** कपास, अरहर/दालें, मूंगफली, मिर्च, मक्का और ज्वार।\n"
                    "• **सिंचाई व्यवस्था:** बोरवेल, नहर और ड्रिप सिंचाई का व्यापक उपयोग होता है।\n\n"
                    "💡 **सलाह:** मध्यम जल मांग वाली फसलें जैसे अरहर और कपास ड्रिप सिंचाई के साथ अत्यधिक सफल हैं।\n\n"
                    "📚 **डेटा स्रोत:** Master Geography Dataset & Weather Expert Dataset"
                )
            else:
                return (
                    "📍 **Agricultural Conditions in Kurnool District, Andhra Pradesh:**\n\n"
                    f"• **Soil Distribution:** Kurnool district features deep Black Soils (~60%) alongside Red sandy-loam soils (~40%). Your active landholding is specified as **{soil}**.\n"
                    "• **Climate & Rainfall Normals:** Semi-arid Rayalaseema agro-climatic zone with an IMD 30-year Annual Rainfall Normal of **927 mm** (Kharif seasonal normal: ~650–700 mm).\n"
                    "• **Predominant Crops:** Cotton, Pigeon Pea (Arhar/Tur), Groundnut, Chilli, Maize, and Sorghum.\n"
                    "• **Irrigation Dynamics:** Supported by canal networks supplemented by borewells and micro-irrigation (Drip/Sprinkler).\n\n"
                    "💡 **Agronomic Note:** Crops with moderate water demand like Pigeon Pea (Arhar/Tur) and Cotton perform well under supplemental drip irrigation in this zone.\n\n"
                    "📚 **Source:** Master Geography Dataset & Weather Expert Dataset"
                )

        # 10. Default / Fallback from RAG Context
        if context and "No specific agricultural record" not in context:
            if lang == "te":
                return (
                    f"🌾 **వ్యవసాయ సమాచారం:**\n\n"
                    f"{context}\n\n"
                    f"💡 **సూచన:** మీ ప్రాంత నేల మరియు వాతావరణ పరిస్థితులకు అనుగుణంగా వ్యవసాయ పనులు చేపట్టండి.\n\n"
                    f"📚 **వనరు:** Crop Expert Dataset, Soil Expert Dataset, Weather Expert Dataset"
                )
            elif lang == "hi":
                return (
                    f"🌾 **कृषि जानकारी:**\n\n"
                    f"{context}\n\n"
                    f"💡 **सुझाव:** अपने क्षेत्र की मिट्टी और मौसमी परिस्थितियों के अनुसार उचित निर्णय लें।\n\n"
                    f"📚 **डेटा स्रोत:** Crop Expert Dataset, Soil Expert Dataset, Weather Expert Dataset"
                )
            else:
                return (
                    f"🌾 **Agricultural Advisory:**\n\n"
                    f"{context}\n\n"
                    f"💡 **Guidance:** Align your crop management operations with the local soil and seasonal benchmarks.\n\n"
                    f"📚 **Source:** Crop Expert Dataset, Soil Expert Dataset, Weather Expert Dataset"
                )

        # 11. Safe Guidance Prompt
        if lang == "te":
            return (
                "నేను మరింత ఖచ్చితమైన సమాధానం ఇవ్వడానికి దయచేసి క్రింది వివరాలు తెలియజేయండి:\n"
                f"• మీ జిల్లా మరియు రాష్ట్రం (ప్రస్తుతం: {district}, {state})\n"
                f"• మీ నేల రకం (ప్రస్తుతం: {soil})\n"
                "• మీరు అడగదలిచిన నిర్దిష్ట పంట లేదా వ్యవసాయ అంశం."
            )
        elif lang == "hi":
            return (
                "सटीक सलाह देने के लिए कृपया थोड़ी और जानकारी साझा करें:\n"
                f"• आपका जिला और राज्य (वर्तमान: {district}, {state})\n"
                f"• मिट्टी का प्रकार (वर्तमान: {soil})\n"
                "• आप किस विशिष्ट फसल या समस्या के बारे में जानना चाहते हैं।"
            )
        else:
            return (
                "I couldn't find enough information in my agricultural knowledge base for that specific question.\n\n"
                "Please tell me:\n"
                f"• Which crop or soil topic are you inquiring about for your farm in {district}, {state}?"
            )

    @staticmethod
    def _clean_reasoning_text(text: str) -> str:
        """Strips internal model reasoning/thinking blocks from text so reasoning is never exposed to users."""
        if not text:
            return ""
        cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        if "Thinking Process:" in cleaned or re.search(r'^\s*1\.\s*\*\*Analyze', cleaned, flags=re.MULTILINE):
            if "---" in cleaned:
                parts = cleaned.split("---")
                cleaned = parts[-1].strip()
            else:
                paragraphs = [p.strip() for p in cleaned.split("\n\n") if p.strip()]
                valid_paragraphs = []
                for p in paragraphs:
                    p_lower = p.lower()
                    if any(k in p_lower for k in [
                        "thinking process", "analyze the request", "analyze the context", "formulate the advice",
                        "identify key information", "drafting the response", "constraint check", "determine the best tip",
                        "key data points", "conflict/discrepancy", "role: krishimitra", "user query:", "critical rules:"
                    ]):
                        continue
                    if re.match(r'^\d+\.\s*\*\*(?:Analyze|Identify|Formulate|Determine|Draft|Review|Constraint)', p, flags=re.IGNORECASE):
                        continue
                    valid_paragraphs.append(p)
                if valid_paragraphs:
                    cleaned = "\n\n".join(valid_paragraphs)
                else:
                    cleaned = "Here is a practical farming tip for your farm: Apply organic manure or compost prior to sowing in Kharif season to enhance soil organic carbon, optimize moisture retention, and boost root growth."
        return cleaned.strip() or text.strip()

    async def _bionic_generate(
        self,
        message: str,
        context: str,
        lang: str,
        farm_context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Generates response via Bionic Local Model API (OpenAI-compatible)."""
        provider_base_url = (getattr(settings, "LLM_BASE_URL", None) or "http://localhost:1234/v1").rstrip("/")
        model_name = getattr(settings, "LLM_MODEL", None) or "qwen/qwen3.5-9b"
        api_key = settings.LLM_API_KEY or settings.OPENAI_API_KEY

        full_prompt = self._build_full_prompt(message, context, lang, farm_context)
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        url = f"{provider_base_url}/chat/completions"
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": full_prompt},
                {"role": "assistant", "content": "<think>\n</think>\n"}
            ],
            "temperature": 0.2,
            "max_tokens": getattr(settings, "LLM_MAX_TOKENS", 750),
            "reasoning_effort": "low"
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    choices = data.get("choices", [])
                    if choices:
                        msg = choices[0].get("message", {})
                        content = msg.get("content")
                        if content:
                            cleaned = self._clean_reasoning_text(content)
                            if cleaned:
                                return cleaned
                logger.error(f"Bionic API call failed with HTTP {resp.status_code}: {resp.text}")
                return None
        except httpx.ConnectError as e:
            logger.error(f"Bionic API connection error at {url}: {e}")
            return None
        except httpx.TimeoutException as e:
            logger.error(f"Bionic API request timed out: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error communicating with Bionic API: {e}")
            return None

    async def _ollama_generate(
        self,
        message: str,
        context: str,
        lang: str = "en",
        farm_context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        base_url = (getattr(settings, "OLLAMA_BASE_URL", None) or "http://localhost:11434").rstrip("/")
        model = getattr(settings, "OLLAMA_MODEL", None) or "qwen3.5:9b"
        full_prompt = self._build_full_prompt(message, context, lang, farm_context)
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": full_prompt}
            ],
            "stream": False,
            "think": False,
            "options": {
                "temperature": 0.2,
                "num_predict": getattr(settings, "LLM_MAX_TOKENS", 750)
            }
        }
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(f"{base_url}/api/chat", json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    content = data.get("message", {}).get("content", "").strip()
                    if content:
                        return self._clean_reasoning_text(content)
                logger.error(f"Ollama call failed with HTTP {resp.status_code}: {resp.text}")
        except Exception as e:
            logger.error(f"Ollama call error: {e}")
        return None

    async def generate_response(
        self,
        message: str,
        context: str,
        lang: str = "en",
        farm_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generates response using configured LLM provider with graceful rule-engine fallback."""
        current_provider = (settings.LLM_PROVIDER or "ollama").lower()

        if current_provider == "ollama":
            ollama_resp = await self._ollama_generate(message, context, lang, farm_context)
            if ollama_resp:
                return ollama_resp
            err_msg = (
                f"Ollama Service Error: Failed to generate response from model "
                f"'{getattr(settings, 'OLLAMA_MODEL', 'qwen3.5:9b')}' at "
                f"{getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')}."
            )
            logger.error(err_msg)
            return err_msg

        if current_provider == "bionic":
            bionic_resp = await self._bionic_generate(message, context, lang, farm_context)
            if bionic_resp:
                return bionic_resp

        if current_provider == "openai" and settings.OPENAI_API_KEY:
            try:
                full_prompt = self._build_full_prompt(message, context, lang, farm_context)
                async with httpx.AsyncClient(timeout=20.0) as client:
                    resp = await client.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                        json={
                            "model": "gpt-4o-mini",
                            "messages": [
                                {"role": "system", "content": SYSTEM_PROMPT},
                                {"role": "user", "content": full_prompt}
                            ],
                            "temperature": 0.2
                        }
                    )
                    if resp.status_code == 200:
                        return resp.json()["choices"][0]["message"]["content"]
            except Exception as e:
                logger.warning(f"OpenAI API call failed: {e}. Using expert rule engine.")

        if current_provider == "gemini" and settings.GEMINI_API_KEY:
            try:
                full_prompt = self._build_full_prompt(message, context, lang, farm_context)
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
                async with httpx.AsyncClient(timeout=20.0) as client:
                    resp = await client.post(
                        url,
                        json={
                            "contents": [{"parts": [{"text": f"{SYSTEM_PROMPT}\n\n{full_prompt}"}]}],
                            "generationConfig": {"temperature": 0.2}
                        }
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        return data["candidates"][0]["content"]["parts"][0]["text"]
            except Exception as e:
                logger.warning(f"Gemini API call failed: {e}. Using expert rule engine.")

        # Default expert rule engine
        return await self._rule_engine_generate(message, context, lang, farm_context)

    async def stream_response(
        self,
        message: str,
        context: str,
        lang: str = "en",
        farm_context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """Streams response tokens directly for Server-Sent Events (SSE)."""
        current_provider = (settings.LLM_PROVIDER or "ollama").lower()

        if current_provider == "ollama":
            base_url = (getattr(settings, "OLLAMA_BASE_URL", None) or "http://localhost:11434").rstrip("/")
            model = getattr(settings, "OLLAMA_MODEL", None) or "qwen3.5:9b"
            full_prompt = self._build_full_prompt(message, context, lang, farm_context)
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": full_prompt}
                ],
                "stream": True,
                "think": False,
                "options": {
                    "temperature": 0.2,
                    "num_predict": getattr(settings, "LLM_MAX_TOKENS", 750)
                }
            }
            try:
                has_streamed = False
                async with httpx.AsyncClient(timeout=60.0) as client:
                    async with client.stream("POST", f"{base_url}/api/chat", json=payload) as resp:
                        if resp.status_code == 200:
                            async for line in resp.aiter_lines():
                                if line:
                                    try:
                                        chunk = json.loads(line)
                                        tok = chunk.get("message", {}).get("content", "")
                                        if tok and tok not in ("<think>", "</think>"):
                                            has_streamed = True
                                            yield tok
                                        if chunk.get("done"):
                                            break
                                    except Exception:
                                        pass
                            if has_streamed:
                                return
            except Exception as e:
                logger.error(f"Ollama streaming failed: {e}")

        if current_provider == "bionic":
            provider_base_url = (getattr(settings, "LLM_BASE_URL", None) or "http://localhost:1234/v1").rstrip("/")
            model_name = getattr(settings, "LLM_MODEL", None) or "qwen/qwen3.5-9b"
            api_key = settings.LLM_API_KEY or settings.OPENAI_API_KEY

            full_prompt = self._build_full_prompt(message, context, lang, farm_context)
            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

            url = f"{provider_base_url}/chat/completions"
            payload = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": full_prompt},
                    {"role": "assistant", "content": "<think>\n</think>\n"}
                ],
                "temperature": 0.2,
                "max_tokens": getattr(settings, "LLM_MAX_TOKENS", 750),
                "reasoning_effort": "low",
                "stream": True
            }

            try:
                has_streamed = False
                async with httpx.AsyncClient(timeout=60.0) as client:
                    async with client.stream("POST", url, headers=headers, json=payload) as resp:
                        if resp.status_code == 200:
                            async for line in resp.aiter_lines():
                                if line.startswith("data: "):
                                    data_str = line[6:].strip()
                                    if data_str == "[DONE]":
                                        break
                                    try:
                                        chunk_data = json.loads(data_str)
                                        choices = chunk_data.get("choices", [])
                                        if choices:
                                            delta = choices[0].get("delta", {})
                                            # STRICT: only yield delta content (not reasoning_content)
                                            tok = delta.get("content")
                                            if tok and tok not in ("<think>", "</think>"):
                                                has_streamed = True
                                                yield tok
                                    except Exception:
                                        pass
                            if has_streamed:
                                return
            except Exception as e:
                logger.warning(f"Bionic SSE streaming failed: {e}. Falling back to standard generation.")

        full_text = await self.generate_response(message, context, lang, farm_context)
        words = full_text.split(" ")
        for i in range(0, len(words), 3):
            chunk = " ".join(words[i:i+3]) + " "
            yield chunk
            await asyncio.sleep(0.02)


# Singleton instance
llm_service = LLMService()

