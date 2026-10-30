# KrishiMitra — Agricultural Dataset Foundation & Quality Catalogue

This repository contains the authoritative agricultural data foundation for **KrishiMitra AI**.  
**Phase 1 & Phase 2 Complete.**  
**No ML models have been retrained. The production recommendation logic remains strictly unchanged.**

---

## 1. Directory Structure

```
data/
├── raw/                          ← Original source files, unmodified
│   ├── crop_production/          ← DES APY PDF, structured JSON raw dump (D13)
│   │   └── des_apy_national_2015_2026_raw.json
│   ├── weather/
│   │   └── nasa_power_monthly_raw/  ← 20 pilot district NASA POWER JSON files (D12)
│   ├── soil/
│   │   └── soilgrids_raw/        ← Per-district SoilGrids JSON (when API accessible)
│   ├── economics/                ← CACP MSP, cost of cultivation benchmarks
│   └── market/
│       ├── agmarknet/            ← Real Agmarknet OGD downloads
│       ├── real_des_historical/  ← Official DES Time Series PDF (D10, 2014-15 to 2025-26)
│       ├── AGMARKNET_SETUP.md    ← Registration & API config guide for data.gov.in
│       ├── SYNTHETIC_DATA_WARNING.md ← ⚠️ Quarantine warning for synthetic mandi records
│       └── raw_agmarknet_historical.json ← ⚠️ QUARANTINED SYNTHETIC (20,164 records)
├── processed/                    ← Standardized, versioned datasets
│   ├── crop_production/
│   │   ├── des_national_production_2015_2026.csv ← D14: 11-yr national time series (682 rows)
│   │   └── provenance_manifest.json
│   ├── weather/
│   │   ├── nasa_power_coverage_assessment.csv    ← D16: Spatial & topographic adequacy audit
│   │   ├── nasa_power_monthly_district_weather_20.csv ← D17: Aligned 43-yr monthly series (10,320 rows)
│   │   └── weather_provenance.json
│   ├── district_crosswalk.csv    ← D15: Auditable crosswalk for 7,066 historical crop rows
│   ├── district_crosswalk_provenance.json
│   ├── master_district_profiles.csv ← D05: 635 district baseline profiles
│   ├── clean_crops.parquet       ← D06: Normalized historical APY records
│   ├── crop_economics.json       ← D09: CACP MSP 2024-25 benchmarks
│   └── historical_market/
│       ├── SYNTHETIC_DATA_WARNING.md ← ⚠️ Quarantine warning
│       └── historical_mandi_prices.json ← ⚠️ QUARANTINED SYNTHETIC (20,160 records)
└── catalog/
    ├── dataset_catalog.csv       ← Full 17-dataset structured inventory (D01–D17)
    ├── phase2_data_quality_report.md ← Comprehensive Phase 2 Quality & Provenance Audit
    └── data_quality_report.md    ← Phase 1 Quality Audit

scripts/
├── extract_des_production_time_series.py ← Extracts & standardizes official DES 2015-2026 APY (D14)
├── build_district_crosswalk.py           ← Generates statutory district reconciliation crosswalk (D15)
├── assess_weather_coverage.py            ← Spatial adequacy audit & monthly alignment (D16, D17)
├── process_agmarknet_mandi.py            ← Standardizes real Agmarknet downloads with validation
├── acquire_agmarknet_ogd.py              ← Downloads real wholesale prices from api.data.gov.in
├── acquire_nasa_power_weather.py         ← Full 635-district NASA POWER acquisition script
├── acquire_nasa_power_sample.py          ← Pilot 20-district NASA POWER acquisition script
├── generate_phase2_report.py             ← Generates Phase 2 QA report & updates catalog CSV
└── verify_phase2_outputs.py              ← Automated acceptance test suite for Phase 2
```

---

## 2. Phase 2 Key Accomplishments

### Task 1 — Real Agmarknet Data & Quarantine
- **Synthetic Mandi Records Quarantined**: `raw_agmarknet_historical.json` (20,164 rows) and `historical_mandi_prices.json` (20,160 rows) identified as programmatic simulations and formally quarantined with prominent warnings in both raw and processed directories.
- **Official OGD API Documented**: Detailed registration steps for data.gov.in and resource ID `9ef84268-d588-465a-a308-a864a43d0070` documented in `data/raw/market/AGMARKNET_SETUP.md`.
- **Validation Pipeline**: Ingestion script preserves state, district, market, commodity, variety, grade, dates (`YYYY-MM-DD`), min/max/modal prices, units (`INR/quintal`), and strictly forbids substituting MSP for mandi prices.

### Task 2 — Crop Production Post-2015
- **Official DES Extraction**: Parsed official DA&FW 3rd Advance Estimates publication (`Time-Series-3rd-AE-2025-26-English.pdf`) into `data/processed/crop_production/des_national_production_2015_2026.csv`.
- **Coverage**: 682 records spanning 2015-16 to 2025-26 across 34 crops and aggregate groups.
- **Conversion Transparency**: Lakh Tonnes converted to Metric Tonnes (*100,000); Cotton Lakh Bales (*17,000); Jute/Mesta Lakh Bales (*18,000). Granularity explicitly documented as National.

### Task 3 — Historical District Crosswalk
- **100% of 7,066 Records Reconciled**: Investigated all 17 unmatched district pairs from `crop_expert.csv` against `master_district_profiles.csv`.
- **Auditable Statutory References**: Created `data/processed/district_crosswalk.csv` tracking LGD codes, Census 2011 codes, spatial centroids, and official state reorganisation/gazette citations.
- **Resolution**: 17/17 pairs resolved with High confidence; 0 records unresolved.

### Task 4 — Weather Alignment
- **Topographic & Spatial Audit**: Audited all 20 NASA POWER files in `data/processed/weather/nasa_power_coverage_assessment.csv`. Established that 0.5° (~55km) grid provides high spatial adequacy for agricultural plains/plateaus, but terrain-induced smoothing must be noted in montane terrain (Mandi).
- **Aligned Monthly Series**: Created `data/processed/weather/nasa_power_monthly_district_weather_20.csv` containing 10,320 observations (1981–2023, 43 years * 12 months) with 0.00% missingness.
- **Explicit Labeling**: Formally categorized as *"Satellite & Reanalysis Estimate (MERRA-2) - Not Ground Station Observed"*.

### Task 5 — Quality & Provenance
- **Updated Catalog**: `data/catalog/dataset_catalog.csv` updated with all 17 datasets (D01–D17).
- **Comprehensive Report**: `data/catalog/phase2_data_quality_report.md` provides before/after counts, crop coverage, district coverage, year coverage, duplicate counts, missingness, and retrieval limitations.

---

## 3. Automated Verification

To run the automated Phase 2 acceptance test suite:
```powershell
python scripts/verify_phase2_outputs.py
```
All checks validate dataset schemas, non-null guarantees, crosswalk accounting, quarantine notices, and model immutability.
