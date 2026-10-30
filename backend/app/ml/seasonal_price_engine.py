"""
Seasonal Price Engine Interface for KrishiMitra AI.
Isolated future-ready service interface for historical monthly wholesale-price data,
seasonal price indexing, expected price movements, and storage-adjusted values.

EVIDENCE-BOUNDED PRINCIPLE:
When verified historical monthly wholesale price datasets are unavailable, this engine
returns an explicit unavailable state and DOES NOT generate synthetic/speculative
price movements or store-vs-sell recommendations.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

UNAVAILABLE_REASON = (
    "Sell-vs-store financial comparison unavailable: historical monthly "
    "wholesale-price data is required to estimate future seasonal price movement."
)


class SeasonalPriceEngine:
    """
    Isolated interface/service for future:
    Historical monthly wholesale prices -> Seasonal price index -> Expected price movement -> Storage-adjusted value.
    """

    def __init__(self, historical_dataset_path: Optional[str] = None):
        self.historical_dataset_path = historical_dataset_path
        self._is_data_available = False  # Set to False until verified real historical dataset is plugged in

    def get_seasonal_analysis(
        self,
        crop: str,
        state: Optional[str] = None,
        district: Optional[str] = None,
        current_price: Optional[float] = None,
        harvest_quantity_quintals: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Returns seasonal analysis object.
        Currently returns an explicit evidence-bounded unavailable state.
        """
        if not self._is_data_available:
            return {
                "available": False,
                "reason": UNAVAILABLE_REASON,
                "crop": crop,
                "state": state,
                "district": district,
                "seasonal_index_calculated": False,
                "historical_monthly_data_status": "unavailable",
                "expected_price_movement": None,
                "storage_adjusted_value": None,
                "financial_recommendation": None,
                "provenance": {
                    "source": "None (Historical wholesale monthly data unavailable)",
                    "data_type": "unavailable",
                    "note": "Requires official multi-year monthly wholesale price series"
                }
            }

        # Future implementation when verified historical monthly dataset is plugged in:
        # 1. Load historical monthly series for crop/state/district
        # 2. Calculate 12-month seasonal price index (S_m)
        # 3. Compute expected price movement and holding period gain
        # 4. Deduct warehouse storage costs and physical loss %
        # 5. Return storage-adjusted value object
        raise NotImplementedError("Historical monthly wholesale-price dataset not yet plugged in.")


# Singleton instance
seasonal_price_engine = SeasonalPriceEngine()
