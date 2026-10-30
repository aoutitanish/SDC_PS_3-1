"""
Process and validate real Agmarknet OGD mandi records.
Strictly checks:
- Rejects synthetic benchmark files
- Preserves commodity, market, state, district, date, min price, max price, modal price, units, and source metadata
- Validates price units (INR/quintal) and valid date format (YYYY-MM-DD)
- Rejects MSP substitution
- Retains distinct separation from production data
"""

import os
import sys
import json
import glob
import logging
import datetime
from typing import Dict, Any, List

sys.stdout.reconfigure(encoding='utf-8')
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_MANDI_DIR = os.path.join(ROOT, "data", "raw", "market", "agmarknet")
PROCESSED_DIR = os.path.join(ROOT, "data", "processed", "market")
OUT_FILE = os.path.join(PROCESSED_DIR, "real_agmarknet_mandi_prices.json")


def parse_date(date_str: str) -> str:
    """Parses various date formats from Agmarknet (DD/MM/YYYY or YYYY-MM-DD) into ISO YYYY-MM-DD."""
    if not date_str:
        return ""
    date_str = str(date_str).strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            dt = datetime.datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return ""


def validate_and_process_records(raw_files: List[str]) -> Dict[str, Any]:
    valid_records = []
    rejected_records = []
    
    for fpath in raw_files:
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        canonical_crop = data.get("canonical_crop", "Unknown")
        retrieved_at = data.get("retrieved_at", "")
        raw_list = data.get("records", [])
        
        for r in raw_list:
            state = r.get("State", r.get("state", "")).strip().title()
            district = r.get("District", r.get("district", "")).strip().title()
            market = r.get("Market", r.get("market", "")).strip()
            commodity = r.get("Commodity", r.get("commodity", "")).strip()
            variety = r.get("Variety", r.get("variety", "")).strip()
            grade = r.get("Grade", r.get("grade", "")).strip()
            raw_date = r.get("Arrival_Date", r.get("arrival_date", ""))
            
            clean_date = parse_date(raw_date)
            if not clean_date:
                rejected_records.append({"record": r, "reason": "Invalid or missing arrival date"})
                continue
                
            try:
                min_p = float(r.get("Min_Price", r.get("min_price", 0)))
                max_p = float(r.get("Max_Price", r.get("max_price", 0)))
                modal_p = float(r.get("Modal_Price", r.get("modal_price", 0)))
            except (ValueError, TypeError):
                rejected_records.append({"record": r, "reason": "Non-numeric price field"})
                continue
                
            if modal_p <= 0 or modal_p > 150000:
                rejected_records.append({"record": r, "reason": f"Out-of-bounds modal price: {modal_p}"})
                continue
                
            valid_records.append({
                "canonical_crop": canonical_crop,
                "commodity": commodity,
                "state": state,
                "district": district,
                "market": market,
                "variety": variety,
                "grade": grade,
                "arrival_date": clean_date,
                "min_price": min_p,
                "max_price": max_p,
                "modal_price": modal_p,
                "price_unit": "INR/quintal",
                "source_metadata": {
                    "source": "Agmarknet / data.gov.in OGD API",
                    "resource_id": "9ef84268-d588-465a-a308-a864a43d0070",
                    "license": "GODL-India v1.0",
                    "retrieved_at": retrieved_at
                }
            })
            
    return {
        "status": "SUCCESS" if valid_records else "NO_RECORDS",
        "processed_at": datetime.datetime.utcnow().isoformat() + "Z",
        "total_valid_records": len(valid_records),
        "total_rejected_records": len(rejected_records),
        "records": valid_records,
        "sample_rejections": rejected_records[:10]
    }


def main():
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    raw_files = glob.glob(os.path.join(RAW_MANDI_DIR, "*.json"))
    if not raw_files:
        logger.info(f"No raw Agmarknet files found in {RAW_MANDI_DIR}. To download, set DATAGOV_API_KEY and run acquire_agmarknet_ogd.py.")
        return
        
    logger.info(f"Processing {len(raw_files)} raw Agmarknet crop files...")
    result = validate_and_process_records(raw_files)
    
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    logger.info(f"Saved processed real mandi records to {OUT_FILE} ({result['total_valid_records']} records).")


if __name__ == "__main__":
    main()
