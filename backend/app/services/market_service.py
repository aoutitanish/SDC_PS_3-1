"""
Market Telemetry Service for KrishiMitra AI.
Retrieves and normalizes live market price telemetry from Agmarknet / data.gov.in,
manages SQLite market_price_cache, and resolves crop names via the 28-crop / 71-alias crosswalk.

STRICT CONSTRAINTS:
- NEVER generate or invent a market price.
- NEVER use Qwen for prices.
- NEVER substitute MSP for a live mandi price.
- Return status 'unavailable' with empty markets when live fetch and cache are unavailable.
"""

import logging
import datetime
from typing import Dict, Any, List, Optional
import httpx

from backend.app.core.config import settings
from backend.app.core.database import get_db_connection
from backend.app.services.economic_service import economic_service

logger = logging.getLogger(__name__)


class MarketService:
    def __init__(self):
        self.api_key = getattr(settings, "DATA_GOV_API_KEY", "") or ""
        self.resource_id = "9ef74d57-d1d5-435a-9110-8128e4411739"

    def get_market_cache(self, state: Optional[str], district: Optional[str], commodity_names: List[str]) -> List[Dict[str, Any]]:
        """Retrieves cached mandi records from SQLite database for given state/district/commodity."""
        if not commodity_names:
            return []

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            st_clean = (state or "").lower().strip()
            dist_clean = (district or "").lower().strip()
            comm_lower = [c.lower().strip() for c in commodity_names]

            placeholders = ",".join(["?"] * len(comm_lower))
            query = f"""
                SELECT state, district, mandi_name, commodity_name, min_price, max_price, modal_price, price_unit, arrival_date, data_source, cached_at
                FROM market_price_cache
                WHERE (LOWER(state) = ? OR LOWER(district) = ? OR ? = '' OR ? = '')
                  AND LOWER(commodity_name) IN ({placeholders})
                ORDER BY cached_at DESC
            """
            params = [st_clean, dist_clean, st_clean, dist_clean] + comm_lower
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            cached = []
            for r in rows:
                cached.append({
                    "mandi_name": r["mandi_name"],
                    "commodity_name": r["commodity_name"],
                    "state": r["state"],
                    "district": r["district"],
                    "min_price": float(r["min_price"]),
                    "max_price": float(r["max_price"]),
                    "modal_price": float(r["modal_price"]),
                    "price_unit": r["price_unit"] or "INR/quintal",
                    "arrival_date": r["arrival_date"],
                    "data_source": r["data_source"] or "Agmarknet Cached Telemetry",
                    "data_type": "cached",
                    "cached_at": r["cached_at"]
                })
            return cached
        except Exception as e:
            logger.warning(f"Error reading from market_price_cache: {e}")
            return []

    def save_market_cache(self, records: List[Dict[str, Any]]):
        """Saves successful market responses into SQLite market_price_cache."""
        if not records:
            return

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            for r in records:
                cursor.execute("""
                    INSERT OR REPLACE INTO market_price_cache
                    (state, district, mandi_name, commodity_name, min_price, max_price, modal_price, price_unit, arrival_date, data_source, data_type, cached_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'cached', CURRENT_TIMESTAMP)
                """, (
                    r.get("state"),
                    r.get("district"),
                    r.get("mandi_name"),
                    r.get("commodity_name"),
                    r.get("min_price"),
                    r.get("max_price"),
                    r.get("modal_price"),
                    r.get("price_unit", "INR/quintal"),
                    r.get("arrival_date"),
                    r.get("data_source", "Agmarknet Live Mandi Service")
                ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"Error writing to market_price_cache: {e}")

    async def get_market_prices(
        self,
        crop: str,
        state: Optional[str] = None,
        district: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieves live or cached market prices for a crop and location.
        Returns safe structured 'unavailable' status when live API and cache have no records.
        NEVER invents, estimates, or substitutes MSP for market prices.
        """
        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # 1. Resolve crop name & aliases via EconomicService crosswalk
        canonical_crop = economic_service.normalize_crop_name(crop)
        if not canonical_crop:
            return {
                "status": "unavailable",
                "crop": crop,
                "commodity": None,
                "location": {"state": state or "", "district": district or ""},
                "markets": [],
                "error": f"Crop '{crop}' not recognized in agricultural dataset.",
                "data_source": "None",
                "data_type": "unavailable",
                "retrieved_at": now_str
            }

        aliases = economic_service.get_commodity_aliases(canonical_crop)
        primary_commodity = aliases[0] if aliases else canonical_crop

        # 2. Attempt live telemetry fetch from data.gov.in / Agmarknet
        live_records = []
        if self.api_key:
            try:
                url = (
                    f"https://api.data.gov.in/resource/{self.resource_id}"
                    f"?api-key={self.api_key}&format=json&limit=20"
                )
                if state:
                    url += f"&filters[state]={state}"
                if district:
                    url += f"&filters[district]={district}"

                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        data = resp.json()
                        records = data.get("records", [])
                        
                        # Filter by commodity aliases
                        comm_clean = [a.lower().strip() for a in aliases]
                        for r in records:
                            rec_comm = (r.get("commodity") or "").lower().strip()
                            if any(c in rec_comm or rec_comm in c for c in comm_clean):
                                try:
                                    live_records.append({
                                        "internal_crop_name": canonical_crop,
                                        "commodity_name": r.get("commodity", primary_commodity),
                                        "state": r.get("state", state),
                                        "district": r.get("district", district),
                                        "mandi_name": r.get("market", "Local Mandi"),
                                        "min_price": float(r.get("min_price", 0.0)),
                                        "max_price": float(r.get("max_price", 0.0)),
                                        "modal_price": float(r.get("modal_price", 0.0)),
                                        "price_unit": "INR/quintal",
                                        "arrival_date": r.get("arrival_date", ""),
                                        "data_source": "Agmarknet / data.gov.in Live Mandi Service",
                                        "data_type": "live",
                                        "retrieved_at": now_str
                                    })
                                except (ValueError, TypeError):
                                    continue
            except Exception as e:
                logger.warning(f"Live market API fetch failed: {e}. Checking cache.")

        # If live records were found, save to cache and return
        if live_records:
            self.save_market_cache(live_records)
            return {
                "status": "success",
                "crop": canonical_crop,
                "commodity": primary_commodity,
                "location": {"state": state or "", "district": district or ""},
                "markets": live_records,
                "data_source": "Agmarknet / data.gov.in Live Mandi Service",
                "data_type": "live",
                "retrieved_at": now_str
            }

        # 3. Check SQLite cache fallback
        cached_records = self.get_market_cache(state, district, aliases)
        if cached_records:
            return {
                "status": "success",
                "crop": canonical_crop,
                "commodity": primary_commodity,
                "location": {"state": state or "", "district": district or ""},
                "markets": cached_records,
                "data_source": cached_records[0].get("data_source", "Agmarknet Cached Telemetry"),
                "data_type": "cached",
                "retrieved_at": now_str
            }

        # 4. If live API & cache both unavailable: return safe structured unavailable response
        # NEVER invent prices, NEVER substitute MSP for mandi price
        return {
            "status": "unavailable",
            "crop": canonical_crop,
            "commodity": primary_commodity,
            "location": {"state": state or "", "district": district or ""},
            "markets": [],
            "data_source": "None",
            "data_type": "unavailable",
            "retrieved_at": now_str
        }


# Singleton instance
market_service = MarketService()
