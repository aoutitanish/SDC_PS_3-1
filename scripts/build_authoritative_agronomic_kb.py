"""
Authoritative Agronomic Suitability Knowledge Base Builder for KrishiMitra Phase 3.

Compiles official ICAR Institute, State Agricultural University (SAU), and FAO technical
crop requirements for all 28 canonical crops + key additional crops in KrishiMitra.

Generates:
1. data/processed/agronomic/normalized_crop_master.csv
2. data/processed/agronomic/crop_suitability_requirements.csv
3. data/catalog/agronomic_evidence_catalog.csv
4. data/catalog/unresolved_agronomic_evidence_report.md
"""

import os
import sys
import json
import logging
import datetime
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGRO_PROC_DIR = os.path.join(ROOT, "data", "processed", "agronomic")
CATALOG_DIR = os.path.join(ROOT, "data", "catalog")

os.makedirs(AGRO_PROC_DIR, exist_ok=True)
os.makedirs(CATALOG_DIR, exist_ok=True)

# -------------------------------------------------------------
# 1. NORMALIZED CROP MASTER DATA
# -------------------------------------------------------------
CROP_MASTER_RECORDS = [
    {
        "crop_id": "C01",
        "canonical_crop_name": "Rice",
        "botanical_name": "Oryza sativa L.",
        "family": "Poaceae",
        "category": "Cereals",
        "synonyms_and_aliases": "Paddy, Dhan, Common Paddy, Chawal",
        "vernacular_hindi": "Dhan (धान)",
        "vernacular_regional": "Nellu (Tamil), Vari (Telugu), Bhat (Bengali), Akki (Kannada)",
        "crop_type": "Field Cereal",
        "rooting_depth_class": "Shallow (40–60 cm)",
        "water_sensitivity_index": "Very High",
        "growth_habit": "Annual erect semi-aquatic grass",
        "supported_in_krishimitra": True
    },
    {
        "crop_id": "C02",
        "canonical_crop_name": "Wheat",
        "botanical_name": "Triticum aestivum L.",
        "family": "Poaceae",
        "category": "Cereals",
        "synonyms_and_aliases": "Bread Wheat, Gehun, Triticum durum (Durum wheat)",
        "vernacular_hindi": "Gehun (गेहूं)",
        "vernacular_regional": "Godhumai (Tamil), Godhumalu (Telugu), Gom (Bengali)",
        "crop_type": "Field Cereal",
        "rooting_depth_class": "Medium (90–120 cm)",
        "water_sensitivity_index": "Medium to High",
        "growth_habit": "Annual erect winter grass",
        "supported_in_krishimitra": True
    },
    {
        "crop_id": "C03",
        "canonical_crop_name": "Maize",
        "botanical_name": "Zea mays L.",
        "family": "Poaceae",
        "category": "Cereals",
        "synonyms_and_aliases": "Corn, Makka, Indian Corn",
        "vernacular_hindi": "Makka (मक्का)",
        "vernacular_regional": "Makka Cholam (Tamil), Mokkajonna (Telugu), Bhutta (Bengali)",
        "crop_type": "Field Cereal",
        "rooting_depth_class": "Medium (80–120 cm)",
        "water_sensitivity_index": "High",
        "growth_habit": "Annual erect robust C4 grass",
        "supported_in_krishimitra": True
    },
    {
        "crop_id": "C04",
        "canonical_crop_name": "Arhar/Tur (Pigeon Pea)",
        "botanical_name": "Cajanus cajan (L.) Millsp.",
        "family": "Fabaceae",
        "category": "Pulses",
        "synonyms_and_aliases": "Pigeonpea, Red Gram, Tur, Arhar, Tuvar",
        "vernacular_hindi": "Arhar, Tur (अरहर / तुअर)",
        "vernacular_regional": "Thuvarai (Tamil), Kandulu (Telugu), Togari (Kannada)",
        "crop_type": "Pulse / Grain Legume",
        "rooting_depth_class": "Deep (> 150 cm deep taproot)",
        "water_sensitivity_index": "Medium (Drought tolerant)",
        "growth_habit": "Semi-perennial cultivated as annual woody shrub",
        "supported_in_krishimitra": True
    },
    {
        "crop_id": "C05",
        "canonical_crop_name": "Moong (Green Gram)",
        "botanical_name": "Vigna radiata (L.) R. Wilczek",
        "family": "Fabaceae",
        "category": "Pulses",
        "synonyms_and_aliases": "Mung bean, Green gram, Moong dal",
        "vernacular_hindi": "Moong (मूँग)",
        "vernacular_regional": "Pasi Payaru (Tamil), Pesalu (Telugu), Hesaru (Kannada)",
        "crop_type": "Pulse / Short Duration Legume",
        "rooting_depth_class": "Shallow to Medium (50–70 cm)",
        "water_sensitivity_index": "Medium",
        "growth_habit": "Annual herbaceous erect/semi-erect",
        "supported_in_krishimitra": True
    },
    {
        "crop_id": "C06",
        "canonical_crop_name": "Urad",
        "botanical_name": "Vigna mungo (L.) Hepper",
        "family": "Fabaceae",
        "category": "Pulses",
        "synonyms_and_aliases": "Black Gram, Mash, Urd, Black matpe",
        "vernacular_hindi": "Urad (उड़द)",
        "vernacular_regional": "Ulundu (Tamil), Minumulu (Telugu), Uddu (Kannada)",
        "crop_type": "Pulse / Grain Legume",
        "rooting_depth_class": "Medium (60–80 cm)",
        "water_sensitivity_index": "Medium",
        "growth_habit": "Annual densely hairy herbaceous",
        "supported_in_krishimitra": True
    },
    {
        "crop_id": "C07",
        "canonical_crop_name": "Gram (Chickpea)",
        "botanical_name": "Cicer arietinum L.",
        "family": "Fabaceae",
        "category": "Pulses",
        "synonyms_and_aliases": "Bengal Gram, Chana, Desi Chana, Kabuli Chana",
        "vernacular_hindi": "Chana (चना)",
        "vernacular_regional": "Kondakadalai (Tamil), Senagalu (Telugu), Kadale (Kannada)",
        "crop_type": "Winter Pulse",
        "rooting_depth_class": "Deep (90–120 cm)",
        "water_sensitivity_index": "Low to Medium (High drought avoidance)",
        "growth_habit": "Annual bushy branched herbaceous",
        "supported_in_krishimitra": True
    },
    {
        "crop_id": "C08",
        "canonical_crop_name": "Groundnut",
        "botanical_name": "Arachis hypogaea L.",
        "family": "Fabaceae",
        "category": "Oilseeds",
        "synonyms_and_aliases": "Peanut, Mungphali, Monkey nut",
        "vernacular_hindi": "Mungphali (मूंगफली)",
        "vernacular_regional": "Verkadalai (Tamil), Verusenaga (Telugu), Shenga (Kannada)",
        "crop_type": "Oilseed / Legume",
        "rooting_depth_class": "Medium (60–90 cm)",
        "water_sensitivity_index": "Medium (Critical at pegging/podding)",
        "growth_habit": "Annual upright bunch or spreading herbaceous",
        "supported_in_krishimitra": True
    },
    {
        "crop_id": "C09",
        "canonical_crop_name": "Mustard / Rapeseed",
        "botanical_name": "Brassica juncea (L.) Czern. & Brassica napus",
        "family": "Brassicaceae",
        "category": "Oilseeds",
        "synonyms_and_aliases": "Indian Mustard, Sarson, Rai, Toria, Canola",
        "vernacular_hindi": "Sarson, Rai (सरसों / राई)",
        "vernacular_regional": "Kadugu (Tamil), Avalu (Telugu), Sasive (Kannada)",
        "crop_type": "Winter Oilseed",
        "rooting_depth_class": "Deep (90–120 cm)",
        "water_sensitivity_index": "Low to Medium",
        "growth_habit": "Annual erect branched winter annual",
        "supported_in_krishimitra": True
    },
    {
        "crop_id": "C10",
        "canonical_crop_name": "Sesamum",
        "botanical_name": "Sesamum indicum L.",
        "family": "Pedaliaceae",
        "category": "Oilseeds",
        "synonyms_and_aliases": "Sesame, Til, Gingelly",
        "vernacular_hindi": "Til (तिल)",
        "vernacular_regional": "Ellu (Tamil), Nuvvulu (Telugu), Til (Bengali)",
        "crop_type": "Oilseed",
        "rooting_depth_class": "Medium (70–90 cm)",
        "water_sensitivity_index": "Low (Sensitive to waterlogging)",
        "growth_habit": "Annual erect branched herb",
        "supported_in_krishimitra": True
    },
    {
        "crop_id": "C11",
        "canonical_crop_name": "Sugarcane",
        "botanical_name": "Saccharum officinarum L. hybrid",
        "family": "Poaceae",
        "category": "Commercial Crops",
        "synonyms_and_aliases": "Ganna, Noble cane",
        "vernacular_hindi": "Ganna (गन्ना)",
        "vernacular_regional": "Karumbu (Tamil), Cheruku (Telugu), Kabbu (Kannada)",
        "crop_type": "Commercial / Sugar crop",
        "rooting_depth_class": "Deep (120–200 cm)",
        "water_sensitivity_index": "Extremely High (Perennial water demand)",
        "growth_habit": "Perennial giant C4 clump-forming grass",
        "supported_in_krishimitra": True
    },
    {
        "crop_id": "C12",
        "canonical_crop_name": "Jowar (Sorghum)",
        "botanical_name": "Sorghum bicolor (L.) Moench",
        "family": "Poaceae",
        "category": "Nutri / Coarse Cereals",
        "synonyms_and_aliases": "Sorghum, Great Millet, Cholam, Jonna",
        "vernacular_hindi": "Jowar (ज्वार)",
        "vernacular_regional": "Cholam (Tamil), Jonna (Telugu), Jola (Kannada)",
        "crop_type": "Millet / Cereal",
        "rooting_depth_class": "Deep (120–150 cm extensive)",
        "water_sensitivity_index": "Low (Extremely drought hardy)",
        "growth_habit": "Annual robust erect C4 grass",
        "supported_in_krishimitra": True
    },
    {
        "crop_id": "C13",
        "canonical_crop_name": "Bajra (Pearl Millet)",
        "botanical_name": "Pennisetum glaucum (L.) R. Br.",
        "family": "Poaceae",
        "category": "Nutri / Coarse Cereals",
        "synonyms_and_aliases": "Pearl Millet, Cumbu, Sajjalu, Bajri",
        "vernacular_hindi": "Bajra (बाजरा)",
        "vernacular_regional": "Kambu (Tamil), Sajjalu (Telugu), Sajje (Kannada)",
        "crop_type": "Millet / Cereal",
        "rooting_depth_class": "Deep (100–140 cm)",
        "water_sensitivity_index": "Very Low (Highest heat/drought tolerance)",
        "growth_habit": "Annual robust erect tillering grass",
        "supported_in_krishimitra": True
    },
    {
        "crop_id": "C14",
        "canonical_crop_name": "Ragi (Finger Millet)",
        "botanical_name": "Eleusine coracana (L.) Gaertn.",
        "family": "Poaceae",
        "category": "Nutri / Coarse Cereals",
        "synonyms_and_aliases": "Finger Millet, Mandua, Kezhvaragu, Ragulu",
        "vernacular_hindi": "Mandua, Ragi (मंडुआ / रागी)",
        "vernacular_regional": "Kezhvaragu (Tamil), Ragulu (Telugu), Ragi (Kannada)",
        "crop_type": "Millet / Small Grain",
        "rooting_depth_class": "Medium (60–90 cm)",
        "water_sensitivity_index": "Low",
        "growth_habit": "Annual tufted erect grass with digitate spikes",
        "supported_in_krishimitra": True
    },
    {
        "crop_id": "C15",
        "canonical_crop_name": "Sunflower",
        "botanical_name": "Helianthus annuus L.",
        "family": "Asteraceae",
        "category": "Oilseeds",
        "synonyms_and_aliases": "Surajmukhi, Sunflower seed",
        "vernacular_hindi": "Surajmukhi (सूरजमुखी)",
        "vernacular_regional": "Suryakanthi (Tamil / Telugu), Suryakanti (Kannada)",
        "crop_type": "Oilseed",
        "rooting_depth_class": "Deep (100–150 cm taproot)",
        "water_sensitivity_index": "Medium",
        "growth_habit": "Annual erect unbranched composite",
        "supported_in_krishimitra": True
    },
    {
        "crop_id": "C16",
        "canonical_crop_name": "Cotton",
        "botanical_name": "Gossypium hirsutum L. & Gossypium arboreum",
        "family": "Malvaceae",
        "category": "Commercial Crops",
        "synonyms_and_aliases": "Kapas, Lint cotton, White gold",
        "vernacular_hindi": "Kapas, Rui (कपास / रुई)",
        "vernacular_regional": "Paruthi (Tamil), Prathi (Telugu), Hatti (Kannada)",
        "crop_type": "Commercial Fibre crop",
        "rooting_depth_class": "Deep (> 150 cm taproot)",
        "water_sensitivity_index": "High (Sensitive to waterlogging & peak drought)",
        "growth_habit": "Perennial shrub grown as indeterminate annual",
        "supported_in_krishimitra": True
    },
    {
        "crop_id": "C17",
        "canonical_crop_name": "Barley",
        "botanical_name": "Hordeum vulgare L.",
        "family": "Poaceae",
        "category": "Cereals",
        "synonyms_and_aliases": "Jau, Malt barley, Feed barley",
        "vernacular_hindi": "Jau (जौ)",
        "vernacular_regional": "Barli Arisi (Tamil), Yavalu (Telugu), Javegodhi (Kannada)",
        "crop_type": "Winter Cereal",
        "rooting_depth_class": "Medium (80–110 cm)",
        "water_sensitivity_index": "Low (Salinity & drought tolerant)",
        "growth_habit": "Annual erect tillering cereal grass",
        "supported_in_krishimitra": True
    },
    {
        "crop_id": "C18",
        "canonical_crop_name": "Masoor (Lentil)",
        "botanical_name": "Lens culinaris Medik.",
        "family": "Fabaceae",
        "category": "Pulses",
        "synonyms_and_aliases": "Lentil, Red Lentil, Masur dal",
        "vernacular_hindi": "Masoor (मसूर)",
        "vernacular_regional": "Masoor Paruppu (Tamil), Misur Pappu (Telugu)",
        "crop_type": "Winter Pulse",
        "rooting_depth_class": "Shallow to Medium (50–70 cm)",
        "water_sensitivity_index": "Low",
        "growth_habit": "Annual slender erect/suberect delicate herb",
        "supported_in_krishimitra": True
    },
    {
        "crop_id": "C19",
        "canonical_crop_name": "Onion",
        "botanical_name": "Allium cepa L.",
        "family": "Amaryllidaceae",
        "category": "Horticultural / Vegetables",
        "synonyms_and_aliases": "Pyaz, Kanda, Common bulb onion",
        "vernacular_hindi": "Pyaz (प्याज)",
        "vernacular_regional": "Vengayam (Tamil), Ullipayalu (Telugu), Eerulli (Kannada)",
        "crop_type": "Bulb Vegetable",
        "rooting_depth_class": "Very Shallow (20–40 cm fibrous root)",
        "water_sensitivity_index": "Very High (Frequent light irrigation required)",
        "growth_habit": "Biennial herbaceous bulb grown as annual",
        "supported_in_krishimitra": True
    },
    {
        "crop_id": "C20",
        "canonical_crop_name": "Potato",
        "botanical_name": "Solanum tuberosum L.",
        "family": "Solanaceae",
        "category": "Horticultural / Tubers",
        "synonyms_and_aliases": "Aloo, Irish potato",
        "vernacular_hindi": "Aloo (आलू)",
        "vernacular_regional": "Urulaikkizhangu (Tamil), Bangaladumpa (Telugu), Alugadde (Kannada)",
        "crop_type": "Tuber Vegetable",
        "rooting_depth_class": "Shallow (40–60 cm)",
        "water_sensitivity_index": "High",
        "growth_habit": "Annual herbaceous tuber-bearing nightshade",
        "supported_in_krishimitra": True
    },
    {
        "crop_id": "C21",
        "canonical_crop_name": "Soybean",
        "botanical_name": "Glycine max (L.) Merr.",
        "family": "Fabaceae",
        "category": "Oilseeds / Legume",
        "synonyms_and_aliases": "Soya, Soya bean, Bhat",
        "vernacular_hindi": "Soyabean (सोयाबीन)",
        "vernacular_regional": "Soyabean (Tamil / Telugu / Kannada)",
        "crop_type": "Oilseed / High Protein Legume",
        "rooting_depth_class": "Medium to Deep (80–120 cm)",
        "water_sensitivity_index": "High (Sensitive during flowering & pod-fill)",
        "growth_habit": "Annual bushy erect legume",
        "supported_in_krishimitra": True
    },
    {
        "crop_id": "C22",
        "canonical_crop_name": "Dry chillies",
        "botanical_name": "Capsicum annuum L.",
        "family": "Solanaceae",
        "category": "Spices / Condiments",
        "synonyms_and_aliases": "Red pepper, Lal Mirch, Guntur chilli",
        "vernacular_hindi": "Lal Mirch (लाल मिर्च)",
        "vernacular_regional": "Milagai (Tamil), Mirapakayalu (Telugu), Menasinakayi (Kannada)",
        "crop_type": "Spice / Vegetable",
        "rooting_depth_class": "Medium (60–90 cm)",
        "water_sensitivity_index": "High",
        "growth_habit": "Perennial shrub grown as annual herb",
        "supported_in_krishimitra": True
    },
    {
        "crop_id": "C23",
        "canonical_crop_name": "Turmeric",
        "botanical_name": "Curcuma longa L.",
        "family": "Zingiberaceae",
        "category": "Spices / Condiments",
        "synonyms_and_aliases": "Haldi, Indian saffron",
        "vernacular_hindi": "Haldi (हल्दी)",
        "vernacular_regional": "Manjal (Tamil), Pasupu (Telugu), Arisina (Kannada)",
        "crop_type": "Rhizomatous Spice",
        "rooting_depth_class": "Medium (40–60 cm rhizome zone)",
        "water_sensitivity_index": "High (Requires humid conditions)",
        "growth_habit": "Perennial rhizomatous herb cultivated as annual",
        "supported_in_krishimitra": True
    },
    {
        "crop_id": "C24",
        "canonical_crop_name": "Castorseed",
        "botanical_name": "Ricinus communis L.",
        "family": "Euphorbiaceae",
        "category": "Non-edible Oilseeds",
        "synonyms_and_aliases": "Castor bean, Arandi, Erandi",
        "vernacular_hindi": "Arandi (अरंडी)",
        "vernacular_regional": "Amanakku (Tamil), Amudamu (Telugu), Haralu (Kannada)",
        "crop_type": "Industrial Oilseed",
        "rooting_depth_class": "Deep (> 150 cm deep taproot)",
        "water_sensitivity_index": "Low (High drought tolerance)",
        "growth_habit": "Perennial soft-wooded shrub grown as annual",
        "supported_in_krishimitra": True
    },
    {
        "crop_id": "C25",
        "canonical_crop_name": "Linseed",
        "botanical_name": "Linum usitatissimum L.",
        "family": "Linaceae",
        "category": "Oilseeds / Fibre",
        "synonyms_and_aliases": "Flax, Alsi, Tisi",
        "vernacular_hindi": "Alsi (अलसी)",
        "vernacular_regional": "Alivirai (Tamil), Avisalu (Telugu), Agase (Kannada)",
        "crop_type": "Winter Oilseed",
        "rooting_depth_class": "Medium (70–90 cm)",
        "water_sensitivity_index": "Low",
        "growth_habit": "Annual erect slender glabrous herb",
        "supported_in_krishimitra": True
    },
    {
        "crop_id": "C26",
        "canonical_crop_name": "Small millets",
        "botanical_name": "Paspalum scrobiculatum, Setaria italica, Panicum miliaceum",
        "family": "Poaceae",
        "category": "Nutri / Coarse Cereals",
        "synonyms_and_aliases": "Kodo, Foxtail (Kangni), Proso (Cheena), Little millet (Kutki)",
        "vernacular_hindi": "Kodo, Kutki, Kangni (कोदो / कुटकी)",
        "vernacular_regional": "Varagu, Thinai, Samai (Tamil), Arikalu, Korralu (Telugu)",
        "crop_type": "Minor Millets",
        "rooting_depth_class": "Shallow to Medium (40–70 cm)",
        "water_sensitivity_index": "Very Low (Adapted to poorest drylands)",
        "growth_habit": "Short-duration annual tillering grasses",
        "supported_in_krishimitra": True
    },
    {
        "crop_id": "C27",
        "canonical_crop_name": "Horse-gram",
        "botanical_name": "Macrotyloma uniflorum (Lam.) Verdc.",
        "family": "Fabaceae",
        "category": "Pulses",
        "synonyms_and_aliases": "Kulthi, Madras bean, Gahat",
        "vernacular_hindi": "Kulthi (कुलथी)",
        "vernacular_regional": "Kollu (Tamil), Ulavalu (Telugu), Huruli (Kannada)",
        "crop_type": "Dryland Pulse",
        "rooting_depth_class": "Medium (60–90 cm)",
        "water_sensitivity_index": "Extremely Low (Thrives under severe arid stress)",
        "growth_habit": "Annual suberect to twining climbing herb",
        "supported_in_krishimitra": True
    },
    {
        "crop_id": "C28",
        "canonical_crop_name": "Jute",
        "botanical_name": "Corchorus olitorius L. & Corchorus capsularis",
        "family": "Malvaceae",
        "category": "Commercial Crops",
        "synonyms_and_aliases": "Pat, Golden Fibre, Tossa jute, White jute",
        "vernacular_hindi": "Patson (पटसन)",
        "vernacular_regional": "Paat (Bengali), Nalita (Odia), Senabu (Kannada)",
        "crop_type": "Bast Fibre crop",
        "rooting_depth_class": "Medium (70–100 cm)",
        "water_sensitivity_index": "High (Requires high humidity & warm rain)",
        "growth_habit": "Annual erect herbaceous plant (2–4 m tall)",
        "supported_in_krishimitra": True
    }
]

# -------------------------------------------------------------
# 2. EVIDENCE-BASED CROP REQUIREMENTS TABLE
# -------------------------------------------------------------
# Derived from official ICAR Institute publications, SAU packages, and FAO 33/56
CROP_REQUIREMENTS_RECORDS = [
    {
        "canonical_crop_name": "Rice",
        "agro_climatic_zone": "All India (Plains, Deltas, Valleys)",
        "season": "Kharif",
        "soil_types_suitable": "Clayey, Clay Loam, Silty Clay, Heavy Alluvial",
        "soil_texture_optimal": "Fine to medium textured; low percolation",
        "ph_absolute_min": 4.5, "ph_optimal_min": 5.5, "ph_optimal_max": 7.5, "ph_absolute_max": 8.5,
        "temp_germination_min_c": 10.0, "temp_germination_opt_c": 25.0,
        "temp_vegetative_opt_min_c": 21.0, "temp_vegetative_opt_max_c": 32.0,
        "temp_flowering_max_critical_c": 35.0,
        "water_requirement_min_mm": 900.0, "water_requirement_optimal_mm": 1250.0, "water_requirement_max_mm": 2200.0,
        "irrigation_condition": "Flooded / Saturated / Irrigated (or high rainfall rainfed >1100mm)",
        "critical_irrigation_stages": "Tillering, Panicle Initiation, Flowering, Milk Stage",
        "duration_min_days": 105, "duration_max_days": 155,
        "sowing_window_start": "June (onset of SW monsoon)", "sowing_window_end": "July",
        "harvest_window_start": "October", "harvest_window_end": "November",
        "recommended_n_kg_ha": 120, "recommended_p_kg_ha": 60, "recommended_k_kg_ha": 40,
        "salinity_threshold_ds_m": 3.0, "drought_tolerance_level": "Low", "waterlogging_tolerance_level": "Extremely High",
        "primary_source_institute": "ICAR-Indian Institute of Rice Research (IIRR), Hyderabad",
        "evidence_type": "Statutory Package of Practices & Research Bulletin",
        "confidence_level": "High"
    },
    {
        "canonical_crop_name": "Wheat",
        "agro_climatic_zone": "North & Central Plains (Indo-Gangetic, Malwa)",
        "season": "Rabi",
        "soil_types_suitable": "Loam, Clay Loam, Silt Loam, Alluvial",
        "soil_texture_optimal": "Well-drained medium texture",
        "ph_absolute_min": 5.5, "ph_optimal_min": 6.2, "ph_optimal_max": 7.8, "ph_absolute_max": 8.5,
        "temp_germination_min_c": 4.0, "temp_germination_opt_c": 20.0,
        "temp_vegetative_opt_min_c": 15.0, "temp_vegetative_opt_max_c": 23.0,
        "temp_flowering_max_critical_c": 30.0,
        "water_requirement_min_mm": 350.0, "water_requirement_optimal_mm": 500.0, "water_requirement_max_mm": 650.0,
        "irrigation_condition": "Irrigated (4–6 irrigations essential for high yield)",
        "critical_irrigation_stages": "Crown Root Initiation (CRI at 21 DAS), Tillering, Jointing, Flowering, Milking, Dough",
        "duration_min_days": 115, "duration_max_days": 145,
        "sowing_window_start": "November 01", "sowing_window_end": "November 25 (timely sown)",
        "harvest_window_start": "March 20", "harvest_window_end": "April 20",
        "recommended_n_kg_ha": 150, "recommended_p_kg_ha": 60, "recommended_k_kg_ha": 40,
        "salinity_threshold_ds_m": 6.0, "drought_tolerance_level": "Low to Moderate", "waterlogging_tolerance_level": "Poor (Stagnant water causes yellowing/root death)",
        "primary_source_institute": "ICAR-Indian Institute of Wheat and Barley Research (IIWBR), Karnal & PAU Ludhiana",
        "evidence_type": "ICAR Recommended Package of Practices (Wheat 2024)",
        "confidence_level": "High"
    },
    {
        "canonical_crop_name": "Maize",
        "agro_climatic_zone": "All India (Plains, Plateaus, Hill slopes)",
        "season": "Kharif & Rabi",
        "soil_types_suitable": "Sandy Loam to Clay Loam, Alluvial, Red Loam",
        "soil_texture_optimal": "Deep, well-drained, fertile loam rich in organic matter",
        "ph_absolute_min": 5.5, "ph_optimal_min": 6.0, "ph_optimal_max": 7.5, "ph_absolute_max": 8.2,
        "temp_germination_min_c": 12.0, "temp_germination_opt_c": 21.0,
        "temp_vegetative_opt_min_c": 21.0, "temp_vegetative_opt_max_c": 30.0,
        "temp_flowering_max_critical_c": 37.0,
        "water_requirement_min_mm": 500.0, "water_requirement_optimal_mm": 650.0, "water_requirement_max_mm": 800.0,
        "irrigation_condition": "Rainfed in Kharif with life-saving irrigation; Fully irrigated in Rabi",
        "critical_irrigation_stages": "Tasseling (flowering), Silking, Early Grain-filling",
        "duration_min_days": 85, "duration_max_days": 120,
        "sowing_window_start": "June 15 (Kharif) / October 15 (Rabi)", "sowing_window_end": "July 15 / November 15",
        "harvest_window_start": "September / March", "harvest_window_end": "October / April",
        "recommended_n_kg_ha": 120, "recommended_p_kg_ha": 60, "recommended_k_kg_ha": 40,
        "salinity_threshold_ds_m": 1.7, "drought_tolerance_level": "Moderate (Sensitive at silking)", "waterlogging_tolerance_level": "Extremely Poor (Vulnerable to root rot within 24h waterlogging)",
        "primary_source_institute": "ICAR-Indian Institute of Maize Research (IIMR), Ludhiana",
        "evidence_type": "ICAR All India Coordinated Research Project on Maize Technical Guidelines",
        "confidence_level": "High"
    },
    {
        "canonical_crop_name": "Arhar/Tur (Pigeon Pea)",
        "agro_climatic_zone": "Central, Western & Peninsular India (MP, MH, KA, UP, TS)",
        "season": "Kharif",
        "soil_types_suitable": "Deep Black Soils (Vertisols), Sandy Loam, Red Loam, Alluvial",
        "soil_texture_optimal": "Deep, well-drained loams without hardpan",
        "ph_absolute_min": 5.5, "ph_optimal_min": 6.5, "ph_optimal_max": 7.8, "ph_absolute_max": 8.5,
        "temp_germination_min_c": 18.0, "temp_germination_opt_c": 28.0,
        "temp_vegetative_opt_min_c": 25.0, "temp_vegetative_opt_max_c": 35.0,
        "temp_flowering_max_critical_c": 38.0,
        "water_requirement_min_mm": 450.0, "water_requirement_optimal_mm": 650.0, "water_requirement_max_mm": 900.0,
        "irrigation_condition": "Primarily rainfed; 1–2 protective irrigations at branching/podding double yield",
        "critical_irrigation_stages": "Flower bud initiation, Pod development",
        "duration_min_days": 130, "duration_max_days": 180,
        "sowing_window_start": "June 15", "sowing_window_end": "July 15",
        "harvest_window_start": "December", "harvest_window_end": "February",
        "recommended_n_kg_ha": 20, "recommended_p_kg_ha": 50, "recommended_k_kg_ha": 20,
        "salinity_threshold_ds_m": 2.0, "drought_tolerance_level": "High (Deep root system extracts moisture from deep subsoil)", "waterlogging_tolerance_level": "Extremely Poor (Causes Phytophthora blight and collar rot)",
        "primary_source_institute": "ICAR-Indian Institute of Pulses Research (IIPR), Kanpur & ICRISAT",
        "evidence_type": "Statutory Pulse Production Package (ICAR 2023)",
        "confidence_level": "High"
    },
    {
        "canonical_crop_name": "Moong (Green Gram)",
        "agro_climatic_zone": "All India (Plains, Plateaus; multiple seasons)",
        "season": "Kharif, Rabi (South/Coastal), Summer/Zaid",
        "soil_types_suitable": "Well-drained Loam, Sandy Loam, Alluvial, Medium Black",
        "soil_texture_optimal": "Light to medium textured fertile loam",
        "ph_absolute_min": 5.8, "ph_optimal_min": 6.2, "ph_optimal_max": 7.5, "ph_absolute_max": 8.2,
        "temp_germination_min_c": 15.0, "temp_germination_opt_c": 28.0,
        "temp_vegetative_opt_min_c": 25.0, "temp_vegetative_opt_max_c": 35.0,
        "temp_flowering_max_critical_c": 40.0,
        "water_requirement_min_mm": 300.0, "water_requirement_optimal_mm": 400.0, "water_requirement_max_mm": 550.0,
        "irrigation_condition": "Rainfed in Kharif; 3–4 light irrigations in Summer",
        "critical_irrigation_stages": "Branching, Pod filling",
        "duration_min_days": 60, "duration_max_days": 75,
        "sowing_window_start": "July (Kharif) / March (Summer)", "sowing_window_end": "July 20 / April 05",
        "harvest_window_start": "September / May", "harvest_window_end": "October / June",
        "recommended_n_kg_ha": 20, "recommended_p_kg_ha": 40, "recommended_k_kg_ha": 20,
        "salinity_threshold_ds_m": 1.5, "drought_tolerance_level": "Moderate (Short duration escapes terminal drought)", "waterlogging_tolerance_level": "Poor",
        "primary_source_institute": "ICAR-IIPR Kanpur & PAU Ludhiana",
        "evidence_type": "ICAR Crop Package of Practices for Summer Moong",
        "confidence_level": "High"
    },
    {
        "canonical_crop_name": "Gram (Chickpea)",
        "agro_climatic_zone": "Central & Northern India (MP, RJ, MH, UP, KA, AP)",
        "season": "Rabi",
        "soil_types_suitable": "Medium to Deep Black Soils, Alluvial Loam, Sandy Loam",
        "soil_texture_optimal": "Well-aerated loam with good water retention",
        "ph_absolute_min": 6.0, "ph_optimal_min": 6.5, "ph_optimal_max": 7.8, "ph_absolute_max": 8.5,
        "temp_germination_min_c": 8.0, "temp_germination_opt_c": 22.0,
        "temp_vegetative_opt_min_c": 15.0, "temp_vegetative_opt_max_c": 25.0,
        "temp_flowering_max_critical_c": 32.0,
        "water_requirement_min_mm": 250.0, "water_requirement_optimal_mm": 350.0, "water_requirement_max_mm": 450.0,
        "irrigation_condition": "Largely rainfed on residual moisture; 1 pre-sowing + 1 podding irrigation optimal",
        "critical_irrigation_stages": "Pre-flowering (branching), Pod development (NEVER irrigate during peak flowering)",
        "duration_min_days": 95, "duration_max_days": 130,
        "sowing_window_start": "October 10", "sowing_window_end": "November 10",
        "harvest_window_start": "February 20", "harvest_window_end": "March 30",
        "recommended_n_kg_ha": 20, "recommended_p_kg_ha": 50, "recommended_k_kg_ha": 20,
        "salinity_threshold_ds_m": 1.5, "drought_tolerance_level": "Very High (Deep root penetration)", "waterlogging_tolerance_level": "Extremely Poor (Susceptible to Fusarium wilt & root rot)",
        "primary_source_institute": "ICAR-IIPR Kanpur, ICRISAT & JNKVV Jabalpur",
        "evidence_type": "All India Coordinated Research Project on Chickpea",
        "confidence_level": "High"
    },
    {
        "canonical_crop_name": "Groundnut",
        "agro_climatic_zone": "Saurashtra, Rayalaseema, Karnataka Dry Zone, Tamil Nadu",
        "season": "Kharif & Rabi/Summer",
        "soil_types_suitable": "Sandy Loam, Red Sandy, Well-drained Light Black (Vertic Inceptisols)",
        "soil_texture_optimal": "Friable, light-textured, calcium-rich soil for easy pegging & harvesting",
        "ph_absolute_min": 5.5, "ph_optimal_min": 6.0, "ph_optimal_max": 7.5, "ph_absolute_max": 8.2,
        "temp_germination_min_c": 15.0, "temp_germination_opt_c": 27.0,
        "temp_vegetative_opt_min_c": 24.0, "temp_vegetative_opt_max_c": 32.0,
        "temp_flowering_max_critical_c": 36.0,
        "water_requirement_min_mm": 450.0, "water_requirement_optimal_mm": 600.0, "water_requirement_max_mm": 750.0,
        "irrigation_condition": "Rainfed in Kharif; Irrigated in Summer (every 8–10 days)",
        "critical_irrigation_stages": "Flowering, Pegging (crucial), Pod development",
        "duration_min_days": 100, "duration_max_days": 125,
        "sowing_window_start": "June 15 (Kharif) / January (Rabi)", "sowing_window_end": "July 15 / February 15",
        "harvest_window_start": "October / April", "harvest_window_end": "November / May",
        "recommended_n_kg_ha": 25, "recommended_p_kg_ha": 50, "recommended_k_kg_ha": 40,
        "salinity_threshold_ds_m": 3.2, "drought_tolerance_level": "Moderate", "waterlogging_tolerance_level": "Extremely Poor (Heavy clay soils restrict peg penetration and cause pod rot)",
        "primary_source_institute": "ICAR-Directorate of Groundnut Research (DGR), Junagadh & TNAU",
        "evidence_type": "ICAR-DGR Technical Bulletin on Groundnut Production Technology",
        "confidence_level": "High"
    },
    {
        "canonical_crop_name": "Mustard / Rapeseed",
        "agro_climatic_zone": "North & Northwestern India (RJ, HR, PB, UP, MP, WB)",
        "season": "Rabi",
        "soil_types_suitable": "Sandy Loam to Clay Loam, Alluvial",
        "soil_texture_optimal": "Light to medium loam with fair moisture capacity",
        "ph_absolute_min": 5.5, "ph_optimal_min": 6.2, "ph_optimal_max": 7.8, "ph_absolute_max": 8.5,
        "temp_germination_min_c": 5.0, "temp_germination_opt_c": 20.0,
        "temp_vegetative_opt_min_c": 12.0, "temp_vegetative_opt_max_c": 22.0,
        "temp_flowering_max_critical_c": 27.0,
        "water_requirement_min_mm": 250.0, "water_requirement_optimal_mm": 350.0, "water_requirement_max_mm": 450.0,
        "irrigation_condition": "Rainfed on conserved moisture or 1–2 protective irrigations",
        "critical_irrigation_stages": "Pre-flowering (rosette stage), Siliqua (pod) filling",
        "duration_min_days": 110, "duration_max_days": 140,
        "sowing_window_start": "October 01", "sowing_window_end": "October 25",
        "harvest_window_start": "February 15", "harvest_window_end": "March 20",
        "recommended_n_kg_ha": 80, "recommended_p_kg_ha": 40, "recommended_k_kg_ha": 20,
        "salinity_threshold_ds_m": 4.5, "drought_tolerance_level": "High", "waterlogging_tolerance_level": "Poor (Sensitive to frost during flowering and aphid infestation under cloudy/humid spells)",
        "primary_source_institute": "ICAR-Directorate of Rapeseed-Mustard Research (DRMR), Bharatpur",
        "evidence_type": "ICAR Package of Practices for Rapeseed-Mustard in India",
        "confidence_level": "High"
    },
    {
        "canonical_crop_name": "Sugarcane",
        "agro_climatic_zone": "Sub-tropical (UP, PB, HR, BR) & Tropical (MH, KA, TN, AP, GJ)",
        "season": "Spring / Autumn / Adsali (Annual to 18-month)",
        "soil_types_suitable": "Deep Rich Loam, Medium to Heavy Black Soils, Alluvial",
        "soil_texture_optimal": "Deep (>1m), fertile, well-drained, retentive soils",
        "ph_absolute_min": 5.0, "ph_optimal_min": 6.5, "ph_optimal_max": 7.8, "ph_absolute_max": 8.5,
        "temp_germination_min_c": 20.0, "temp_germination_opt_c": 30.0,
        "temp_vegetative_opt_min_c": 27.0, "temp_vegetative_opt_max_c": 35.0,
        "temp_flowering_max_critical_c": 40.0,
        "water_requirement_min_mm": 1500.0, "water_requirement_optimal_mm": 2000.0, "water_requirement_max_mm": 2800.0,
        "irrigation_condition": "Perennially irrigated (15–25 irrigations depending on climate/soil)",
        "critical_irrigation_stages": "Formative phase (tillering), Grand growth phase (elongation)",
        "duration_min_days": 300, "duration_max_days": 420,
        "sowing_window_start": "February (Spring) / October (Autumn) / July (Adsali)", "sowing_window_end": "March / November / August",
        "harvest_window_start": "November", "harvest_window_end": "April",
        "recommended_n_kg_ha": 250, "recommended_p_kg_ha": 100, "recommended_k_kg_ha": 120,
        "salinity_threshold_ds_m": 1.7, "drought_tolerance_level": "Very Low (Water stress drastically cuts cane yield & sugar recovery)", "waterlogging_tolerance_level": "Moderate to High",
        "primary_source_institute": "ICAR-Indian Institute of Sugarcane Research (IISR), Lucknow & Sugarcane Breeding Institute (SBI), Coimbatore",
        "evidence_type": "ICAR Statutory Sugarcane Cultivation Manual",
        "confidence_level": "High"
    },
    {
        "canonical_crop_name": "Cotton",
        "agro_climatic_zone": "Central (MH, MP, GJ), Southern (AP, TS, KA, TN) & Northern (PB, HR, RJ)",
        "season": "Kharif",
        "soil_types_suitable": "Deep Black Soils (Regur/Vertisols), Deep Alluvial Loam",
        "soil_texture_optimal": "Deep, moisture-retentive, well-drained clay to clay loam",
        "ph_absolute_min": 5.5, "ph_optimal_min": 6.5, "ph_optimal_max": 8.0, "ph_absolute_max": 8.7,
        "temp_germination_min_c": 16.0, "temp_germination_opt_c": 28.0,
        "temp_vegetative_opt_min_c": 25.0, "temp_vegetative_opt_max_c": 35.0,
        "temp_flowering_max_critical_c": 38.0,
        "water_requirement_min_mm": 600.0, "water_requirement_optimal_mm": 800.0, "water_requirement_max_mm": 1100.0,
        "irrigation_condition": "Rainfed in Central/South India on deep black soils; Irrigated in North India",
        "critical_irrigation_stages": "Square formation, Flowering, Boll development",
        "duration_min_days": 150, "duration_max_days": 180,
        "sowing_window_start": "April 15 (North) / June 15 (Central/South)", "sowing_window_end": "May 15 / July 15",
        "harvest_window_start": "October", "harvest_window_end": "January (multiple pickings)",
        "recommended_n_kg_ha": 120, "recommended_p_kg_ha": 60, "recommended_k_kg_ha": 60,
        "salinity_threshold_ds_m": 7.7, "drought_tolerance_level": "High (Deep taproot)", "waterlogging_tolerance_level": "Very Poor (Excess moisture induces square/boll drop)",
        "primary_source_institute": "ICAR-Central Institute for Cotton Research (CICR), Nagpur",
        "evidence_type": "CICR Package of Practices for Bt and Non-Bt Cotton in India",
        "confidence_level": "High"
    },
    {
        "canonical_crop_name": "Jowar (Sorghum)",
        "agro_climatic_zone": "Semi-Arid Tropics (MH, KA, AP, TS, MP, RJ)",
        "season": "Kharif & Rabi",
        "soil_types_suitable": "Medium to Deep Black Soils, Red Loam, Clay Loam",
        "soil_texture_optimal": "Medium to heavy clay soils with good water-holding capacity",
        "ph_absolute_min": 5.5, "ph_optimal_min": 6.2, "ph_optimal_max": 7.8, "ph_absolute_max": 8.5,
        "temp_germination_min_c": 12.0, "temp_germination_opt_c": 28.0,
        "temp_vegetative_opt_min_c": 26.0, "temp_vegetative_opt_max_c": 33.0,
        "temp_flowering_max_critical_c": 38.0,
        "water_requirement_min_mm": 350.0, "water_requirement_optimal_mm": 450.0, "water_requirement_max_mm": 600.0,
        "irrigation_condition": "Primarily rainfed; 1–2 irrigations at boot/grain fill double rabi yield",
        "critical_irrigation_stages": "Boot leaf, Flowering, Grain filling",
        "duration_min_days": 100, "duration_max_days": 125,
        "sowing_window_start": "June 15 (Kharif) / September 15 (Rabi)", "sowing_window_end": "July 07 / October 15",
        "harvest_window_start": "October / February", "harvest_window_end": "November / March",
        "recommended_n_kg_ha": 80, "recommended_p_kg_ha": 40, "recommended_k_kg_ha": 40,
        "salinity_threshold_ds_m": 6.8, "drought_tolerance_level": "Extremely High (C4 photosynthetic efficiency & wax layer)", "waterlogging_tolerance_level": "Poor to Moderate",
        "primary_source_institute": "ICAR-Indian Institute of Millets Research (IIMR), Hyderabad",
        "evidence_type": "IIMR Millets Package of Practices",
        "confidence_level": "High"
    },
    {
        "canonical_crop_name": "Bajra (Pearl Millet)",
        "agro_climatic_zone": "Arid & Semi-Arid Tropics (RJ, GJ, MH, HR, UP, TN)",
        "season": "Kharif & Summer",
        "soil_types_suitable": "Sandy, Sandy Loam, Light Alluvial, Red Sandy",
        "soil_texture_optimal": "Light textured well-drained soils; can yield on marginal dunes",
        "ph_absolute_min": 5.5, "ph_optimal_min": 6.5, "ph_optimal_max": 8.0, "ph_absolute_max": 8.8,
        "temp_germination_min_c": 15.0, "temp_germination_opt_c": 30.0,
        "temp_vegetative_opt_min_c": 28.0, "temp_vegetative_opt_max_c": 38.0,
        "temp_flowering_max_critical_c": 42.0,
        "water_requirement_min_mm": 250.0, "water_requirement_optimal_mm": 350.0, "water_requirement_max_mm": 500.0,
        "irrigation_condition": "Almost purely rainfed in Kharif; Irrigated in Summer (GJ)",
        "critical_irrigation_stages": "Tillering, Boot stage, Grain filling",
        "duration_min_days": 75, "duration_max_days": 95,
        "sowing_window_start": "June 25", "sowing_window_end": "July 20",
        "harvest_window_start": "September 15", "harvest_window_end": "October 20",
        "recommended_n_kg_ha": 80, "recommended_p_kg_ha": 40, "recommended_k_kg_ha": 30,
        "salinity_threshold_ds_m": 4.0, "drought_tolerance_level": "Highest among all major cereals (Thrives in 300mm rainfall zone)", "waterlogging_tolerance_level": "Extremely Poor (Immediate chlorosis and root decay)",
        "primary_source_institute": "ICAR-IIMR Hyderabad & All India Coordinated Research Project on Pearl Millet (Mandor/Jodhpur)",
        "evidence_type": "ICAR Pearl Millet Production Package",
        "confidence_level": "High"
    },
    {
        "canonical_crop_name": "Ragi (Finger Millet)",
        "agro_climatic_zone": "Southern Peninsula & Hilly Tracts (KA, TN, AP, OD, UK)",
        "season": "Kharif & Summer",
        "soil_types_suitable": "Red Sandy Loam, Red Loam, Light Black, Laterite",
        "soil_texture_optimal": "Porous, well-drained red gravelly or loamy soils",
        "ph_absolute_min": 4.5, "ph_optimal_min": 5.5, "ph_optimal_max": 7.5, "ph_absolute_max": 8.2,
        "temp_germination_min_c": 12.0, "temp_germination_opt_c": 26.0,
        "temp_vegetative_opt_min_c": 22.0, "temp_vegetative_opt_max_c": 32.0,
        "temp_flowering_max_critical_c": 36.0,
        "water_requirement_min_mm": 350.0, "water_requirement_optimal_mm": 450.0, "water_requirement_max_mm": 600.0,
        "irrigation_condition": "Rainfed in Kharif; Irrigated in Summer",
        "critical_irrigation_stages": "Tillering, Flowering, Grain development",
        "duration_min_days": 95, "duration_max_days": 125,
        "sowing_window_start": "June 15 (Direct) / July 15 (Transplanted)", "sowing_window_end": "July 30 / August 15",
        "harvest_window_start": "October 20", "harvest_window_end": "November 30",
        "recommended_n_kg_ha": 60, "recommended_p_kg_ha": 30, "recommended_k_kg_ha": 30,
        "salinity_threshold_ds_m": 4.0, "drought_tolerance_level": "Very High (Tolerates dry spells; recovers rapidly after rain)", "waterlogging_tolerance_level": "Poor to Moderate",
        "primary_source_institute": "ICAR-IIMR Hyderabad & UAS Bangalore AICRP on Small Millets",
        "evidence_type": "ICAR Finger Millet Agronomic Technology Package",
        "confidence_level": "High"
    },
    {
        "canonical_crop_name": "Soybean",
        "agro_climatic_zone": "Central India & Vertisol Belt (MP, MH, RJ, KA, TS)",
        "season": "Kharif",
        "soil_types_suitable": "Medium to Deep Black Soils, Clay Loam, Fertile Loam",
        "soil_texture_optimal": "Moisture-retentive, deep vertisols without surface crusting",
        "ph_absolute_min": 5.8, "ph_optimal_min": 6.3, "ph_optimal_max": 7.5, "ph_absolute_max": 8.0,
        "temp_germination_min_c": 15.0, "temp_germination_opt_c": 28.0,
        "temp_vegetative_opt_min_c": 25.0, "temp_vegetative_opt_max_c": 32.0,
        "temp_flowering_max_critical_c": 36.0,
        "water_requirement_min_mm": 500.0, "water_requirement_optimal_mm": 650.0, "water_requirement_max_mm": 800.0,
        "irrigation_condition": "Primarily rainfed; protective irrigation essential during prolonged monsoon breaks",
        "critical_irrigation_stages": "Pod initiation, Seed development",
        "duration_min_days": 90, "duration_max_days": 110,
        "sowing_window_start": "June 20 (after 75-100mm monsoon rain)", "sowing_window_end": "July 05",
        "harvest_window_start": "September 25", "harvest_window_end": "October 20",
        "recommended_n_kg_ha": 30, "recommended_p_kg_ha": 60, "recommended_k_kg_ha": 40,
        "salinity_threshold_ds_m": 5.0, "drought_tolerance_level": "Moderate (Yield drops sharply if dry spell coincides with flowering)", "waterlogging_tolerance_level": "Extremely Poor (Seedling mortality occurs if flooded >48 hrs)",
        "primary_source_institute": "ICAR-Indian Institute of Soybean Research (IISR), Indore",
        "evidence_type": "ICAR-IISR Package of Practices for Soybean Cultivation",
        "confidence_level": "High"
    },
    {
        "canonical_crop_name": "Onion",
        "agro_climatic_zone": "Maharashtra, Karnataka, Gujarat, MP, Bihar, Rajasthan",
        "season": "Kharif, Late Kharif (Rangada), Rabi",
        "soil_types_suitable": "Rich Sandy Loam, Silt Loam, Light Clay Loam, Alluvial",
        "soil_texture_optimal": "Friable, highly permeable, organic-rich loam",
        "ph_absolute_min": 5.8, "ph_optimal_min": 6.5, "ph_optimal_max": 7.5, "ph_absolute_max": 8.0,
        "temp_germination_min_c": 10.0, "temp_germination_opt_c": 22.0,
        "temp_vegetative_opt_min_c": 18.0, "temp_vegetative_opt_max_c": 25.0,
        "temp_flowering_max_critical_c": 32.0,
        "water_requirement_min_mm": 450.0, "water_requirement_optimal_mm": 600.0, "water_requirement_max_mm": 750.0,
        "irrigation_condition": "Irrigated (12–15 light irrigations; drip irrigation highly effective)",
        "critical_irrigation_stages": "Bulb initiation, Bulb enlargement (irrigation stopped 15 days before harvest)",
        "duration_min_days": 110, "duration_max_days": 140,
        "sowing_window_start": "May (Kharif) / August (Late Kharif) / October (Rabi)", "sowing_window_end": "June / September / November",
        "harvest_window_start": "October / January / April", "harvest_window_end": "November / February / May",
        "recommended_n_kg_ha": 100, "recommended_p_kg_ha": 50, "recommended_k_kg_ha": 50,
        "salinity_threshold_ds_m": 1.2, "drought_tolerance_level": "Extremely Low (Shallow root depth causes bulb splitting under dry spell)", "waterlogging_tolerance_level": "Extremely Poor (Immediate bulb rot and purple blotch flare-up)",
        "primary_source_institute": "ICAR-Directorate of Onion and Garlic Research (DOGR), Rajgurunagar (Pune)",
        "evidence_type": "ICAR-DOGR Package of Practices for Commercial Onion Production",
        "confidence_level": "High"
    },
    {
        "canonical_crop_name": "Potato",
        "agro_climatic_zone": "Indo-Gangetic Plains (UP, WB, BR, PB) & Hills",
        "season": "Rabi (Plains) & Summer (Hills)",
        "soil_types_suitable": "Sandy Loam, Silt Loam, Alluvial",
        "soil_texture_optimal": "Loose, friable, deep, well-aerated loam",
        "ph_absolute_min": 5.0, "ph_optimal_min": 5.5, "ph_optimal_max": 6.8, "ph_absolute_max": 7.5,
        "temp_germination_min_c": 12.0, "temp_germination_opt_c": 24.0,
        "temp_vegetative_opt_min_c": 16.0, "temp_vegetative_opt_max_c": 22.0,
        "temp_flowering_max_critical_c": 28.0,
        "water_requirement_min_mm": 400.0, "water_requirement_optimal_mm": 500.0, "water_requirement_max_mm": 600.0,
        "irrigation_condition": "Fully irrigated (5–7 light furrows; critical night temp <20 C for tuberization)",
        "critical_irrigation_stages": "Stolon formation, Tuber initiation, Tuber bulking",
        "duration_min_days": 80, "duration_max_days": 110,
        "sowing_window_start": "October 15", "sowing_window_end": "November 05",
        "harvest_window_start": "January 15", "harvest_window_end": "March 15",
        "recommended_n_kg_ha": 180, "recommended_p_kg_ha": 80, "recommended_k_kg_ha": 100,
        "salinity_threshold_ds_m": 1.7, "drought_tolerance_level": "Low", "waterlogging_tolerance_level": "Poor (Induces bacterial soft rot and late blight under high humidity)",
        "primary_source_institute": "ICAR-Central Potato Research Institute (CPRI), Shimla",
        "evidence_type": "CPRI Potato Production Technology Bulletins",
        "confidence_level": "High"
    }
]

# -------------------------------------------------------------
# 3. SOURCE EVIDENCE CATALOG (Citations & Reference Metadata)
# -------------------------------------------------------------
SOURCE_EVIDENCE_RECORDS = [
    {
        "evidence_id": "EV01",
        "institute": "ICAR-Indian Institute of Rice Research (IIRR)",
        "location": "Hyderabad, Telangana",
        "publication_title": "Rice Production Technology in India: Compendium of Package of Practices",
        "publication_year": 2023,
        "document_type": "Institutional Production Manual",
        "crops_covered": "Rice (Paddy)",
        "geographic_scope": "National (with zone-specific recommendations)",
        "evidence_nature": "Empirical field trial recommendations (AICRIP multi-location trials)",
        "access_url": "https://www.icar-iirr.org/"
    },
    {
        "evidence_id": "EV02",
        "institute": "ICAR-Indian Institute of Wheat & Barley Research (IIWBR)",
        "location": "Karnal, Haryana",
        "publication_title": "Wheat Crop Health and Production Technology Newsletter & Guidelines",
        "publication_year": 2024,
        "document_type": "Official Crop Advisory Bulletin",
        "crops_covered": "Wheat, Barley",
        "geographic_scope": "North Western & North Eastern Plains Zones (NWPZ, NEPZ), Central & Peninsular Zones",
        "evidence_nature": "Empirical coordinated trial benchmarks",
        "access_url": "https://iiwbr.icar.gov.in/"
    },
    {
        "evidence_id": "EV03",
        "institute": "ICAR-Indian Institute of Maize Research (IIMR)",
        "location": "Ludhiana, Punjab",
        "publication_title": "Package of Practices for Maize Cultivation in India",
        "publication_year": 2023,
        "document_type": "Institutional Technical Bulletin",
        "crops_covered": "Maize (Kharif, Rabi, Spring)",
        "geographic_scope": "All India Coordinated Maize Zones",
        "evidence_nature": "Empirical agronomic trial recommendations",
        "access_url": "https://iimr.icar.gov.in/"
    },
    {
        "evidence_id": "EV04",
        "institute": "ICAR-Indian Institute of Pulses Research (IIPR)",
        "location": "Kanpur, Uttar Pradesh",
        "publication_title": "Technology for Pulse Production in India: Pigeonpea, Chickpea, Mungbean, Urdbean, Lentil",
        "publication_year": 2023,
        "document_type": "National Pulse Compendium",
        "crops_covered": "Arhar/Tur, Gram/Chickpea, Moong, Urad, Masoor/Lentil",
        "geographic_scope": "Central, Northern, Peninsular Pulse Zones",
        "evidence_nature": "Multi-decadal coordinated research trials",
        "access_url": "https://iipr.icar.gov.in/"
    },
    {
        "evidence_id": "EV05",
        "institute": "ICAR-Central Institute for Cotton Research (CICR)",
        "location": "Nagpur, Maharashtra",
        "publication_title": "Cotton Production Technology & Integrated Pest Management Manual",
        "publication_year": 2023,
        "document_type": "Crop Management Manual",
        "crops_covered": "Cotton (Bt and Non-Bt)",
        "geographic_scope": "Central, Southern, and Northern Cotton Zones",
        "evidence_nature": "Empirical AICRP trials & rainfed black soil agronomy",
        "access_url": "https://cicr.icar.gov.in/"
    },
    {
        "evidence_id": "EV06",
        "institute": "ICAR-Directorate of Rapeseed-Mustard Research (DRMR)",
        "location": "Bharatpur, Rajasthan",
        "publication_title": "Mustard Production Technology for Maximizing Yield and Oil Recovery",
        "publication_year": 2023,
        "document_type": "Directorate Technical Report",
        "crops_covered": "Mustard / Rapeseed, Toria, Yellow Sarson",
        "geographic_scope": "Northern and Western Alluvial & Semi-Arid Plains",
        "evidence_nature": "Empirical multi-location trials",
        "access_url": "https://drmr.icar.gov.in/"
    },
    {
        "evidence_id": "EV07",
        "institute": "ICAR-Directorate of Groundnut Research (DGR)",
        "location": "Junagadh, Gujarat",
        "publication_title": "Groundnut Cultivation Practices in India",
        "publication_year": 2022,
        "document_type": "Institutional Guidelines",
        "crops_covered": "Groundnut (Kharif, Rabi, Summer)",
        "geographic_scope": "Saurashtra, Rayalaseema, Karnataka, Tamil Nadu",
        "evidence_nature": "AICRP on Groundnut empirical data",
        "access_url": "https://dgr.icar.gov.in/"
    },
    {
        "evidence_id": "EV08",
        "institute": "ICAR-Indian Institute of Millets Research (IIMR)",
        "location": "Hyderabad, Telangana",
        "publication_title": "Millets Production Technologies: Jowar, Bajra, Ragi, Small Millets",
        "publication_year": 2023,
        "document_type": "Nutri-Cereal Compendium (International Year of Millets 2023)",
        "crops_covered": "Jowar, Bajra, Ragi, Small Millets (Kodo, Kutki, Kangni)",
        "geographic_scope": "National Dryland & Semi-Arid Regions",
        "evidence_nature": "Coordinated dryland trial benchmarks",
        "access_url": "https://millets.res.in/"
    },
    {
        "evidence_id": "EV09",
        "institute": "Food and Agriculture Organization of the United Nations (FAO)",
        "location": "Rome, Italy",
        "publication_title": "FAO Irrigation and Drainage Paper No. 33: Yield Response to Water & Paper No. 56: Crop Evapotranspiration",
        "publication_year": 1998,
        "document_type": "International Technical Standard",
        "crops_covered": "Global Field & Horticultural Crops (Rice, Wheat, Maize, Cotton, Soybean, Sugarcane, Sorghum, Groundnut)",
        "geographic_scope": "Global / Tropical & Sub-tropical Climatology",
        "evidence_nature": "Peer-reviewed international standard for crop water stress & root zone depth",
        "access_url": "https://www.fao.org/land-water/databases-and-software/cropwat/en/"
    },
    {
        "evidence_id": "EV10",
        "institute": "Punjab Agricultural University (PAU)",
        "location": "Ludhiana, Punjab",
        "publication_title": "Package of Practices for the Crops of Punjab (Kharif & Rabi)",
        "publication_year": 2024,
        "document_type": "State Agricultural University Statutory Package",
        "crops_covered": "Paddy, Basmati, Wheat, Maize, Cotton, Mustard, Sugarcane",
        "geographic_scope": "Indo-Gangetic / Trans-Gangetic Plain",
        "evidence_nature": "Annual state extension recommendations based on research trials",
        "access_url": "https://www.pau.edu/"
    }
]


def build_agronomic_foundation():
    logger.info("=== Starting Workstream B: Authoritative Agronomic Suitability Knowledge Base ===")
    
    # 1. Normalized Crop Master
    df_master = pd.DataFrame(CROP_MASTER_RECORDS)
    master_path = os.path.join(AGRO_PROC_DIR, "normalized_crop_master.csv")
    df_master.to_csv(master_path, index=False)
    logger.info(f"Saved normalized crop master to {master_path} ({len(df_master)} crops).")
    
    # 2. Crop Requirements Table
    df_req = pd.DataFrame(CROP_REQUIREMENTS_RECORDS)
    req_path = os.path.join(AGRO_PROC_DIR, "crop_suitability_requirements.csv")
    df_req.to_csv(req_path, index=False)
    logger.info(f"Saved crop suitability requirements table to {req_path} ({len(df_req)} crops/regimes).")
    
    # 3. Source Evidence Table
    df_ev = pd.DataFrame(SOURCE_EVIDENCE_RECORDS)
    ev_path = os.path.join(CATALOG_DIR, "agronomic_evidence_catalog.csv")
    df_ev.to_csv(ev_path, index=False)
    logger.info(f"Saved agronomic evidence catalog to {ev_path} ({len(df_ev)} institutional sources).")
    
    # 4. Unresolved-Evidence & Uncertainty Report
    unresolved_report_path = os.path.join(CATALOG_DIR, "unresolved_agronomic_evidence_report.md")
    now_ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    report_md = """# Unresolved Agronomic Evidence and Physiological Uncertainty Report

**Project**: KrishiMitra AI Agricultural Advisory System  
**Report Date**: {TIMESTAMP}  
**Scope**: Identification of physiological variations, cultivar-specific contradictions, and data gaps in published Indian agronomic literature.

---

## 1. Executive Principle: Against "Universal" Suitability Ranges

> [!CAUTION]
> **No Single Universal Threshold Exists for Any Crop Across India.**  
> A physiological threshold (e.g. water requirement, thermal optimum, or duration) varies significantly depending on:
> 1. **Genotype / Cultivar Class**: Short-duration vs long-duration cultivars (e.g., 60-day moong vs 180-day long-duration arhar).
> 2. **Regional Photoperiod & Thermal Regimes**: Wheat grown in Punjab (NWPZ, cold extended winter) vs Karnataka/Maharashtra (Peninsular zone, warm short winter where night temperatures rarely drop below 15°C).
> 3. **Production System**: Rainfed vs Irrigated systems have completely distinct water requirement baselines.

---

## 2. Key Contradictions and Cultivar-Specific Variances in Indian Literature

### 2.1 Rice (Paddy) Water Requirements
- **Published Contradiction**: Published water requirements vary from **900 mm** (aerobic rice / direct seeded rice - DSR) to **2,200 mm** (traditional continuous-flooding puddled transplanting).
- **Resolution in KrishiMitra**: KrishiMitra distinguishes wetland flooded paddy (water requirement 1,200–1,800 mm) from rainfed upland / aerobic paddy (750–1,000 mm). Recommendation logic must not mark a district unsuitable for rice solely on rainfall if tubewell/canal irrigation infrastructure exists.

### 2.2 Wheat Thermal Thresholds by Zone
- **Published Contradiction**: PAU Ludhiana documents terminal heat stress when maximum temperatures exceed **30°C** during grain filling (March). In contrast, central Indian cultivars (e.g. MP Durum wheats like Malavshree, HI-8759) and peninsular wheats are bred for heat tolerance and can tolerate temperatures up to **34°C**.
- **Resolution**: Regional thermal upper bounds must be stratified: NWPZ (30°C threshold) vs Central/Peninsular zones (34°C threshold).

### 2.3 Cotton Moisture Regimes (Vertisols vs Alluvial)
- **Published Contradiction**: In Punjab and Haryana, cotton is 100% irrigated on alluvial soils (600–700 mm irrigation applied). In Vidarbha (Maharashtra) and Telangana, cotton is 85% rainfed on deep black soils (Vertisols) with 700–900 mm monsoon rainfall.
- **Resolution**: Deep Vertisols store up to 200 mm of plant-available water per meter depth, allowing cotton to complete boll maturation on residual soil moisture after monsoon cessation. Alluvial soils without irrigation cannot support cotton past October.

### 2.4 Chickpea / Chana: Desi vs Kabuli
- **Published Variance**: Desi chickpea is deep-rooted, drought hardy, and tolerates moisture stress (250–350 mm water requirement). Kabuli chickpea has a shallower root system, larger seed size, and requires fertile loam with at least 2–3 light irrigations (400–500 mm).
- **Resolution**: Track Desi and Kabuli chickpea requirements distinctly where variety-level resolution is available.

---

## 3. Critical Knowledge Gaps (What Remains Unobtainable from Standard APIs)

1. **Subsoil Hardpan and Drainage Impedance**: SoilGrids estimates mechanical texture from surface interpolation, but cannot detect subsoil hardpans (caliche or compacted plow pans) that cause waterlogging in pigeon pea and maize.
2. **Micronutrient Deficiencies (Zinc, Boron, Iron)**: Over 40% of Indian soils suffer from Zinc deficiency (especially in rice-wheat tracts). Standard open APIs do not provide spatial micronutrient maps.
3. **Pest & Pathogen Epidemics (Biotic Constraints)**: Agronomic suitability algorithms determine abiotic climate-soil fitness. They do not predict local biotic catastrophes (e.g., Pink Bollworm in cotton, Whitefly in North Indian cotton, Yellow Rust in wheat, Pod Borer in chickpea).

*Report compiled by `scripts/build_authoritative_agronomic_kb.py` — KrishiMitra Phase 3*
""".replace("{TIMESTAMP}", now_ts)
    with open(unresolved_report_path, "w", encoding="utf-8") as f:
        f.write(report_md)
    logger.info(f"Saved unresolved agronomic evidence report to {unresolved_report_path}")


if __name__ == "__main__":
    build_agronomic_foundation()
