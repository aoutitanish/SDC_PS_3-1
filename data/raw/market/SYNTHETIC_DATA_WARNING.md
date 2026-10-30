# ⚠️ SYNTHETIC DATA QUARANTINE WARNING: Mandi Market Prices

## Dataset Classification: SYNTHETIC BENCHMARK ONLY
- **File**: `data/raw/market/raw_agmarknet_historical.json`
- **Total Records**: 20,164 records
- **Origin**: Programmatically synthesized by `scripts/acquire_historical_mandi_data.py` using baseline CACP MSP benchmarks and sinusoidal seasonal formulas.
- **Date Generated**: Phase 6B historical market pipeline.

## MANDATORY USAGE POLICY
1. **NEVER USE FOR PRODUCTION RECOMMENDATION**: These records represent synthetic telemetry and must not be fed to farmer-facing decision logic.
2. **NEVER USE FOR MODEL TRAINING**: Do not train or fine-tune machine learning models (e.g. crop recommendation, price forecasting) on these records.
3. **NEVER USE FOR REAL-WORLD EVALUATION**: Backtesting or benchmarking against these synthetic records does not reflect real APMC mandi market price dynamics.
4. **DO NOT SUBSTITUTE MSP FOR MANDI PRICE**: Minimum Support Price (MSP) is a policy floor, not an equilibrium mandi transaction price.

## REAL AGMARKNET ACQUISITION
To acquire genuine, real-time APMC wholesale price arrivals:
- Follow configuration instructions in `data/raw/market/AGMARKNET_SETUP.md`.
- Register at `https://data.gov.in/user/register` to receive an API key.
- Execute `python scripts/acquire_agmarknet_ogd.py`.
