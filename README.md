# 🌾 KrishiMitra AI (కృషిమిత్ర / कृषिमित्र)
### *Sole Agricultural Intelligence Architecture: Local Ollama Qwen 3.5 9B + Dynamic RAG*

KrishiMitra AI is an end-to-end, full-stack agricultural intelligence assistant for Indian farmers. Its sole intelligence architecture is powered by **Local Ollama Qwen 3.5 9B (`"think": false`)** combined with **Dynamic Request-Time Retrieval-Augmented Generation (RAG)** querying permitted, authoritative external agronomic literature repositories (Crossref ICAR/FAO works, OpenAlex agricultural database, and Wikimedia agronomy REST API).

All dependencies on legacy Random Forest crop-prediction models, static crop datasets, hardcoded soil/district lookup tables, and heuristic scoring engines have been completely removed and isolated from the agricultural answer request path.

---

## 🏗️ Architecture & Data Flow

```
                               ┌────────────────────────────────┐
                               │  Farmer / User (Mobile/Web)    │
                               └───────────────┬────────────────┘
                                               │
                                               ▼
                               ┌────────────────────────────────┐
                               │ React + Vite + TypeScript PWA  │
                               │ (Dynamic RAG & Audio Support)  │
                               └───────────────┬────────────────┘
                                               │ (REST & SSE Stream)
                                               ▼
                               ┌────────────────────────────────┐
                               │     FastAPI Backend Router     │
                               └───────────────┬────────────────┘
                                               │
                                               ▼
                               ┌────────────────────────────────┐
                               │   Context Relevance Gate       │
                               │  (Strict Precedence Hierarchy) │
                               └───────┬──────────────┬─────────┘
                                       │              │
                   ┌───────────────────┘              └────────────────────┐
                   ▼                                                       ▼
  ┌─────────────────────────────────┐                     ┌──────────────────────────────────┐
  │   Live Meteorological & Market  │                     │ Dynamic Request-Time RAG Service │
  │    • Open-Meteo High-Res API    │                     │  • Crossref Works (ICAR/FAO)     │
  │    • Agmarknet Live Telemetry   │                     │  • OpenAlex Agricultural Papers  │
  │    (Never fabricated from CSV)  │                     │  • Wikimedia Agronomic REST API  │
  └────────────────┬────────────────┘                     │  • Transient Cache (1-hr TTL)    │
                   │                                      └────────────────┬─────────────────┘
                   │                                                       │
                   └───────────────────┬───────────────────────────────────┘
                                       │ Evidence + Provenance + Direct Query
                                       ▼
                       ┌────────────────────────────────┐
                       │  Sole Local LLM Provider       │
                       │  • Ollama (qwen3.5:9b)         │
                       │  • http://localhost:11434      │
                       │  • POST /api/chat              │
                       │  • "think": false              │
                       └───────────────┬────────────────┘
                                       │ Direct grounded answer + adaptive follow-up
                                       ▼
                       ┌────────────────────────────────┐
                       │ Multilingual Response Engine   │
                       │ (English / తెలుగు / हिंदी)     │
                       │ Real URLs & Source Citations   │
                       └────────────────────────────────┘
```

---

## 🌟 Key Features

1. **Explainable AI Recommendations (XAI)**:
   - Does not just predict a crop name; explains **WHY** the crop fits the farmer's land.
   - Calibrated suitability breakdown across 5 factors: **Soil Texture & Physicochemical Fit**, **Precipitation Alignment**, **Thermal Range**, **Soil pH Window**, and **Nitrogen Reserves**.
   - Qualitative status (**High / Medium / Low**) and risk mitigation warnings (e.g. frost susceptibility, waterlogging risk, alkalinity amendment).
2. **Retrieval-Augmented Generation (RAG)**:
   - Context-grounded retrieval from 668 structured knowledge documents across 637 Indian districts, 105 crops, and official Indian government agricultural schemes (PM-KISAN, PMFBY, Soil Health Card, PMKSY).
   - Zero hallucination policy: Returns verified citations (`[Crop Expert Dataset]`, `[Soil Expert Dataset]`, `[Weather Expert Data]`).
3. **Multilingual Voice & Text**:
   - Native support for **English**, **Telugu (తెలుగు)**, and **Hindi (हिंदी)**.
   - Built-in speech recognition (`webkitSpeechRecognition`) for voice querying.
   - Integrated text-to-speech audio reader (`SpeechSynthesis`) with play, pause, and stop controls.
4. **Live Weather & Agricultural Advisory**:
   - Real-time meteorological telemetry and 7-day forecast via Open-Meteo.
   - Automated agro-advisories (foliar spraying feasibility based on wind speed, fungal disease pressure warnings based on humidity/temp, irrigation planning).
5. **Soil Health Assessment & USDA Texture Calculator**:
   - Interactive Sand %, Silt %, and Clay % sliders with automatic 100% normalization.
   - USDA Texture triangle classification (Clay, Sandy Clay, Clay Loam, Sandy Loam, etc.).
   - Tailored soil amendment advice (e.g., Agricultural Lime for acidic soils, Gypsum/compost for alkaline soils).
6. **"My Farm" Personalized Profile & Offline PWA**:
   - Stores farmer state, district, soil type, irrigation setup, and acreage.
   - Installable PWA with offline caching.
7. **Production Quality & Fault-Tolerant**:
   - Runs with zero crashes even without external LLM API keys via the deterministic Expert Agricultural Reasoning Engine.

---

## 📊 Datasets & Feature Engineering

The system ingests 4 foundational agricultural datasets in `/data`:
1. `master_geography.csv` (643 Indian districts, latitude, longitude, 33 states)
2. `soil_expert.csv` (SoilGrids physical/chemical properties: Bulk density, CEC, Clay %, Sand %, Silt %, Total Nitrogen, pH in H2O, Organic Carbon)
3. `weather_expert.csv` (145,236 monthly records: NASA & IMD rainfall, T2M, T2M_MAX, T2M_MIN, RH2M, WS2M from 1997-2015)
4. `crop_expert.csv` (246,091 historical cultivation records across 105 crops with production and yield in tonnes/ha)

---

## 🚀 Quick Start (Local Setup)

### 1. Prerequisites
- Python 3.10+
- Node.js 18+ / npm

### 2. Backend Setup
```bash
# Clone or navigate to the project directory
cd FarmerHelp

# Optional: Create and activate a virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Run data ingestion & ML training pipeline (if not already built)
python scripts/clean_data.py
python scripts/train_model.py
python scripts/ingest_data.py
python scripts/create_embeddings.py
python scripts/validate_data.py

# Start FastAPI Backend Server
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation will be live at: `http://localhost:8000/api/docs`

### 3. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start Vite Development Server
npm run dev
```
Web Application will be live at: `http://localhost:5173`

---

## 🧪 Running Automated Tests

Run the complete test suite covering ML inference, explainability scoring bounds, RAG vector retrieval, language detection, and FastAPI endpoints:

```bash
python -m pytest tests/test_all.py
```

---

## 🐳 Docker Deployment

To run the complete production stack (Backend + Frontend + Nginx) with Docker Compose:

```bash
docker-compose up --build
```

Access the frontend at `http://localhost:5173` and the backend at `http://localhost:8000/api`.

---

## ⚙️ Environment Variables (`.env`)

| Variable | Default | Description |
| :--- | :--- | :--- |
| `LLM_PROVIDER` | `rule_engine` | Options: `rule_engine`, `gemini`, `openai`, `ollama` |
| `GEMINI_API_KEY` | *(empty)* | Optional Google Gemini API Key |
| `OPENAI_API_KEY` | *(empty)* | Optional OpenAI API Key |
| `WEATHER_API_KEY`| *(empty)* | Optional OpenWeatherMap API Key (Open-Meteo works without key) |
| `DATABASE_URL` | `sqlite:///./krishimitra.db` | SQLite Database Connection URI |
| `VITE_API_URL` | `http://localhost:8000/api` | Backend API URL for Frontend |

---

## 📱 Mobile-First Verification & Demo Flow

1. **Step 1**: Open `http://localhost:5173` on laptop or mobile browser.
2. **Step 2**: Switch language to **తెలుగు** using the top language selector.
3. **Step 3**: Navigate to **AI Assistant (`/chat`)**.
4. **Step 4**: Press the Microphone button (🎤) and ask: *"నల్ల నేలలో ఏ పంట వేయాలి?"*
5. **Step 5**: The system detects Telugu, retrieves soil/crop knowledge, runs Random Forest suitability, and streams a structured explainable recommendation in Telugu with visual suitability percentages.
6. **Step 6**: Press **🔊 వినండి (Listen)** to hear the synthesized audio response aloud.
7. **Step 7**: Navigate to **పంట సిఫార్సు (`/recommend`)** or **నేల విశ్లేషణ (`/soil`)** to test interactive sliders and print/share PDF reports.

---

## 🛡️ Agricultural Safety & Disclaimer

All chemical pest control advice follows CIBRC guidelines and directs farmers to verify official product labels and consult local Agricultural Extension Officers / Krishi Vigyan Kendras (KVK) for exact dosage.
