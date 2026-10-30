# KrishiMitra Source Access, API Authentication and Acquisition Runbook

**Project**: KrishiMitra AI Agricultural Advisory System  
**Updated**: 2026-10-15 07:23:13 UTC  
**Status**: Authoritative Reference for Data Pipelines & API Ingestion

---

## 1. Primary Source Access Registry

| Data Provider | Target Domain | Endpoint / Portal | Authentication Required | Rate Limits & Throttling | Current Status (Phase 3) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **NASA POWER Project** | Meteorological Reanalysis | `https://power.larc.nasa.gov/api/temporal/` | **None** (Open Access) | Recommended 1.0–1.5 s per query | **ACTIVE (HTTP 200)**: 55 monthly + 10 daily series downloaded |
| **Open Government Data (OGD)** | Mandi Prices (Agmarknet) | `https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070` | `DATAGOV_API_KEY` (Free registration) | 5,000 records/page; 1 req/sec | **CONFIGURED**: Pipeline ready in `acquire_agmarknet_ogd.py` |
| **DES (Ministry of Ag)** | National APY Time Series | `data.desagri.gov.in` / PDF publications | Direct connection refused; official PDFs accessible | Batch download / PDF extraction | **STANDARDIZED (D14)**: 682 rows (2015–2026) extracted |
| **ICAR Institutes & SAUs** | Crop Suitability & Agronomy | ICAR Institute Bulletins & SAU packages | Public Domain / Technical Manuals | Manual compendium & AICRP data | **COMPILED (D21, D22)**: 28 crops + 10 institutes |
| **ICAR-NBSS&LUP** | Soil Fertility & Depth Limits | National Soil Fertility Atlases & SHC portal | Public domain / Institutional atlas | Regional benchmarks | **INTEGRATED (D23)**: N, P2O5, K2O benchmarks |
| **ISRIC SoilGrids v2.0** | Soil Physical Properties | `https://rest.isric.org/soilgrids/v2.0/` | **None** (CC BY 4.0) | High failure rate / timeouts | **BASELINE PRESERVED**: Clean 0-5cm baseline kept |
| **IMD (India Met Dept)** | Station Observed Weather | `https://ndc.imd.gov.in/` | Formal institutional data request | Manual approval | **BASELINE PRESERVED (D04)** |

---

## 2. Step-by-Step Acquisition Runbook

### 2.1 Expanding NASA POWER Weather to Full Master Profile
To download any additional districts beyond the 55 currently acquired:
```powershell
python scripts/acquire_nasa_power_weather.py
```
- **Caching**: The script automatically checks `data/raw/weather/nasa_power_monthly_raw/` and skips existing files.
- **Resumability**: Can be interrupted and resumed at any time without data loss.

### 2.2 Ingesting Real Agmarknet Mandi Telemetry
1. Register for an API key at [https://data.gov.in/user/register](https://data.gov.in/user/register).
2. Set your environment variable:
   ```powershell
   $env:DATAGOV_API_KEY = "your_64_char_api_key_here"
   ```
3. Run the ingestion and validation pipeline:
   ```powershell
   python scripts/acquire_agmarknet_ogd.py
   python scripts/process_agmarknet_mandi.py
   ```

### 2.3 Re-generating Agronomic Knowledge Base & Soil Layers
```powershell
python scripts/build_authoritative_agronomic_kb.py
python scripts/build_enhanced_soil_profiles.py
python scripts/construct_learning_targets.py
```

### 2.4 Running Leakage-Safe Benchmark Verification
```powershell
python scripts/evaluate_leakage_safe_benchmark.py
```
