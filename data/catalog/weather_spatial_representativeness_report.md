# Weather Spatial Representativeness & Agro-Climatic Coverage Report

## 1. Overview & Data Sources
- **Source**: NASA Prediction Of Worldwide Energy Resources (POWER) Project
- **Meteorological Model**: Goddard Earth Observing System (GEOS) / MERRA-2 Meteorological Assimilation Model
- **Spatial Resolution**: 0.5° latitude $\times$ 0.5° longitude grid cell spacing ($\approx 55\text{ km} \times 55\text{ km}$)
- **Temporal Coverage**:
  - **Monthly Climate Normals**: 1981–2023 (43 continuous calendar years, 516 months per district) across **55 representative districts** covering all 15 Agro-Climatic Zones of India (**28,380 monthly observations**).
  - **Daily Agro-Meteorology**: 2020–2023 (1,461 daily records per district) across **10 anchor agricultural districts** (**14,610 daily observations**).

---

## 2. Essential Provenance & Scientific Distinctions

> [!IMPORTANT]
> **Reanalysis Model Estimates $\neq$ Ground Station Observations**
> NASA POWER data are derived from satellite observations and the MERRA-2 global atmospheric reanalysis model. They represent grid-box spatial area averages, NOT point measurements from an IMD meteorological surface station.
> 
> Key scientific distinctions:
> 1. **Grid-Cell Area Averaging**: A 0.5° grid averages precipitation and temperature over $\sim 3,000\text{ km}^2$. Local microclimatic thunderstorms and localized hail/frost are smoothed.
> 2. **Precipitation Conversion**: Monthly precipitation ($mm$) was derived from daily corrected precipitation rate (`PRECTOTCORR`, $mm/\text{day}$) multiplied by the exact calendar days in each month.
> 3. **Annual Aggregation Artifacts Removed**: NASA POWER raw files report a 13th month representing the annual mean. All 13th-month entries have been filtered out of time-series alignment.

---

## 3. Topographic and Agro-Climatic Zone Representativeness

### 3.1 Indo-Gangetic Plains & Trans-Gangetic Plain (High Representativeness)
- **Districts**: Ludhiana, Amritsar, Bathinda (Punjab); Karnal, Hisar, Ambala (Haryana); Meerut, Agra, Kanpur, Varanasi (UP); Patna, Muzaffarpur (Bihar); Bardhaman (West Bengal).
- **Evaluation**: Topography is predominantly flat alluvial plains ($< 250\text{ m}$ elevation). Spatial heterogeneity across a 0.5° cell is low. MERRA-2 reanalysis captures temperature, monsoon onset, winter cold waves, and solar radiation with high fidelity.

### 3.2 Deccan & Central Plateau Regions (High to Moderate Representativeness)
- **Districts**: Indore, Ujjain, Bhopal, Jabalpur (MP); Raipur, Bilaspur (Chhattisgarh); Ranchi (Jharkhand); Nagpur, Pune, Ahmednagar, Solapur (Maharashtra); Kurnool, Anantapur (AP); Warangal, Nizamabad (Telangana); Dharwad, Raichur, Belagavi, Mysuru (Karnataka).
- **Evaluation**: Undulating plateau topography ($300\text{ m} - 800\text{ m}$). Macroclimatic monsoon rainfall gradients and thermal regimes are well represented. In rain-shadow scarcity zones (Ahmednagar, Solapur, Anantapur), the 0.5° grid accurately identifies chronic moisture deficit and prolonged dry spells.

### 3.3 Coastal Plains & Deltaic Regions (Moderate Representativeness)
- **Districts**: Surat, Rajkot (Gujarat); Cuttack, Puri (Odisha); Thanjavur (Tamil Nadu); Thrissur (Kerala); Guntur (AP).
- **Evaluation**: The interface between sea and land causes sharp gradients in relative humidity, sea breezes, and cyclone precipitation. The 0.5° grid averages marine and land cells along the immediate shoreline. Centroid coordinates were anchored to inland APMC agricultural command areas rather than coastal waters.

### 3.4 Montane & Western Himalayan Region (Limited Spatial Representativeness — Explicit Caution)
- **Districts**: Mandi, Shimla (Himachal Pradesh); Dehradun (Uttarakhand).
- **Evaluation**: Steep vertical elevation gradients (ranging from 700m in valleys to >3,500m on ridgelines within a single district). The 0.5° cell smooths out severe elevation lapse rates ($\sim 6.5^\circ\text{C}$ per 1,000m).
- **Policy**: Data for Mandi, Shimla, and Dehradun represent **valley-level macroclimate** and must not be used as high-altitude alpine weather measurements.

---

## 4. Daily Agro-Climatic Stress Dynamics (2020–2023)

Empirical daily observations across the 10 anchor districts provide critical agro-climatic indicators:
- **Heat Stress Days ($T_{\max} \ge 35^\circ\text{C}$)**: Kurnool (99–177 days/yr), Rajkot (85–130 days/yr), Varanasi (80–115 days/yr). Crucial for identifying terminal heat stress during wheat anthesis and chickpea podding.
- **Extreme Heat Days ($T_{\max} \ge 40^\circ\text{C}$)**: Peak in May–June across Northern and Central plains prior to monsoon arrival.
- **Monsoon Rainfall Concentration**: In Ludhiana, Indore, and Nagpur, **78% to 92%** of annual precipitation falls within the June–September window, leaving the remaining 8 months dependent on residual soil moisture or tubewell/canal irrigation.
- **Max Monsoon Dry Spells**: Consecutive dry days ($< 2.5\text{ mm}$) during the active monsoon season reached **14 to 28 days** in rainfed districts (e.g. Kurnool, Rajkot), directly determining crop failure risk for rainfed Kharif pulses and oilseeds.
- **Growing Degree Days ($\text{GDD}_{10}$)**: Annual accumulated thermal units range from **$4,800\text{ GDD}$** in Punjab to **$>6,500\text{ GDD}$** in Rayalaseema.
