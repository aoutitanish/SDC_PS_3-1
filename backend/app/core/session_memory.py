"""
Conversational State & Session Memory Manager for KrishiMitra AI.
Maintains structured multi-turn conversation memory, dynamic farm context, and previous consultation states.
Implements Phase 2 Context Precedence:
1. Explicit facts in current message.
2. Explicit facts earlier in current conversation (not superseded).
3. Saved My Farm profile (only when relevant and question needs farm context).
4. General agricultural knowledge supported by retrieved evidence.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger(__name__)


@dataclass
class PendingFollowUp:
    original_query: str
    target_field: str  # 'district', 'soil_type', 'farm_size_acres', 'irrigation_type', 'season'
    consultation_id: str
    accumulated_facts: Dict[str, Any] = field(default_factory=dict)
    prompt_question: str = ""
    quick_replies: List[str] = field(default_factory=list)


class ConversationState:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.consultation_id = session_id
        self.pending_follow_up: Optional[PendingFollowUp] = None
        
        # Phase 2 & 4 distinct context layers
        self.primary_saved_farm: Optional[Dict[str, Any]] = None
        self.conversation_farm_context: Dict[str, Any] = {}
        self.current_message_location: Optional[Dict[str, str]] = None
        self.unresolved_attributes: List[str] = []
        
        # Core farm attributes for backward compatibility
        self.farm_size_acres: Optional[float] = None
        self.state: Optional[str] = None
        self.district: Optional[str] = None
        self.soil_type: Optional[str] = None
        self.irrigation_type: Optional[str] = None
        self.water_source: Optional[str] = None
        self.water_availability: Optional[str] = None
        self.season: Optional[str] = None
        self.rainfall_condition: Optional[str] = None
        self.temperature_condition: Optional[str] = None
        self.ph: Optional[float] = None
        self.has_borewell: Optional[bool] = None
        self.has_drip: Optional[bool] = None
        self.language: str = "en"
        
        # Historical memory
        self.last_intent: Optional[str] = None
        self.last_query: Optional[str] = None
        self.last_topic: Optional[str] = None
        self.last_recommendation_result: Optional[Dict[str, Any]] = None
        self.last_recommended_crops: List[str] = []
        self.conversation_turn_count: int = 0

    @property
    def farm_area(self) -> Optional[float]:
        return self.farm_size_acres

    @farm_area.setter
    def farm_area(self, val: Optional[float]):
        self.farm_size_acres = val

    def resolve_context(
        self,
        extracted_facts: Dict[str, Any],
        req_farm_profile: Any = None,
        req_location: Any = None,
        req_soil_type: Optional[str] = None,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Resolves agricultural context according to strict Phase 2 precedence rules:
        1. EXPLICIT FACTS FROM CURRENT USER MESSAGE (Highest)
        2. EXPLICIT FACTS EARLIER IN CURRENT CONVERSATION (When not superseded)
        3. SAVED MY FARM PROFILE (Only when question needs farm-specific context and profile is relevant)
        4. GENERAL AGRICULTURAL KNOWLEDGE (Lowest)
        """
        # Save snapshot of previous session state before resolution
        prev_memory = {
            "state": self.state,
            "district": self.district,
            "soil_type": self.soil_type,
            "water_availability": self.water_availability,
            "irrigation_type": self.irrigation_type,
            "water_source": self.water_source,
            "farm_size_acres": self.farm_size_acres,
            "season": self.season,
            "rainfall_condition": self.rainfall_condition,
            "temperature_condition": self.temperature_condition,
            "ph": self.ph,
            "has_borewell": self.has_borewell,
            "has_drip": self.has_drip
        }

        # 0. Sync primary saved farm profile if provided in request
        if req_farm_profile or req_location:
            p_state = req_location.state if (req_location and req_location.state) else (req_farm_profile.state if req_farm_profile else None)
            p_dist = req_location.district if (req_location and req_location.district) else (req_farm_profile.district if req_farm_profile else None)
            p_soil = req_soil_type or (req_farm_profile.soil_type if req_farm_profile else None)
            p_size = req_farm_profile.farm_size_acres if req_farm_profile else None
            p_irrig = req_farm_profile.irrigation_type if req_farm_profile else None
            p_water_src = req_farm_profile.water_source if req_farm_profile else None
            p_season = req_farm_profile.season if req_farm_profile else None
            
            # Save or keep primary saved farm
            if not self.primary_saved_farm:
                self.primary_saved_farm = {}
            if p_state: self.primary_saved_farm["state"] = p_state
            if p_dist: self.primary_saved_farm["district"] = p_dist
            if p_soil: self.primary_saved_farm["soil_type"] = p_soil
            if p_size: self.primary_saved_farm["farm_size_acres"] = p_size
            if p_irrig: self.primary_saved_farm["irrigation_type"] = p_irrig
            if p_water_src: self.primary_saved_farm["water_source"] = p_water_src
            if p_season: self.primary_saved_farm["season"] = p_season

        # 1. Explicit Current Message Facts
        cur_state = extracted_facts.get("state")
        cur_district = extracted_facts.get("district")
        cur_soil = extracted_facts.get("soil_type")
        cur_water_avail = extracted_facts.get("water_availability")
        cur_irrigation = extracted_facts.get("irrigation_type")
        cur_water_src = extracted_facts.get("water_source")
        cur_size = extracted_facts.get("farm_size_acres")
        cur_season = extracted_facts.get("season")
        cur_rain_cond = extracted_facts.get("rainfall_condition")
        cur_temp_cond = extracted_facts.get("temperature_condition")
        cur_ph = extracted_facts.get("ph")
        cur_has_borewell = extracted_facts.get("has_borewell")
        cur_has_drip = extracted_facts.get("has_drip")

        reset_location = extracted_facts.get("reset_location", False)
        is_other_farm = extracted_facts.get("is_other_farm", False)
        has_explicit_location = extracted_facts.get("has_explicit_location", False)

        if has_explicit_location:
            self.current_message_location = {
                "state": cur_state,
                "district": cur_district
            }
        else:
            self.current_message_location = None

        # Handle explicit location reset ("ignore my previous location; this farm is in...")
        if reset_location:
            self.conversation_farm_context.pop("district", None)
            self.conversation_farm_context.pop("state", None)
            self.state = cur_state
            self.district = cur_district
            self.last_recommendation_result = None
            self.last_recommended_crops = []

        # Handle "my other farm is in..." - do NOT overwrite primary saved farm
        if is_other_farm:
            self.conversation_farm_context["is_other_farm"] = True
            if cur_state: self.conversation_farm_context["state"] = cur_state
            if cur_district: self.conversation_farm_context["district"] = cur_district
            if cur_soil: self.conversation_farm_context["soil_type"] = cur_soil
            self.last_recommendation_result = None
            self.last_recommended_crops = []

        # Update conversation_farm_context with any newly mentioned facts
        if cur_state and not is_other_farm: self.conversation_farm_context["state"] = cur_state
        if cur_district and not is_other_farm: self.conversation_farm_context["district"] = cur_district
        if cur_soil: self.conversation_farm_context["soil_type"] = cur_soil
        if cur_water_avail: self.conversation_farm_context["water_availability"] = cur_water_avail
        if cur_irrigation: self.conversation_farm_context["irrigation_type"] = cur_irrigation
        if cur_water_src: self.conversation_farm_context["water_source"] = cur_water_src
        if cur_size: self.conversation_farm_context["farm_size_acres"] = cur_size
        if cur_season: self.conversation_farm_context["season"] = cur_season
        if cur_ph: self.conversation_farm_context["ph"] = cur_ph
        if cur_has_borewell is not None: self.conversation_farm_context["has_borewell"] = cur_has_borewell
        if cur_has_drip is not None: self.conversation_farm_context["has_drip"] = cur_has_drip

        # Determine if this query should receive farm context
        # Pure crop facts and general agronomy knowledge should NOT force user's saved farm location
        is_general_or_crop_fact = category in ["CROP_FACT", "GENERAL_KNOWLEDGE"]
        is_regional_query = category == "REGIONAL_QUERY"
        needs_farm_context = category in ["FARM_RECOMMENDATION", "EXPLANATION", "CROP_COMPARISON"] or extracted_facts.get("is_my_farm_query", False)

        # Resolve location:
        # If explicit location in current message -> use it unconditionally!
        if cur_district or cur_state:
            resolved_state = cur_state
            resolved_district = cur_district
        elif is_general_or_crop_fact:
            # General crop question: do NOT force farm location!
            resolved_state = None
            resolved_district = None
        elif is_regional_query:
            # Regional query without explicit location in current turn: check conversation context
            resolved_state = self.conversation_farm_context.get("state")
            resolved_district = self.conversation_farm_context.get("district")
        else:
            # Farm recommendation or contextual follow-up:
            # Priority: conversation context > primary saved farm
            resolved_state = (
                self.conversation_farm_context.get("state")
                or (self.primary_saved_farm.get("state") if (self.primary_saved_farm and needs_farm_context) else None)
                or self.state
            )
            resolved_district = (
                self.conversation_farm_context.get("district")
                or (self.primary_saved_farm.get("district") if (self.primary_saved_farm and needs_farm_context) else None)
                or self.district
            )

        # Resolve other farm attributes:
        if is_general_or_crop_fact:
            resolved_soil = cur_soil
            resolved_water_avail = cur_water_avail
            resolved_irrigation = cur_irrigation
            resolved_water_src = cur_water_src
            resolved_size = cur_size
            resolved_season = cur_season
            resolved_rain_cond = cur_rain_cond
            resolved_temp_cond = cur_temp_cond
            resolved_ph = cur_ph
            resolved_has_borewell = cur_has_borewell
            resolved_has_drip = cur_has_drip
        else:
            resolved_soil = (
                cur_soil
                or self.conversation_farm_context.get("soil_type")
                or (self.primary_saved_farm.get("soil_type") if (self.primary_saved_farm and needs_farm_context) else None)
                or self.soil_type
            )
            resolved_water_avail = (
                cur_water_avail
                or self.conversation_farm_context.get("water_availability")
                or self.water_availability
            )
            resolved_irrigation = (
                cur_irrigation
                or self.conversation_farm_context.get("irrigation_type")
                or (self.primary_saved_farm.get("irrigation_type") if (self.primary_saved_farm and needs_farm_context) else None)
                or self.irrigation_type
            )
            resolved_water_src = (
                cur_water_src
                or self.conversation_farm_context.get("water_source")
                or (self.primary_saved_farm.get("water_source") if (self.primary_saved_farm and needs_farm_context) else None)
                or self.water_source
            )
            resolved_size = (
                cur_size
                or self.conversation_farm_context.get("farm_size_acres")
                or (self.primary_saved_farm.get("farm_size_acres") if (self.primary_saved_farm and needs_farm_context) else None)
                or self.farm_size_acres
            )
            resolved_season = (
                cur_season
                or self.conversation_farm_context.get("season")
                or (self.primary_saved_farm.get("season") if (self.primary_saved_farm and needs_farm_context) else None)
                or self.season
            )
            resolved_rain_cond = cur_rain_cond or self.rainfall_condition
            resolved_temp_cond = cur_temp_cond or self.temperature_condition
            resolved_ph = cur_ph or self.conversation_farm_context.get("ph") or self.ph
            resolved_has_borewell = (
                cur_has_borewell
                if cur_has_borewell is not None
                else self.conversation_farm_context.get("has_borewell", self.has_borewell)
            )
            resolved_has_drip = (
                cur_has_drip
                if cur_has_drip is not None
                else self.conversation_farm_context.get("has_drip", self.has_drip)
            )

        # Update persistent backward-compatible properties only for farm-context queries
        if not is_general_or_crop_fact:
            if resolved_state is not None: self.state = resolved_state
            if resolved_district is not None: self.district = resolved_district
            if resolved_soil is not None: self.soil_type = resolved_soil
            if resolved_water_avail is not None: self.water_availability = resolved_water_avail
            if resolved_irrigation is not None: self.irrigation_type = resolved_irrigation
            if resolved_water_src is not None: self.water_source = resolved_water_src
            if resolved_size is not None: self.farm_size_acres = resolved_size
            if resolved_season is not None: self.season = resolved_season
            if resolved_rain_cond is not None: self.rainfall_condition = resolved_rain_cond
            if resolved_temp_cond is not None: self.temperature_condition = resolved_temp_cond
            if resolved_ph is not None: self.ph = resolved_ph
            if resolved_has_borewell is not None: self.has_borewell = resolved_has_borewell
            if resolved_has_drip is not None: self.has_drip = resolved_has_drip

        # Calculate unresolved attributes for recommendation
        unresolved: List[str] = []
        if not resolved_district:
            unresolved.append("district")
        if not resolved_soil:
            unresolved.append("soil_type")
        if not resolved_irrigation and not resolved_water_avail:
            unresolved.append("irrigation_type")
        if not resolved_size:
            unresolved.append("farm_size_acres")
        if not resolved_season:
            unresolved.append("season")
        self.unresolved_attributes = unresolved

        resolved_context = {
            "state": None if is_general_or_crop_fact else self.state,
            "district": None if is_general_or_crop_fact else self.district,
            "soil_type": cur_soil if is_general_or_crop_fact else self.soil_type,
            "water_availability": None if is_general_or_crop_fact else self.water_availability,
            "irrigation_type": None if is_general_or_crop_fact else self.irrigation_type,
            "water_source": None if is_general_or_crop_fact else self.water_source,
            "farm_size_acres": None if is_general_or_crop_fact else self.farm_size_acres,
            "season": None if is_general_or_crop_fact else self.season,
            "rainfall_condition": None if is_general_or_crop_fact else self.rainfall_condition,
            "temperature_condition": None if is_general_or_crop_fact else self.temperature_condition,
            "ph": cur_ph if is_general_or_crop_fact else self.ph,
            "has_borewell": None if is_general_or_crop_fact else self.has_borewell,
            "has_drip": None if is_general_or_crop_fact else self.has_drip,
            "unresolved_attributes": self.unresolved_attributes,
            "is_general_or_crop_fact": is_general_or_crop_fact,
            "is_other_farm": is_other_farm,
            "has_explicit_location": has_explicit_location,
            "category": category
        }

        logger.info(
            f"\n[SESSION CONTEXT RESOLUTION]\n"
            f"category: {category}\n"
            f"cur_location: {self.current_message_location}\n"
            f"resolved_district: {self.district}, state: {self.state}\n"
            f"unresolved_attributes: {self.unresolved_attributes}\n"
            f"is_general_or_crop_fact: {is_general_or_crop_fact}\n"
        )

        return resolved_context

    def update_from_entities(self, entities: Dict[str, Any]):
        """Updates cumulative conversational context from newly extracted entities."""
        if entities.get("state"):
            self.state = entities["state"]
            self.conversation_farm_context["state"] = entities["state"]
        if entities.get("district"):
            self.district = entities["district"]
            self.conversation_farm_context["district"] = entities["district"]
        if entities.get("soil_type"):
            self.soil_type = entities["soil_type"]
            self.conversation_farm_context["soil_type"] = entities["soil_type"]
        if entities.get("farm_size_acres"):
            self.farm_size_acres = entities["farm_size_acres"]
            self.conversation_farm_context["farm_size_acres"] = entities["farm_size_acres"]
        if entities.get("irrigation_type"):
            self.irrigation_type = entities["irrigation_type"]
            self.conversation_farm_context["irrigation_type"] = entities["irrigation_type"]
        if entities.get("water_source"):
            self.water_source = entities["water_source"]
            self.conversation_farm_context["water_source"] = entities["water_source"]
        if entities.get("water_availability"):
            self.water_availability = entities["water_availability"]
            self.conversation_farm_context["water_availability"] = entities["water_availability"]
        if entities.get("season"):
            self.season = entities["season"]
            self.conversation_farm_context["season"] = entities["season"]
        if entities.get("ph"):
            self.ph = entities["ph"]
            self.conversation_farm_context["ph"] = entities["ph"]
        if entities.get("language"):
            self.language = entities["language"]

    def update_from_farm_profile(self, profile: Dict[str, Any]):
        """Updates context from saved/active farm profile without overriding explicit message overrides."""
        if not self.primary_saved_farm:
            self.primary_saved_farm = {}
        for k in ["state", "district", "soil_type", "farm_size_acres", "irrigation_type", "water_source", "season"]:
            if profile.get(k):
                self.primary_saved_farm[k] = profile[k]

    def set_pending_follow_up(
        self,
        original_query: str,
        target_field: str,
        prompt_question: str,
        quick_replies: List[str],
        accumulated_facts: Optional[Dict[str, Any]] = None,
        consultation_id: Optional[str] = None
    ):
        """Registers a structured pending follow-up state."""
        self.pending_follow_up = PendingFollowUp(
            original_query=original_query,
            target_field=target_field,
            consultation_id=consultation_id or self.session_id,
            accumulated_facts=accumulated_facts or {},
            prompt_question=prompt_question,
            quick_replies=quick_replies
        )

    def clear_pending_follow_up(self):
        """Clears active pending follow-up."""
        self.pending_follow_up = None

    def resolve_pending_follow_up(
        self, message: str, extracted: Dict[str, Any]
    ) -> Tuple[bool, Optional[str], Optional[Any]]:
        """
        Determines whether the incoming user message answers the pending follow-up question.
        Returns:
            (is_resolved, original_goal_query, resolved_value)
        """
        if not self.pending_follow_up:
            return False, None, None

        field_name = self.pending_follow_up.target_field
        orig_q = self.pending_follow_up.original_query
        msg_clean = message.strip()
        msg_lower = msg_clean.lower()

        # 1. Farm Size Acres
        if field_name in ["farm_size_acres", "farm_area"]:
            size_val = extracted.get("farm_size_acres")
            if size_val is not None:
                self.farm_size_acres = size_val
                self.conversation_farm_context["farm_size_acres"] = size_val
                self.clear_pending_follow_up()
                return True, orig_q, size_val
            # Quick-reply chips or short numeric text
            chip_map = {
                "1-2 acres": 2.0, "3-5 acres": 4.0, "more than 5 acres": 8.0,
                "small plot (< 1 acre)": 0.75, "< 1 acre": 0.5, "1 acre": 1.0, "2 acres": 2.0, "3 acres": 3.0, "5 acres": 5.0
            }
            if msg_lower in chip_map:
                val = chip_map[msg_lower]
                self.farm_size_acres = val
                self.conversation_farm_context["farm_size_acres"] = val
                self.clear_pending_follow_up()
                return True, orig_q, val
            # Bare digit (e.g. "3", "5", "10")
            num_match = re.match(r'^(\d+(?:\.\d+)?)\s*(?:acres?)?$', msg_lower)
            if num_match:
                val = float(num_match.group(1))
                self.farm_size_acres = val
                self.conversation_farm_context["farm_size_acres"] = val
                self.clear_pending_follow_up()
                return True, orig_q, val

        # 2. District / Location
        elif field_name == "district":
            dist = extracted.get("district")
            st = extracted.get("state")
            if dist or st:
                if dist: self.district = dist; self.conversation_farm_context["district"] = dist
                if st: self.state = st; self.conversation_farm_context["state"] = st
                self.clear_pending_follow_up()
                return True, orig_q, dist or st
            if len(msg_clean.split()) <= 3 and not any(q_word in msg_lower for q_word in ["what", "which", "how", "why"]):
                self.district = msg_clean
                self.conversation_farm_context["district"] = msg_clean
                self.clear_pending_follow_up()
                return True, orig_q, msg_clean

        # 3. Soil Type
        elif field_name == "soil_type":
            soil = extracted.get("soil_type")
            if soil:
                self.soil_type = soil
                self.conversation_farm_context["soil_type"] = soil
                self.clear_pending_follow_up()
                return True, orig_q, soil
            soil_keywords = ["black", "red", "alluvial", "loam", "sandy", "laterite", "clay"]
            for sk in soil_keywords:
                if sk in msg_lower:
                    self.soil_type = msg_clean.title()
                    self.conversation_farm_context["soil_type"] = self.soil_type
                    self.clear_pending_follow_up()
                    return True, orig_q, self.soil_type

        # 4. Irrigation / Water
        elif field_name == "irrigation_type":
            irrig = extracted.get("irrigation_type") or extracted.get("water_source")
            if irrig:
                self.irrigation_type = irrig
                self.conversation_farm_context["irrigation_type"] = irrig
                self.clear_pending_follow_up()
                return True, orig_q, irrig
            irrig_keywords = ["drip", "sprinkler", "borewell", "rainfed", "canal", "well"]
            for ik in irrig_keywords:
                if ik in msg_lower:
                    self.irrigation_type = msg_clean.title()
                    self.conversation_farm_context["irrigation_type"] = self.irrigation_type
                    self.clear_pending_follow_up()
                    return True, orig_q, self.irrigation_type

        # 5. Season
        elif field_name == "season":
            s_val = extracted.get("season")
            if s_val:
                self.season = s_val
                self.conversation_farm_context["season"] = s_val
                self.clear_pending_follow_up()
                return True, orig_q, s_val
            for sk, s_name in [("kharif", "Kharif"), ("rabi", "Rabi"), ("summer", "Summer"), ("zaid", "Summer")]:
                if sk in msg_lower:
                    self.season = s_name
                    self.conversation_farm_context["season"] = s_name
                    self.clear_pending_follow_up()
                    return True, orig_q, s_name

        # If user asks an independent new question (e.g. "What is cotton price?"), clear pending follow-up
        interrogatives = ["what", "which", "how", "why", "where", "when", "tell me", "explain", "price", "weather"]
        if any(w in msg_lower for w in interrogatives):
            self.clear_pending_follow_up()
            return False, None, None

        return False, None, None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "consultation_id": self.consultation_id,
            "has_pending_follow_up": self.pending_follow_up is not None,
            "pending_field": self.pending_follow_up.target_field if self.pending_follow_up else None,
            "farm_size_acres": self.farm_size_acres,
            "state": self.state,
            "district": self.district,
            "soil_type": self.soil_type,
            "irrigation_type": self.irrigation_type,
            "water_source": self.water_source,
            "water_availability": self.water_availability,
            "season": self.season,
            "ph": self.ph,
            "language": self.language,
            "last_intent": self.last_intent,
            "last_topic": self.last_topic,
            "last_recommended_crops": self.last_recommended_crops,
            "has_recommendation": self.last_recommendation_result is not None,
            "unresolved_attributes": self.unresolved_attributes,
            "primary_saved_farm": self.primary_saved_farm,
            "conversation_farm_context": self.conversation_farm_context
        }


class SessionMemoryStore:
    def __init__(self):
        self._sessions: Dict[str, ConversationState] = {}

    def get_or_create(self, session_id: str) -> ConversationState:
        if session_id not in self._sessions:
            self._sessions[session_id] = ConversationState(session_id)
        return self._sessions[session_id]

    def get_session(self, session_id: str) -> ConversationState:
        return self.get_or_create(session_id)

    def reset_session(self, session_id: str):
        if session_id in self._sessions:
            del self._sessions[session_id]

    def update_farm_profile(self, session_id: str, profile: Any) -> None:
        session = self.get_or_create(session_id)
        if hasattr(profile, "dict"):
            p_dict = profile.dict()
        elif isinstance(profile, dict):
            p_dict = profile
        else:
            p_dict = getattr(profile, "__dict__", {})

        loc = p_dict.get("location") or {}
        if isinstance(loc, dict):
            if loc.get("state"): session.state = loc.get("state")
            if loc.get("district"): session.district = loc.get("district")
        elif hasattr(loc, "state"):
            if loc.state: session.state = loc.state
            if loc.district: session.district = loc.district

        if p_dict.get("state"): session.state = p_dict.get("state")
        if p_dict.get("district"): session.district = p_dict.get("district")
        if p_dict.get("soil_type"): session.soil_type = p_dict.get("soil_type")
        if p_dict.get("area_acres"): session.farm_size_acres = p_dict.get("area_acres")

    def resolve_context(self, session_id: str, user_message: str, category: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        session = self.get_or_create(session_id)
        from backend.app.services.intent_service import intent_service
        extracted = intent_service.extract_entities(user_message)
        return session.resolve_context(extracted_facts=extracted, category=category, **kwargs)


# Singleton instance
session_memory = SessionMemoryStore()
