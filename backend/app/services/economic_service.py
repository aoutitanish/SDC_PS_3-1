"""
Economic Data Foundation Service for KrishiMitra AI.
Loads verified official economic benchmarks (MSP, Cost of Cultivation, Post-Harvest Storage)
and handles crop-name normalization and Agmarknet commodity crosswalk lookups.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "data", "processed")
ECONOMICS_PATH = os.path.join(DATA_DIR, "crop_economics.json")


class EconomicService:
    def __init__(self, data_path: Optional[str] = None):
        self.path = data_path or ECONOMICS_PATH
        self._economics_data: Dict[str, Any] = {}
        self._alias_map: Dict[str, str] = {}
        self._load_data()

    def _load_data(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self._economics_data = json.load(f)
                
                # Build alias normalization index
                for canonical_name, rec in self._economics_data.items():
                    self._alias_map[canonical_name.lower().strip()] = canonical_name
                    aliases = rec.get("commodity_aliases", [])
                    for alias in aliases:
                        a_clean = alias.lower().strip()
                        if a_clean not in self._alias_map:
                            self._alias_map[a_clean] = canonical_name
                logger.info(f"Loaded {len(self._economics_data)} crop economic profiles and {len(self._alias_map)} alias mappings.")
            except Exception as e:
                logger.warning(f"Failed to load crop economics dataset from {self.path}: {e}")

    def normalize_crop_name(self, query: str) -> Optional[str]:
        """Maps an internal crop name, alias, or commodity name to canonical crop name."""
        if not query or not isinstance(query, str):
            return None
        q_clean = query.lower().strip()
        if q_clean in self._alias_map:
            return self._alias_map[q_clean]

        # Partial substring match across canonical names and aliases
        for alias_clean, canonical in self._alias_map.items():
            if q_clean in alias_clean or alias_clean in q_clean:
                return canonical

        return None

    def get_crop_economics(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves economic profile for a given crop name or commodity alias.
        Returns None for unknown crops or if data is unrecorded.
        """
        canonical = self.normalize_crop_name(query)
        if canonical and canonical in self._economics_data:
            return self._economics_data[canonical]
        return None

    def get_commodity_aliases(self, crop_name: str) -> List[str]:
        """Returns official Agmarknet/eNAM commodity aliases for a crop."""
        rec = self.get_crop_economics(crop_name)
        if rec:
            return rec.get("commodity_aliases", [])
        return []

    def get_all_records(self) -> Dict[str, Any]:
        """Returns full dataset of crop economics."""
        return self._economics_data


# Singleton instance
economic_service = EconomicService()
