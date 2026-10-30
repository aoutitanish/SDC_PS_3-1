"""
Data Ingestion and RAG Knowledge Base Builder for KrishiMitra AI.
Constructs structured agricultural knowledge records with metadata for vector search.
"""

import os
import json
import logging
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "processed")
KNOWLEDGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "knowledge_base")
os.makedirs(KNOWLEDGE_DIR, exist_ok=True)

# Curated Official Indian Government Agricultural Schemes & Best Practice Guidelines
GOVERNMENT_SCHEMES = [
    {
        "doc_id": "gov_scheme_pm_kisan",
        "category": "government_scheme",
        "title": "PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)",
        "state": "All India",
        "district": "All",
        "crop": "All",
        "soil_type": "All",
        "season": "All",
        "content": (
            "PM-KISAN is a central sector scheme that provides income support of Rs. 6,000 per year to all landholding farmer families "
            "across India, payable in three equal installments of Rs. 2,000 every four months directly into bank accounts via DBT. "
            "Eligibility: Small, marginal, and landholding farmers with land in their name. Application via pmkisan.gov.in or CSC centers."
        ),
        "source": "Ministry of Agriculture & Farmers Welfare, Govt of India"
    },
    {
        "doc_id": "gov_scheme_pmfby",
        "category": "government_scheme",
        "title": "Pradhan Mantri Fasal Bima Yojana (PMFBY)",
        "state": "All India",
        "district": "All",
        "crop": "All",
        "soil_type": "All",
        "season": "Kharif/Rabi",
        "content": (
            "PMFBY provides comprehensive crop insurance coverage against non-preventable natural risks (drought, flood, unseasonal rains, "
            "pests, diseases) from pre-sowing to post-harvest. Premium rates are capped at 2% for Kharif crops, 1.5% for Rabi crops, "
            "and 5% for commercial/horticultural crops. Farmers can enroll via banks, CSC, or pmfby.gov.in."
        ),
        "source": "Government of India, PMFBY Portal"
    },
    {
        "doc_id": "gov_scheme_soil_health_card",
        "category": "soil",
        "title": "Soil Health Card Scheme (SHC)",
        "state": "All India",
        "district": "All",
        "crop": "All",
        "soil_type": "All",
        "season": "All",
        "content": (
            "The Soil Health Card scheme assesses soil nutrient status on 12 parameters: N, P, K (macro-nutrients); S (secondary-nutrient); "
            "Zn, Fe, Cu, Mn, Bo (micro-nutrients); and pH, EC, OC (physical parameters). It provides customized fertilizer dosage recommendations "
            "to prevent overuse of urea and enhance soil organic matter. Farmers should test soil every 3 years."
        ),
        "source": "Department of Agriculture and Cooperation, Govt of India"
    },
    {
        "doc_id": "gov_scheme_pmksy",
        "category": "irrigation",
        "title": "Pradhan Mantri Krishi Sinchayee Yojana (PMKSY) - Per Drop More Crop",
        "state": "All India",
        "district": "All",
        "crop": "All",
        "soil_type": "All",
        "season": "All",
        "content": (
            "PMKSY promotes micro-irrigation technologies (drip and sprinkler systems) with up to 55% financial subsidy for small/marginal farmers "
            "and 45% for other farmers. Drip irrigation saves 40-60% water, reduces weed growth, and increases fertilizer use efficiency via fertigation."
        ),
        "source": "Ministry of Jal Shakti & Ministry of Agriculture"
    },
    {
        "doc_id": "safety_chemical_disclaimer",
        "category": "agronomy_safety",
        "title": "Integrated Pest Management & Safe Pesticide Application Guidelines",
        "state": "All India",
        "district": "All",
        "crop": "All",
        "soil_type": "All",
        "season": "All",
        "content": (
            "Agricultural Safety Notice: Always follow CIBRC (Central Insecticides Board & Registration Committee) registered dosages and read product labels carefully. "
            "Use protective equipment (gloves, masks) during pesticide application. Spray during calm morning or late afternoon hours to prevent drift. "
            "Avoid spraying near water bodies. Consult your local Krishi Vigyan Kendra (KVK) or district agricultural extension officer for specific pest diagnosis before applying chemicals."
        ),
        "source": "ICAR - Central Insecticides Board & Registration Committee"
    }
]


def generate_knowledge_documents():
    logger.info("Generating RAG knowledge base documents...")
    documents = []

    # 1. Add Government Schemes & Guidelines
    documents.extend(GOVERNMENT_SCHEMES)

    # 2. Add District-level Soil & Climate Knowledge Records
    master_path = os.path.join(DATA_DIR, "master_district_profiles.csv")
    if os.path.exists(master_path):
        master = pd.read_csv(master_path)
        for _, row in master.iterrows():
            state = str(row["State_Name"])
            district = str(row["District_Name"])
            ph = round(float(row["ph"]), 2)
            soil_group = str(row["indian_soil_group"])
            texture = str(row["usda_texture"])
            nitrogen_lvl = str(row["nitrogen_level"])
            rainfall = round(float(row["annual_rainfall_mm"]), 1)
            kharif_rain = round(float(row["kharif_rainfall_mm"]), 1)
            rabi_rain = round(float(row["rabi_rainfall_mm"]), 1)
            mean_temp = round(float(row["mean_temperature_c"]), 1)
            max_temp = round(float(row["max_temperature_c"]), 1)
            humidity = round(float(row["relative_humidity_pct"]), 1)

            doc = {
                "doc_id": f"dist_{row['district_key']}",
                "category": "district_profile",
                "title": f"Agricultural Profile: {district}, {state}",
                "state": state,
                "district": district,
                "crop": "General",
                "soil_type": soil_group,
                "season": "All",
                "content": (
                    f"In {district} district, {state}: Predominant soil is {soil_group} with USDA texture class '{texture}'. "
                    f"Soil pH is {ph} ({row['ph_category']}), clay content is {round(float(row['clay_pct']), 1)}%, "
                    f"and total nitrogen is {nitrogen_lvl} ({round(float(row['nitrogen_cg_kg']), 1)} cg/kg). "
                    f"Climate Profile: Mean annual rainfall is {rainfall} mm (Kharif monsoon: {kharif_rain} mm, Rabi: {rabi_rain} mm). "
                    f"Average temperature is {mean_temp}°C (summer max ~{max_temp}°C) with relative humidity around {humidity}%."
                ),
                "source": "Master Geography, Soil Expert & Weather Datasets"
            }
            documents.append(doc)

    # 3. Add Crop Agronomy Knowledge Records
    crop_profiles_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ml", "models", "crop_agronomic_profiles.json")
    if os.path.exists(crop_profiles_path):
        with open(crop_profiles_path, "r") as fp:
            crop_profiles = json.load(fp)

        for crop_name, prof in crop_profiles.items():
            top_st = ", ".join(list(prof["top_states"].keys())[:3])
            top_se = ", ".join(list(prof["top_seasons"].keys())[:2])
            ph_min, ph_max = prof["ph_optimal"]
            rain_min, rain_max = prof["rainfall_optimal_mm"]
            temp_min, temp_max = prof["temp_optimal_c"]
            mean_yield = prof["mean_yield_tonnes_ha"]

            doc = {
                "doc_id": f"crop_prof_{crop_name.lower().replace(' ', '_')}",
                "category": "crop_agronomy",
                "title": f"Crop Agronomy Guide: {crop_name}",
                "state": "Multi-State",
                "district": "All",
                "crop": crop_name,
                "soil_type": "Various",
                "season": top_se,
                "content": (
                    f"{crop_name} Agronomic Requirements: Optimal soil pH is {ph_min} to {ph_max}. "
                    f"Optimal annual rainfall requirement is {rain_min} to {rain_max} mm. "
                    f"Temperature tolerance range is {temp_min}°C to {temp_max}°C. "
                    f"Primary cultivation seasons: {top_se}. Leading producing states: {top_st}. "
                    f"Historical benchmark average yield is approximately {mean_yield} tonnes per hectare under standard agronomic practices."
                ),
                "source": "Crop Expert Dataset & ICAR Agronomy Guidelines"
            }
            documents.append(doc)

    logger.info(f"Total knowledge documents compiled: {len(documents)}")
    output_path = os.path.join(KNOWLEDGE_DIR, "agricultural_knowledge_documents.json")
    with open(output_path, "w", encoding="utf-8") as fp:
        json.dump(documents, fp, indent=2, ensure_ascii=False)

    logger.info(f"Saved knowledge base to {output_path}")
    return documents


if __name__ == "__main__":
    generate_knowledge_documents()
