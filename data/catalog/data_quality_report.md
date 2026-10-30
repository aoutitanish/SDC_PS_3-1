# KrishiMitra — Phase 1 Dataset Acquisition: Data Quality Report

**Generated**: 2026-10-15T05:37:18.193598Z  
**Workspace**: `C:\Users\aouti\Desktop\PS-3\FarmerHelp`  
**Phase**: 1 — Source Audit & Dataset Acquisition (Pre-Training)  
**Model Status**: Production model unchanged. No retraining performed.

---

## 1. EXECUTIVE SUMMARY

| Metric | Value |
|:---|---:|
| Total datasets catalogued | 12 |
| Files/directories present on disk | 12 |
| Sources inaccessible / not yet downloaded | 0 |
| Datasets containing synthetic/generated data | 2 |
| Datasets with real official data | 10 |

> [!CAUTION]
> **2 dataset(s)** contain **synthetically generated data** and must not be used as real market intelligence. See D07 and D08.

---

## 2. SOURCE ACCESS AUDIT (2026-10-15)

| Source | Status | Notes |
|:---|:---|:---|
| **NASA POWER API** | ✅ ACCESSIBLE | HTTP 200. Free, no key. Monthly + climatology endpoints confirmed. |
| **SoilGrids REST API** (rest.isric.org) | ⚠️ TIMEOUT | Intermittent availability. Retry recommended. Existing data from previous query available. |
| **DES APY Portal** (data.desagri.gov.in) | ❌ REFUSED | Connection actively refused (WinError 10061). PDF publication downloaded 2026-09-30 is valid. |
| **Agmarknet** (agmarknet.gov.in) | ⚠️ PARTIAL | HTTP 200 but HTML stub only. Main interface requires JS + form POST. No scraping performed. |
| **data.gov.in OGD API** | ⚠️ KEY REQUIRED | HTTP 403 without API key. Free registration at data.gov.in required for real Agmarknet data. |
| **FAO FAOSTAT API** (fenixservices.fao.org) | ⚠️ TIMEOUT | API endpoint unreachable. Manual bulk CSV download available at fao.org/faostat. |
| **IMD** (mausam.imd.gov.in) | ✅ ACCESSIBLE | HTTP 200. Station data requires inter-departmental request. District normals already in D04. |
| **ICAR** (icar.org.in) | ✅ ACCESSIBLE | HTTP 200. Publications downloadable. No structured API; PDF parsing required for new data. |
| **ICAR NBSS&LUP** (nbsslup.in) | ✅ ACCESSIBLE | HTTP 200. Soil maps and district soil reports. No open API; PDF/GIS layer format. |

### Access Restriction Notes
- **data.desagri.gov.in**: Portal uses VPN-only or institutional access. Alternative: desagri.gov.in main site serves PDF reports directly.
- **Agmarknet**: Bulk scraping violates ToS. data.gov.in OGD API is the official programmatic access method.
- **FAOSTAT**: Bulk CSV available without API at https://www.fao.org/faostat/en/#data/QCL (recommended over API).
- **IMD Station Data**: Requires formal data request to IMD (ndc.imd.gov.in). District normal series already captured.

---

## 3. DATASET INVENTORY

| ID | Name | Category | Rows | Size | Temporal | Missing% | Status |
|:---|:---|:---|---:|---:|:---|---:|:---|
| D01 | `crop_expert.csv` | Crop Production | 246,091 | 30.2 MB | 1997–2015 | 1.5% | ✅ Present |
| D02 | `master_geography.csv` | Geography Reference | 643 | 0.0 MB | Current (2024) | 0.0% | ✅ Present |
| D03 | `soil_expert.csv` | Soil Properties | 641 | 0.0 MB | Multi-decadal (derived from remote sensing + ML model) | 25.0% | ✅ Present |
| D04 | `weather_expert.csv` | Weather / Climate | 145,236 | 11.1 MB | Monthly data 1981–2020 approx | 0.1% | ✅ Present |
| D05 | `master_district_profiles.csv` | Integrated District Profiles | 635 | 0.2 MB | Multi-decadal climate normals | 0.0% | ✅ Present |
| D06 | `clean_crops.parquet` | Crop Production (Cleaned) | 238,838 | 3.2 MB | 1997–2015 | 0.0% | ✅ Present |
| D07 | `raw_agmarknet_historical.json` | Market Prices (Synthetic Benchmark) | 20,164 | 8.1 MB | 2021–2026 (synthetic monthly samples) | N/A | ⚠️ Synthetic |
| D08 | `historical_mandi_prices.json` | Market Prices (Processed/Synthetic) | 20,160 | 9.7 MB | 2021–2026 | N/A | ⚠️ Synthetic |
| D09 | `crop_economics.json` | Economics / MSP / Cost of Cultivation | N/A | 0.0 MB | 2024–25 MSP season; 1997–2015 yield benchmarks | N/A | ✅ Present |
| D10 | `DES Time Series PDF (3rd AE 2025-26` | Crop Production (National Time Series) | N/A | 0.4 MB | 2014–15 to 2025–26 (3rd Advance Estimate) | N/A | ✅ Present |
| D11 | `crop_agronomic_profiles.json` | Crop Requirements (ICAR Agronomic) | N/A | 0.0 MB | Reference (not time-series) | N/A | ✅ Present |
| D12 | `nasa_power_monthly_raw/ (sample: 20` | Weather / Climate (Real — Extended Range) | 20 | 1.1 MB | 1981–2023 monthly (43 years) | N/A | ✅ Present |


---

## 4. DATA INTEGRITY FINDINGS

### 4.1 Duplicate Analysis
- **`crop_expert.csv` (D01)**: 0 exact duplicate rows (0.00%). Multiple rows per district-year
  are valid (multi-crop cultivation across Kharif/Rabi/Summer seasons).
- **`soil_expert.csv` (D03)**: 0 duplicate district rows.
- **`weather_expert.csv` (D04)**: No structural duplicates. Multiple rows per district are
  expected (one row per month × year).
- **`raw_agmarknet_historical.json` (D07)**: 1 intentional duplicate injected for pipeline testing.
  Removed in cleaned output (D08).

### 4.2 Unit Inconsistency Findings
| Dataset | Column | Raw Unit | Standardized Unit | Conversion Applied |
|:---|:---|:---|:---|:---|
| D01 crop_expert.csv | Area | Lakh Hectares (state-level) / Hectares (district) | Hectares | Verified per record |
| D03 soil_expert.csv | phh2o_0_5cm | 10 × pH value | Real pH (divide by 10) | Applied in D05 |
| D03 soil_expert.csv | nitrogen_0_5cm | cg/kg | cg/kg (preserved) | Native unit kept |
| D03 soil_expert.csv | soc_0_5cm | dg/kg | dg/kg (preserved) | Native unit kept |
| D07/D08 mandi prices | modal_price | INR/quintal | INR/quintal | No conversion |
| D07 Paddy→Rice | commodity | Raw Paddy (unmilled) | Rice (milled) | Conversion factor 0.67 noted |

### 4.3 Missing Value Summary
- **D01** `Production`: 1.52% missing (3,730 records) — unrecorded where area was cultivated.
- **D03** `soil properties`: 24.8–25.0% missing in raw file — imputed in D05 using state-level medians.
- **D04** `Rainfall_mm_IMD`: 0.05% missing.
- **D05** `master_district_profiles.csv`: 0% missing (imputation complete).
- **D07/D08**: No missing values (synthetic data by design).

### 4.4 Impossible Value Flags
- **`soil_expert.csv`** `ph_outlier_flag`: Records where soil pH fell outside [3.5, 9.5] range.
- **`crop_expert.csv`** `extreme_yield_flag`: Records with yield > 95th percentile flagged.
- **`crop_expert.csv`** `zero_area_flag`: Records with Area = 0 flagged.
- **Mandi data (D07)**: 2 invalid price records injected (zero price, price > 150,000 INR/q)
  and filtered in D08 processing pipeline.

### 4.5 Geographic Mismatch
- **D01 ↔ D05 join**: 97.13% match rate. 7,066 records (2.87%) use pre-2001 administrative
  district names not present in LGD master geography. These are safely dropped during training join.
  RECOMMENDATION: Create a legacy district name mapping table for full coverage.

---

## 5. DATA LEAKAGE & LABEL QUALITY AUDIT

> [!IMPORTANT]
> **Historical cultivation ≠ optimal suitability.** The fact that a crop was grown in a district
> does not prove it is agronomically optimal there — it may reflect irrigation infrastructure,
> market proximity, government support, or farmer preference rather than soil-climate fitness.

### 5.1 Leakage-Safe Feature Matrix (Enforced)
| Feature | Leakage Risk | Status |
|:---|:---|:---|
| `Yield_tonnes_per_ha` | CRITICAL (post-harvest outcome) | EXCLUDED from X |
| `Production` | CRITICAL (post-harvest outcome) | EXCLUDED from X |
| `Area` | HIGH (post-sowing allocation) | EXCLUDED from X |
| `Crop_Year` | TEMPORAL LEAKAGE | EXCLUDED from X |
| `District_Name` / `district_key` | OVERFITTING risk | EXCLUDED from X |
| `yield_quantile` | Used as filter ONLY | Not a feature — used to filter Y≥2 records |

### 5.2 Label Ambiguity
- 88.38% of district feature vectors support **≥2 crops** under identical soil/climate conditions.
- Mean crops per district vector: **7.43**.
- Theoretical Bayes Optimal Top-1 accuracy upper bound: **21.60%**.
- RECOMMENDATION: Treat as **multi-label** or **top-K recommendation** problem, not single-crop classification.

### 5.3 Temporal Mismatch Risk
- D01 crop records cover 1997–2015.
- D03 soil properties are modelled estimates (multi-decadal; effectively current).
- D04 weather normals cover 1981–2020 approx.
- **These temporal ranges are NOT aligned year-by-year.** Joining D01 crop-year records to
  D04 monthly normals as if they correspond to the same year is INCORRECT.
- Correct use: Use D04 climate normals as **location-representative features** for a district,
  not as the weather that occurred in a specific crop year.

---

## 6. SYNTHETIC DATA WARNINGS

> [!CAUTION]
> The following files contain **synthetically generated data** and must NOT be used as real market data:

| File | Location | Issue |
|:---|:---|:---|
| `raw_agmarknet_historical.json` | `data/raw/market/` | Generated programmatically with seasonal variation formulas |
| `historical_mandi_prices.json` | `data/processed/historical_market/` | Derived from above synthetic source |

**Action Required**: Replace with real Agmarknet data via:
1. Register at https://data.gov.in/user/register (free)
2. Set `DATAGOV_API_KEY` environment variable
3. Run `python scripts/acquire_agmarknet_ogd.py`

---

## 7. CROP NAME NORMALIZATION MAP

The following explicit mapping is applied when joining across datasets:

| Raw Crop Name (D01) | Canonical Crop Name | Notes |
|:---|:---|:---|
| Cotton(lint) | Cotton | Lint cotton only |
| Soyabean | Soybean | Spelling normalization |
| Rapeseed & Mustard | Mustard / Rapeseed | Combined |
| Arhar/Tur | Arhar/Tur (Pigeon Pea) | Full name |
| Gram | Gram (Chickpea) | Full name |
| Jowar | Jowar (Sorghum) | Full name |
| Bajra | Bajra (Pearl Millet) | Full name |
| Ragi | Ragi (Finger Millet) | Full name |
| Paddy(Dhan)(Common) | Rice | Unmilled paddy; conversion factor 0.67 for milled rice |
| Kapas / Cotton(Kapas) | Cotton | Raw seed cotton; lint conversion applies |

---

## 8. ADDITIONAL SOURCES — ASSESSMENT & PRIORITY

| Source | Dataset | Priority | Accessibility | Recommended Action |
|:---|:---|:---|:---|:---|
| **data.gov.in OGD** | Agmarknet Daily Prices | HIGH | Requires free API key | Register + run acquire_agmarknet_ogd.py |
| **FAO FAOSTAT** | India Crop Production QCL | HIGH | Bulk CSV available | Download from fao.org/faostat/en/#data/QCL |
| **DES/desagri.gov.in** | APY Report 2016–2026 | HIGH | PDF accessible via direct URL | Extract post-2015 data from PDF |
| **ICAR Publications** | Crop Technology Bulletins | MEDIUM | Web accessible | Manual download of crop-specific bulletins |
| **ICAR NBSS&LUP** | Soil Resource Maps | MEDIUM | Web accessible | GIS shapefiles or district soil reports |
| **IMD** | District Monthly Rainfall | MEDIUM | Registration required | Submit formal data request to NDC |
| **SoilGrids v2.0** | Deep profile (5–15cm) | MEDIUM | API intermittent | Retry via acquire_soilgrids.py |
| **CACP** | MSP History 2000–2026 | LOW | PDF available | Download annual CACP reports |

---

## 9. ACQUISITION SCRIPTS REGISTRY

| Script | Purpose | API/Source | Status |
|:---|:---|:---|:---|
| `acquire_nasa_power_sample.py` | 20-district NASA POWER sample | NASA POWER API | ✅ Run completed |
| `acquire_nasa_power_weather.py` | Full 635-district NASA POWER | NASA POWER API | Ready to run |
| `acquire_soilgrids.py` | SoilGrids soil depth profiles | SoilGrids REST | Retry needed (API intermittent) |
| `acquire_faostat.py` | FAO crop production India | FAO FAOSTAT API | API timeout; use manual CSV |
| `acquire_agmarknet_ogd.py` | Real Agmarknet mandi prices | data.gov.in OGD | Requires DATAGOV_API_KEY |
| `process_nasa_power_weather.py` | Process NASA POWER → clean CSV | Local files | Ready to run after acquisition |
| `generate_catalog.py` | This script — catalog + QA report | Local | Active |

---

## 10. RECOMMENDATIONS FOR NEXT PHASE

1. **Fill the 2015→2025 crop production gap**: Download DES APY data post-2015 via
   desagri.gov.in PDF parsing or request from State Agriculture Departments via RTI.

2. **Replace synthetic mandi data**: Set `DATAGOV_API_KEY` and run `acquire_agmarknet_ogd.py`
   for real 2020–2026 wholesale price records.

3. **Complete FAOSTAT download**: Download bulk CSV from https://www.fao.org/faostat/en/#data/QCL
   for internationally comparable production statistics.

4. **Add Phosphorus & Potassium**: SoilGrids does not provide P/K. Consider ICAR NBSS&LUP
   district soil fertility maps or the STCR (Soil Test Crop Response) database from ICAR.

5. **Multi-label reframing**: Consider training a multi-label classifier or top-K ranking
   model instead of single-label classification given the 7.43 crops-per-district ambiguity.

6. **Legacy district name mapping**: Create a formal `district_name_mapping.csv` to recover
   the 2.87% unmatched crop records from pre-2001 administrative boundaries.

---

*Report generated by `scripts/generate_catalog.py` — KrishiMitra Phase 1 Data Audit*  
*Production model NOT modified. No retraining performed.*
