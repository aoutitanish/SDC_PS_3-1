# Unresolved Agronomic Evidence and Physiological Uncertainty Report

**Project**: KrishiMitra AI Agricultural Advisory System  
**Report Date**: 2026-10-15 07:05:32 UTC  
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
