"""
KrishiMitra AI -- RAG Knowledge Base Ingestion
scripts/ingest_rag_knowledge.py

Loads Phase 3 agronomic datasets (D21, D22, D23) plus existing crop agronomic profiles
into a hybrid TF-IDF + BM25 retrievable document store.

Sources ingested (with full provenance):
  - data/processed/agronomic/normalized_crop_master.csv (D21) -- ICAR crop taxonomy
  - data/processed/agronomic/crop_suitability_requirements.csv (D22) -- ICAR/FAO physiology
  - data/processed/soil/enhanced_district_soil_profiles.csv (D23) -- ICAR-NBSS district soil
  - ml/models/crop_agronomic_profiles.json -- ICAR detailed crop management profiles
  - data/processed/crop_economics.json -- CACP MSP and cost of cultivation

Document schema per chunk:
  doc_id, content, title, source_institution, source_url, publication_year,
  retrieval_date, region, state, crop, season, topic, language

Run from project root:
  python scripts/ingest_rag_knowledge.py
"""

import os
import sys
import json
import logging
import datetime
from typing import List, Dict, Any

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
import joblib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("KrishiMitraRAGIngest")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
ML_DIR = os.path.join(ROOT, "ml", "models")
OUTPUT_DIR = os.path.join(DATA_DIR, "knowledge_base", "rag_index")
TODAY = datetime.date.today().isoformat()


def make_doc(
    doc_id: str,
    content: str,
    title: str,
    source_institution: str,
    source_url: str = "",
    publication_year: str = "",
    region: str = "",
    state: str = "",
    crop: str = "",
    season: str = "",
    topic: str = "",
    language: str = "en",
) -> Dict[str, Any]:
    return {
        "doc_id": doc_id,
        "content": content.strip(),
        "title": title,
        "source_institution": source_institution,
        "source_url": source_url,
        "publication_year": publication_year,
        "retrieval_date": TODAY,
        "region": region,
        "state": state,
        "crop": crop,
        "season": season,
        "topic": topic,
        "language": language,
    }


# ---------------------------------------------------------------------------
# Ingestion functions
# ---------------------------------------------------------------------------

def ingest_crop_master(documents: List[Dict]) -> int:
    """D21 -- normalized_crop_master.csv (ICAR crop taxonomy & vernacular names)."""
    path = os.path.join(DATA_DIR, "processed", "agronomic", "normalized_crop_master.csv")
    if not os.path.exists(path):
        logger.warning(f"D21 not found: {path}")
        return 0
    df = pd.read_csv(path)
    count = 0
    for _, row in df.iterrows():
        crop_name = str(row.get("canonical_crop_name", "")).strip()
        if not crop_name:
            continue
        parts = [f"Crop: {crop_name}"]
        for col in [
            "botanical_name", "family", "category", "vernacular_hindi",
            "vernacular_regional", "synonyms_and_aliases", "crop_type",
            "rooting_depth_class", "water_sensitivity_index", "growth_habit"
        ]:
            val = row.get(col)
            if pd.notna(val) and str(val).strip():
                parts.append(f"{col.replace('_', ' ').title()}: {val}")
        content = ". ".join(parts) + "."
        documents.append(make_doc(
            doc_id=f"d21_crop_{count}",
            content=content,
            title=f"Crop Profile: {crop_name}",
            source_institution="ICAR (Multiple Institutes) via KrishiMitra Phase 3",
            source_url="https://icar.org.in/",
            publication_year="2023-2024",
            crop=crop_name,
            topic="crop_taxonomy",
        ))
        count += 1
    logger.info(f"D21 crop master: {count} documents ingested.")
    return count


def ingest_suitability_requirements(documents: List[Dict]) -> int:
    """D22 -- crop_suitability_requirements.csv (ICAR/FAO physiological requirements)."""
    path = os.path.join(DATA_DIR, "processed", "agronomic", "crop_suitability_requirements.csv")
    if not os.path.exists(path):
        logger.warning(f"D22 not found: {path}")
        return 0
    df = pd.read_csv(path)
    count = 0
    for _, row in df.iterrows():
        crop = str(row.get("canonical_crop_name", "")).strip()
        season = str(row.get("season", "")).strip()
        zone = str(row.get("agro_climatic_zone", "")).strip()
        if not crop:
            continue

        parts = [f"Crop: {crop}", f"Season: {season}", f"Agro-climatic Zone: {zone}"]

        for field, label in [
            ("soil_types_suitable", "Suitable Soil Types"),
            ("soil_texture_optimal", "Optimal Soil Texture"),
            ("ph_absolute_min", "Absolute Min Soil pH"),
            ("ph_optimal_min", "Optimal Min Soil pH"),
            ("ph_optimal_max", "Optimal Max Soil pH"),
            ("ph_absolute_max", "Absolute Max Soil pH"),
            ("temp_germination_min_c", "Min Germination Temp (°C)"),
            ("temp_germination_opt_c", "Optimal Germination Temp (°C)"),
            ("temp_vegetative_opt_min_c", "Optimal Vegetative Min Temp (°C)"),
            ("temp_vegetative_opt_max_c", "Optimal Vegetative Max Temp (°C)"),
            ("temp_flowering_max_critical_c", "Critical Max Flowering Temp (°C)"),
            ("water_requirement_min_mm", "Min Water Requirement (mm)"),
            ("water_requirement_optimal_mm", "Optimal Water Requirement (mm)"),
            ("water_requirement_max_mm", "Max Water Requirement (mm)"),
            ("irrigation_condition", "Irrigation Condition"),
            ("critical_irrigation_stages", "Critical Irrigation Stages"),
            ("duration_min_days", "Min Duration (days)"),
            ("duration_max_days", "Max Duration (days)"),
            ("sowing_window_start", "Sowing Window Start"),
            ("sowing_window_end", "Sowing Window End"),
            ("harvest_window_start", "Harvest Window Start"),
            ("harvest_window_end", "Harvest Window End"),
            ("recommended_n_kg_ha", "Recommended Nitrogen (kg/ha)"),
            ("recommended_p_kg_ha", "Recommended Phosphorus (kg/ha)"),
            ("recommended_k_kg_ha", "Recommended Potassium (kg/ha)"),
            ("salinity_threshold_ds_m", "Salinity Threshold (dS/m)"),
            ("drought_tolerance_level", "Drought Tolerance"),
            ("waterlogging_tolerance_level", "Waterlogging Tolerance"),
            ("primary_source_institute", "Primary Source Institute"),
            ("evidence_type", "Evidence Type"),
            ("confidence_level", "Evidence Confidence Level"),
        ]:
            val = row.get(field)
            if pd.notna(val) and str(val).strip() and str(val).strip() not in ("nan", "None", ""):
                parts.append(f"{label}: {val}")

        content = "\n".join(parts)
        inst = str(row.get("primary_source_institute", "ICAR Institutes + FAO Irrigation & Drainage Papers"))
        documents.append(make_doc(
            doc_id=f"d22_req_{count}",
            content=content,
            title=f"Agronomic Requirements: {crop} ({season}) - {zone}",
            source_institution=inst,
            source_url="https://icar.org.in/",
            publication_year="2022-2024",
            crop=crop,
            season=season,
            topic="agronomic_requirements",
        ))
        count += 1
    logger.info(f"D22 suitability requirements: {count} documents ingested.")
    return count


def ingest_soil_profiles(documents: List[Dict]) -> int:
    """D23 -- enhanced_district_soil_profiles.csv (ICAR-NBSS&LUP district soil data)."""
    path = os.path.join(DATA_DIR, "processed", "soil", "enhanced_district_soil_profiles.csv")
    if not os.path.exists(path):
        logger.warning(f"D23 not found: {path}")
        return 0
    df = pd.read_csv(path)
    count = 0
    for _, row in df.iterrows():
        state = str(row.get("state", "")).strip()
        district = str(row.get("district", "")).strip()
        if not state or not district:
            continue
        if row.get("soil_evidence_status") == "INSUFFICIENT_EVIDENCE":
            content = (
                f"District: {district}, State: {state}. "
                f"Note: Soil data for this district is flagged as INSUFFICIENT_EVIDENCE "
                f"(geographic constraints such as coastal lagoons, urban density, or arid sand dunes prevent standard profiling). "
                f"Do not impute standard soil parameters for this district."
            )
        else:
            parts = [f"District: {district}", f"State: {state}"]
            for field, label in [
                ("ph_surface_0_5cm", "Soil pH (0-5cm)"),
                ("clay_pct_surface_0_5cm", "Clay % (0-5cm)"),
                ("sand_pct_surface_0_5cm", "Sand % (0-5cm)"),
                ("silt_pct_surface_0_5cm", "Silt % (0-5cm)"),
                ("soc_dg_kg_surface_0_5cm", "Soil Organic Carbon (dg/kg, 0-5cm)"),
                ("nitrogen_cg_kg_surface_0_5cm", "Nitrogen (cg/kg, 0-5cm)"),
                ("cec_cmolc_kg_surface_0_5cm", "CEC (cmol/kg, 0-5cm)"),
                ("bulk_density_g_cm3_surface", "Bulk Density (g/cm³)"),
                ("usda_texture_class", "USDA Texture Class"),
                ("dominant_indian_soil_group", "Dominant Indian Soil Group"),
                ("available_nitrogen_status", "Available Nitrogen Status"),
                ("available_phosphorus_p2o5_status", "Available Phosphorus Status (ICAR-NBSS)"),
                ("available_potassium_k2o_status", "Available Potassium Status (ICAR-NBSS)"),
                ("plant_available_water_capacity_awc_mm_m", "Plant Available Water Capacity (mm/m)"),
                ("micronutrient_vulnerability", "Micronutrient Vulnerability"),
                ("data_source_authority", "Data Authority"),
            ]:
                val = row.get(field)
                if pd.notna(val) and str(val).strip() not in ("nan", "None", ""):
                    parts.append(f"{label}: {val}")
            content = "\n".join(parts)
        documents.append(make_doc(
            doc_id=f"d23_soil_{count}",
            content=content,
            title=f"Soil Profile: {district}, {state}",
            source_institution=str(row.get("data_source_authority", "ICAR-NBSS&LUP National Soil Fertility Atlas + SoilGrids v2.0")),
            source_url="https://www.nbsslup.in/",
            publication_year="2020-2024",
            region=f"{district}, {state}",
            state=state,
            topic="soil_profile",
        ))
        count += 1
    logger.info(f"D23 soil profiles: {count} documents ingested.")
    return count


def ingest_crop_agronomic_profiles(documents: List[Dict]) -> int:
    """ml/models/crop_agronomic_profiles.json -- ICAR detailed crop management."""
    path = os.path.join(ML_DIR, "crop_agronomic_profiles.json")
    if not os.path.exists(path):
        logger.warning(f"crop_agronomic_profiles.json not found: {path}")
        return 0
    with open(path, "r", encoding="utf-8") as f:
        profiles = json.load(f)
    count = 0
    for crop_name, profile in profiles.items():
        if not isinstance(profile, dict):
            continue
        parts = [f"Crop: {crop_name}"]
        # Flatten nested fields into natural-language sentences
        for k, v in profile.items():
            if isinstance(v, dict):
                sub = "; ".join(f"{sk}: {sv}" for sk, sv in v.items() if sv is not None)
                if sub:
                    parts.append(f"{k.replace('_', ' ').title()}: {sub}")
            elif isinstance(v, list):
                parts.append(f"{k.replace('_', ' ').title()}: {', '.join(str(i) for i in v)}")
            elif v is not None:
                parts.append(f"{k.replace('_', ' ').title()}: {v}")
        content = "\n".join(parts)
        documents.append(make_doc(
            doc_id=f"profile_{count}",
            content=content,
            title=f"ICAR Agronomic Management Profile: {crop_name}",
            source_institution="ICAR Institute Network (AICRP data)",
            source_url="https://icar.org.in/",
            publication_year="2023",
            crop=crop_name,
            topic="crop_management",
        ))
        count += 1
    logger.info(f"Crop agronomic profiles: {count} documents ingested.")
    return count


def ingest_crop_economics(documents: List[Dict]) -> int:
    """data/processed/crop_economics.json -- CACP MSP and cost of cultivation."""
    path = os.path.join(DATA_DIR, "processed", "crop_economics.json")
    if not os.path.exists(path):
        logger.warning(f"crop_economics.json not found: {path}")
        return 0
    with open(path, "r", encoding="utf-8") as f:
        economics = json.load(f)
    count = 0
    for crop_name, econ in economics.items():
        if not isinstance(econ, dict):
            continue
        parts = [f"Crop: {crop_name}"]
        msp = econ.get("msp_information") or {}
        coc = econ.get("cost_of_cultivation") or {}
        yld = econ.get("yield_benchmark_reference") or {}
        if msp.get("value"):
            parts.append(f"Minimum Support Price (MSP): Rs {msp['value']} per quintal (Season: {msp.get('season','')}, Year: {msp.get('year','')}).")
        if coc.get("value"):
            parts.append(f"Cost of Cultivation: Rs {coc['value']} per acre (Source: {coc.get('source','CACP')}, Year: {coc.get('year','')}).")
        if yld.get("equivalent_quintals_per_acre"):
            parts.append(f"Reference Yield: {yld['equivalent_quintals_per_acre']} quintals per acre.")
        parts.append("Source: CACP (Commission for Agricultural Costs and Prices), Ministry of Agriculture & Farmers Welfare, Government of India.")
        content = "\n".join(parts)
        documents.append(make_doc(
            doc_id=f"econ_{count}",
            content=content,
            title=f"CACP Economics: {crop_name}",
            source_institution="CACP (Commission for Agricultural Costs and Prices), Govt of India",
            source_url="https://cacp.dacnet.nic.in/",
            publication_year="2023-2024",
            crop=crop_name,
            topic="crop_economics",
        ))
        count += 1
    logger.info(f"Crop economics: {count} documents ingested.")
    return count


def ingest_evidence_catalog(documents: List[Dict]) -> int:
    """data/catalog/agronomic_evidence_catalog.csv -- bibliography of ICAR/FAO sources."""
    path = os.path.join(DATA_DIR, "catalog", "agronomic_evidence_catalog.csv")
    if not os.path.exists(path):
        logger.warning(f"Evidence catalog not found: {path}")
        return 0
    df = pd.read_csv(path)
    count = 0
    for _, row in df.iterrows():
        title = str(row.get("publication_title", "")).strip()
        institute = str(row.get("institute", "")).strip()
        crops = str(row.get("crops_covered", "")).strip()
        scope = str(row.get("geographic_scope", "")).strip()
        evidence = str(row.get("evidence_nature", "")).strip()
        url = str(row.get("access_url", "")).strip()
        year = str(row.get("publication_year", "")).strip()
        content = (
            f"Publication: {title}. "
            f"Institution: {institute}. "
            f"Crops covered: {crops}. "
            f"Geographic scope: {scope}. "
            f"Evidence type: {evidence}."
        )
        documents.append(make_doc(
            doc_id=f"evcat_{count}",
            content=content,
            title=title,
            source_institution=institute,
            source_url=url,
            publication_year=year,
            topic="agronomic_evidence",
        ))
        count += 1
    logger.info(f"Evidence catalog: {count} documents ingested.")
    return count


def build_tfidf_index(documents: List[Dict], output_dir: str):
    """Build and persist TF-IDF vectorizer and matrix."""
    os.makedirs(output_dir, exist_ok=True)
    corpus = [d["content"] for d in documents]
    vectorizer = TfidfVectorizer(
        max_features=30000,
        ngram_range=(1, 2),
        min_df=1,
        sublinear_tf=True,
        strip_accents="unicode",
    )
    matrix = vectorizer.fit_transform(corpus)
    joblib.dump(vectorizer, os.path.join(output_dir, "tfidf_vectorizer.pkl"))
    joblib.dump(matrix, os.path.join(output_dir, "tfidf_matrix.pkl"))
    with open(os.path.join(output_dir, "documents.json"), "w", encoding="utf-8") as f:
        json.dump(documents, f, ensure_ascii=False, indent=2)
    logger.info(f"TF-IDF index built: {matrix.shape[0]} docs, {matrix.shape[1]} features -> {output_dir}")


def main():
    logger.info("=== KrishiMitra RAG Knowledge Base Ingestion ===")
    documents: List[Dict] = []

    total = 0
    total += ingest_suitability_requirements(documents)   # D22 -- most important
    total += ingest_crop_agronomic_profiles(documents)    # Detailed ICAR profiles
    total += ingest_crop_master(documents)                # D21 -- taxonomy
    total += ingest_soil_profiles(documents)              # D23 -- district soil
    total += ingest_crop_economics(documents)             # CACP economics
    total += ingest_evidence_catalog(documents)           # Bibliography

    logger.info(f"Total documents ingested: {total}")

    if total == 0:
        logger.error("No documents ingested. Check data paths above.")
        sys.exit(1)

    build_tfidf_index(documents, OUTPUT_DIR)

    logger.info(f"=== Ingestion complete: {total} documents in {OUTPUT_DIR} ===")
    print(f"\nRAG Knowledge Base built: {total} documents")
    print(f"Index location: {OUTPUT_DIR}")
    print("Next: set RAG_LLM_MODE=true in .env and restart the backend.")


if __name__ == "__main__":
    main()
