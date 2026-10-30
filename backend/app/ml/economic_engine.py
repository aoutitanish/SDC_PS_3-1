"""
Economic Intelligence Engine for KrishiMitra AI.
Calculates economic metrics (production, gross revenue, cultivation cost, estimated net return,
gross margin %, break-even price, ROI) from explicitly supplied price/yield/cost inputs.

STRICT RULES:
- EconomicEngine MUST NOT modify or rerank AgriculturalEngine results.
- NEVER call the final result "guaranteed profit".
- Historical yield data must retain data_type: "historical".
- MSP must be labeled price_basis: "MSP reference" and price_data_type: "official".
- Live/Cached mandi prices must be labeled price_basis: "Mandi modal price".
- NEVER invent missing prices, yields, or costs.
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Constants for unit conversions
HECTARES_TO_ACRES = 2.47105
TONNES_TO_QUINTALS = 10.0
# 1 tonne/ha = 10 quintals / 2.47105 acres ≈ 4.04686267 quintals/acre
TONNES_PER_HA_TO_QUINTALS_PER_ACRE = TONNES_TO_QUINTALS / HECTARES_TO_ACRES

DISCLAIMER_TEXT = (
    "Illustrative economic estimate; actual returns vary based on local market "
    "fluctuations, weather conditions, and farm management practices."
)


class EconomicEngine:
    """
    Computes deterministic economic metrics and provenance metadata.
    Does NOT rank crops or modify agronomic suitability scores.
    """

    @staticmethod
    def convert_yield_to_quintals_per_acre(
        yield_tonnes_per_ha: Optional[float] = None,
        yield_quintals_per_acre: Optional[float] = None
    ) -> Optional[float]:
        """Converts yield from tonnes/ha to quintals/acre if needed."""
        if yield_quintals_per_acre is not None:
            return float(yield_quintals_per_acre)
        if yield_tonnes_per_ha is not None:
            return float(yield_tonnes_per_ha) * TONNES_PER_HA_TO_QUINTALS_PER_ACRE
        return None

    def calculate_crop_economics(
        self,
        crop: str,
        farm_size_acres: float,
        yield_tonnes_per_ha: Optional[float] = None,
        yield_quintals_per_acre: Optional[float] = None,
        price_inr_per_quintal: Optional[float] = None,
        cultivation_cost_inr_per_acre: Optional[float] = None,
        price_source: str = "Unspecified",
        price_data_type: str = "official",
        price_basis: Optional[str] = None,
        price_date: Optional[str] = None,
        yield_source: str = "Historical District Dataset",
        yield_data_type: str = "historical",
        yield_year: Optional[str] = "2017-2020 Benchmark",
        cost_source: str = "DES / CACP Govt Reports",
        cost_data_type: str = "official",
        cost_year: Optional[str] = "2024-25",
        agronomic_score: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calculates economic profile for a single crop given explicit inputs.
        Returns detailed metrics, missing data indicators, and complete provenance metadata.
        """
        # 1. Reject negative or invalid inputs
        if farm_size_acres is None or farm_size_acres < 0:
            return self._build_invalid_response(crop, "Farm size in acres must be non-negative.", agronomic_score)
        
        if farm_size_acres == 0:
            return self._build_invalid_response(crop, "Farm size in acres must be greater than zero for economic calculations.", agronomic_score)

        if yield_tonnes_per_ha is not None and yield_tonnes_per_ha < 0:
            return self._build_invalid_response(crop, "Yield value cannot be negative.", agronomic_score)
        
        if yield_quintals_per_acre is not None and yield_quintals_per_acre < 0:
            return self._build_invalid_response(crop, "Yield value cannot be negative.", agronomic_score)

        if price_inr_per_quintal is not None and price_inr_per_quintal < 0:
            return self._build_invalid_response(crop, "Price cannot be negative.", agronomic_score)

        if cultivation_cost_inr_per_acre is not None and cultivation_cost_inr_per_acre < 0:
            return self._build_invalid_response(crop, "Cultivation cost cannot be negative.", agronomic_score)

        # 2. Convert yield to quintals per acre
        final_yield_q_per_acre = self.convert_yield_to_quintals_per_acre(
            yield_tonnes_per_ha=yield_tonnes_per_ha,
            yield_quintals_per_acre=yield_quintals_per_acre
        )

        # 3. Determine price basis labeling if not explicitly provided
        if not price_basis:
            if price_data_type == "official":
                price_basis = "MSP reference"
            elif price_data_type in ["live", "cached"]:
                price_basis = "Mandi modal price"
            else:
                price_basis = "User input"

        # 4. Check for missing essential data
        has_yield = final_yield_q_per_acre is not None
        has_price = price_inr_per_quintal is not None
        has_cost = cultivation_cost_inr_per_acre is not None

        missing_fields = []
        if not has_yield:
            missing_fields.append("yield")
        if not has_price:
            missing_fields.append("price")
        if not has_cost:
            missing_fields.append("cost")

        # Provenance dictionary building
        yield_meta = {
            "value": round(final_yield_q_per_acre, 4) if has_yield else None,
            "unit": "quintals/acre",
            "yield_tonnes_per_ha": round(yield_tonnes_per_ha, 4) if yield_tonnes_per_ha is not None else None,
            "source": yield_source,
            "year": yield_year,
            "data_type": yield_data_type  # Strictly preserves 'historical'
        }

        price_meta = {
            "value": price_inr_per_quintal,
            "unit": "INR/quintal",
            "source": price_source,
            "price_basis": price_basis,
            "date": price_date,
            "data_type": price_data_type
        }

        cost_meta = {
            "value": cultivation_cost_inr_per_acre,
            "unit": "INR/acre",
            "source": cost_source,
            "year": cost_year,
            "data_type": cost_data_type
        }

        if missing_fields:
            return {
                "status": "partially_available" if (has_yield or has_price or has_cost) else "unavailable",
                "crop": crop,
                "agronomic_score": agronomic_score,
                "farm_size_acres": farm_size_acres,
                "missing_fields": missing_fields,
                "economic_metrics": None,
                "provenance": {
                    "yield": yield_meta,
                    "price": price_meta,
                    "cost": cost_meta,
                    "calculation": {
                        "data_type": "incomplete",
                        "metric_name": "Unavailable",
                        "disclaimer": f"Economic metrics cannot be fully calculated due to missing data: {', '.join(missing_fields)}."
                    }
                }
            }

        # 5. Execute calculations with complete inputs
        production_quintals = final_yield_q_per_acre * farm_size_acres
        gross_revenue = production_quintals * price_inr_per_quintal
        total_cost = cultivation_cost_inr_per_acre * farm_size_acres
        net_estimate = gross_revenue - total_cost

        gross_margin_pct = ((gross_revenue - total_cost) / gross_revenue * 100.0) if gross_revenue > 0 else None
        break_even_price = (total_cost / production_quintals) if production_quintals > 0 else None
        roi = ((net_estimate / total_cost) * 100.0) if total_cost > 0 else None

        economic_metrics = {
            "production_quintals": round(production_quintals, 2),
            "gross_revenue_inr": round(gross_revenue, 2),
            "total_cultivation_cost_inr": round(total_cost, 2),
            "estimated_net_return_inr": round(net_estimate, 2),
            "gross_margin_pct": round(gross_margin_pct, 2) if gross_margin_pct is not None else None,
            "break_even_price_inr_per_quintal": round(break_even_price, 2) if break_even_price is not None else None,
            "roi_pct": round(roi, 2) if roi is not None else None
        }

        return {
            "status": "success",
            "crop": crop,
            "agronomic_score": agronomic_score,  # Unchanged pass-through
            "farm_size_acres": farm_size_acres,
            "economic_metrics": economic_metrics,
            "provenance": {
                "yield": yield_meta,
                "price": price_meta,
                "cost": cost_meta,
                "calculation": {
                    "data_type": "estimated",
                    "metric_name": "Estimated net return",
                    "disclaimer": DISCLAIMER_TEXT
                }
            }
        }

    def calculate_multiple_crops(
        self,
        crop_items: List[Dict[str, Any]],
        farm_size_acres: float
    ) -> List[Dict[str, Any]]:
        """
        Calculates economic metrics for a list of crops independently.
        Does NOT alter the order or rank of the input list.
        """
        results = []
        for item in crop_items:
            res = self.calculate_crop_economics(
                crop=item.get("crop", "Unknown"),
                farm_size_acres=farm_size_acres,
                yield_tonnes_per_ha=item.get("yield_tonnes_per_ha"),
                yield_quintals_per_acre=item.get("yield_quintals_per_acre"),
                price_inr_per_quintal=item.get("price_inr_per_quintal"),
                cultivation_cost_inr_per_acre=item.get("cultivation_cost_inr_per_acre"),
                price_source=item.get("price_source", "Unspecified"),
                price_data_type=item.get("price_data_type", "official"),
                price_basis=item.get("price_basis"),
                price_date=item.get("price_date"),
                yield_source=item.get("yield_source", "Historical District Dataset"),
                yield_data_type=item.get("yield_data_type", "historical"),
                yield_year=item.get("yield_year", "2017-2020 Benchmark"),
                cost_source=item.get("cost_source", "DES / CACP Govt Reports"),
                cost_data_type=item.get("cost_data_type", "official"),
                cost_year=item.get("cost_year", "2024-25"),
                agronomic_score=item.get("agronomic_score")
            )
            results.append(res)
        return results

    def _build_invalid_response(
        self,
        crop: str,
        error_msg: str,
        agronomic_score: Optional[float] = None
    ) -> Dict[str, Any]:
        """Returns structured error response for invalid inputs."""
        return {
            "status": "invalid_input",
            "crop": crop,
            "agronomic_score": agronomic_score,
            "error": error_msg,
            "economic_metrics": None,
            "provenance": {
                "calculation": {
                    "data_type": "invalid",
                    "disclaimer": error_msg
                }
            }
        }


# Singleton instance
economic_engine = EconomicEngine()
