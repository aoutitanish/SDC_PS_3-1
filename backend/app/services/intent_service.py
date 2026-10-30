"""
Intent Detection, Query Normalization & Contextual Intent Resolution Service for KrishiMitra AI.
Accurately categorizes farmer queries into 14 distinct agricultural intents.
Handles spelling mistakes, missing spaces, phonetic Indian terminology, and multi-turn follow-ups.
Supports English, Telugu (తెలుగు), and Hindi (हिन्दी).
"""

import re
import logging
from typing import Dict, Any, Tuple, Optional, List

logger = logging.getLogger(__name__)

INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa", "Gujarat",
    "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh",
    "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
    "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh",
    "Uttarakhand", "West Bengal", "Andaman And Nicobar Islands", "Jammu And Kashmir", "Ladakh"
]

import os
import pandas as pd

DISTRICT_TO_STATE_MAP: Dict[str, str] = {}
DISTRICT_CANONICAL_MAP: Dict[str, Tuple[str, str]] = {}

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "data", "processed")
_MASTER_CSV = os.path.join(_DATA_DIR, "master_district_profiles.csv")

if os.path.exists(_MASTER_CSV):
    try:
        _df = pd.read_csv(_MASTER_CSV)
        for _, _row in _df.iterrows():
            _st = str(_row["State_Name"]).strip()
            _dt = str(_row["District_Name"]).strip()
            DISTRICT_TO_STATE_MAP[_dt.lower()] = _st
            DISTRICT_CANONICAL_MAP[_dt.lower()] = (_dt, _st)
    except Exception as _e:
        logger.warning(f"Could not load master district profiles: {_e}")

# Common regional aliases
REGIONAL_DISTRICT_ALIASES = {
    "ganganagar": ("Ganganagar", "Rajasthan"),
    "sri ganganagar": ("Ganganagar", "Rajasthan"),
    "sriganganagar": ("Ganganagar", "Rajasthan"),
    "vidarbha": ("Amravati", "Maharashtra"),
    "ludhiana": ("Ludhiana", "Punjab"),
    "palakkad": ("Palakkad", "Kerala"),
    "warangal": ("Warangal", "Telangana"),
    "kurnool": ("Kurnool", "Andhra Pradesh"),
    "vizag": ("Visakhapatnam", "Andhra Pradesh"),
    "hyderabad": ("Hyderabad", "Telangana"),
    "kashmir": ("Kashmir", "Jammu And Kashmir"),
    "srinagar": ("Srinagar", "Jammu And Kashmir"),
    "jammu": ("Jammu", "Jammu And Kashmir"),
    "ladakh": ("Leh", "Ladakh"),
    "rayalaseema": ("Kurnool", "Andhra Pradesh")
}
for _k, _v in REGIONAL_DISTRICT_ALIASES.items():
    DISTRICT_TO_STATE_MAP[_k] = _v[1]
    DISTRICT_CANONICAL_MAP[_k] = _v

# Common agricultural typos and missing spaces dictionary
TYPO_CORRECTIONS = {
    r'\bkurnooland\b': 'kurnool and',
    r'\bandhrapradesh\b': 'andhra pradesh',
    r'\bblacksoil\b': 'black soil',
    r'\bredsoil\b': 'red soil',
    r'\bdripirrigation\b': 'drip irrigation',
    r'\bborewellwater\b': 'borewell water',
    r'\bwaterrequirement\b': 'water requirement',
    r'\bcrock\b': 'crop',
    r'\bcrocks\b': 'crops',
    r'\bcrp\b': 'crop',
    r'\bcrps\b': 'crops',
    r'\bwhick\b': 'which',
    r'\bwatr\b': 'water',
    r'\birigation\b': 'irrigation',
    r'\bfertelizer\b': 'fertilizer',
    r'\bfertilyzer\b': 'fertilizer',
    r'\bsuitable\b': 'suitable',
    r'\bsutable\b': 'suitable',
    r'\bsuitble\b': 'suitable',
    r'\brecommend\b': 'recommend',
    r'\brecomand\b': 'recommend',
    r'\brecomnd\b': 'recommend',
    r'\bsoil\b': 'soil',
    r'\bsoyl\b': 'soil',
    r'\bpigeonpea\b': 'pigeon pea',
    r'\bpigionpea\b': 'pigeon pea',
    r'\bgroundnut\b': 'groundnut',
    r'\bgrounnut\b': 'groundnut',
    r'\bkhariff\b': 'kharif',
    r'\brabii\b': 'rabi',
    r'\bcotton\b': 'cotton',
    r'\bcoton\b': 'cotton'
}


class IntentService:
    @staticmethod
    def normalize_query(query: str) -> str:
        """
        Normalizes query internally by fixing typos, missing spaces, and punctuation
        without altering the original user display string.
        """
        if not query:
            return ""
        norm = query.lower()
        for pattern, replacement in TYPO_CORRECTIONS.items():
            norm = re.sub(pattern, replacement, norm, flags=re.IGNORECASE)
        
        # Insert space before 'which', 'what', 'and', 'with', 'for' if accidentally glued to a word
        norm = re.sub(r'([a-z]+)(which|what|where|when|and|with|for|crop|soil)\b', r'\1 \2', norm)
        return norm.strip()

    @classmethod
    def extract_entities(cls, query: str) -> Dict[str, Any]:
        """Extracts location, soil, size, irrigation, season, crops, and pH from query."""
        norm = cls.normalize_query(query)
        q_lower = norm.lower()

        extracted: Dict[str, Any] = {
            "state": None,
            "district": None,
            "soil_type": None,
            "farm_size_acres": None,
            "irrigation_type": None,
            "water_source": None,
            "water_availability": None,
            "season": None,
            "rainfall_condition": None,
            "temperature_condition": None,
            "ph": None,
            "crop_mentions": []
        }

        # 1. State detection
        for st in INDIAN_STATES:
            if re.search(r'\b' + re.escape(st.lower()) + r'\b', q_lower):
                extracted["state"] = st
                break
        if not extracted["state"]:
            if "ఆంధ్రప్రదేశ్" in query or "ఆంధ్ర" in query or "andhra" in q_lower:
                extracted["state"] = "Andhra Pradesh"
            elif "తెలంగాణ" in query or "telangana" in q_lower:
                extracted["state"] = "Telangana"
            elif "पंजाब" in query or "punjab" in q_lower:
                extracted["state"] = "Punjab"
            elif "राजस्थान" in query or "rajasthan" in q_lower:
                extracted["state"] = "Rajasthan"
            elif "महाराष्ट्र" in query or "maharashtra" in q_lower:
                extracted["state"] = "Maharashtra"
            elif "కేరళ" in query or "kerala" in q_lower:
                extracted["state"] = "Kerala"

        # 2. District detection across all 635+ district terms
        sorted_dist_keys = sorted(DISTRICT_CANONICAL_MAP.keys(), key=len, reverse=True)
        for dk in sorted_dist_keys:
            if re.search(r'\b' + re.escape(dk) + r'\b', q_lower):
                canonical_dist, canonical_st = DISTRICT_CANONICAL_MAP[dk]
                extracted["district"] = canonical_dist
                if not extracted["state"]:
                    extracted["state"] = canonical_st
                break

        # Regex fallback for "farm in <Location>", "in <Location>, <State>"
        if not extracted["district"] or not extracted["state"]:
            loc_match = re.search(r'(?:farm\s+is\s+in|farm\s+in|in)\s+([a-z\s]+?)(?:,|\.|\b|\s+state|\s+district)', q_lower)
            if loc_match:
                candidate = loc_match.group(1).strip()
                if candidate in DISTRICT_CANONICAL_MAP:
                    canonical_dist, canonical_st = DISTRICT_CANONICAL_MAP[candidate]
                    extracted["district"] = extracted["district"] or canonical_dist
                    extracted["state"] = extracted["state"] or canonical_st

        # 3. Farm size (e.g. 5 acres, 4 ఎకరాలు, 5 ha)
        size_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:acres?|acre|ఎకరాల|ఎకరాలు|एकड़|hectares?|ha)', query, re.IGNORECASE)
        if size_match:
            try:
                extracted["farm_size_acres"] = float(size_match.group(1))
            except ValueError:
                pass

        # 4. Soil Type
        if any(w in q_lower or w in query for w in ["sandy/loamy", "sandy loamy", "sandy loam", "sandy soil", "desert soil", "ఇసుక నేల", "बलुई"]):
            extracted["soil_type"] = "Sandy / Loamy Soil"
        elif any(w in q_lower or w in query for w in ["fertile loamy", "loamy soil", "loamy", "loam", "alluvial soil", "alluvial", "ఒండ్రు నేల", "जलोढ़"]):
            extracted["soil_type"] = "Alluvial / Loamy Soil"
        elif any(w in q_lower or w in query for w in ["black cotton soil", "black cotton", "black soil", "vertisol", "regur", "నల్ల నేల", "నల్లరేగడి", "కాళీ మిట్టి", "काली मिट्टी"]):
            extracted["soil_type"] = "Black Soil (Regur/Vertisol)"
        elif any(w in q_lower or w in query for w in ["laterite soil", "laterite", "లేటరైట్"]):
            extracted["soil_type"] = "Laterite Soil"
        elif any(w in q_lower or w in query for w in ["red soil", "red cotton", "ఎర్ర నేల", "ఎర్ర", "लाल मिट्टी", "alfisol"]):
            extracted["soil_type"] = "Red and Yellow Soil"

        # 5. Water Availability & Irrigation Type
        if any(w in q_lower or w in query for w in ["very limited water", "limited water availability", "limited water", "water scarcity", "low water"]):
            extracted["water_availability"] = "Limited"
        elif any(w in q_lower or w in query for w in ["moderate water availability", "moderate water"]):
            extracted["water_availability"] = "Moderate"
        elif any(w in q_lower or w in query for w in ["good irrigation availability", "good water", "high rainfall", "heavy rainfall"]):
            extracted["water_availability"] = "Good"

        # Check negative facts explicitly
        has_no_borewell = any(w in q_lower for w in ["no borewell", "without borewell", "no borewell and", "no borewell or", "borewell is not", "don't have borewell", "dont have borewell", "no borewell and no drip"])
        has_no_drip = any(w in q_lower for w in ["no drip", "without drip", "no drip irrigation", "don't have drip", "dont have drip", "no borewell and no drip"])
        is_only_rainwater = any(w in q_lower for w in ["only rainwater", "rainwater only", "just rainwater", "rainfed only"])

        if is_only_rainwater:
            extracted["water_source"] = "Rainwater / Surface"
            extracted["irrigation_type"] = "Rainfed"
            extracted["has_borewell"] = False
            extracted["has_drip"] = False
        
        if has_no_borewell:
            extracted["has_borewell"] = False
            if not extracted["water_source"] or extracted["water_source"] == "Borewell":
                extracted["water_source"] = "Canal / Rainwater"
        elif any(w in q_lower or w in query for w in ["borewell", "బోర్వెల్", "బోరు", "नलकूप", "बोरवेल"]):
            extracted["water_source"] = "Borewell"
            extracted["has_borewell"] = True
        elif any(w in q_lower or w in query for w in ["open well", "well", "బావి", "कुआं"]):
            extracted["water_source"] = "Open Well"
            extracted["has_borewell"] = False
        elif any(w in q_lower or w in query for w in ["river", "నది"]):
            extracted["water_source"] = "River"
            extracted["has_borewell"] = False

        if has_no_drip:
            extracted["has_drip"] = False
            if not extracted["irrigation_type"] or extracted["irrigation_type"] == "Drip Irrigation":
                extracted["irrigation_type"] = "Rainfed" if is_only_rainwater else "Canal Irrigation"
        elif any(w in q_lower or w in query for w in ["drip", "డ్రిప్", "ड्रिप"]):
            extracted["irrigation_type"] = "Drip Irrigation"
            extracted["has_drip"] = True
        elif any(w in q_lower or w in query for w in ["sprinkler", "స్ప్రింక్లర్", "स्प्रिंकलर"]):
            extracted["irrigation_type"] = "Sprinkler Irrigation"
            extracted["has_drip"] = False
        elif any(w in q_lower or w in query for w in ["canal", "కాలువ", "नहर"]):
            extracted["irrigation_type"] = "Canal Irrigation"
            extracted["has_drip"] = False
        elif any(w in q_lower or w in query for w in ["rainfed farming", "rainfed", "వర్షాధార", "वर्षा आधारित", "no irrigation"]):
            extracted["irrigation_type"] = "Rainfed"
            extracted["has_drip"] = False
        elif any(w in q_lower or w in query for w in ["good irrigation availability", "good irrigation"]):
            extracted["irrigation_type"] = "Good Irrigation"
        elif any(w in q_lower or w in query for w in ["limited irrigation"]):
            extracted["irrigation_type"] = "Limited Irrigation"

        # 6. Season & Weather Conditions
        if any(w in q_lower or w in query for w in ["kharif", "ఖరీఫ్", "खरीफ", "monsoon rainfall", "monsoon", "వర్షాకాలం"]):
            extracted["season"] = "Kharif"
        elif any(w in q_lower or w in query for w in ["rabi", "రబీ", "रबी", "winter conditions", "winter", "శీతాకాలం"]):
            extracted["season"] = "Rabi"
        elif any(w in q_lower or w in query for w in ["summer/zaid", "summer", "zaid", "వేసవి", "जायद", "hot and dry", "hot dry"]):
            extracted["season"] = "Summer"

        # Rainfall condition
        if any(w in q_lower or w in query for w in ["drought", "very low rainfall", "scarce rainfall", "dry spell", "water scarcity"]):
            extracted["rainfall_condition"] = "drought"
            extracted["water_availability"] = "Limited"
        elif any(w in q_lower or w in query for w in ["heavy rainfall", "excess water", "excessive rain", "flooding", "heavy monsoon"]):
            extracted["rainfall_condition"] = "heavy"
            extracted["water_availability"] = "Good"
        elif any(w in q_lower or w in query for w in ["normal monsoon", "normal rainfall", "moderate rainfall"]):
            extracted["rainfall_condition"] = "normal"
            if not extracted["water_availability"]:
                extracted["water_availability"] = "Moderate"

        # Temperature condition
        if any(w in q_lower or w in query for w in ["hot and dry", "hot dry", "hot weather", "high temperature", "extreme heat"]):
            extracted["temperature_condition"] = "hot"
        elif any(w in q_lower or w in query for w in ["winter conditions", "cold weather", "cool temperature"]):
            extracted["temperature_condition"] = "cold"

        # 7. pH extraction
        ph_match = re.search(r'ph\s*(?:is|=|:)?\s*(\d+(?:\.\d+)?)', q_lower)
        if ph_match:
            try:
                extracted["ph"] = float(ph_match.group(1))
            except ValueError:
                pass

        # 8. International Country / Global Region Detection
        extracted["country"] = "India"
        global_countries = [
            ("kenya", "Kenya"), ("california", "United States"), ("usa", "United States"),
            ("united states", "United States"), ("australia", "Australia"), ("brazil", "Brazil"),
            ("egypt", "Egypt"), ("nigeria", "Nigeria"), ("vietnam", "Vietnam"), ("thailand", "Thailand"),
            ("china", "China"), ("canada", "Canada"), ("ukraine", "Ukraine"), ("argentina", "Argentina"),
            ("bangladesh", "Bangladesh"), ("nepal", "Nepal"), ("sri lanka", "Sri Lanka")
        ]
        for c_term, c_name in global_countries:
            if re.search(r'\b' + re.escape(c_term) + r'\b', q_lower):
                extracted["country"] = c_name
                extracted["has_explicit_location"] = True
                if not extracted["state"]:
                    extracted["state"] = c_name
                break

        # 9. Comprehensive Crop Mentions (50+ Major Indian and Global Crops)
        known_crops = [
            # Cereals & Millets
            ("rice", "Rice / Paddy"), ("paddy", "Rice / Paddy"), ("వరి", "Rice / Paddy"), ("धान", "Rice / Paddy"),
            ("wheat", "Wheat"), ("గోధుమ", "Wheat"), ("गेहूं", "Wheat"),
            ("maize", "Maize"), ("corn", "Maize"), ("మొక్కజొన్న", "Maize"), ("मक्का", "Maize"),
            ("sorghum", "Sorghum (Jowar)"), ("jowar", "Sorghum (Jowar)"), ("జొన్న", "Sorghum (Jowar)"), ("ज्वार", "Sorghum (Jowar)"),
            ("pearl millet", "Pearl Millet (Bajra)"), ("bajra", "Pearl Millet (Bajra)"), ("సజ్జ", "Pearl Millet (Bajra)"), ("बाजरा", "Pearl Millet (Bajra)"),
            ("finger millet", "Finger Millet (Ragi)"), ("ragi", "Finger Millet (Ragi)"), ("రాగి", "Finger Millet (Ragi)"), ("रागी", "Finger Millet (Ragi)"),
            ("barley", "Barley"), ("జావ", "Barley"), ("जौ", "Barley"),
            # Pulses
            ("arhar", "Arhar/Tur (Pigeon Pea)"), ("tur", "Arhar/Tur (Pigeon Pea)"), ("pigeon pea", "Arhar/Tur (Pigeon Pea)"),
            ("pigeonpea", "Arhar/Tur (Pigeon Pea)"), ("కంది", "Arhar/Tur (Pigeon Pea)"), ("अरहर", "Arhar/Tur (Pigeon Pea)"),
            ("chickpea", "Chickpea (Gram)"), ("gram", "Chickpea (Gram)"), ("chana", "Chickpea (Gram)"), ("శనగ", "Chickpea (Gram)"), ("चना", "Chickpea (Gram)"),
            ("green gram", "Green Gram (Moong)"), ("moong", "Green Gram (Moong)"), ("పెసర", "Green Gram (Moong)"), ("मूंग", "Green Gram (Moong)"),
            ("black gram", "Black Gram (Urad)"), ("urad", "Black Gram (Urad)"), ("మినుము", "Black Gram (Urad)"), ("उड़द", "Black Gram (Urad)"),
            ("lentil", "Lentil (Masoor)"), ("masoor", "Lentil (Masoor)"), ("मसूर", "Lentil (Masoor)"),
            # Cash & Fiber Crops
            ("cotton", "Cotton"), ("పత్తి", "Cotton"), ("कपास", "Cotton"),
            ("sugarcane", "Sugarcane"), ("చెరకు", "Sugarcane"), ("गन्ना", "Sugarcane"),
            ("jute", "Jute"), ("పనస", "Jute"), ("पटसन", "Jute"),
            ("tobacco", "Tobacco"), ("పొగాకు", "Tobacco"), ("तंबाकू", "Tobacco"),
            # Oilseeds
            ("groundnut", "Groundnut"), ("peanut", "Groundnut"), ("వేరుశనగ", "Groundnut"), ("मूंगफली", "Groundnut"),
            ("soybean", "Soybean"), ("సోయాబీన్", "Soybean"), ("सोयाबीन", "Soybean"),
            ("mustard", "Mustard / Rapeseed"), ("rapeseed", "Mustard / Rapeseed"), ("ఆవాలు", "Mustard / Rapeseed"), ("सरसों", "Mustard / Rapeseed"),
            ("sunflower", "Sunflower"), ("పొద్దుతిరుగుడు", "Sunflower"), ("सूरजमुखी", "Sunflower"),
            ("sesame", "Sesame (Til)"), ("sesamum", "Sesame (Til)"), ("nuvvulu", "Sesame (Til)"), ("నువ్వులు", "Sesame (Til)"), ("तिल", "Sesame (Til)"),
            ("castor", "Castor"), ("ఆముదం", "Castor"), ("अरंडी", "Castor"),
            # Vegetables & Spices
            ("chilli", "Chilli"), ("chillies", "Chilli"), ("మిరప", "Chilli"), ("मिर्च", "Chilli"),
            ("tomato", "Tomato"), ("టమోటా", "Tomato"), ("టమాట", "Tomato"), ("टमाटर", "Tomato"),
            ("onion", "Onion"), ("ఉల్లి", "Onion"), ("प्याज", "Onion"),
            ("potato", "Potato"), ("బంగాళాదుంప", "Potato"), ("आलू", "Potato"),
            ("turmeric", "Turmeric"), ("పసుపు", "Turmeric"), ("हल्दी", "Turmeric"),
            ("ginger", "Ginger"), ("అల్లం", "Ginger"), ("अदरक", "Ginger"),
            ("garlic", "Garlic"), ("వెల్లుల్లి", "Garlic"), ("लहसुन", "Garlic"),
            # Fruits & Plantation
            ("banana", "Banana"), ("అరటి", "Banana"), ("केला", "Banana"),
            ("mango", "Mango"), ("మామిడి", "Mango"), ("आम", "Mango"),
            ("papaya", "Papaya"), ("బొప్పాయి", "Papaya"), ("पपीता", "Papaya"),
            ("apple", "Apple"), ("ఆపిల్", "Apple"), ("सेब", "Apple"),
            ("saffron", "Saffron"), ("కుంకుమపువ్వు", "Saffron"), ("केसर", "Saffron"),
            ("coffee", "Coffee"), ("కాఫీ", "Coffee"), ("कॉफी", "Coffee"),
            ("tea", "Tea"), ("టీ", "Tea"), ("चाय", "Tea"),
            ("rubber", "Rubber"), ("రబ్బరు", "Rubber"),
            ("coconut", "Coconut"), ("కొబ్బరి", "Coconut"), ("नारियल", "Coconut")
        ]
        for term, standard_name in known_crops:
            if re.search(r'\b' + re.escape(term) + r'\b', q_lower) or term in query:
                if standard_name not in extracted["crop_mentions"]:
                    extracted["crop_mentions"].append(standard_name)

        # Location reset & farm context flags
        extracted["reset_location"] = any(
            p in q_lower for p in [
                "ignore my previous location", "ignore previous location", "ignore the previous location",
                "not in my previous location", "forget my previous location", "ignore old location"
            ]
        )
        extracted["is_other_farm"] = any(
            p in q_lower for p in [
                "my other farm", "another farm", "different farm", "second farm", "other farm"
            ]
        )
        extracted["is_my_farm_query"] = any(
            p in q_lower for p in [
                "my farm", "for my farm", "on my farm", "in my farm", "నా పొలం", "నా భూమి", "मेरे खेत", "मेरा खेत"
            ]
        )
        extracted["has_explicit_location"] = bool(extracted.get("state") or extracted.get("district") or extracted.get("country") != "India")

        return extracted

    @classmethod
    def classify_question_category(cls, query: str, extracted: Optional[Dict[str, Any]] = None) -> str:
        """
        Classifies query into 16 distinct agricultural and boundary categories:
          - OUT_OF_SCOPE: non-agricultural queries (crypto, coding, entertainment, politics, tech)
          - PEST_DISEASE: plant diseases, insect pests, IPM, spray fungicides/insecticides
          - FERTILIZER_NUTRIENT: NPK ratios, fertilizer dosing, deficiency symptoms, organic manure
          - GOVERNMENT_SCHEME: PM-KISAN, PMFBY insurance, subsidies, KCC loans, portals
          - SOWING_CALENDAR: sowing windows, planting dates, maturity duration
          - CROP_ROTATION: crop succession, intercropping, green manuring
          - POST_HARVEST: harvesting stage, storage moisture, grain protection, warehousing
          - CROP_FACT: specific crop physiology / requirement (e.g. ideal soil pH for cotton)
          - GENERAL_KNOWLEDGE: agronomic science concepts (e.g. characteristics of black soil)
          - REGIONAL_QUERY: location-specific crop suitability (e.g. what crops suit Kashmir/Kenya?)
          - FARM_RECOMMENDATION: farm-specific recommendation request
          - CROP_COMPARISON: comparing two or more crops
          - EXPLANATION: explaining an earlier recommendation ("why?")
          - MARKET_WEATHER: weather forecast, rain, or mandi prices
          - OTHER: general greeting, ambiguous agricultural question
        """
        norm = cls.normalize_query(query).lower()
        ext = extracted or cls.extract_entities(query)

        # 0. Out-of-Scope non-agricultural detection
        out_of_scope_cues = [
            r'\b(crypto|cryptocurrenc(?:y|ies)|bitcoin|ethereum|blockchain|nft|forex trading|stock market|share price)\b',
            r'\b(python|javascript|typescript|c\+\+|java|react|angular|sql|github|docker|api key|write code|coding|binary search|algorithm)\b',
            r'\b(iphone|ipad|macbook|android|smartphones?|mobile phones?|windows update|graphics card|nvidia|laptop repair)\b',
            r'\b(cricket|cricket score|ipl|fifa|world cup|football|messi|ronaldo|virat kohli|rohit sharma)\b',
            r'\b(bollywood|hollywood|movies?|cinemas?|theatres?|theaters?|actor|actress|box office|song lyrics|netflix|celebrity)\b',
            r'\b(capital of france|who is the president of|election result|parliament vote|prime minister of)\b'
        ]
        if any(re.search(pat, norm) for pat in out_of_scope_cues):
            return "OUT_OF_SCOPE"

        # 1. Pests, Diseases, and Crop Protection
        pest_disease_cues = [
            "pest", "pests", "disease", "diseases", "fungus", "fungal", "bacterial", "viral",
            "blight", "rust", "wilt", "rot", "caterpillar", "bollworm", "whitefly", "aphid",
            "leaf curl", "yellowing", "yellow leaf", "yellow leaves", "spots", "neem oil",
            "spray", "pesticide", "fungicide", "insecticide", "control measure", "infestation",
            "పురుగు", "తెగులు", "నివారణ", "పురుగుల మందు", "రోగం", "कीट", "रोग", "इल्ली", "छिड़काव"
        ]
        if any(re.search(r'\b' + re.escape(cue) + r'\b', norm) for cue in pest_disease_cues):
            return "PEST_DISEASE"

        # 2. Fertilizers, Nutrients, and Soil Fertility
        fertilizer_cues = [
            "fertilizer", "fertilizers", "manure", "npk", "nitrogen", "phosphorus", "potash",
            "potassium", "urea", "dap", "zinc", "boron", "sulfur", "sulphur", "micronutrient", "micronutrients",
            "compost", "vermicompost", "dosage", "deficiency", "fertilizer dose", "per hectare",
            "ఎరువులు", "ఎరువుల", "ఎరువు", "యూరియా", "డిఎపి", "సేంద్రీయ ఎరువు", "ఖరీదైన ఎరువు", "उर्वरक", "खाद", "यूरिया", "डीएपी"
        ]
        if any(re.search(r'\b' + re.escape(cue) + r'\b', norm) for cue in fertilizer_cues):
            return "FERTILIZER_NUTRIENT"

        # 3. Government Schemes, Subsidies & Insurance
        scheme_cues = [
            "pm-kisan", "pm kisan", "pmfby", "crop insurance", "insurance", "subsidy", "subsidies",
            "rythu bandhu", "rythu bharosa", "kcc", "kisan credit card", "government scheme",
            "subsidy eligibility", "insurance claim", "పథకం", "సబ్సిడీ", "భీమా", "రైతు భరోసా", "రైతు బంధు",
            "योजना", "सब्सिडी", "बीमा", "किसान क्रेडिट कार्ड"
        ]
        if any(cue in norm for cue in scheme_cues):
            return "GOVERNMENT_SCHEME"

        # 4. Sowing Windows & Crop Duration
        calendar_cues = [
            "sowing time", "sowing date", "when to sow", "when to plant", "planting date",
            "planting time", "maturity period", "crop duration", "how many days to harvest",
            "harvest days", "విత్తే సమయం", "విత్తే", "కాలపరిమితి", "బువాయి కా సమయ్", "బువాయి", "बुवाई का समय", "बुवाई", "बोने", "अवधि"
        ]
        if any(cue in norm for cue in calendar_cues):
            return "SOWING_CALENDAR"

        # 5. Crop Rotation & Intercropping
        rotation_cues = [
            "crop rotation", "intercrop", "intercropping", "after paddy", "rotate with",
            "companion crop", "green manure", "పంట మార్పిడి", "అంతర పంట", "फसल चक्र", "मिश्रित खेती"
        ]
        if any(cue in norm for cue in rotation_cues):
            return "CROP_ROTATION"

        # 6. Harvest & Post-Harvest Storage
        harvest_cues = [
            "harvesting", "harvest time", "threshing", "storage moisture", "grain storage",
            "cold storage", "warehouse", "post harvest", "కోత కోయడం", "ధాన్యం నిల్వ", "कटाई", "भंडारण"
        ]
        if any(cue in norm for cue in harvest_cues):
            return "POST_HARVEST"

        # 7. Weather / Market
        if any(w in norm for w in ["weather", "forecast", "rain today", "temperature today", "వాతావరణం", "मौसम", "mandi price", "market price", "ధర", "भाव"]):
            if "which crop" not in norm and "recommend" not in norm:
                return "MARKET_WEATHER"

        # 8. Explanation / Why
        if any(norm.startswith(w) for w in ["why", "why so", "explain why", "ఎందుకు", "కారణం", "क्यों", "स्पष्ट करें"]):
            return "EXPLANATION"

        # 9. Crop Comparison
        if any(w in norm for w in ["compare", "difference between", "versus", "vs", "పోల్చండి", "तुलना"]):
            return "CROP_COMPARISON"

        # 10. Regional Query without "my farm" (e.g. "What crops suit Kashmir?", "crops grown in Kenya")
        if ext.get("has_explicit_location") and not ext.get("is_my_farm_query"):
            if any(w in norm for w in ["suit", "suitable", "grow", "grown", "crops", "plant", "farming in", "agriculture in"]):
                return "REGIONAL_QUERY"

        # 11. Crop-Specific Fact (Strict: requires known crop AND a physiological attribute)
        crop_fact_cues = [
            "ideal soil ph", "soil ph for", "ph for", "ph of", "water requirement", "water requirements",
            "how much water does", "seed rate", "spacing for", "spacing between", "temperature for",
            "how deep do", "root depth", "germination temperature", "soil requirement", "water depth",
            "temperature range", "optimal temperature", "temperature", "transplanting", "depth", "growth"
        ]
        if ext.get("crop_mentions") and not ext.get("is_my_farm_query"):
            if any(cue in norm for cue in crop_fact_cues) or any(w in norm for w in ["what", "how", "optimal", "required", "growth"]):
                if not any(rec in norm for rec in ["which crop should", "what crop should", "recommend a crop", "best crop"]):
                    return "CROP_FACT"

        # 12. General Agricultural Knowledge (e.g. "characteristics of black soil", "what is alluvial soil")
        general_science_cues = [
            "characteristics of", "properties of", "what is black soil", "what is red soil", "what is alluvial",
            "types of soil", "how does drip irrigation", "what is vermicompost", "soil texture",
            "soil structure", "organic farming principles"
        ]
        if any(cue in norm for cue in general_science_cues):
            return "GENERAL_KNOWLEDGE"

        # 13. Farm Recommendation
        rec_triggers = [
            "which crop should", "which crops should", "what crop should", "what crops should",
            "which crop to grow", "what crop to grow", "recommend a crop", "recommend crop",
            "best crop for my farm", "best crop to grow", "crop recommendation", "suitable for my farm",
            "crops suit my farm", "which crop is suitable", "what crops to plant", "suggest a crop",
            "for my farm", "నా పొలం", "ఏ పంట వేయాలి", "कौन सी फसल", "मेरे खेत के लिए"
        ]
        if any(t in norm for t in rec_triggers) or ext.get("is_my_farm_query"):
            return "FARM_RECOMMENDATION"

        return "OTHER"

    @classmethod
    def classify_and_extract(cls, query: str) -> Tuple[str, Dict[str, Any]]:
        """Convenience method returning (category, extracted_entities)."""
        entities = cls.extract_entities(query)
        cat = cls.classify_question_category(query, entities)
        return cat, entities

    @classmethod
    def is_info_statement(cls, query: str) -> bool:
        """
        Determines whether user input is an informational statement updating farm facts
        rather than an explicit question or advisory request.
        """
        if not query:
            return False

        if "?" in query:
            return False

        q_lower = cls.normalize_query(query).lower().strip()

        interrogatives = [
            "what", "which", "how", "why", "where", "when", "can i", "could", "would", "should",
            "is it", "is this", "is my", "is there", "do i", "does it", "give me", "tell me",
            "recommend", "suggest", "compare", "analyze", "explain", "help", "grow", "plant",
            "suitable", "best", "consider", "which crop", "what crop",
            "ఏ", "ఏమి", "ఎందుకు", "ఎంత", "ఎలా", "ఎక్కడ", "చెప్పండి", "ఇవ్వండి", "సిఫార్సు", "అనుకూలం",
            "क्या", "कौन", "कैसे", "क्यों", "कहाँ", "कितना", "बताएं", "बताओ", "सुझाएं", "सिफारिश", "उपयुक्त"
        ]

        for word in interrogatives:
            if re.search(r'\b' + re.escape(word) + r'\b', q_lower, flags=re.IGNORECASE):
                return False

        declarative_triggers = [
            "my soil", "soil is", "i have", "my farm", "my location", "my district",
            "నా నేల", "నా వద్ద", "నా పొలం", "మేరా खेत", "मेरे पास"
        ]
        if any(trig in q_lower for trig in declarative_triggers):
            return True

        entities = cls.extract_entities(query)
        if any([entities.get("soil_type"), entities.get("water_availability"), entities.get("farm_size_acres"), entities.get("irrigation_type")]):
            return True

        return False

    @staticmethod
    def _log_intent_debug(query: str, detected_intent: str, matched_rule: str, explicit_negative: bool, references_previous_result: bool):
        debug_msg = (
            f"\n[INTENT DEBUG]\n"
            f"query={query}\n"
            f"detected_intent={detected_intent}\n"
            f"matched_rule={matched_rule}\n"
            f"explicit_negative={explicit_negative}\n"
            f"references_previous_result={references_previous_result}\n"
        )
        logger.info(debug_msg)

    @classmethod
    def detect_intent(cls, query: str, has_prior_recommendation: bool = False, last_intent: str = "", last_crops: List[str] = None) -> str:
        """
        Multi-stage intent detection with strict priority hierarchy:
        Priority 1: Explicit farm context/profile queries (farm_context_query)
        Priority 2: Existing recommendation explanation queries (crop_explanation / recommendation_explanation)
        Priority 3: Explicit negative recommendation instructions
        Priority 4: Actual crop recommendation queries (phrase-aware, no standalone 'recommend')
        Priority 5: Seasonal advice
        Priority 6: General agriculture / fallback
        """
        norm = cls.normalize_query(query)
        q_lower = norm.lower().strip()

        explicit_negative = any(
            neg in q_lower for neg in [
                "do not recommend", "don't recommend", "dont recommend",
                "do not give a new recommendation", "don't give a recommendation",
                "no new recommendation", "don't suggest a crop", "do not suggest",
                "do not recommend a crop"
            ]
        )
        references_previous_result = any(
            ref in q_lower for ref in [
                "previous recommendation", "existing recommendation", "selected",
                "why was", "why did", "why this crop", "instead of", "previous result"
            ]
        )

        # -------------------------------------------------------------
        # PRIORITY 1: EXPLICIT FARM CONTEXT / PROFILE QUERIES
        # -------------------------------------------------------------
        farm_context_triggers = [
            "exact factors", "farm profile", "stored for my farm", "currently stored",
            "values are currently stored", "what soil and irrigation", "list my current farm profile",
            "what values are being used", "what location, soil, irrigation", "what factors from my current farm profile",
            "tell me the current farm factors", "current farm factors", "farm-profile", "farm profile factors",
            "values currently stored", "factors are currently stored", "factors are being used",
            "factors from my current farm profile are being used", "stored for my farm",
            "current farm-profile and weather values"
        ]
        if any(trig in q_lower for trig in farm_context_triggers) and not any(exp in q_lower for exp in ["why was", "why did", "explain why"]):
            matched_rule = "farm_context_query_explicit"
            detected_intent = "farm_context_query"
            cls._log_intent_debug(query, detected_intent, matched_rule, explicit_negative, references_previous_result)
            return detected_intent

        # -------------------------------------------------------------
        # PRIORITY 2: EXISTING RECOMMENDATION EXPLANATION QUERIES
        # -------------------------------------------------------------
        explanation_phrases = [
            "why was", "why did you select", "why did the system select", "why did you choose",
            "why did you recommend", "why recommend", "explain why", "explain why the system selected",
            "explain why maize", "explain why cotton", "explain why arhar", "explain the previous recommendation",
            "explain the existing recommendation", "what factors caused the existing recommendation",
            "what factors caused", "show me the factors", "why this crop", "instead of",
            "explain why the system", "explain the choice"
        ]
        if any(trig in q_lower for trig in explanation_phrases):
            matched_rule = "recommendation_explanation_query"
            detected_intent = "crop_explanation"
            cls._log_intent_debug(query, detected_intent, matched_rule, explicit_negative, references_previous_result)
            return detected_intent

        # -------------------------------------------------------------
        # PRIORITY 3: EXPLICIT NEGATIVE RECOMMENDATION INSTRUCTIONS
        # -------------------------------------------------------------
        if explicit_negative:
            if "factor" in q_lower or "value" in q_lower or "profile" in q_lower or "detail" in q_lower or "stored" in q_lower:
                matched_rule = "explicit_negative_with_context_request"
                detected_intent = "farm_context_query"
            elif "explain" in q_lower or "why" in q_lower:
                matched_rule = "explicit_negative_with_explanation_request"
                detected_intent = "crop_explanation"
            else:
                matched_rule = "explicit_negative_default"
                detected_intent = "farm_context_query"
            
            cls._log_intent_debug(query, detected_intent, matched_rule, explicit_negative, references_previous_result)
            return detected_intent

        # -------------------------------------------------------------
        # INFO STATEMENT CHECK
        # -------------------------------------------------------------
        if cls.is_info_statement(query):
            matched_rule = "info_statement"
            detected_intent = "info_statement"
            cls._log_intent_debug(query, detected_intent, matched_rule, explicit_negative, references_previous_result)
            return detected_intent

        # -------------------------------------------------------------
        # EXACT YIELD & DEFINITIONS
        # -------------------------------------------------------------
        yield_triggers = [
            "exact yield", "yield i will get", "how much yield", "what will be my yield",
            "yield from my", "yield from 5 acre", "yield of crop",
            "దిగుబడి ఎంత వస్తుంది", "దిగుబడి ఎంత", "ఖచ్చితమైన దిగుబడి", "సరాసరి దిగుబడి",
            "सटीक उपज", "कितनी उपज होगी", "कितनी पैदावार होगी", "उपज कितनी मिलेगी"
        ]
        if any(trig in q_lower or trig in query for trig in yield_triggers):
            matched_rule = "exact_yield"
            detected_intent = "exact_yield"
            cls._log_intent_debug(query, detected_intent, matched_rule, explicit_negative, references_previous_result)
            return detected_intent

        definition_triggers = [
            "what is drip irrigation", "what is drip", "what is black soil", "what is red soil",
            "what is crop rotation", "what is soil ph", "what is ph",
            "డ్రిప్ ఇరిగేషన్ అంటే ఏమిటి", "డ్రిప్ అంటే ఏమిటి", "నల్ల నేల అంటే ఏమిటి",
            "పంట మార్పిడి అంటే ఏమిటి", "నేల ph అంటే ఏమిటి",
            "ड्रिप सिंचाई क्या है", "काली मिट्टी क्या है", "फसल चक्र क्या है", "मृदा पीएच क्या है", "पीएच क्या है"
        ]
        if any(trig in q_lower or trig in query for trig in definition_triggers):
            matched_rule = "generic_agri_definition"
            detected_intent = "generic_agri_definition"
            cls._log_intent_debug(query, detected_intent, matched_rule, explicit_negative, references_previous_result)
            return detected_intent

        # -------------------------------------------------------------
        # STAGE 2: CONTEXTUAL SHORT FOLLOW-UPS
        # -------------------------------------------------------------
        why_triggers = [
            "why", "why?", "why so", "why so?", "and why", "and why?", "how so?", "how so",
            "tell me more", "explain", "explain.", "explain?", "what does that mean", "what does that mean?",
            "why arhar", "why pigeon pea", "why cotton", "why is this suitable", "what made you choose this",
            "how did you decide", "కారణం?", "కారణం", "కారణాలు", "ఎందుకు?", "ఎందుకు",
            "ఎందుకు సిఫార్సు చేశారు", "కారణాలు ఏమిటి", "వివరించండి", "ఎందుకు ఈ పంట?",
            "क्यों?", "क्यों", "कारण बताएं", "क्यों सिफारिश की", "यह फसल क्यों?"
        ]
        if q_lower in why_triggers or (has_prior_recommendation and any(q_lower.startswith(w) for w in ["why", "ఎందుకు", "क्यों"])):
            matched_rule = "short_why_followup"
            detected_intent = "crop_explanation"
            cls._log_intent_debug(query, detected_intent, matched_rule, explicit_negative, references_previous_result)
            return detected_intent

        water_triggers = [
            "what about water", "what about water?", "what about water requirement", "what about water requirements",
            "what about irrigation", "what about irrigation?", "water requirement", "water requirements",
            "water requirements?", "water demand", "how much water", "how much water?", "water?", "water",
            "water requirement entha", "water requirement entha?", "నీరు?", "నీటి గురించి?", "నీటి అవసరం?",
            "నీటి అవసరం ఎంత?", "నీటి అవసరం ఎంత", "నీటిపారుదల?", "నీరు ఎంత కావాలి?",
            "पानी के बारे में?", "पानी?", "पानी की कितनी जरूरत है?", "पानी की कितनी जरूरत है",
            "पानी की आवश्यकता?", "सिंचाई की जरूरत?"
        ]
        if q_lower in water_triggers or (has_prior_recommendation and any(w in q_lower for w in ["water requirement", "నీటి అవసరం", "पानी की जरूरत"])):
            matched_rule = "water_followup"
            detected_intent = "irrigation"
            cls._log_intent_debug(query, detected_intent, matched_rule, explicit_negative, references_previous_result)
            return detected_intent

        rainfall_triggers = [
            "what about rainfall", "what about rainfall?", "what about rain", "rainfall?", "rain?",
            "వర్షపాతం?", "వర్షపాతం ఎంత?", "వర్షం ఎంత?", "बारिश कितनी चाहिए?", "वर्षा कितनी?"
        ]
        if q_lower in rainfall_triggers:
            matched_rule = "rainfall_followup"
            detected_intent = "rainfall_for_previous_crop"
            cls._log_intent_debug(query, detected_intent, matched_rule, explicit_negative, references_previous_result)
            return detected_intent

        translation_triggers = [
            "explain that in telugu", "explain in telugu", "in telugu", "tell in telugu",
            "తెలుగులో చెప్పండి", "తెలుగులో వివరించండి",
            "explain that in hindi", "explain in hindi", "in hindi", "हिंदी में बताएं", "हिंदी में समझाइए"
        ]
        if any(trig in q_lower or trig in query for trig in translation_triggers):
            matched_rule = "translation_followup"
            detected_intent = "translation_followup"
            cls._log_intent_debug(query, detected_intent, matched_rule, explicit_negative, references_previous_result)
            return detected_intent

        which_more_water = [
            "which needs more water", "which crop needs more water", "which requires more water",
            "దేనికి ఎక్కువ నీరు కావాలి", "దేనికి నీరు ఎక్కువ", "किसमें ज्यादा पानी चाहिए"
        ]
        if any(trig in q_lower or trig in query for trig in which_more_water):
            matched_rule = "water_comparison"
            detected_intent = "water_comparison_for_previous"
            cls._log_intent_debug(query, detected_intent, matched_rule, explicit_negative, references_previous_result)
            return detected_intent

        # -------------------------------------------------------------
        # PRIORITY 3.5: ECONOMIC CROP RECOMMENDATION QUERIES
        # -------------------------------------------------------------
        economic_triggers = [
            "most profitable", "highest profit", "highest estimated return", "highest return",
            "best return", "profitable crop", "crop with highest profit", "crop with highest estimated profit",
            "highest estimated profit", "highest profit this season", "which crop is most profitable",
            "most profitable crop", "highest return crop", "highest margin crop",
            "అత్యధిక లాభం", "ఎక్కువ లాభం ఇచే పంట", "లాభదాయకమైన పంట", "లాభం వచ్చే పంట",
            "सबसे लाभदायक", "सबसे ज्यादा मुनाफा", "अधिकतम लाभ", "मुनाफे वाली फसल"
        ]
        if any(trig in q_lower for trig in economic_triggers) and not any(comp in q_lower for comp in ["compare", "versus", "vs", "difference between", "పోల్చండి", "तुलना"]):
            matched_rule = "economic_recommendation_phrase"
            detected_intent = "economic_recommendation"
            cls._log_intent_debug(query, detected_intent, matched_rule, explicit_negative, references_previous_result)
            return detected_intent

        # -------------------------------------------------------------
        # PRIORITY 4: ACTUAL CROP RECOMMENDATION QUERIES
        # -------------------------------------------------------------
        phrase_recommend_triggers = [
            "which crop should i consider", "which crops should i consider", "what crop should i consider", "what crops should i consider",
            "which crop should i grow", "which crops should i grow", "what crop should i grow", "what crops should i grow",
            "which crop should i plant", "which crops should i plant", "what crop should i plant", "what crops should i plant",
            "best crop for my farm", "best crops for my farm", "what is the best crop", "best crop to grow",
            "recommend a crop", "recommend crops", "recommend suitable crops", "recommend a suitable crop",
            "crop recommendation for my farm", "which crops are suitable", "crops suitable for my farm",
            "crops to consider", "what crops to consider", "which crops to grow", "which crops to plant",
            "suitable for my farm", "suggest a crop", "suggest crops",
            "em crop", "em crops", "which crock is suitable", "crock is suitable",
            "what crops are suitable for me", "what crops are suitable",
            "ఏ పంటలు అనుకూలంగా ఉంటాయి", "ఏ పంట వేయాలి", "పంట సిఫార్సు", "పంటల ఎంపిక", "ఏ పంట", "ఏమి పంట",
            "कौन सी फसल", "क्या उगाएं", "फसल सिफारिश", "कौन सी फसल उपयुक्त", "फसल सुझाव", "फसल उपयुक्त",
            "खरीफ में मेरे खेत के लिए कौन सी फसल उपयुक्त है", "कौन सी फसल उपयुक्त है"
        ]
        
        is_rec_phrase = any(trig in q_lower for trig in phrase_recommend_triggers)
        if not is_rec_phrase:
            if any(p in q_lower for p in ["which crop", "what crop", "which kharif crop", "which rabi crop"]):
                if not any(ex in q_lower for ex in ["factor", "profile", "why", "value", "stored", "used", "explain", "because"]):
                    is_rec_phrase = True
            elif "recommend crop" in q_lower or "recommend a crop" in q_lower or "crop recommendation" in q_lower:
                if not any(ex in q_lower for ex in ["factor", "profile", "why", "value", "stored", "used", "explain", "because"]):
                    is_rec_phrase = True

        if is_rec_phrase:
            matched_rule = "actual_crop_recommendation_phrase"
            detected_intent = "crop_recommendation"
            cls._log_intent_debug(query, detected_intent, matched_rule, explicit_negative, references_previous_result)
            return detected_intent

        # -------------------------------------------------------------
        # PRIORITY 5: SEASONAL ADVICE
        # -------------------------------------------------------------
        seasonal_triggers = [
            "what to plant in kharif", "what to grow in rabi", "season crops", "kharif crops",
            "ఖరీఫ్ పంటలు", "రబీ పంటలు", "खरीफ की फसलें", "रबी की फसलें"
        ]
        if any(trig in q_lower for trig in seasonal_triggers) and "my farm" not in q_lower and "should i consider" not in q_lower and "which" not in q_lower:
            matched_rule = "seasonal_advice"
            detected_intent = "seasonal_advice"
            cls._log_intent_debug(query, detected_intent, matched_rule, explicit_negative, references_previous_result)
            return detected_intent

        # -------------------------------------------------------------
        # PRIORITY 6: OTHER LITERAL INTENTS / GENERAL AGRICULTURE
        # -------------------------------------------------------------
        comparison_triggers = [
            "compare", "comparison", "difference between", "versus", "vs", "compare it with",
            "compare with", "compare this with", "how does it compare",
            "పోల్చండి", "పోలిక", "తులనాత్మక", "తुलना करें", "तुलना", "अंतर बताएं"
        ]
        if any(trig in q_lower or trig in query for trig in comparison_triggers):
            matched_rule = "crop_comparison"
            detected_intent = "crop_comparison"
            cls._log_intent_debug(query, detected_intent, matched_rule, explicit_negative, references_previous_result)
            return detected_intent

        weather_triggers = [
            "weather in", "forecast in", "rainfall in", "temperature in", "rain today", "weather today",
            "what is the weather", "current weather", "what is the current weather",
            "వాతావరణం", "వర్షపాతం", "ఎండ", "मौसम", "वर्षा", "तापमान"
        ]
        if any(trig in q_lower or trig in query for trig in weather_triggers) and "which crop" not in q_lower:
            matched_rule = "weather"
            detected_intent = "weather"
            cls._log_intent_debug(query, detected_intent, matched_rule, explicit_negative, references_previous_result)
            return detected_intent

        disease_triggers = [
            "turning yellow", "yellow leaves", "leaves turning yellow", "leaf yellowing",
            "pest", "disease", "insect", "fungal", "blast", "blight", "spots on leaves", "worms",
            "పురుగు", "తెగులు", "ఆకు పసుపు", "ఆకులు పసుపు", "కీటకాలు", "రోగం",
            "कीट", "रोग", "पत्ते पीले", "पत्तियां पीली", "कीटनाशक"
        ]
        if any(trig in q_lower or trig in query for trig in disease_triggers):
            matched_rule = "disease_help"
            detected_intent = "disease_help"
            cls._log_intent_debug(query, detected_intent, matched_rule, explicit_negative, references_previous_result)
            return detected_intent

        fertilizer_triggers = [
            "fertilizer dosage", "fertiliser dosage", "exact fertilizer", "npk dosage", "how much urea",
            "dap dose", "fertilizer dose", "fertilizer", "fertiliser",
            "ఎరువుల మోతాదు", "ఎరువులు", "రసాయన ఎరువులు",
            "उर्वरक मात्रा", "खाद की मात्रा", "यूरिया"
        ]
        if any(trig in q_lower or trig in query for trig in fertilizer_triggers) and "which crop" not in q_lower:
            matched_rule = "fertilizer"
            detected_intent = "fertilizer"
            cls._log_intent_debug(query, detected_intent, matched_rule, explicit_negative, references_previous_result)
            return detected_intent

        soil_info_triggers = [
            "characteristics of black soil", "characteristics of red soil", "characteristics of alluvial",
            "properties of black soil", "about black soil", "what is black soil", "what is red soil",
            "main characteristics of black soil", "useful for agriculture",
            "నల్ల నేల లక్షణాలు", "నల్లరేగడి లక్షణాలు", "ఎర్ర నేల లక్షణాలు", "కాళీ మిట్టి గుణాలు",
            "काली मिट्टी की विशेषताएं", "काली मिट्टी के गुण", "लाल मिट्टी की विशेषताएं"
        ]
        if any(trig in q_lower or trig in query for trig in soil_info_triggers):
            matched_rule = "soil_information"
            detected_intent = "soil_information"
            cls._log_intent_debug(query, detected_intent, matched_rule, explicit_negative, references_previous_result)
            return detected_intent

        soil_analysis_triggers = [
            "my soil ph", "is that suitable for soil", "analyze my soil", "soil health", "soil test",
            "నేల పరీక్ష", "మట్టి ph", "నేల ph", "మృదా పరీక్ష", "मिट्टी की जांच", "मिट्टी का ph"
        ]
        if any(trig in q_lower or trig in query for trig in soil_analysis_triggers) and "which crop" not in q_lower:
            matched_rule = "soil_analysis"
            detected_intent = "soil_analysis"
            cls._log_intent_debug(query, detected_intent, matched_rule, explicit_negative, references_previous_result)
            return detected_intent

        location_triggers = [
            "agricultural conditions in", "agricultural conditions are common in", "conditions in",
            "conditions are common in", "farming in", "agriculture in", "crops grown in",
            "వ్యవసాయ పరిస్థితులు", "వ్యవసాయం ఎలా ఉంటుంది", "పరిస్థితులు", "కూర్నూలు వ్యవసాయం",
            "कृषि परिस्थितियां", "खेती कैसी होती है", "कुरनूल में खेती"
        ]
        if any(trig in q_lower or trig in query for trig in location_triggers) and "which crop" not in q_lower:
            matched_rule = "location_agriculture"
            detected_intent = "location_agriculture"
            cls._log_intent_debug(query, detected_intent, matched_rule, explicit_negative, references_previous_result)
            return detected_intent

        matched_rule = "general_agriculture_default"
        detected_intent = "general_agriculture"
        cls._log_intent_debug(query, detected_intent, matched_rule, explicit_negative, references_previous_result)
        return detected_intent


# Singleton instance
intent_service = IntentService()



# Singleton instance
intent_service = IntentService()
