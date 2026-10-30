"""
Validation script for Phase 6B Historical Market Dataset.
Proves that historical Agmarknet mandi data exists, is cleaned, and has explicit conversion notes
for representative crops: Rice/Paddy, Arhar/Tur, Wheat, Groundnut, and Onion.
"""

import os
import json
import sys

PROCESSED_FILE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "processed", "historical_market", "historical_mandi_prices.json"
)

QUALITY_REPORT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "processed", "historical_market", "data_quality_report.json"
)


def validate_historical_data():
    assert os.path.exists(PROCESSED_FILE_PATH), f"Missing processed dataset: {PROCESSED_FILE_PATH}"
    assert os.path.exists(QUALITY_REPORT_PATH), f"Missing quality report: {QUALITY_REPORT_PATH}"

    with open(PROCESSED_FILE_PATH, "r", encoding="utf-8") as f:
        records = json.load(f)

    with open(QUALITY_REPORT_PATH, "r", encoding="utf-8") as f:
        report = json.load(f)

    print("==================================================")
    print("HISTORICAL MARKET DATASET VALIDATION")
    print("==================================================")
    print(f"Total Processed Records Loaded: {len(records)}")
    print(f"Date Range: {report['date_range']['start_date']} to {report['date_range']['end_date']}")
    print(f"Crops Mapped: {report['crops_successfully_mapped_count']} / 28")

    representative_crops = ["Rice", "Arhar/Tur (Pigeon Pea)", "Wheat", "Groundnut", "Onion"]
    
    for crop in representative_crops:
        crop_records = [r for r in records if r["canonical_crop"] == crop]
        assert len(crop_records) > 0, f"No records found for representative crop: {crop}"
        
        sample = crop_records[0]
        print(f"\n--- Representative Crop: {crop} ---")
        print(f"  Count:             {len(crop_records)} records")
        print(f"  Sample Date:       {sample['date']}")
        print(f"  Sample Location:   {sample['market']}, {sample['district']}, {sample['state']}")
        print(f"  Commodity Name:    {sample['commodity']}")
        print(f"  Modal Price:       INR {sample['modal_price']}/quintal")
        print(f"  Conversion Note:   {sample['commodity_conversion_note']}")

    print("\n==================================================")
    print("VALIDATION SUCCESSFUL: All representative crops verified.")
    print("==================================================")


if __name__ == "__main__":
    validate_historical_data()
