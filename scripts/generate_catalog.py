"""
Dataset Catalog Generator for KrishiMitra Phase 1 Acquisition.

Scans all existing datasets (raw + processed) and generates:
  - data/catalog/dataset_catalog.csv   — structured inventory
  - data/catalog/data_quality_report.md — full quality audit

This script is READ-ONLY with respect to source data — it only reads and reports.
"""

import os
import sys
import json
import csv
import glob
import datetime
import logging
import hashlib
import pandas as pd
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
PROC_DIR = os.path.join(DATA_DIR, "processed")
RAW_DIR = os.path.join(DATA_DIR, "raw")
CATALOG_DIR = os.path.join(DATA_DIR, "catalog")
os.makedirs(CATALOG_DIR, exist_ok=True)

NOW = datetime.datetime.utcnow().isoformat() + "Z"


def file_md5(fpath: str) -> str:
    if not os.path.exists(fpath):
        return ""
    h = hashlib.md5()
    with open(fpath, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def analyze_csv(fpath: str) -> dict:
    try:
        df = pd.read_csv(fpath)
        missing = df.isnull().mean().mul(100).round(2)
        result = {
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": list(df.columns),
            "missing_pct_by_col": missing.to_dict(),
            "max_missing_pct": float(missing.max()),
            "avg_missing_pct": float(missing.mean().round(2)),
            "duplicate_rows": int(df.duplicated().sum()),
        }
        # Numeric range checks
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        result["numeric_columns"] = list(numeric_cols)
        return result
    except Exception as e:
        return {"error": str(e)}


def analyze_json(fpath: str) -> dict:
    try:
        with open(fpath, encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):
            return {"records": len(data), "type": "list"}
        elif isinstance(data, dict):
            return {"keys": list(data.keys())[:10], "type": "dict"}
        return {"type": str(type(data))}
    except Exception as e:
        return {"error": str(e)}


def analyze_parquet(fpath: str) -> dict:
    try:
        df = pd.read_parquet(fpath)
        missing = df.isnull().mean().mul(100).round(2)
        return {
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": list(df.columns),
            "missing_pct_by_col": missing.to_dict(),
            "max_missing_pct": float(missing.max()),
        }
    except Exception as e:
        return {"error": str(e)}


# ---- Dataset registry with metadata ----
DATASETS = [
    # ===== EXISTING CORE DATASETS =====
    {
        "dataset_id": "D01",
        "name": "crop_expert.csv",
        "category": "Crop Production",
        "path": os.path.join(DATA_DIR, "crop_expert.csv"),
        "source": "Ministry of Agriculture & Farmers Welfare – APY data",
        "source_url": "https://data.gov.in / State Agriculture Departments",
        "temporal_range": "1997–2015",
        "geographic_coverage": "All India (33 states, 646 districts)",
        "format": "CSV",
        "license": "Government Open Data License India (GODL-India)",
        "access_method": "Existing local file (originally sourced from data.gov.in APY dataset)",
        "units": "Area: ha, Production: Tonnes, Yield: Tonnes/Ha",
        "provenance_notes": (
            "Official district-level Area, Production, Yield (APY) statistics from Indian state "
            "agricultural departments compiled by Ministry of Agriculture. 1997–2015 coverage. "
            "IMPORTANT: Reflects HISTORICAL CULTIVATION — does not imply optimal crop suitability. "
            "See data leakage analysis in ml_data_audit_report.md."
        ),
        "limitations": (
            "Coverage ends 2015; no data for 2016–2026. 1.52% missing Production/Yield "
            "values. ~2.87% district names use legacy administrative boundaries "
            "not matching current LGD codes. No sub-district resolution."
        ),
    },
    {
        "dataset_id": "D02",
        "name": "master_geography.csv",
        "category": "Geography Reference",
        "path": os.path.join(DATA_DIR, "master_geography.csv"),
        "source": "LGD / NIC India District Gazetteer",
        "source_url": "https://lgdirectory.gov.in/",
        "temporal_range": "Current (2024)",
        "geographic_coverage": "All India (643 districts)",
        "format": "CSV",
        "license": "Government Open Data (India)",
        "access_method": "Existing local file",
        "units": "Latitude/Longitude: decimal degrees",
        "provenance_notes": "District centroid coordinates for 643 Indian districts.",
        "limitations": "District boundaries may not match 1997–2015 APY administrative names exactly.",
    },
    {
        "dataset_id": "D03",
        "name": "soil_expert.csv",
        "category": "Soil Properties",
        "path": os.path.join(DATA_DIR, "soil_expert.csv"),
        "source": "ISRIC SoilGrids v2.0 (250m)",
        "source_url": "https://rest.isric.org/soilgrids/v2.0/",
        "temporal_range": "Multi-decadal (derived from remote sensing + ML model)",
        "geographic_coverage": "641 Indian districts",
        "format": "CSV",
        "license": "CC BY 4.0",
        "access_method": "Existing local file (previously retrieved via SoilGrids REST API)",
        "units": "pH: 10*pH, N: cg/kg, Clay/Sand/Silt: g/kg (0-1000 scale), SOC: dg/kg, BDOD: cg/cm3, CEC: mmol(c)/kg",
        "provenance_notes": (
            "SoilGrids 0–5cm depth profile queried at district centroids. "
            "Values are MODELLED ESTIMATES from remote sensing + spatial ML, not direct soil measurements. "
            "Raw API was inaccessible (timeout) on 2026-10-15 probe."
        ),
        "limitations": (
            "~24.8–25% missing values for remote/hill districts (original raw values before imputation). "
            "Point estimates at district centroids do not capture within-district soil variability. "
            "Only 0-5cm depth available; subsoil properties absent. No Phosphorus or Potassium available from SoilGrids."
        ),
    },
    {
        "dataset_id": "D04",
        "name": "weather_expert.csv",
        "category": "Weather / Climate",
        "path": os.path.join(DATA_DIR, "weather_expert.csv"),
        "source": "NASA POWER AG Community API + IMD District Climate Normals",
        "source_url": "https://power.larc.nasa.gov/",
        "temporal_range": "Monthly data 1981–2020 approx",
        "geographic_coverage": "635 Indian districts",
        "format": "CSV",
        "license": "NASA Open Data; IMD: Government of India (research use permitted)",
        "access_method": "Existing local file; NASA POWER API confirmed ACCESSIBLE on 2026-10-15",
        "units": "T2M: °C, Rainfall: mm/month, RH: %, WS: m/s",
        "provenance_notes": (
            "Monthly climate telemetry from NASA POWER (T2M, Tmax, Tmin, RH, WS) and IMD (rainfall). "
            "Used as climate feature matrix for crop suitability inference."
        ),
        "limitations": (
            "Contains 30-year CLIMATE NORMALS only — not real-time weather. "
            "0.05% missing Rainfall_mm_IMD values. "
            "CRITICAL: Do not join per-district normals to crop-year records without "
            "explicit season-period (growing month) alignment."
        ),
    },
    {
        "dataset_id": "D05",
        "name": "master_district_profiles.csv",
        "category": "Integrated District Profiles",
        "path": os.path.join(PROC_DIR, "master_district_profiles.csv"),
        "source": "Derived: SoilGrids D03 + NASA/IMD D04 + Geography D02",
        "source_url": "Derived (see component sources)",
        "temporal_range": "Multi-decadal climate normals",
        "geographic_coverage": "635 Indian districts",
        "format": "CSV",
        "license": "Composite (CC BY 4.0 + NASA Open + GODL-India)",
        "access_method": "Existing local file (derived from D02, D03, D04)",
        "units": "Mixed (see component datasets)",
        "provenance_notes": "Unified 635-district feature matrix joining soil and climate normals.",
        "limitations": (
            "Imputed soil values for 25% of districts (state-level median imputation). "
            "Climate normals not time-series. No P/K soil nutrients."
        ),
    },
    {
        "dataset_id": "D06",
        "name": "clean_crops.parquet",
        "category": "Crop Production (Cleaned)",
        "path": os.path.join(PROC_DIR, "clean_crops.parquet"),
        "source": "Derived from D01 (crop_expert.csv) — cleaned, normalized",
        "source_url": "Derived",
        "temporal_range": "1997–2015",
        "geographic_coverage": "635 districts (97.13% of D01)",
        "format": "Parquet",
        "license": "GODL-India",
        "access_method": "Existing local file",
        "units": "Same as D01",
        "provenance_notes": "Cleaned APY records with normalized crop names and yield quantiles.",
        "limitations": "Same as D01. yield_quantile used only as quality filter; NOT a suitability label.",
    },
    {
        "dataset_id": "D07",
        "name": "raw_agmarknet_historical.json",
        "category": "Market Prices (Synthetic Benchmark)",
        "path": os.path.join(RAW_DIR, "market", "raw_agmarknet_historical.json"),
        "source": "Synthetically generated benchmark data (Agmarknet commodity price ranges)",
        "source_url": "https://agmarknet.gov.in/",
        "temporal_range": "2021–2026 (synthetic monthly samples)",
        "geographic_coverage": "10 states, 20 districts",
        "format": "JSON",
        "license": "Internal (synthetic — NOT real Agmarknet records)",
        "access_method": "Existing local file — SYNTHETIC DATA",
        "units": "INR/quintal",
        "provenance_notes": (
            "CRITICAL: This file contains SYNTHETICALLY GENERATED price observations "
            "with seasonal variation formulas — NOT actual downloaded Agmarknet data. "
            "Real Agmarknet data requires data.gov.in API key (DATAGOV_API_KEY)."
        ),
        "limitations": (
            "SYNTHETIC — not suitable as real market intelligence. "
            "Must be replaced with real Agmarknet OGD API data before production use. "
            "Includes deliberately injected dirty records for pipeline testing."
        ),
    },
    {
        "dataset_id": "D08",
        "name": "historical_mandi_prices.json",
        "category": "Market Prices (Processed/Synthetic)",
        "path": os.path.join(PROC_DIR, "historical_market", "historical_mandi_prices.json"),
        "source": "Processed from D07 (synthetic Agmarknet benchmarks)",
        "source_url": "Internal",
        "temporal_range": "2021–2026",
        "geographic_coverage": "10 states, 20 districts",
        "format": "JSON",
        "license": "Internal (synthetic)",
        "access_method": "Existing local file",
        "units": "INR/quintal (modal price)",
        "provenance_notes": "Cleaned and normalized from D07 synthetic data. See Phase 6B pipeline.",
        "limitations": "Inherits D07 synthetic limitations. Not real observed mandi prices.",
    },
    {
        "dataset_id": "D09",
        "name": "crop_economics.json",
        "category": "Economics / MSP / Cost of Cultivation",
        "path": os.path.join(PROC_DIR, "crop_economics.json"),
        "source": "CACP (MSP), DES Cost of Cultivation, FCI Storage Guidelines",
        "source_url": "https://cacp.dacnet.nic.in, https://eands.dacnet.nic.in",
        "temporal_range": "2024–25 MSP season; 1997–2015 yield benchmarks",
        "geographic_coverage": "National (28 crops)",
        "format": "JSON",
        "license": "Government of India Open Data",
        "access_method": "Existing local file (manually compiled from official CACP publications)",
        "units": "MSP: INR/quintal; Cost: INR/acre",
        "provenance_notes": (
            "MSP from CACP notifications. Cost of Cultivation (A2+FL metric) from DES. "
            "Post-harvest guidance from FCI and ICAR. "
            "Profit calculations are ILLUSTRATIVE estimates, not guaranteed yields."
        ),
        "limitations": (
            "MSP covers only 28 crops. Cost of cultivation is state-average — varies by farm. "
            "Yield benchmarks are 1997–2015 historical means, not current season forecasts."
        ),
    },
    {
        "dataset_id": "D10",
        "name": "DES Time Series PDF (3rd AE 2025-26)",
        "category": "Crop Production (National Time Series)",
        "path": os.path.join(RAW_DIR, "market", "real_des_historical", "Time-Series-3rd-AE-2025-26-English.pdf"),
        "source": "Directorate of Economics & Statistics (DES), Govt of India",
        "source_url": "https://desagri.gov.in/wp-content/uploads/2026/06/Time-Series-3rd-AE-2025-26-English.pdf",
        "temporal_range": "2014–15 to 2025–26 (3rd Advance Estimate)",
        "geographic_coverage": "All India + States/UTs, 23 major commodities",
        "format": "PDF",
        "license": "Government of India Open Publication",
        "access_method": "Existing local file — direct download from desagri.gov.in",
        "units": "Area: Lakh Ha, Production: Lakh MT, Yield: Kg/Ha",
        "provenance_notes": (
            "Official DES Time Series publication with 12 years of national-level APY statistics. "
            "Covers: Rice, Wheat, Jowar, Bajra, Maize, Ragi, Barley, Gram, Tur/Arhar, Moong, "
            "Urad, Masoor, Groundnut, Mustard, Soyabean, Sunflower, Sesame, Castor, Cotton, "
            "Sugarcane, Jute, Potato, Onion. "
            "IMPORTANT: desagri.gov.in portal was NOT accessible via direct HTTP on 2026-10-15 "
            "(connection refused). PDF was downloaded on 2026-09-30."
        ),
        "limitations": (
            "PDF format — requires parsing to extract structured tabular data. "
            "National and state-level only — no district granularity. "
            "Portal currently inaccessible for fresh downloads."
        ),
    },
    {
        "dataset_id": "D11",
        "name": "crop_agronomic_profiles.json",
        "category": "Crop Requirements (ICAR Agronomic)",
        "path": os.path.join(ROOT, "ml", "models", "crop_agronomic_profiles.json"),
        "source": "ICAR crop management guidelines (manually compiled)",
        "source_url": "https://icar.org.in/, ICAR crop technology publications",
        "temporal_range": "Reference (not time-series)",
        "geographic_coverage": "28 Indian crops (national)",
        "format": "JSON",
        "license": "Reference knowledge (ICAR publications, public domain)",
        "access_method": "Existing local file",
        "units": "pH: 0-14, Temperature: °C, Rainfall: mm, Humidity: %",
        "provenance_notes": (
            "Agronomic suitability bounds (pH min/max, temperature range, water requirements, "
            "nutrient needs) for 28 crops based on ICAR crop technology publications. "
            "Used exclusively for Stage 2 ICAR Engine post-ML agronomic filtering."
        ),
        "limitations": (
            "Manually compiled — should be reviewed against latest ICAR publications. "
            "Values represent typical optimal ranges; actual thresholds vary by variety and location."
        ),
    },
    # ===== NEW DATA ACQUIRED IN PHASE 1 =====
    {
        "dataset_id": "D12",
        "name": "nasa_power_monthly_raw/ (sample: 20 districts)",
        "category": "Weather / Climate (Real — Extended Range)",
        "path": os.path.join(RAW_DIR, "weather", "nasa_power_monthly_raw"),
        "source": "NASA POWER Agroclimatology API",
        "source_url": "https://power.larc.nasa.gov/api/temporal/monthly/point",
        "temporal_range": "1981–2023 monthly (43 years)",
        "geographic_coverage": "20 sample districts (full 635 planned)",
        "format": "JSON (per district)",
        "license": "NASA Open Data — no registration required",
        "access_method": "API (CONFIRMED ACCESSIBLE 2026-10-15) — see acquire_nasa_power_weather.py",
        "units": "T2M: °C, PRECTOTCORR: mm/day, RH2M: %, WS2M: m/s",
        "provenance_notes": (
            "Real monthly climate data from NASA POWER AG community (1981–2023). "
            "Covers: mean/max/min temperature (T2M, T2M_MAX, T2M_MIN), total precipitation "
            "(PRECTOTCORR), relative humidity (RH2M), wind speed (WS2M). "
            "Extends existing weather_expert.csv with 3 additional years (2021–2023) "
            "and adds daily-resolution seasonal aggregates."
        ),
        "limitations": (
            "0.5° x 0.5° spatial resolution (not district-specific surveys). "
            "Monthly API; not daily. Satellite-model derived, not ground observations. "
            "API request rate limit: recommended 1 request per 1.5s per grid point."
        ),
    },
]


def compute_dataset_stats(ds: dict) -> dict:
    """Compute live stats for a dataset entry."""
    path = ds["path"]
    stats = {"file_exists": os.path.exists(path)}

    if not stats["file_exists"]:
        if os.path.isdir(path):
            files = glob.glob(os.path.join(path, "*.json"))
            stats["is_directory"] = True
            stats["file_count"] = len(files)
            stats["size_bytes"] = sum(os.path.getsize(f) for f in files)
        else:
            stats["size_bytes"] = 0
        return stats

    if os.path.isdir(path):
        files = glob.glob(os.path.join(path, "*.json"))
        stats["is_directory"] = True
        stats["file_count"] = len(files)
        stats["size_bytes"] = sum(os.path.getsize(f) for f in files)
        return stats

    stats["size_bytes"] = os.path.getsize(path)
    stats["size_mb"] = round(stats["size_bytes"] / (1024 * 1024), 3)

    if path.endswith(".csv"):
        detail = analyze_csv(path)
        stats.update(detail)
    elif path.endswith(".json"):
        detail = analyze_json(path)
        stats.update(detail)
    elif path.endswith(".parquet"):
        detail = analyze_parquet(path)
        stats.update(detail)
    elif path.endswith(".pdf"):
        stats["note"] = "PDF — requires extraction for structured analysis"

    return stats


def generate_catalog():
    catalog_rows = []
    for ds in DATASETS:
        logger.info(f"  Analyzing {ds['dataset_id']}: {ds['name']}")
        stats = compute_dataset_stats(ds)

        row = {
            "dataset_id": ds["dataset_id"],
            "name": ds["name"],
            "category": ds["category"],
            "source": ds["source"],
            "source_url": ds["source_url"],
            "temporal_range": ds["temporal_range"],
            "geographic_coverage": ds["geographic_coverage"],
            "format": ds["format"],
            "license": ds["license"],
            "access_method": ds["access_method"],
            "units": ds["units"],
            "file_exists": stats.get("file_exists", False) or stats.get("is_directory", False),
            "size_mb": stats.get("size_mb", round(stats.get("size_bytes", 0) / 1048576, 3)),
            "rows": stats.get("rows", stats.get("records", stats.get("file_count", "N/A"))),
            "columns": stats.get("columns", "N/A"),
            "max_missing_pct": stats.get("max_missing_pct", "N/A"),
            "avg_missing_pct": stats.get("avg_missing_pct", "N/A"),
            "duplicate_rows": stats.get("duplicate_rows", "N/A"),
            "provenance_notes": ds["provenance_notes"],
            "limitations": ds["limitations"],
            "catalog_generated_at": NOW,
        }
        catalog_rows.append(row)

    return catalog_rows


def write_catalog_csv(rows: list):
    out_path = os.path.join(CATALOG_DIR, "dataset_catalog.csv")
    if not rows:
        return

    fieldnames = list(rows[0].keys())
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    logger.info(f"Catalog CSV saved: {out_path}")
    return out_path


def write_quality_report(rows: list):
    out_path = os.path.join(CATALOG_DIR, "data_quality_report.md")

    # Count key metrics
    total = len(rows)
    existing = sum(1 for r in rows if r["file_exists"])
    missing = total - existing
    synthetic = sum(1 for r in rows if "SYNTHETIC" in str(r.get("provenance_notes", "")).upper()
                    or "Synthetic" in str(r.get("provenance_notes", "")))

    md = f"""# KrishiMitra — Phase 1 Dataset Acquisition: Data Quality Report

**Generated**: {NOW}  
**Workspace**: `C:\\Users\\aouti\\Desktop\\PS-3\\FarmerHelp`  
**Phase**: 1 — Source Audit & Dataset Acquisition (Pre-Training)  
**Model Status**: Production model unchanged. No retraining performed.

---

## 1. EXECUTIVE SUMMARY

| Metric | Value |
|:---|---:|
| Total datasets catalogued | {total} |
| Files/directories present on disk | {existing} |
| Sources inaccessible / not yet downloaded | {missing} |
| Datasets containing synthetic/generated data | {synthetic} |
| Datasets with real official data | {total - synthetic} |

> [!CAUTION]
> **{synthetic} dataset(s)** contain **synthetically generated data** and must not be used as real market intelligence. See D07 and D08.

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
"""
    for r in rows:
        rows_val = r.get("rows", "N/A")
        size_val = r.get("size_mb", "N/A")
        try:
            size_str = f"{size_val:.1f} MB" if isinstance(size_val, (int, float)) else str(size_val)
        except Exception:
            size_str = str(size_val)
        missing_val = r.get("max_missing_pct", "N/A")
        try:
            missing_str = f"{missing_val:.1f}%" if isinstance(missing_val, (int, float)) else str(missing_val)
        except Exception:
            missing_str = str(missing_val)
        status = "✅ Present" if r.get("file_exists") else "❌ Missing"
        if "SYNTHETIC" in str(r.get("provenance_notes", "")).upper() or "synthetic" in str(r.get("provenance_notes","")).lower():
            status = "⚠️ Synthetic"
        try:
            rows_str = f"{rows_val:,}" if isinstance(rows_val, int) else str(rows_val)
        except Exception:
            rows_str = str(rows_val)
        md += f"| {r['dataset_id']} | `{r['name'][:35]}` | {r['category']} | {rows_str} | {size_str} | {r['temporal_range']} | {missing_str} | {status} |\n"

    md += f"""

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
"""

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(md)
    logger.info(f"Quality report saved: {out_path}")
    return out_path


def run():
    logger.info("Generating dataset catalog...")
    rows = generate_catalog()

    logger.info("Writing catalog CSV...")
    write_catalog_csv(rows)

    logger.info("Writing quality report...")
    write_quality_report(rows)

    logger.info(f"\n{'='*60}")
    logger.info(f"CATALOG COMPLETE")
    logger.info(f"  Datasets catalogued: {len(rows)}")
    logger.info(f"  CSV: {os.path.join(CATALOG_DIR, 'dataset_catalog.csv')}")
    logger.info(f"  Report: {os.path.join(CATALOG_DIR, 'data_quality_report.md')}")


if __name__ == "__main__":
    run()
