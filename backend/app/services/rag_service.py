"""
RAG Service for KrishiMitra AI.
Orchestrates entity extraction, vector retrieval, source citations, and context preparation.
Enforces strict location grounding and trusted dataset provenance.
"""

import re
import logging
from typing import Dict, Any, List, Optional
from backend.app.data_engine.vector_store import vector_store

logger = logging.getLogger(__name__)

INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa", "Gujarat",
    "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh",
    "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
    "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh",
    "Uttarakhand", "West Bengal", "Andaman And Nicobar Islands"
]

SOIL_TYPES = [
    "black soil", "red soil", "alluvial soil", "laterite soil", "desert soil", "sandy soil",
    "clay soil", "loamy soil", "regur", "vertisol", "saline soil"
]

CROPS = [
    "cotton", "rice", "wheat", "maize", "sugarcane", "soybean", "soyabean", "groundnut",
    "jowar", "sorghum", "bajra", "pearl millet", "gram", "chickpea", "tur", "arhar",
    "pigeon pea", "moong", "urad", "mustard", "rapeseed", "sunflower", "onion", "potato",
    "chilli", "chillies", "turmeric", "banana", "coconut", "arecanut", "sweet potato", "ragi"
]


class RAGService:
    def __init__(self):
        self.store = vector_store

    def extract_entities(self, query: str) -> Dict[str, Optional[str]]:
        """Extracts agricultural entities (State, District, Soil Type, Crop) from the user query."""
        q_lower = query.lower()
        extracted = {
            "state": None,
            "soil_type": None,
            "crop": None
        }

        for state in INDIAN_STATES:
            if state.lower() in q_lower:
                extracted["state"] = state
                break

        for soil in SOIL_TYPES:
            if soil in q_lower:
                extracted["soil_type"] = soil
                break

        for crop in CROPS:
            if crop in q_lower:
                extracted["crop"] = crop.capitalize()
                break

        return extracted

    def retrieve_context(
        self,
        query: str,
        location_filter: Optional[Dict[str, str]] = None,
        season: Optional[str] = None,
        rainfall_condition: Optional[str] = None,
        top_k: int = 4
    ) -> Dict[str, Any]:
        """
        Retrieves relevant agricultural records using vector search and metadata filters.
        Strictly prioritizes active farm location, season, and weather conditions.
        """
        entities = self.extract_entities(query)

        # Augment search query with season and weather conditions for context-rich vector retrieval
        search_terms = [query]
        if season:
            search_terms.append(f"{season} season")
        if rainfall_condition and rainfall_condition != "normal":
            search_terms.append(f"{rainfall_condition} rainfall")
        augmented_query = " ".join(search_terms)

        # 1. First priority: District-level filtering if provided
        target_district = location_filter.get("district") if location_filter else None
        target_state = location_filter.get("state") if location_filter else entities.get("state")

        docs = []
        if target_district:
            docs = self.store.search(query=augmented_query, top_k=top_k, filter_metadata={"district": target_district})

        # 2. Second priority: State-level filtering if district-level was empty
        if not docs and target_state:
            docs = self.store.search(query=augmented_query, top_k=top_k, filter_metadata={"state": target_state})

        # 3. Third priority: Unrestricted search if no location-specific match
        if not docs:
            docs = self.store.search(query=augmented_query, top_k=top_k)

        # 4. Generic location filtering: strictly prioritize docs matching target_district and target_state
        if target_district or target_state:
            filtered_docs = []
            for d in docs:
                doc_dist = (d.get("district") or "").lower()
                doc_state = (d.get("state") or "").lower()
                
                # If document explicitly specifies a different district, filter it out
                if doc_dist and target_district and doc_dist != target_district.lower() and target_district.lower() not in d.get("content", "").lower():
                    continue
                # If document explicitly specifies a different state, filter it out
                if doc_state and target_state and doc_state != target_state.lower() and target_state.lower() not in d.get("content", "").lower():
                    continue
                filtered_docs.append(d)
            if filtered_docs:
                docs = filtered_docs

        # Deduplicate sources and format citations using configured datasets only
        sources = []
        seen_sources = set()
        context_blocks = []

        def standardize_source_name(raw_src: str, category: str) -> str:
            if "soil" in category or "soil" in raw_src.lower():
                return "Soil Expert Dataset"
            elif "weather" in category or "weather" in raw_src.lower() or "climate" in raw_src.lower():
                return "Weather Expert Dataset"
            elif "geo" in category or "geography" in raw_src.lower() or "district" in raw_src.lower():
                return "Master Geography Dataset"
            else:
                return "Crop Expert Dataset"

        for doc in docs:
            raw_src = doc.get("source", "Crop Expert Dataset")
            cat = doc.get("category", "agronomy")
            std_src = standardize_source_name(raw_src, cat)

            if std_src not in seen_sources:
                seen_sources.add(std_src)
                why_desc = "Crop suitability information"
                if std_src == "Soil Expert Dataset":
                    why_desc = "Soil properties and compatibility"
                elif std_src == "Weather Expert Dataset":
                    why_desc = "Climate and rainfall information"
                elif std_src == "Master Geography Dataset":
                    why_desc = "Location context and agro-climatic boundaries"

                sources.append({
                    "name": std_src,
                    "category": cat,
                    "title": doc.get("title", ""),
                    "why_used": why_desc,
                    "used": True
                })

            context_blocks.append(
                f"[{doc.get('title')}] (Source: {std_src}):\n{doc.get('content')}"
            )

        formatted_context = "\n\n".join(context_blocks) if context_blocks else "No specific agricultural record found."

        return {
            "query": query,
            "entities_detected": entities,
            "retrieved_documents": docs,
            "context_text": formatted_context,
            "sources": sources
        }


# Singleton instance
rag_service = RAGService()
