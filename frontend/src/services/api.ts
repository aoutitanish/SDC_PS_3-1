import {
  ChatMessage,
  CropSummary,
  FarmProfile,
  LanguageCode,
  LocationData,
  RecommendationResponse,
  SoilAnalysisData,
  WeatherData
} from '../types';

const BASE_URL = import.meta.env.VITE_API_URL || '/api';

export const api = {
  // Chat standard endpoint
  async sendChatMessage(
    message: string,
    language: LanguageCode = 'en',
    location?: LocationData,
    soilType?: string,
    sessionId: string = 'default_session',
    farmProfile?: FarmProfile,
    detailLevel: string = 'simple'
  ) {
    const res = await fetch(`${BASE_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        language,
        session_id: sessionId,
        location,
        soil_type: soilType,
        farm_profile: farmProfile,
        detail_level: detailLevel
      })
    });
    if (!res.ok) throw new Error('Chat API failed');
    return res.json();
  },

  // SSE streaming chat
  async streamChatMessage(
    message: string,
    language: LanguageCode = 'en',
    location?: LocationData,
    soilType?: string,
    sessionId: string = 'default_session',
    farmProfile?: FarmProfile,
    detailLevel: string = 'simple',
    onToken?: (token: string) => void,
    onMetadata?: (meta: any) => void,
    onDone?: () => void,
    onError?: (err: any) => void,
    signal?: AbortSignal
  ) {
    try {
      const response = await fetch(`${BASE_URL}/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal,
        body: JSON.stringify({
          message,
          language,
          session_id: sessionId,
          location,
          soil_type: soilType,
          farm_profile: farmProfile,
          detail_level: detailLevel
        })
      });

      if (!response.ok || !response.body) {
        throw new Error('Streaming connection failed');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.replace('data: ', '').trim();
            if (!dataStr) continue;
            try {
              const parsed = JSON.parse(dataStr);
              if (parsed.type === 'token' && onToken) {
                onToken(parsed.token);
              } else if (parsed.type === 'metadata' && onMetadata) {
                onMetadata(parsed);
              } else if (parsed.type === 'done' && onDone) {
                onDone();
              }
            } catch (e) {
              console.error('SSE parse error:', e);
            }
          }
        }
      }
      if (onDone) onDone();
    } catch (err) {
      if (onError) onError(err);
    }
  },

  // Crop Recommendation
  async getCropRecommendation(params: Record<string, any>): Promise<RecommendationResponse> {
    const res = await fetch(`${BASE_URL}/recommend`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    });
    if (!res.ok) throw new Error('Recommendation API failed');
    return res.json();
  },

  // Soil Analysis
  async analyzeSoil(params: Record<string, any>): Promise<SoilAnalysisData> {
    const res = await fetch(`${BASE_URL}/soil/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    });
    if (!res.ok) throw new Error('Soil Analysis API failed');
    return res.json();
  },

  // Weather
  async getWeather(params: { state?: string; district?: string; lat?: number; lon?: number }): Promise<WeatherData> {
    const query = new URLSearchParams();
    if (params.state) query.append('state', params.state);
    if (params.district) query.append('district', params.district);
    if (params.lat) query.append('lat', params.lat.toString());
    if (params.lon) query.append('lon', params.lon.toString());

    const res = await fetch(`${BASE_URL}/weather?${query.toString()}`);
    if (!res.ok) throw new Error('Weather API failed');
    return res.json();
  },

  // Crops Encyclopedia
  async getCrops(search?: string, season?: string, state?: string): Promise<{ crops: CropSummary[]; total_count: number }> {
    const query = new URLSearchParams();
    if (search) query.append('search', search);
    if (season) query.append('season', season);
    if (state) query.append('state', state);

    const res = await fetch(`${BASE_URL}/crops?${query.toString()}`);
    if (!res.ok) throw new Error('Crops listing API failed');
    return res.json();
  },

  async getCropDetail(cropName: string) {
    const res = await fetch(`${BASE_URL}/crops/${encodeURIComponent(cropName)}`);
    if (!res.ok) throw new Error('Crop detail API failed');
    return res.json();
  },

  // Geography
  async getStates(): Promise<string[]> {
    const res = await fetch(`${BASE_URL}/geography/states`);
    if (!res.ok) return [];
    const data = await res.json();
    return data.states || [];
  },

  async getDistricts(state?: string): Promise<{ State_Name: string; District_Name: string; latitude: number; longitude: number }[]> {
    const query = state ? `?state=${encodeURIComponent(state)}` : '';
    const res = await fetch(`${BASE_URL}/geography/districts${query}`);
    if (!res.ok) return [];
    const data = await res.json();
    return data.districts || [];
  },

  // Farm Profile
  async getFarmProfile(userId: string = 'guest'): Promise<FarmProfile> {
    const res = await fetch(`${BASE_URL}/farm?user_id=${userId}`);
    if (!res.ok) throw new Error('Get farm profile failed');
    const data = await res.json();
    return data.profile;
  },

  async saveFarmProfile(profile: FarmProfile, userId: string = 'guest') {
    const res = await fetch(`${BASE_URL}/farm?user_id=${userId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(profile)
    });
    if (!res.ok) throw new Error('Save farm profile failed');
    return res.json();
  },

  // Admin & Health
  async getAdminStatus() {
    const res = await fetch(`${BASE_URL}/admin/status`);
    if (!res.ok) throw new Error('Admin status API failed');
    return res.json();
  },

  async getHealth() {
    const res = await fetch(`${BASE_URL}/health`);
    if (!res.ok) return { status: 'offline' };
    return res.json();
  },

  // History
  async getChatHistory(sessionId: string) {
    const res = await fetch(`${BASE_URL}/chat/history/${sessionId}`);
    if (!res.ok) return { messages: [] };
    return res.json();
  },

  async clearChatHistory(sessionId: string) {
    const res = await fetch(`${BASE_URL}/chat/history/${sessionId}`, { method: 'DELETE' });
    return res.json();
  },

  // Market & Profit Intelligence
  async getMarketPrices(crop: string, state?: string, district?: string) {
    const query = new URLSearchParams({ crop });
    if (state) query.append('state', state);
    if (district) query.append('district', district);
    const res = await fetch(`${BASE_URL}/market/prices?${query.toString()}`);
    if (!res.ok) throw new Error('Market prices API failed');
    return res.json();
  },

  async calculateEconomics(payload: {
    crop?: string;
    farm_size_acres?: number;
    price_inr_per_quintal?: number;
    cultivation_cost_inr_per_acre?: number;
    yield_quintals_per_acre?: number;
    crops?: any[];
  }) {
    const res = await fetch(`${BASE_URL}/market/economics`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error('Economics calculation API failed');
    return res.json();
  },

  async getPostHarvest(
    crop: string,
    farmSizeAcres?: number,
    harvestQuantityQuintals?: number,
    currentPrice?: number,
    farmerGoal?: string
  ) {
    const query = new URLSearchParams({ crop });
    if (farmSizeAcres) query.append('farm_size_acres', farmSizeAcres.toString());
    if (harvestQuantityQuintals) query.append('harvest_quantity_quintals', harvestQuantityQuintals.toString());
    if (currentPrice) query.append('current_price', currentPrice.toString());
    if (farmerGoal) query.append('farmer_goal', farmerGoal);
    const res = await fetch(`${BASE_URL}/market/post-harvest?${query.toString()}`);
    if (!res.ok) throw new Error('Post-harvest API failed');
    return res.json();
  }
};

