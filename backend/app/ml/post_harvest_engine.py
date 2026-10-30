"""
Post-Harvest Intelligence Engine for KrishiMitra AI.
Provides structured, deterministic post-harvest guidance and storage advisories derived
exclusively from official verified data in crop_economics.json.

STRICT CONSTRAINTS:
- NEVER invent storage facts, moisture targets, shelf-life values, or future market prices.
- NEVER calculate speculative future profit or store-vs-sell profit gains without verified storage cost/future price data.
- MUST NOT modify or rerank AgriculturalEngine or EconomicEngine outputs.
- Never use forbidden terms like 'guaranteed shelf life', 'guaranteed profit', or 'guaranteed price increase'.
"""

import logging
from typing import Dict, Any, List, Optional
from backend.app.services.economic_service import economic_service

logger = logging.getLogger(__name__)

SAFETY_DISCLAIMER = (
    "Recommended under cited reference conditions. Actual shelf life and storage quality "
    "depend on ambient humidity, pest control, and local facility management."
)


class PostHarvestEngine:
    """
    Deterministic post-harvest advisory engine.
    Reads verified post_harvest_storage benchmarks from EconomicService.
    """

    def get_post_harvest_advisory(
        self,
        crop: str,
        farm_size_acres: Optional[float] = None,
        harvest_quantity_quintals: Optional[float] = None,
        current_price: Optional[float] = None,
        price_data_type: Optional[str] = None,
        storage_available: Optional[bool] = None,
        storage_type: Optional[str] = None,
        farmer_goal: Optional[str] = None,
        economic_result: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Retrieves post-harvest profile and builds structured advisory guidance.
        Farmer goal options: 'sell_now', 'store', 'process', 'compare_options', or None.
        """
        # 1. Resolve canonical crop name & economics record
        canonical_crop = economic_service.normalize_crop_name(crop)
        if not canonical_crop:
            return self._build_unknown_crop_response(crop)

        econ_data = economic_service.get_crop_economics(canonical_crop)
        if not econ_data or "post_harvest_storage" not in econ_data:
            return self._build_missing_data_response(canonical_crop)

        ph_data = econ_data.get("post_harvest_storage", {})

        # 2. Extract verified storage fields and metadata
        storage_method = ph_data.get("storage_method")
        shelf_life_days = ph_data.get("shelf_life_days")
        optimal_moisture_pct = ph_data.get("optimal_moisture_pct")
        source = ph_data.get("source", "Official ICAR / FCI Guidelines")
        source_url = ph_data.get("source_url", "")
        data_type = ph_data.get("data_type", "official")
        year_ref = ph_data.get("year", "2024-25 Reference")

        # Missing field check
        missing_fields = []
        if storage_method is None:
            missing_fields.append("storage_method")
        if shelf_life_days is None:
            missing_fields.append("shelf_life_days")
        if optimal_moisture_pct is None:
            missing_fields.append("optimal_moisture_pct")

        # 3. Determine perishability category based strictly on verified shelf life
        perishability = self._classify_perishability(shelf_life_days)

        # 4. Build post-harvest storage profile
        storage_profile = {
            "crop": canonical_crop,
            "storage_method": storage_method,
            "shelf_life_days": shelf_life_days,
            "optimal_moisture_pct": optimal_moisture_pct,
            "perishability": perishability,
            "source": source,
            "source_url": source_url,
            "data_type": data_type,
            "reference_year": year_ref
        }

        # 5. Build storage advisory guidance
        advisory = {
            "storage_recommendation": f"Recommended storage method: {storage_method}" if storage_method else "Storage method details unavailable.",
            "moisture_target": f"Target moisture level: {optimal_moisture_pct}%" if optimal_moisture_pct is not None else "Moisture target unspecified.",
            "shelf_life_days": shelf_life_days,
            "handling_notes": (
                f"Ensure crop is dried to optimal moisture content of {optimal_moisture_pct}% prior to bagging/storing "
                f"to prevent fungal growth and pest infestation."
            ) if optimal_moisture_pct is not None else "Ensure proper drying and aeration prior to storage.",
            "storage_risk": (
                "High risk of rapid spoilage if stored moist." if perishability in ["high", "medium"]
                else "Moderate to low risk when stored under dry, ventilated conditions."
            )
        }

        # 6. Build sell vs store comparison framework (no speculative future profit)
        sell_vs_store = self._build_sell_vs_store_framework(
            harvest_quantity_quintals=harvest_quantity_quintals,
            current_price=current_price,
            storage_method=storage_method,
            shelf_life_days=shelf_life_days,
            optimal_moisture_pct=optimal_moisture_pct
        )

        # 7. Processing options (strictly empty if not verified in dataset)
        processing_options = ph_data.get("processing_options", [])

        # 8. Assemble structured response
        response = {
            "status": "success" if not missing_fields else "partially_available",
            "crop": canonical_crop,
            "farmer_goal": farmer_goal,
            "missing_fields": missing_fields,
            "post_harvest_profile": storage_profile,
            "storage_advisory": advisory,
            "sell_vs_store_comparison": sell_vs_store,
            "processing_options": processing_options,
            "economic_reference": economic_result,  # Kept separate, unmodified
            "provenance": {
                "source": source,
                "source_url": source_url,
                "data_type": data_type,
                "reference_year": year_ref,
                "disclaimer": SAFETY_DISCLAIMER
            }
        }

        return response

    @staticmethod
    def _classify_perishability(shelf_life_days: Optional[int]) -> str:
        """Classifies perishability based ONLY on verified shelf_life_days."""
        if shelf_life_days is None or not isinstance(shelf_life_days, (int, float)):
            return "unknown"
        if shelf_life_days < 30:
            return "high"
        elif shelf_life_days <= 120:
            return "medium"
        else:
            return "low"

    def _build_sell_vs_store_framework(
        self,
        harvest_quantity_quintals: Optional[float],
        current_price: Optional[float],
        storage_method: Optional[str],
        shelf_life_days: Optional[int],
        optimal_moisture_pct: Optional[float]
    ) -> Dict[str, Any]:
        """
        Constructs evidence-bounded sell vs store framework.
        If historical monthly wholesale price data is unavailable, returns comparison_status = 'unavailable'
        with explicit limitation message to avoid speculative profit or seasonal appreciation calculations.
        """
        sell_now_data = {
            "label": "Current sale-value estimate",
            "available_price_inr_per_quintal": current_price,
            "estimated_production_quantity_quintals": harvest_quantity_quintals,
            "estimated_revenue_inr": (
                round(harvest_quantity_quintals * current_price, 2)
                if (harvest_quantity_quintals is not None and current_price is not None)
                else None
            ),
            "is_recommendation": False
        }

        store_data = {
            "label": "Store Information",
            "storage_method": storage_method,
            "target_moisture_pct": optimal_moisture_pct,
            "shelf_life_days": shelf_life_days,
            "storage_requirements": (
                f"Maintain moisture content at or below {optimal_moisture_pct}% under {storage_method}."
                if (optimal_moisture_pct is not None and storage_method)
                else "Follow standard warehouse dry-storage protocol."
            ),
            "disclaimer": "Storage details provided for guidance only. Storing does not guarantee a higher financial return."
        }

        return {
            "comparison_status": "unavailable",
            "reason": (
                "Sell-vs-store financial comparison unavailable: historical monthly "
                "wholesale-price data is required to estimate future seasonal price movement."
            ),
            "sell_now": sell_now_data,
            "store": store_data,
            "speculative_future_profit_calculated": False,
            "seasonal_appreciation_calculated": False
        }

    def _build_unknown_crop_response(self, crop: str) -> Dict[str, Any]:
        """Structured response for unrecognized crop names."""
        return {
            "status": "unavailable",
            "crop": crop,
            "error": f"Crop '{crop}' not recognized in agricultural database.",
            "post_harvest_profile": None,
            "storage_advisory": None,
            "sell_vs_store_comparison": None,
            "processing_options": [],
            "provenance": {
                "source": "None",
                "source_url": "",
                "data_type": "unavailable",
                "disclaimer": SAFETY_DISCLAIMER
            }
        }

    def _build_missing_data_response(self, crop: str) -> Dict[str, Any]:
        """Structured response when post-harvest data is unrecorded for a crop."""
        return {
            "status": "partially_available",
            "crop": crop,
            "missing_fields": ["post_harvest_storage"],
            "post_harvest_profile": {
                "crop": crop,
                "storage_method": None,
                "shelf_life_days": None,
                "optimal_moisture_pct": None,
                "perishability": "unknown",
                "source": "None",
                "source_url": "",
                "data_type": "unavailable",
                "reference_year": "N/A"
            },
            "storage_advisory": None,
            "sell_vs_store_comparison": None,
            "processing_options": [],
            "provenance": {
                "source": "None",
                "source_url": "",
                "data_type": "unavailable",
                "disclaimer": SAFETY_DISCLAIMER
            }
        }


# Singleton instance
post_harvest_engine = PostHarvestEngine()
