"""
Machine Learning Inference Pipeline for KrishiMitra AI.
Provides deterministic crop suitability ranking, Random Forest classification, and verified district defaults.
Supports MODEL_V1 and MODEL_V2 candidate staging modes via CROP_MODEL_VERSION environment variable.
"""

import os
import logging
import joblib
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from backend.app.ml.explain import ExplainabilityEngine
from backend.app.ml.agricultural_engine import agricultural_engine

logger = logging.getLogger(__name__)

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "ml", "models")
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "data", "processed")


class CropRecommender:
    def __init__(self):
        self.model = None
        self.pipeline = None
        self.label_encoder = None
        self.features = []
        self.feature_cols = []
        self.categorical_features = []
        self.top_crops = []
        self.district_profiles = {}
        self.model_version = os.getenv("CROP_MODEL_VERSION", "v1").lower().strip()
        self.explainability_engine = ExplainabilityEngine()
        # In RAG-only mode, legacy trained ML models are NOT loaded into memory at startup
        from backend.app.core.config import settings
        if not getattr(settings, "RAG_LLM_MODE", True):
            self._load_artifacts()

    def set_model_version(self, version: str):
        """Allows dynamic switching between 'v1' and 'v2' for testing and staging."""
        self.model_version = version.lower().strip()
        self._load_artifacts()

    def _load_artifacts(self):
        v1_path = os.path.join(MODELS_DIR, "crop_recommendation_model.pkl")
        v2_path = os.path.join(MODELS_DIR, "crop_recommendation_model_v2_candidate.pkl")

        if self.model_version == "v2":
            if os.path.exists(v2_path):
                try:
                    artifact = joblib.load(v2_path)
                    self.pipeline = artifact["pipeline"]
                    self.model = artifact["pipeline"]
                    self.label_encoder = artifact["label_encoder"]
                    self.feature_cols = artifact["feature_cols"]
                    self.categorical_features = artifact.get("categorical_features", [])
                    self.features = artifact.get("numeric_features", [])
                    self.top_crops = artifact.get("classes", [])
                    logger.info("Loaded Crop Recommendation Model V2 Candidate successfully.")
                except Exception as e:
                    logger.warning(f"Could not load V2 model artifact ({v2_path}): {e}. Falling back to V1.")
                    self.model_version = "v1"
            else:
                logger.warning(f"V2 model candidate requested but artifact not found at {v2_path}. Falling back to V1.")
                self.model_version = "v1"

        if self.model_version == "v1":
            if os.path.exists(v1_path):
                try:
                    artifact = joblib.load(v1_path)
                    self.model = artifact["model"]
                    self.pipeline = None
                    self.label_encoder = artifact["label_encoder"]
                    self.features = artifact["features"]
                    self.feature_cols = artifact["features"]
                    self.categorical_features = []
                    self.top_crops = artifact["top_crops"]
                    logger.info("Loaded Crop Recommendation Model V1 successfully.")
                except Exception as e:
                    logger.warning(f"Could not load ML model artifact: {e}")

        master_path = os.path.join(DATA_DIR, "master_district_profiles.csv")
        if os.path.exists(master_path):
            try:
                df = pd.read_csv(master_path)
                for _, row in df.iterrows():
                    key = str(row["district_key"]).lower().strip()
                    self.district_profiles[key] = row.to_dict()
                logger.info(f"Loaded {len(self.district_profiles)} district profiles.")
            except Exception as e:
                logger.warning(f"Could not load master district profiles: {e}")

    def get_district_defaults(self, state: Optional[str], district: Optional[str]) -> Optional[Dict[str, Any]]:
        st_clean = (state or "").lower().strip()
        dist_clean = (district or "").lower().strip()

        # 1. Exact state__district key match
        if st_clean and dist_clean:
            key = f"{st_clean}__{dist_clean}"
            if key in self.district_profiles:
                return self.district_profiles[key]

        # 2. Search by district alone across all profiles
        if dist_clean:
            for p_key, prof in self.district_profiles.items():
                p_dist = str(prof.get("District_Name", "")).lower().strip()
                if p_dist == dist_clean or dist_clean in p_key:
                    return prof

        # 3. Search by state alone
        if st_clean:
            for p_key, prof in self.district_profiles.items():
                p_st = str(prof.get("State_Name", "")).lower().strip()
                if p_st == st_clean:
                    return prof

        # 4. Fallback to first profile if available
        if self.district_profiles:
            return next(iter(self.district_profiles.values()))
        return None

    def get_model_probabilities(
        self,
        merged_feat: Dict[str, float],
        season: str,
        soil_type: str,
        defaults: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Computes 28-class probability predictions using active model version (v1 or v2).
        """
        if self.model is None and self.pipeline is None:
            self._load_artifacts()

        if self.label_encoder is None:
            return {}

        try:
            if self.model_version == "v2" and self.pipeline is not None:
                v2_dict = dict(merged_feat)
                v2_dict["Season"] = season or "Kharif"
                v2_dict["indian_soil_group"] = soil_type or defaults.get("indian_soil_group", "Black Soil (Regur/Vertisol)")
                
                X_df = pd.DataFrame([v2_dict])[self.feature_cols]
                probs = self.pipeline.predict_proba(X_df)[0]

                top5_idx = np.argsort(probs)[::-1][:5]
                top5_pred = [(self.label_encoder.classes_[i], round(float(probs[i]), 4)) for i in top5_idx]

                logger.info(f"MODEL_VERSION: v2 | MODEL_INPUT_FEATURES: {list(X_df.columns)} | MODEL_PREDICTION_TOP5: {top5_pred}")
                return dict(zip(self.label_encoder.classes_, probs))
            elif self.model is not None:
                X_df = pd.DataFrame([merged_feat])[self.features]
                probs = self.model.predict_proba(X_df)[0]

                top5_idx = np.argsort(probs)[::-1][:5]
                top5_pred = [(self.label_encoder.classes_[i], round(float(probs[i]), 4)) for i in top5_idx]

                logger.info(f"MODEL_VERSION: v1 | MODEL_INPUT_FEATURES: {list(X_df.columns)} | MODEL_PREDICTION_TOP5: {top5_pred}")
                return dict(zip(self.label_encoder.classes_, probs))
        except Exception as e:
            logger.warning(f"Error executing ML model probabilities ({self.model_version}): {e}")
            return {}

        return {}

    def recommend(
        self,
        features: Dict[str, Any],
        top_k: int = 4
    ) -> Dict[str, Any]:
        """
        Recommends optimal crops with deterministic agronomic scoring and explainability.
        """
        req_state = features.get("state")
        req_district = features.get("district")
        defaults = self.get_district_defaults(req_state, req_district) or {}

        state = req_state or defaults.get("State_Name", "Andhra Pradesh")
        district = req_district or defaults.get("District_Name", "Kurnool")
        soil_type = features.get("soil_type") or defaults.get("indian_soil_group") or "Alluvial / Loamy Soil"
        
        has_borewell = features.get("has_borewell")
        has_drip = features.get("has_drip")

        water_source = features.get("water_source")
        if not water_source:
            if has_borewell is False:
                water_source = "Canal / Rainwater"
            else:
                water_source = "Borewell / Local Source" if has_borewell else "Canal / Local Source"

        irrigation_type = features.get("irrigation_type")
        if not irrigation_type:
            if has_drip is False:
                irrigation_type = "Canal / Rainfed Irrigation"
            elif has_drip is True:
                irrigation_type = "Drip Irrigation"
            else:
                irrigation_type = "Canal / Rainfed Irrigation"

        season = features.get("season") or "Kharif"
        farm_size = features.get("farm_size_acres") or 5.0

        # Merge input features with verified district telemetry
        merged_feat = {
            "ph": float(features.get("ph") or defaults.get("ph", 7.1)),
            "clay_pct": float(features.get("clay_pct") or defaults.get("clay_pct", 31.2)),
            "sand_pct": float(features.get("sand_pct") or defaults.get("sand_pct", 41.6)),
            "silt_pct": float(features.get("silt_pct") or defaults.get("silt_pct", 27.2)),
            "nitrogen_cg_kg": float(features.get("nitrogen_cg_kg") or defaults.get("nitrogen_cg_kg", 165.0)),
            "soc_dg_kg": float(features.get("soc_dg_kg") or defaults.get("soc_dg_kg", 170.0)),
            "cec": float(features.get("cec") or defaults.get("cec", 340.0)),
            "bulk_density": float(features.get("bulk_density") or defaults.get("bulk_density", 1.58)),
            "annual_rainfall_mm": float(features.get("annual_rainfall_mm") or defaults.get("annual_rainfall_mm", 927.0)),
            "kharif_rainfall_mm": float(features.get("kharif_rainfall_mm") or defaults.get("kharif_rainfall_mm", 820.0)),
            "rabi_rainfall_mm": float(features.get("rabi_rainfall_mm") or defaults.get("rabi_rainfall_mm", 85.0)),
            "mean_temperature_c": float(features.get("mean_temperature_c") or defaults.get("mean_temperature_c", 27.2)),
            "max_temperature_c": float(features.get("max_temperature_c") or defaults.get("max_temperature_c", 36.5)),
            "min_temperature_c": float(features.get("min_temperature_c") or defaults.get("min_temperature_c", 18.5)),
            "relative_humidity_pct": float(features.get("relative_humidity_pct") or defaults.get("relative_humidity_pct", 58.5)),
            "wind_speed_ms": float(features.get("wind_speed_ms") or defaults.get("wind_speed_ms", 2.2))
        }

        # Modulate telemetry based on explicit weather/rainfall/temperature conditions
        rain_cond = features.get("rainfall_condition") or "normal"
        temp_cond = features.get("temperature_condition") or "moderate"

        if rain_cond == "drought" or features.get("water_availability") == "Limited":
            merged_feat["annual_rainfall_mm"] = min(merged_feat["annual_rainfall_mm"], 450.0)
            merged_feat["kharif_rainfall_mm"] = min(merged_feat["kharif_rainfall_mm"], 350.0)
        elif rain_cond == "heavy":
            merged_feat["annual_rainfall_mm"] = max(merged_feat["annual_rainfall_mm"], 1500.0)
            merged_feat["kharif_rainfall_mm"] = max(merged_feat["kharif_rainfall_mm"], 1200.0)

        if temp_cond == "hot" or season.lower() == "summer":
            merged_feat["mean_temperature_c"] = max(merged_feat["mean_temperature_c"], 33.0)
            merged_feat["max_temperature_c"] = max(merged_feat["max_temperature_c"], 41.0)
        elif temp_cond == "cold" or season.lower() == "rabi":
            merged_feat["mean_temperature_c"] = min(merged_feat["mean_temperature_c"], 21.0)
            merged_feat["min_temperature_c"] = min(merged_feat["min_temperature_c"], 12.0)

        # Get ML probabilities for active model version (v1 or v2)
        ml_probs = self.get_model_probabilities(merged_feat, season, soil_type, defaults)

        # Construct farm context evaluation dict for AgriculturalEngine
        eval_context = {
            "state": state,
            "district": district,
            "soil_type": soil_type,
            "season": season,
            "water_availability": features.get("water_availability"),
            "irrigation_type": irrigation_type,
            "water_source": water_source,
            "has_drip": has_drip,
            "has_borewell": has_borewell,
            "rainfall_condition": rain_cond,
            "temperature_condition": temp_cond,
            "weather_condition": features.get("weather_condition") or rain_cond,
            "ph": merged_feat["ph"],
            "clay_pct": merged_feat["clay_pct"],
            "sand_pct": merged_feat["sand_pct"],
            "silt_pct": merged_feat["silt_pct"],
            "nitrogen_cg_kg": merged_feat["nitrogen_cg_kg"],
            "annual_rainfall_mm": merged_feat["annual_rainfall_mm"],
            "mean_temperature_c": merged_feat["mean_temperature_c"],
        }

        # Resolve candidate crops across all 28 dataset classes
        candidate_crops = features.get("candidate_crops")
        if not candidate_crops:
            candidate_crops = list(agricultural_engine.profiles.keys())

        # Exclude explicit negative crop facts if supplied
        negative_crops = features.get("negative_crops") or []
        if negative_crops:
            neg_lower = [str(nc).lower().strip() for nc in negative_crops]
            candidate_crops = [c for c in candidate_crops if not any(nl in c.lower() for nl in neg_lower)]

        # Central suitability ranking via AgriculturalEngine
        engine_results = agricultural_engine.rank_crops(
            farm_context=eval_context,
            candidate_crops=candidate_crops,
            ml_probabilities=ml_probs,
            top_k=len(candidate_crops)
        )

        if not engine_results:
            # Safe fallback if candidate_crops is empty
            engine_results = agricultural_engine.rank_crops(
                farm_context=eval_context,
                ml_probabilities=ml_probs,
                top_k=4
            )

        primary = engine_results[0]
        primary_crop = primary["crop"]
        primary_score = primary["overall_score"]

        exp = self.explainability_engine.explain_recommendation(
            primary_crop,
            merged_feat,
            irrigation_type=irrigation_type,
            water_source=water_source,
            season=season,
            rainfall_condition=rain_cond,
            temperature_condition=temp_cond
        )

        # Merge supporting factors & limitations between AgriculturalEngine and ExplainabilityEngine
        primary_supporting = list(primary.get("supporting_factors", []))
        for sf in exp.get("supporting_factors", []):
            if sf not in primary_supporting:
                primary_supporting.append(sf)

        primary_limitations = list(primary.get("limitations", []))
        for lim in exp.get("potential_limitations", []):
            if lim not in primary_limitations:
                primary_limitations.append(lim)

        if primary_score >= 85.0:
            conf_level = "High"
        elif primary_score >= 70.0:
            conf_level = "Medium"
        else:
            conf_level = "Low"

        opt_ranges = exp.get("optimal_ranges", {})
        clay_opt = opt_ranges.get("clay_pct_optimal", [20.0, 45.0])
        ph_opt = opt_ranges.get("ph_optimal", [6.0, 7.8])
        rain_opt = opt_ranges.get("rainfall_optimal_mm", [600.0, 1200.0])
        temp_opt = opt_ranges.get("temp_optimal_c", [20.0, 32.0])

        alternatives = []
        for alt in engine_results[1:top_k]:
            alt_crop = alt["crop"]
            alt_score = alt["overall_score"]
            alt_exp = self.explainability_engine.explain_recommendation(
                alt_crop,
                merged_feat,
                irrigation_type=irrigation_type,
                water_source=water_source,
                season=season,
                rainfall_condition=rain_cond,
                temperature_condition=temp_cond
            )
            alt_factors = alt.get("supporting_factors") or alt_exp.get("supporting_factors", [])
            
            if alt_score >= 85.0:
                alt_conf = "High"
            elif alt_score >= 70.0:
                alt_conf = "Medium"
            else:
                alt_conf = "Low"

            alternatives.append({
                "crop": alt_crop,
                "suitability_score": alt_score,
                "confidence_level": alt_conf,
                "supporting_factors": alt_factors,
                "water_assessment": alt_exp.get("water_assessment", {}),
                "key_advantage": alt_factors[0] if alt_factors else "High regional yield track record"
            })

        # Prepare factor scores with both AgriculturalEngine factor keys and legacy schema alias keys
        engine_factor_scores = primary.get("factor_scores", {})
        combined_factor_scores = {
            # AgriculturalEngine 9-factor scores
            "soil": engine_factor_scores.get("soil", 80.0),
            "climate": engine_factor_scores.get("climate", 80.0),
            "temperature": engine_factor_scores.get("temperature", 80.0),
            "nutrients": engine_factor_scores.get("nutrients", 80.0),
            "season": engine_factor_scores.get("season", 80.0),
            "water": engine_factor_scores.get("water", 80.0),
            "weather": engine_factor_scores.get("weather", 80.0),
            "regional": engine_factor_scores.get("regional", 80.0),
            "ml_evidence": engine_factor_scores.get("ml_evidence", 80.0),
            # Schema compatibility alias keys
            "soil_suitability": engine_factor_scores.get("soil", 80.0),
            "rainfall_suitability": engine_factor_scores.get("climate", 80.0),
            "temperature_suitability": engine_factor_scores.get("temperature", 80.0),
            "ph_suitability": engine_factor_scores.get("soil", 80.0),
            "nutrient_suitability": engine_factor_scores.get("nutrients", 80.0),
        }

        return {
            "success": True,
            "resolved_context": dict(features),
            "primary_recommendation": {
                "crop": primary_crop,
                "agronomic_suitability_score": primary_score,
                "confidence_score_pct": primary_score,
                "confidence_level": conf_level,
                "supporting_factors": primary_supporting,
                "potential_limitations": primary_limitations,
                "factor_scores": combined_factor_scores,
                "radar_scores": exp.get("radar_scores", {}),
                "water_assessment": exp.get("water_assessment", {}),
                "sources": exp.get("sources", []),
                "soil_analysis": {
                    "clay_pct": merged_feat["clay_pct"],
                    "ph": merged_feat["ph"],
                    "clay_optimal_range": f"{clay_opt[0]}–{clay_opt[1]}%",
                    "ph_optimal_range": f"{ph_opt[0]}–{ph_opt[1]}"
                },
                "climate_analysis": {
                    "rainfall_mm": merged_feat["annual_rainfall_mm"],
                    "rainfall_optimal_range": f"{rain_opt[0]}–{rain_opt[1]} mm",
                    "temperature_c": merged_feat["mean_temperature_c"],
                    "temp_optimal_range": f"{temp_opt[0]}–{temp_opt[1]}°C"
                }
            },
            "alternative_crops": alternatives,
            "location_context": {
                "state": state,
                "district": district,
                "soil_group": soil_type,
                "farm_size_acres": farm_size,
                "irrigation_type": irrigation_type,
                "water_source": water_source,
                "season": season,
                "rainfall_condition": rain_cond,
                "temperature_condition": temp_cond,
                "mean_rainfall_mm": merged_feat["annual_rainfall_mm"],
                "mean_temperature_c": merged_feat["mean_temperature_c"],
                "live_weather": features.get("live_weather")
            },
            "sources": [
                {"name": "Crop Expert Dataset", "category": "agronomy", "why_used": "Crop suitability and water requirements"},
                {"name": "Soil Expert Dataset", "category": "soil", "why_used": "Physicochemical soil matching"},
                {"name": "Weather Expert Dataset", "category": "climate", "why_used": "District rainfall and thermal ranges"},
                {"name": "Master Geography Dataset", "category": "geography", "why_used": f"Agricultural profile for {district}, {state}"}
            ]
        }


# Singleton instance
recommender = CropRecommender()
