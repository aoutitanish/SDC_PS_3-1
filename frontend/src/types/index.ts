export type LanguageCode = 'en' | 'te' | 'hi';

export interface LocationData {
  state?: string;
  district?: string;
  latitude?: number;
  longitude?: number;
}

export interface FactorScores {
  soil_suitability: number;
  rainfall_suitability: number;
  temperature_suitability: number;
  ph_suitability: number;
  nutrient_suitability: number;
}

export interface QualitativeRatings {
  soil: 'High' | 'Medium' | 'Low';
  rainfall: 'High' | 'Medium' | 'Low';
  temperature: 'High' | 'Medium' | 'Low';
  ph: 'High' | 'Medium' | 'Low';
  nutrients: 'High' | 'Medium' | 'Low';
}

export interface PrimaryRecommendation {
  crop: string;
  confidence_score_pct: number;
  confidence_level: 'High' | 'Medium' | 'Low';
  confidence_note: string;
  factor_scores: FactorScores;
  qualitative_ratings: QualitativeRatings;
  supporting_factors: string[];
  potential_limitations: string[];
  benchmark_yield_tonnes_ha: number;
  top_seasons: string[];
  sources: string[];
  actual_values?: Record<string, any>;
  optimal_ranges?: Record<string, any>;
  agronomic_suitability_score?: number;
}

export interface AlternativeCrop {
  crop: string;
  confidence_score_pct: number;
  confidence_level: 'High' | 'Medium' | 'Low';
  factor_scores: FactorScores;
  key_reason: string;
}

export interface RecommendationResponse {
  success: boolean;
  primary_recommendation: PrimaryRecommendation;
  alternative_crops: AlternativeCrop[];
  input_parameters_used: Record<string, any>;
  location_context: {
    state: string;
    district: string;
    soil_group: string;
    irrigation_type?: string;
    season?: string;
  };
}

export interface SourceCitation {
  name: string;
  category?: string;
  title?: string;
  why_used?: string;
}

export interface SimpleFarmerSummary {
  title: string;
  main_crop?: string;
  simple_reason: string[];
  water_requirement?: string;
  season?: string;
  warning?: string;
  next_steps?: string[];
}

export interface DetailedAgronomicAnalysis {
  crop: string;
  agronomic_suitability_score?: number;
  model_confidence?: string;
  soil_parameters?: Record<string, any>;
  climate_parameters?: Record<string, any>;
  water_analysis?: Record<string, any>;
  explainability_factors?: Array<{ factor: string; status: string; impact: string }>;
  sources?: Array<{ name: string; why_used: string }>;
  limitations?: string[];
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  content: string;
  timestamp: string;
  language?: LanguageCode;
  intent?: string;
  simple_summary?: SimpleFarmerSummary | null;
  detailed_analysis?: DetailedAgronomicAnalysis | null;
  sources?: SourceCitation[];
  recommendation_data?: RecommendationResponse | null;
  comparison_data?: any | null;
  confidence?: 'High' | 'Medium' | 'Low';
  isStreaming?: boolean;
  follow_up?: string | null;
  quick_replies?: string[] | null;
  latency_metrics?: Record<string, any> | null;
}

export interface SoilAnalysisData {
  success: boolean;
  soil_profile: {
    usda_texture: string;
    indian_soil_group: string;
    ph: number;
    ph_category: string;
    ph_status: string;
    ph_amendment_advice: string;
    nitrogen_cg_kg: number;
    nitrogen_status: string;
    nitrogen_advice: string;
    organic_carbon_status: string;
    texture_composition: {
      sand_pct: number;
      silt_pct: number;
      clay_pct: number;
    };
  };
  recommendations: RecommendationResponse;
}

export interface WeatherDay {
  date: string;
  max_temp_c: number | null;
  min_temp_c: number | null;
  rainfall_mm: number;
  condition: string;
}

export interface WeatherData {
  success: boolean;
  location: {
    state: string;
    district: string;
    latitude: number;
    longitude: number;
  };
  current: {
    temperature_c: number;
    relative_humidity_pct: number;
    rainfall_mm: number;
    wind_speed_ms: number;
    condition: string;
    weather_code?: number;
  };
  forecast: WeatherDay[];
  agricultural_advisory: string;
  data_source: string;
}

export interface CropSummary {
  crop: string;
  mean_yield_tonnes_ha: number;
  total_records: number;
  top_seasons: string[];
  top_states: string[];
  has_agronomic_profile: boolean;
}

export interface FarmProfile {
  farm_name: string;
  state: string;
  district: string;
  soil_type: string;
  farm_size_acres: number;
  irrigation_type: string;
  primary_crops: string[];
  preferred_language: string;
  season?: string;
  water_source?: string;
  water_availability?: string;
}
