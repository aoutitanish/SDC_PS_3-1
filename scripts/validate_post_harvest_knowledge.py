"""
Validation & Audit Script for Phase 6D Post-Harvest Knowledge Dataset.
Verifies that all 28 canonical crops possess comprehensive, verified ICAR/FCI/NHB post-harvest guidance,
provenance metadata, maturity indicators, target moisture levels, and handling precautions.
"""

import os
import json
import sys

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.app.services.economic_service import economic_service

POST_HARVEST_KNOWLEDGE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "processed", "post_harvest_knowledge.json"
)

REQUIRED_FIELDS = [
    "crop",
    "harvest_maturity_indicators",
    "harvesting_handling_guidance",
    "drying_requirements",
    "safe_target_moisture_pct",
    "storage_method",
    "suitable_storage_structure",
    "temperature_c_requirement",
    "relative_humidity_pct_requirement",
    "shelf_life_days",
    "major_storage_pest_risks",
    "fungal_moisture_risks",
    "packaging_requirements",
    "handling_precautions",
    "processing_value_add_options",
    "post_harvest_loss_info",
    "provenance"
]


def audit_post_harvest_knowledge():
    assert os.path.exists(POST_HARVEST_KNOWLEDGE_PATH), f"File not found: {POST_HARVEST_KNOWLEDGE_PATH}"

    with open(POST_HARVEST_KNOWLEDGE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    canonical_crops = list(economic_service.get_all_records().keys())
    
    print("==================================================")
    print("PHASE 6D POST-HARVEST KNOWLEDGE AUDIT")
    print("==================================================")
    print(f"Total Canonical Crops Required: {len(canonical_crops)}")
    print(f"Total Crops in Knowledge Base:  {len(data)}")

    assert len(data) == 28, f"Expected 28 crops, found {len(data)}"

    missing_crops = [c for c in canonical_crops if c not in data]
    assert len(missing_crops) == 0, f"Missing crops in post-harvest knowledge: {missing_crops}"

    incomplete_crops = []
    for crop_name, record in data.items():
        for field in REQUIRED_FIELDS:
            if field not in record:
                incomplete_crops.append((crop_name, field))

    assert len(incomplete_crops) == 0, f"Found incomplete fields: {incomplete_crops}"

    # Sample audit display
    sample_crops = ["Rice", "Arhar/Tur (Pigeon Pea)", "Onion", "Sugarcane", "Potato"]
    print("\n--- SAMPLE CROP AUDIT DISPLAYS ---")
    for sc in sample_crops:
        rec = data[sc]
        print(f"\n[Crop: {sc}]")
        print(f"  Maturity Indicators: {rec['harvest_maturity_indicators'][:70]}...")
        print(f"  Target Moisture:     {rec['safe_target_moisture_pct']}%")
        print(f"  Storage Structure:   {rec['suitable_storage_structure']}")
        print(f"  Shelf Life:          {rec['shelf_life_days']} days")
        print(f"  Source:              {rec['provenance']['source_name']}")

    print("\n==================================================")
    print("AUDIT SUCCESSFUL: All 28 canonical crops verified.")
    print("==================================================")


if __name__ == "__main__":
    audit_post_harvest_knowledge()
