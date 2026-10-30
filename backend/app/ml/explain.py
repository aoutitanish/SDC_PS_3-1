"""
Explainability Engine for KrishiMitra AI.
Calculates agronomic factor suitability matching, positive drivers, limitations, and calibrated explanations.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "ml", "models")


class ExplainabilityEngine:
    def __init__(self):
        self.profiles = {}
        self.metadata = {}
        self._load_profiles()

    def _load_profiles(self):
        profiles_path = os.path.join(MODELS_DIR, "crop_agronomic_profiles.json")
        metadata_path = os.path.join(MODELS_DIR, "model_metadata.json")

        if os.path.exists(profiles_path):
            with open(profiles_path, "r", encoding="utf-8") as fp:
                self.profiles = json.load(fp)
        if os.path.exists(metadata_path):
            with open(metadata_path, "r", encoding="utf-8") as fp:
                self.metadata = json.load(fp)

    def _calculate_factor_fit(self, actual: float, opt_min: float, opt_max: float, tolerance: float = 0.35) -> float:
        """Calculates deterministic matching score (0-100) based on actual agronomic distance."""
        if opt_min <= actual <= opt_max:
            mid = (opt_min + opt_max) / 2.0
            spread = max(0.1, (opt_max - opt_min) / 2.0)
            return round(90.0 + 10.0 * (1.0 - abs(actual - mid) / spread), 1)
        elif actual < opt_min:
            dist = opt_min - actual
            max_dist = max(1.0, opt_min * tolerance)
            score = max(35.0, 90.0 - (dist / max_dist) * 55.0)
            return round(score, 1)
        else:
            dist = actual - opt_max
            max_dist = max(1.0, opt_max * tolerance)
            score = max(35.0, 90.0 - (dist / max_dist) * 55.0)
            return round(score, 1)

    def explain_recommendation(
        self,
        crop: str,
        features: Dict[str, Any],
        irrigation_type: Optional[str] = None,
        water_source: Optional[str] = None,
        season: Optional[str] = None,
        rainfall_condition: Optional[str] = None,
        temperature_condition: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generates grounded agronomic explainability matching scores and factor reasoning."""
        prof = self.profiles.get(crop, {})

        ph_range = prof.get("ph_optimal", [6.0, 7.8])
        rain_range = prof.get("rainfall_optimal_mm", [600.0, 1200.0])
        temp_range = prof.get("temp_optimal_c", [20.0, 32.0])
        clay_range = prof.get("clay_pct_optimal", [20.0, 45.0])

        ph_val = float(features.get("ph", 7.0))
        rain_val = float(features.get("annual_rainfall_mm", 945.0))
        temp_val = float(features.get("mean_temperature_c", 27.0))
        clay_val = float(features.get("clay_pct", 32.6))
        nitrogen_val = float(features.get("nitrogen_cg_kg", 163.0))

        # Factor Suitability Matches (0 - 100)
        ph_match = min(100.0, self._calculate_factor_fit(ph_val, ph_range[0], ph_range[1], 0.25))
        rain_match = min(100.0, self._calculate_factor_fit(rain_val, rain_range[0], rain_range[1], 0.35))
        temp_match = min(100.0, self._calculate_factor_fit(temp_val, temp_range[0], temp_range[1], 0.30))
        soil_match = min(100.0, self._calculate_factor_fit(clay_val, clay_range[0], clay_range[1], 0.35))
        nutrient_match = min(100.0, 75.0 + min(25.0, (nitrogen_val / 250.0) * 20.0))

        # Water & Irrigation Assessment
        is_drip = irrigation_type and "drip" in irrigation_type.lower()
        is_borewell = water_source and "borewell" in water_source.lower()
        
        # High water crops (Paddy/Rice, Sugarcane) vs Moderate water crops (Cotton, Chilli, Maize, Pulses)
        crop_lower = crop.lower()
        if "rice" in crop_lower or "paddy" in crop_lower or "sugarcane" in crop_lower:
            water_demand = "High (1200 - 1500 mm)"
            if is_drip:
                water_compatibility = "Moderate"
                water_note = "Water demand is high; drip irrigation is non-traditional for paddy and requires flood/canal or heavy standing water management."
            else:
                water_compatibility = "High" if is_borewell else "Moderate"
                water_note = "Requires continuous standing water; borewell yield must be sustained throughout vegetative & panicle stages."
        elif "cotton" in crop_lower or "chilli" in crop_lower or "maize" in crop_lower:
            water_demand = "Moderate (650 - 900 mm)"
            water_compatibility = "Optimal / High"
            if is_drip and is_borewell:
                water_note = "Drip irrigation with borewell allows targeted moisture delivery to the root zone and reduces evaporative losses during dry spells."
            elif is_drip:
                water_note = "Drip irrigation provides efficient micro-application during key moisture-sensitive growth windows."
            elif "canal" in (irrigation_type or "").lower() or "canal" in (water_source or "").lower():
                water_note = "Canal irrigation infrastructure supplies surface water during crucial vegetative and reproductive stages."
            elif "rainfed" in (irrigation_type or "").lower() or "rainwater" in (water_source or "").lower():
                water_note = "Rainfed crop development relies on seasonal monsoon rainfall timing and soil moisture conservation."
            else:
                water_note = f"Your current irrigation setup ({irrigation_type or 'Standard'}) supplies required moisture during critical growth stages."
        else:
            water_demand = "Low to Moderate (400 - 650 mm)"
            water_compatibility = "Optimal"
            if is_drip:
                water_note = "Well-suited for semi-arid conditions and supplemental drip irrigation during critical growth stages."
            elif "canal" in (irrigation_type or "").lower():
                water_note = "Well-suited for semi-arid conditions with canal water availability during critical growth stages."
            elif "rainfed" in (irrigation_type or "").lower() or "rainwater" in (water_source or "").lower():
                water_note = "Well-suited for rainfed cultivation under seasonal rainfall conditions."
            else:
                water_note = f"Well-suited for your farm's water setup ({irrigation_type or 'Standard'})."

        overall_suitability = round(
            0.25 * soil_match + 0.25 * rain_match + 0.20 * temp_match + 0.15 * ph_match + 0.15 * nutrient_match, 1
        )

        # Categorical Model Confidence
        if overall_suitability >= 85.0:
            confidence_level = "High"
            confidence_note = "High confidence based on tightly aligned soil chemistry, climate normal, and irrigation setup."
        elif overall_suitability >= 70.0:
            confidence_level = "Medium"
            confidence_note = "Moderate confidence. Yield optimization depends on season and micro-irrigation management."
        else:
            confidence_level = "Low"
            confidence_note = "Lower suitability due to environmental or soil texture deviations."

        # Supporting factors
        supporting_factors = []
        limitations = []

        # Soil driver
        supporting_factors.append(
            f"Soil texture (clay {clay_val:.1f}%, pH {ph_val:.1f}) matches {crop}'s optimal range ({clay_range[0]}-{clay_range[1]}% clay, pH {ph_range[0]}-{ph_range[1]})."
        )
        # Climate driver
        supporting_factors.append(
            f"Precipitation (~{rain_val:.0f} mm) and thermal normal ({temp_val:.1f}°C) support healthy vegetative and reproductive growth."
        )

        # Season driver
        top_seasons_dict = prof.get("top_seasons", {})
        top_seasons_list = [s.lower() for s in top_seasons_dict.keys()]
        user_season_clean = (season or "Kharif").lower().strip()

        if user_season_clean in top_seasons_list:
            supporting_factors.append(
                f"Sowing in {season or 'Kharif'} aligns with historical regional production windows for {crop}."
            )
        elif "whole year" in top_seasons_list:
            supporting_factors.append(
                f"{crop} can be cultivated year-round with adequate irrigation."
            )
        else:
            limitations.append(
                f"Sowing in {season or 'Kharif'} is outside {crop}'s primary historical season ({', '.join(top_seasons_dict.keys())}); monitor temperature & moisture closely."
            )

        # Weather / Rainfall condition driver
        if rainfall_condition == "drought":
            supporting_factors.append(
                "Severe drought and low rainfall increase the importance of drought tolerance and efficient water use."
            )
        elif rainfall_condition == "heavy":
            supporting_factors.append(
                "Heavy rainfall and excess water favor crops that can tolerate higher moisture availability, while drainage remains important."
            )

        if temperature_condition == "hot":
            supporting_factors.append(
                "Hot conditions increase thermal stress and favor crops suited to higher temperatures."
            )
        elif temperature_condition == "cold":
            supporting_factors.append(
                "Cold conditions favor crops suited to cooler Rabi conditions."
            )

        # Irrigation driver
        if is_drip and is_borewell:
            supporting_factors.append(
                "Drip irrigation + borewell setup enhances nutrient efficiency and mitigates mid-season dry spells."
            )
        elif is_drip:
            supporting_factors.append(
                "Drip irrigation system enhances water-use efficiency."
            )
        elif "canal" in (irrigation_type or "").lower():
            supporting_factors.append(
                "Canal irrigation supplies surface water during critical growth stages."
            )
        elif "rainfed" in (irrigation_type or "").lower() or "rainwater" in (water_source or "").lower():
            supporting_factors.append(
                "Rainfed crop management aligns with seasonal precipitation."
            )

        # Risk / limitation checks
        if "rice" in crop_lower and is_drip:
            limitations.append("Paddy/Rice requires standing water during critical growth phases; evaluate water supply capacity before full-field planting.")
        elif rain_val < rain_range[0]:
            if is_borewell or is_drip:
                limitations.append(f"Rainfall (~{rain_val:.0f} mm) is below peak rainfed demand; rely on scheduled borewell/drip irrigation.")
            elif "canal" in (irrigation_type or "").lower():
                limitations.append(f"Rainfall (~{rain_val:.0f} mm) is below peak rainfed demand; rely on scheduled canal irrigation supply.")
            else:
                limitations.append(f"Rainfall (~{rain_val:.0f} mm) is below peak rainfed demand; monitor rainfall timing closely.")

        return {
            "crop": crop,
            "agronomic_suitability_score": overall_suitability,
            "model_confidence": confidence_level,
            "confidence_note": confidence_note,
            "factor_scores": {
                "soil_suitability": soil_match,
                "rainfall_suitability": rain_match,
                "temperature_suitability": temp_match,
                "ph_suitability": ph_match,
                "nutrient_suitability": nutrient_match
            },
            "radar_scores": {
                "soil": soil_match,
                "rainfall": rain_match,
                "temperature": temp_match,
                "ph": ph_match,
                "nutrients": nutrient_match
            },
            "actual_values": {
                "soil_clay_pct": clay_val,
                "ph": ph_val,
                "rainfall_mm": rain_val,
                "mean_temp_c": temp_val,
                "nitrogen_cg_kg": nitrogen_val,
                "irrigation": irrigation_type or "Standard",
                "water_source": water_source or "Standard",
                "season": season or "Kharif"
            },
            "optimal_ranges": {
                "ph_optimal": ph_range,
                "rainfall_optimal_mm": rain_range,
                "temp_optimal_c": temp_range,
                "clay_pct_optimal": clay_range,
                "water_demand": water_demand
            },
            "water_assessment": {
                "water_demand": water_demand,
                "compatibility": water_compatibility,
                "note": water_note
            },
            "supporting_factors": supporting_factors,
            "potential_limitations": limitations,
            "benchmark_yield_tonnes_ha": prof.get("mean_yield_tonnes_ha", 1.8),
            "top_seasons": list(prof.get("top_seasons", {}).keys()),
            "sources": [
                "Crop Expert Dataset (Historical District Production 1997-2015)",
                "Soil Expert Dataset (SoilGrids Physicochemical Profile)",
                "Weather Expert Dataset (IMD / NASA Climate Records)",
                "Master Geography Dataset (District Agro-Climatic Zone)"
            ]
        }
