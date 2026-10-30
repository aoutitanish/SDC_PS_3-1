# ⚠️ SYNTHETIC DATA QUARANTINE WARNING: Processed Mandi Data

## Dataset Classification: SYNTHETIC BENCHMARK ONLY
- **Files**:
  - `data/processed/historical_market/historical_mandi_prices.json` (20,160 records, 9.7 MB)
  - `data/processed/historical_market/data_quality_report.json`
- **Origin**: Derived directly from `data/raw/market/raw_agmarknet_historical.json`.
- **Reason**: Generated programmatically from sinusoidal price formulas seeded by CACP price benchmarks.

## PROHIBITIONS
- 🚫 **Model Training Prohibited**: Must NEVER be used as training targets or features.
- 🚫 **Real Evaluation Prohibited**: Must NEVER be cited as historical empirical evidence.
- 🚫 **Production API Prohibited**: Live advice systems must not pull from this directory.

## OFFICIAL REAL DATA ALTERNATIVE
- See `data/raw/market/AGMARKNET_SETUP.md` for fetching official APMC transaction records from the Open Government Data (OGD) platform (Resource ID: `9ef84268-d588-465a-a308-a864a43d0070`).
