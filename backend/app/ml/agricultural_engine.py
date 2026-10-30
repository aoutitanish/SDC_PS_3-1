"""
Isolated Agricultural Intelligence Scoring Engine for KrishiMitra AI.

Centralizes multi-factor crop suitability scoring across soil, climate,
temperature, nutrients, season, water availability, weather stress,
regional historical evidence, and ML model probability evidence.

NOTE: This module is currently isolated for evaluation and testing.
It does NOT alter existing production behavior or ML model artifacts.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Configurable Component Weights (Must sum to 1.0)
# Frozen Validated Balanced Weight Vector
# -----------------------------------------------------------------------------
WEIGHT_SOIL: float = 0.15
WEIGHT_CLIMATE: float = 0.15
WEIGHT_TEMPERATURE: float = 0.12
WEIGHT_NUTRIENTS: float = 0.10
WEIGHT_SEASON: float = 0.15
WEIGHT_WATER: float = 0.12
WEIGHT_WEATHER: float = 0.08
WEIGHT_REGIONAL: float = 0.08
WEIGHT_ML_EVIDENCE: float = 0.05

# -----------------------------------------------------------------------------
# Categorical Crop Knowledge Groupings
# -----------------------------------------------------------------------------
DROUGHT_TOLERANT_CROPS = {
    "gram (chickpea)", "chickpea", "gram", "bajra (pearl millet)", "bajra",
    "millet", "small millets", "ragi (finger millet)", "ragi",
    "moong (green gram)", "moong", "urad", "jowar (sorghum)", "jowar",
    "groundnut", "mustard / rapeseed", "mustard", "sesamum", "horse-gram"
}

WATER_INTENSIVE_CROPS = {
    "rice", "paddy", "sugarcane"
}

WATERLOGGING_SENSITIVE_CROPS = {
    "gram (chickpea)", "chickpea", "gram", "bajra (pearl millet)", "bajra",
    "sesamum", "mustard / rapeseed", "mustard", "groundnut"
}

COOL_SEASON_CROPS = {
    "wheat", "mustard / rapeseed", "mustard", "barley", "potato",
    "gram (chickpea)", "gram", "chickpea", "masoor", "linseed"
}

HEAT_TOLERANT_CROPS = {
    "cotton", "bajra (pearl millet)", "jowar (sorghum)", "sugarcane",
    "sesamum", "groundnut", "maize"
}


class AgriculturalEngine:
    """
    Deterministic Agricultural Intelligence Scoring Engine.
    Evaluates individual crops or ranks multiple crops against a given farm context.
    """

    def __init__(self, profiles_path: Optional[str] = None):
        self.profiles: Dict[str, Any] = {}
        self.profiles_path = profiles_path or self._default_profiles_path()
        self._load_profiles()

    @staticmethod
    def _default_profiles_path() -> str:
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        return os.path.join(root_dir, "ml", "models", "crop_agronomic_profiles.json")

    def _load_profiles(self):
        if os.path.exists(self.profiles_path):
            try:
                with open(self.profiles_path, "r", encoding="utf-8") as f:
                    self.profiles = json.load(f)
                logger.info(f"Loaded {len(self.profiles)} crop profiles into AgriculturalEngine.")
            except Exception as e:
                logger.warning(f"Could not load crop agronomic profiles from {self.profiles_path}: {e}")
                self.profiles = {}
        else:
            logger.warning(f"Agronomic profiles file not found at {self.profiles_path}.")

    def score_soil(self, crop_name: str, farm_context: Dict[str, Any]) -> Tuple[float, List[str], List[str]]:
        """Evaluates pH and clay content against crop agronomic profile ranges."""
        prof = self.profiles.get(crop_name, {})
        supporting_factors: List[str] = []
        limitations: List[str] = []

        sub_scores: List[float] = []

        # 1. pH Evaluation
        ph_val = farm_context.get("ph")
        ph_range = prof.get("ph_optimal")
        if ph_val is not None and ph_range and len(ph_range) == 2:
            ph_min, ph_max = float(ph_range[0]), float(ph_range[1])
            ph_val = float(ph_val)
            if ph_min <= ph_val <= ph_max:
                sub_scores.append(100.0)
                supporting_factors.append(f"Soil pH ({ph_val:.1f}) matches historical optimal range ({ph_min}–{ph_max})")
            else:
                dist = min(abs(ph_val - ph_min), abs(ph_val - ph_max))
                score = max(20.0, 100.0 - dist * 25.0)
                sub_scores.append(score)
                limitations.append(f"Soil pH ({ph_val:.1f}) deviates from historical optimal range ({ph_min}–{ph_max})")

        # 2. Clay Percentage Evaluation
        clay_val = farm_context.get("clay_pct")
        clay_range = prof.get("clay_pct_optimal")
        if clay_val is not None and clay_range and len(clay_range) == 2:
            c_min, c_max = float(clay_range[0]), float(clay_range[1])
            clay_val = float(clay_val)
            if c_min <= clay_val <= c_max:
                sub_scores.append(100.0)
                supporting_factors.append(f"Soil clay content ({clay_val:.1f}%) matches historical range ({c_min}%–{c_max}%)")
            else:
                dist = min(abs(clay_val - c_min), abs(clay_val - c_max))
                score = max(25.0, 100.0 - dist * 3.0)
                sub_scores.append(score)
                limitations.append(f"Soil clay content ({clay_val:.1f}%) is outside historical range ({c_min}%–{c_max}%)")

        if sub_scores:
            final_soil_score = sum(sub_scores) / len(sub_scores)
        else:
            final_soil_score = 75.0  # Baseline neutral when soil data is omitted

        return round(final_soil_score, 1), supporting_factors, limitations

    def score_climate(self, crop_name: str, farm_context: Dict[str, Any]) -> Tuple[float, List[str], List[str]]:
        """Evaluates annual and seasonal rainfall against historical optimal bounds."""
        prof = self.profiles.get(crop_name, {})
        supporting_factors: List[str] = []
        limitations: List[str] = []

        rain_val = farm_context.get("annual_rainfall_mm") or farm_context.get("mean_rainfall_mm")
        rain_range = prof.get("rainfall_optimal_mm")

        if rain_val is not None and rain_range and len(rain_range) == 2:
            r_min, r_max = float(rain_range[0]), float(rain_range[1])
            rain_val = float(rain_val)

            if r_min <= rain_val <= r_max:
                score = 100.0
                supporting_factors.append(f"Annual rainfall ({rain_val:.0f}mm) fits historical range ({r_min:.0f}–{r_max:.0f}mm)")
            elif rain_val < r_min:
                deficit_ratio = (r_min - rain_val) / r_min
                score = max(20.0, 100.0 - deficit_ratio * 100.0)
                limitations.append(f"Annual rainfall ({rain_val:.0f}mm) is lower than historical benchmark ({r_min:.0f}–{r_max:.0f}mm)")
            else:
                excess_ratio = (rain_val - r_max) / r_max
                score = max(30.0, 100.0 - excess_ratio * 60.0)
                limitations.append(f"Annual rainfall ({rain_val:.0f}mm) exceeds historical benchmark ({r_min:.0f}–{r_max:.0f}mm)")
        else:
            score = 75.0  # Baseline neutral when rainfall data is omitted

        return round(score, 1), supporting_factors, limitations

    def score_temperature(self, crop_name: str, farm_context: Dict[str, Any]) -> Tuple[float, List[str], List[str]]:
        """Evaluates mean temperature against crop optimal thermal bounds."""
        prof = self.profiles.get(crop_name, {})
        supporting_factors: List[str] = []
        limitations: List[str] = []

        temp_val = farm_context.get("mean_temperature_c") or farm_context.get("temperature_c")
        temp_range = prof.get("temp_optimal_c")

        if temp_val is not None and temp_range and len(temp_range) == 2:
            t_min, t_max = float(temp_range[0]), float(temp_range[1])
            temp_val = float(temp_val)

            if t_min <= temp_val <= t_max:
                score = 100.0
                supporting_factors.append(f"Mean temperature ({temp_val:.1f}°C) is within optimal range ({t_min}–{t_max}°C)")
            else:
                dist = min(abs(temp_val - t_min), abs(temp_val - t_max))
                score = max(15.0, 100.0 - dist * 12.0)
                limitations.append(f"Mean temperature ({temp_val:.1f}°C) deviates from historical optimal range ({t_min}–{t_max}°C)")
        else:
            score = 75.0  # Baseline neutral when temperature is omitted

        return round(score, 1), supporting_factors, limitations

    def score_nutrients(self, crop_name: str, farm_context: Dict[str, Any]) -> Tuple[float, List[str], List[str]]:
        """Evaluates nitrogen levels against crop historical nitrogen optimal ranges."""
        prof = self.profiles.get(crop_name, {})
        supporting_factors: List[str] = []
        limitations: List[str] = []

        n_val = farm_context.get("nitrogen_cg_kg") or farm_context.get("nitrogen")
        n_range = prof.get("nitrogen_optimal_cg_kg")

        if n_val is not None and n_range and len(n_range) == 2:
            n_min, n_max = float(n_range[0]), float(n_range[1])
            n_val = float(n_val)

            if n_min <= n_val <= n_max:
                score = 100.0
                supporting_factors.append(f"Soil nitrogen ({n_val:.0f} cg/kg) matches historical range ({n_min:.0f}–{n_max:.0f})")
            else:
                dist = min(abs(n_val - n_min), abs(n_val - n_max))
                score = max(30.0, 100.0 - dist * 0.5)
                limitations.append(f"Soil nitrogen ({n_val:.0f} cg/kg) is outside historical range ({n_min:.0f}–{n_max:.0f})")
        else:
            score = 75.0  # Baseline neutral when nitrogen data is omitted

        return round(score, 1), supporting_factors, limitations

    def score_season(self, crop_name: str, farm_context: Dict[str, Any]) -> Tuple[float, List[str], List[str], List[str]]:
        """Evaluates requested season against crop's historical top_seasons records."""
        prof = self.profiles.get(crop_name, {})
        supporting_factors: List[str] = []
        limitations: List[str] = []
        hard_constraints: List[str] = []

        season_req = farm_context.get("season")
        top_seasons = prof.get("top_seasons", {})

        if not season_req:
            return 70.0, [], [], []

        s_clean = str(season_req).strip().title()

        if not top_seasons:
            return 70.0, [], [], []

        # Find primary (most frequent) growing season in historical profiles
        primary_season = max(top_seasons, key=lambda k: top_seasons[k])
        primary_count = max(top_seasons.values())

        # Case-insensitive season matching dictionary
        season_map = {k.lower(): (k, v) for k, v in top_seasons.items()}
        req_key = s_clean.lower()

        if req_key in season_map:
            matched_name, count = season_map[req_key]
            ratio_to_primary = count / primary_count if primary_count > 0 else 0.0

            if matched_name.lower() == primary_season.lower():
                score = 100.0
                supporting_factors.append(f"Primary historical growing season ({s_clean}) match")
            elif ratio_to_primary >= 0.15:
                score = 75.0
                supporting_factors.append(f"Secondary historical growing season ({s_clean}) match")
            else:
                score = 25.0
                limitations.append(f"Minor historical growing season representation ({s_clean})")
                hard_constraints.append(f"Out-of-season penalty for {s_clean}")
        elif "whole year" in season_map and req_key in ["kharif", "rabi", "summer", "zaid"]:
            score = 75.0
            supporting_factors.append(f"Cultivated throughout the year including {s_clean}")
        else:
            score = 15.0
            limitations.append(f"Crop is not historically grown in {s_clean} season")
            hard_constraints.append(f"Out-of-season penalty for {s_clean}")

        return round(score, 1), supporting_factors, limitations, hard_constraints

    def score_water(self, crop_name: str, farm_context: Dict[str, Any]) -> Tuple[float, List[str], List[str], List[str]]:
        """Evaluates water availability and irrigation setup without assuming unstated drip/borewell."""
        supporting_factors: List[str] = []
        limitations: List[str] = []
        hard_constraints: List[str] = []

        water_avail = farm_context.get("water_availability")
        irrigation_type = farm_context.get("irrigation_type")
        has_drip = farm_context.get("has_drip")
        has_borewell = farm_context.get("has_borewell")

        c_lower = crop_name.lower()
        is_water_intensive = any(w in c_lower for w in WATER_INTENSIVE_CROPS)
        is_drought_tolerant = any(w in c_lower for w in DROUGHT_TOLERANT_CROPS)

        is_limited = (water_avail == "Limited") or (irrigation_type == "Rainfed" and not (has_drip or has_borewell))
        is_high_water_supply = (water_avail == "High") or (has_borewell is True) or (has_drip is True) or ("drip" in str(irrigation_type).lower())

        if is_limited:
            if is_drought_tolerant:
                score = 95.0
                supporting_factors.append("Drought-tolerant crop suitable for limited water / rainfed conditions")
            elif is_water_intensive:
                score = 25.0
                limitations.append("High water requirement crop is at risk under limited water / rainfed conditions")
                hard_constraints.append("High water risk")
            else:
                score = 60.0
        elif is_high_water_supply:
            if is_water_intensive:
                score = 95.0
                supporting_factors.append("Assured irrigation / high water availability supports water-intensive crop")
            else:
                score = 85.0
        else:
            score = 80.0

        # STRICT CONTEXT CHECK: Only report explicit drip/borewell if explicitly verified True
        if has_drip is True and "drip" in str(irrigation_type).lower():
            supporting_factors.append("Drip irrigation setup available")
        if has_borewell is True:
            supporting_factors.append("Borewell water source confirmed")

        return round(score, 1), supporting_factors, limitations, hard_constraints

    def score_weather(self, crop_name: str, farm_context: Dict[str, Any]) -> Tuple[float, List[str], List[str]]:
        """Evaluates weather condition stress (drought, heavy rain, hot, cold)."""
        supporting_factors: List[str] = []
        limitations: List[str] = []

        cond = (
            farm_context.get("weather_condition") or
            farm_context.get("rainfall_condition") or
            farm_context.get("temperature_condition") or
            "normal"
        ).lower().strip()

        c_lower = crop_name.lower()
        is_drought_tolerant = any(w in c_lower for w in DROUGHT_TOLERANT_CROPS)
        is_water_intensive = any(w in c_lower for w in WATER_INTENSIVE_CROPS)
        is_waterlogging_sensitive = any(w in c_lower for w in WATERLOGGING_SENSITIVE_CROPS)
        is_cool_season = any(w in c_lower for w in COOL_SEASON_CROPS)
        is_heat_tolerant = any(w in c_lower for w in HEAT_TOLERANT_CROPS)

        if cond == "drought":
            if is_drought_tolerant:
                score = 95.0
                supporting_factors.append("Resilient under drought conditions")
            elif is_water_intensive:
                score = 25.0
                limitations.append("Vulnerable to severe yield loss under drought")
            else:
                score = 55.0
        elif cond in ["heavy", "heavy_rainfall"]:
            if is_water_intensive or "maize" in c_lower:
                score = 95.0
                supporting_factors.append("Tolerates heavy rainfall / high moisture")
            elif is_waterlogging_sensitive:
                score = 30.0
                limitations.append("Sensitive to waterlogging from heavy rainfall")
            else:
                score = 65.0
        elif cond == "hot":
            if is_heat_tolerant:
                score = 90.0
                supporting_factors.append("Tolerates high thermal conditions")
            elif is_cool_season:
                score = 30.0
                limitations.append("High temperature stress reduces cool-season crop performance")
            else:
                score = 65.0
        elif cond == "cold":
            if is_cool_season:
                score = 95.0
                supporting_factors.append("Well-adapted to cool temperatures")
            elif is_heat_tolerant or is_water_intensive:
                score = 40.0
                limitations.append("Low temperature stress may retard growth")
            else:
                score = 70.0
        else:
            score = 85.0

        return round(score, 1), supporting_factors, limitations

    def score_regional(self, crop_name: str, farm_context: Dict[str, Any]) -> Tuple[float, List[str], List[str], List[str]]:
        """Evaluates historical regional production records without assigning hardcoded location fallbacks."""
        prof = self.profiles.get(crop_name, {})
        supporting_factors: List[str] = []
        limitations: List[str] = []
        evidence: List[str] = []

        state_val = farm_context.get("state")
        if not state_val:
            evidence.append("Location state not specified; regional historical evidence omitted")
            return 50.0, [], [], evidence

        state_clean = str(state_val).strip()
        top_states = prof.get("top_states", {})

        # Case-insensitive search across historical top_states
        matched_entry = None
        for st_name, count in top_states.items():
            if st_name.lower() == state_clean.lower():
                matched_entry = (st_name, count)
                break

        if matched_entry:
            st_name, count = matched_entry
            score = min(100.0, 80.0 + (count / 100.0))
            supporting_factors.append(f"Strong historical cultivation record in {st_name} ({count} dataset records)")
            evidence.append(f"Historical evidence: {count} recorded production entries in {st_name}")
        else:
            score = 45.0
            limitations.append(f"Lower historical dataset representation for {crop_name} in {state_clean}")

        return round(score, 1), supporting_factors, limitations, evidence

    def score_ml_evidence(self, crop_name: str, ml_probability: Optional[float]) -> Tuple[float, List[str]]:
        """Translates external Random Forest ML probability into a 0-100 evidence score."""
        evidence: List[str] = []

        if ml_probability is None:
            evidence.append("No external ML model probability provided")
            return 50.0, evidence

        p = max(0.0, min(1.0, float(ml_probability)))
        # Map 28-class probability p to a 0-100 evidence scale (e.g. p=0.25 -> 75.0)
        score = round(min(100.0, p * 300.0), 1)
        evidence.append(f"ML model prediction probability: {p:.4f}")
        return score, evidence

    def evaluate_crop(
        self,
        crop_name: str,
        farm_context: Dict[str, Any],
        ml_probability: Optional[float] = None
    ) -> Dict[str, Any]:
        """Evaluates a single crop against farm context across all agronomic dimensions."""
        soil_score, soil_sup, soil_lim = self.score_soil(crop_name, farm_context)
        climate_score, climate_sup, climate_lim = self.score_climate(crop_name, farm_context)
        temp_score, temp_sup, temp_lim = self.score_temperature(crop_name, farm_context)
        nutr_score, nutr_sup, nutr_lim = self.score_nutrients(crop_name, farm_context)
        season_score, season_sup, season_lim, season_hard = self.score_season(crop_name, farm_context)
        water_score, water_sup, water_lim, water_hard = self.score_water(crop_name, farm_context)
        weather_score, weather_sup, weather_lim = self.score_weather(crop_name, farm_context)
        reg_score, reg_sup, reg_lim, reg_evi = self.score_regional(crop_name, farm_context)
        ml_score, ml_evi = self.score_ml_evidence(crop_name, ml_probability)

        overall_score = (
            WEIGHT_SOIL * soil_score +
            WEIGHT_CLIMATE * climate_score +
            WEIGHT_TEMPERATURE * temp_score +
            WEIGHT_NUTRIENTS * nutr_score +
            WEIGHT_SEASON * season_score +
            WEIGHT_WATER * water_score +
            WEIGHT_WEATHER * weather_score +
            WEIGHT_REGIONAL * reg_score +
            WEIGHT_ML_EVIDENCE * ml_score
        )

        overall_score = round(max(0.0, min(100.0, overall_score)), 1)

        # Consolidate factors and limitations
        supporting_factors = soil_sup + climate_sup + temp_sup + nutr_sup + season_sup + water_sup + weather_sup + reg_sup
        limitations = soil_lim + climate_lim + temp_lim + nutr_lim + season_lim + water_lim + weather_lim + reg_lim
        hard_constraints = season_hard + water_hard

        evidence: List[str] = []
        prof = self.profiles.get(crop_name, {})
        rec_count = prof.get("sample_records")
        if rec_count:
            evidence.append(f"Historical dataset records: {rec_count}")
        evidence.extend(reg_evi)
        evidence.extend(ml_evi)
        evidence.append("Historical profile ranges reflect dataset evidence, not absolute physiological crop requirements.")

        return {
            "crop": crop_name,
            "overall_score": overall_score,
            "factor_scores": {
                "soil": soil_score,
                "climate": climate_score,
                "temperature": temp_score,
                "nutrients": nutr_score,
                "season": season_score,
                "water": water_score,
                "weather": weather_score,
                "regional": reg_score,
                "ml_evidence": ml_score
            },
            "hard_constraints": hard_constraints,
            "supporting_factors": supporting_factors,
            "limitations": limitations,
            "evidence": evidence
        }

    def rank_crops(
        self,
        farm_context: Dict[str, Any],
        candidate_crops: Optional[List[str]] = None,
        ml_probabilities: Optional[Dict[str, float]] = None,
        top_k: int = 4
    ) -> List[Dict[str, Any]]:
        """Ranks multiple candidate crops based on agricultural suitability scores."""
        crops_to_eval = candidate_crops or list(self.profiles.keys())
        if not crops_to_eval:
            return []

        results: List[Dict[str, Any]] = []
        ml_probs = ml_probabilities or {}

        for crop in crops_to_eval:
            p_val = ml_probs.get(crop)
            res = self.evaluate_crop(crop, farm_context, ml_probability=p_val)
            results.append(res)

        results.sort(key=lambda x: x["overall_score"], reverse=True)
        return results[:top_k]


# Singleton instance for evaluation
agricultural_engine = AgriculturalEngine()
