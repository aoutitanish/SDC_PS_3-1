"""
Crop Comparison Service for KrishiMitra AI.
Generates comprehensive agronomic comparison matrices across crops for a given farm profile.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from backend.app.ml.predict import recommender

logger = logging.getLogger(__name__)


class ComparisonService:
    def __init__(self):
        self.recommender = recommender

    def compare_crops(
        self,
        crops_to_compare: List[str],
        farm_context: Dict[str, Any],
        lang: str = "en"
    ) -> Dict[str, Any]:
        """Compares multiple crops against the specific farm profile and outputs a structured matrix."""
        if not crops_to_compare:
            # Default to top 3 from last recommendation or fresh evaluation
            rec = self.recommender.recommend(farm_context, top_k=3)
            crops_to_compare = [rec["primary_recommendation"]["crop"]] + [a["crop"] for a in rec["alternative_crops"][:2]]

        state = farm_context.get("state", "Andhra Pradesh")
        district = farm_context.get("district", "Kurnool")
        defaults = self.recommender.get_district_defaults(state, district) or {}

        merged_feat = {
            "ph": float(farm_context.get("ph") or defaults.get("ph", 7.1)),
            "clay_pct": float(farm_context.get("clay_pct") or defaults.get("clay_pct", 31.2)),
            "annual_rainfall_mm": float(farm_context.get("annual_rainfall_mm") or defaults.get("annual_rainfall_mm", 927.0)),
            "mean_temperature_c": float(farm_context.get("mean_temperature_c") or defaults.get("mean_temperature_c", 27.2)),
            "nitrogen_cg_kg": float(farm_context.get("nitrogen_cg_kg") or defaults.get("nitrogen_cg_kg", 165.0))
        }

        comparison_data = []
        for crop in crops_to_compare[:4]: # Cap at 4 for readable table layout
            exp = self.recommender.explainability_engine.explain_recommendation(
                crop,
                merged_feat,
                irrigation_type=farm_context.get("irrigation_type"),
                water_source=farm_context.get("water_source"),
                season=farm_context.get("season", "Kharif")
            )
            comparison_data.append({
                "crop": crop,
                "suitability_score": exp["agronomic_suitability_score"],
                "confidence": exp["model_confidence"],
                "soil_fit": f"{exp['factor_scores']['soil_suitability']}% ({exp['optimal_ranges']['clay_pct_optimal'][0]}-{exp['optimal_ranges']['clay_pct_optimal'][1]}% clay)",
                "rainfall_fit": f"{exp['factor_scores']['rainfall_suitability']}% (~{exp['optimal_ranges']['rainfall_optimal_mm'][0]}-{exp['optimal_ranges']['rainfall_optimal_mm'][1]} mm)",
                "temp_fit": f"{exp['factor_scores']['temperature_suitability']}% ({exp['optimal_ranges']['temp_optimal_c'][0]}-{exp['optimal_ranges']['temp_optimal_c'][1]}°C)",
                "water_demand": exp["water_assessment"]["water_demand"],
                "water_compatibility": exp["water_assessment"]["compatibility"],
                "water_note": exp["water_assessment"]["note"],
                "benchmark_yield": f"{exp['benchmark_yield_tonnes_ha']} t/ha",
                "seasons": ", ".join(exp.get("top_seasons", ["Kharif"])),
                "advantage": exp["supporting_factors"][0] if exp["supporting_factors"] else "Favorable climate match",
                "limitation": exp["potential_limitations"][0] if exp["potential_limitations"] else "Monitor nutrient timing"
            })

        # Format Markdown Table
        table_headers = ["Agronomic Factor"] + [c["crop"] for c in comparison_data]
        rows = [
            ["Agronomic Suitability"] + [f"{c['suitability_score']}/100" for c in comparison_data],
            ["Model Confidence"] + [c["confidence"] for c in comparison_data],
            ["Soil Compatibility"] + [c["soil_fit"] for c in comparison_data],
            ["Rainfall Compatibility"] + [c["rainfall_fit"] for c in comparison_data],
            ["Thermal Range"] + [c["temp_fit"] for c in comparison_data],
            ["Water Requirement"] + [c["water_demand"] for c in comparison_data],
            ["Drip Irrigation Fit"] + [c["water_compatibility"] for c in comparison_data],
            ["Benchmark Yield"] + [c["benchmark_yield"] for c in comparison_data],
            ["Key Advantage"] + [c["advantage"] for c in comparison_data],
            ["Management Caution"] + [c["limitation"] for c in comparison_data]
        ]

        md_lines = []
        md_lines.append("| " + " | ".join(table_headers) + " |")
        md_lines.append("| " + " | ".join(["---"] * len(table_headers)) + " |")
        for row in rows:
            md_lines.append("| " + " | ".join(row) + " |")

        markdown_table = "\n".join(md_lines)

        return {
            "crops_compared": [c["crop"] for c in comparison_data],
            "crops": comparison_data,
            "comparison_matrix": comparison_data,
            "markdown_table": markdown_table,
            "sources": [
                "Crop Expert Dataset (Historical Yields 1997-2015)",
                "Soil Expert Dataset (SoilGrids Profiles)",
                "Weather Expert Dataset (IMD Climate Records)",
                "Master Geography Dataset"
            ]
        }


# Singleton instance
comparison_service = ComparisonService()
