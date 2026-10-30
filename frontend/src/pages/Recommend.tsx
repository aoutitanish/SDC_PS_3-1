import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { useLanguage } from '../contexts/LanguageContext';
import { useFarm } from '../contexts/FarmContext';
import { RecommendationResponse } from '../types';
import { FactorBreakdownCard } from '../components/explainability/FactorBreakdownCard';
import {
  Sparkles,
  MapPin,
  Layers,
  Droplets,
  Thermometer,
  FlaskConical,
  RotateCcw,
  Printer,
  Share2,
  Check,
  ShieldCheck,
  ChevronRight,
  Sprout
} from 'lucide-react';

export const Recommend: React.FC = () => {
  const { t, language } = useLanguage();
  const { farm } = useFarm();

  const [states, setStates] = useState<string[]>([]);
  const [districts, setDistricts] = useState<{ State_Name: string; District_Name: string }[]>([]);
  
  const [formData, setFormData] = useState({
    state: farm.state || 'Andhra Pradesh',
    district: farm.district || 'Kurnool',
    soil_type: farm.soil_type || 'Black Soil (Regur/Vertisol)',
    ph: 7.1,
    clay_pct: 32.6,
    sand_pct: 39.5,
    silt_pct: 27.9,
    nitrogen_cg_kg: 180.0,
    annual_rainfall_mm: 945.0,
    temperature: 27.2,
    season: 'Kharif',
    irrigation_available: true
  });

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<RecommendationResponse | null>(null);
  const [copiedShare, setCopiedShare] = useState(false);

  useEffect(() => {
    api.getStates().then(setStates).catch(console.error);
  }, []);

  useEffect(() => {
    if (formData.state) {
      api.getDistricts(formData.state).then(setDistricts).catch(console.error);
    }
  }, [formData.state]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await api.getCropRecommendation(formData);
      if (res && res.success) {
        setResult(res);
      }
    } catch (err) {
      console.error("Recommendation failed:", err);
      alert("Failed to compute crop recommendation. Please verify inputs.");
    } finally {
      setLoading(false);
    }
  };

  const handleShare = () => {
    if (!result) return;
    const text = `KrishiMitra AI Crop Recommendation:\nPrimary: ${result.primary_recommendation.crop} (${result.primary_recommendation.confidence_score_pct}% Match)\nLocation: ${formData.district}, ${formData.state}\nSoil: ${formData.soil_type}`;
    navigator.clipboard.writeText(text);
    setCopiedShare(true);
    setTimeout(() => setCopiedShare(false), 2000);
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12 animate-in fade-in">
      
      {/* Header Banner */}
      <div className="bg-gradient-to-br from-[#059669] to-[#047857] text-white p-6 sm:p-8 rounded-3xl shadow-depth flex flex-wrap items-center justify-between gap-4">
        <div>
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/15 backdrop-blur-md text-emerald-100 text-xs font-bold uppercase tracking-wider font-display mb-2">
            <Sparkles className="w-3.5 h-3.5 text-amber-300" />
            <span>FasalMargadarshak • ML Crop Suitability Engine</span>
          </span>
          <h1 className="text-2xl sm:text-4xl font-extrabold tracking-tight font-display">
            Crop Recommendation Studio
          </h1>
          <p className="text-xs sm:text-sm text-emerald-100 mt-1 max-w-xl font-sans">
            Input your farm parameters to generate data-backed suitability rankings with 100% agronomic factor explainability.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Input Form Column (5 Cols) */}
        <div className="lg:col-span-5 bg-white p-6 rounded-3xl border border-[#E2ECE6] shadow-panel space-y-4">
          <h2 className="text-sm font-extrabold uppercase tracking-wider text-[#0F281E] flex items-center gap-2 font-display">
            <FlaskConical className="w-4 h-4 text-[#059669]" />
            <span>Farm Parameters</span>
          </h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            
            {/* State Selection */}
            <div>
              <label className="block text-xs font-bold text-[#526B60] mb-1 font-display">State</label>
              <select
                value={formData.state}
                onChange={(e) => setFormData({ ...formData, state: e.target.value })}
                className="w-full px-3.5 py-2.5 rounded-2xl bg-[#F8FAF9] border border-[#D0E5DA] text-xs font-semibold text-[#0F281E] focus:border-[#059669] focus:outline-none font-sans"
              >
                {states.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>

            {/* District Selection */}
            <div>
              <label className="block text-xs font-bold text-[#526B60] mb-1 font-display">District</label>
              <select
                value={formData.district}
                onChange={(e) => setFormData({ ...formData, district: e.target.value })}
                className="w-full px-3.5 py-2.5 rounded-2xl bg-[#F8FAF9] border border-[#D0E5DA] text-xs font-semibold text-[#0F281E] focus:border-[#059669] focus:outline-none font-sans"
              >
                {districts.map((d, idx) => (
                  <option key={idx} value={d.District_Name}>{d.District_Name}</option>
                ))}
              </select>
            </div>

            {/* Soil Type */}
            <div>
              <label className="block text-xs font-bold text-[#526B60] mb-1 font-display">Soil Group</label>
              <select
                value={formData.soil_type}
                onChange={(e) => setFormData({ ...formData, soil_type: e.target.value })}
                className="w-full px-3.5 py-2.5 rounded-2xl bg-[#F8FAF9] border border-[#D0E5DA] text-xs font-semibold text-[#0F281E] focus:border-[#059669] focus:outline-none font-sans"
              >
                <option value="Black Soil (Regur/Vertisol)">Black Soil (Regur/Vertisol)</option>
                <option value="Red and Yellow Soil">Red and Yellow Soil</option>
                <option value="Alluvial Soil">Alluvial Soil</option>
                <option value="Laterite Soil">Laterite Soil</option>
                <option value="Desert / Arid Soil">Desert / Arid Soil</option>
                <option value="Saline / Alkaline Soil">Saline / Alkaline Soil</option>
              </select>
            </div>

            {/* pH Slider */}
            <div>
              <div className="flex justify-between text-xs font-bold text-[#526B60] mb-1 font-display">
                <span>Soil pH Level</span>
                <span className="font-extrabold text-[#059669]">{formData.ph}</span>
              </div>
              <input
                type="range"
                min="4.5"
                max="9.0"
                step="0.1"
                value={formData.ph}
                onChange={(e) => setFormData({ ...formData, ph: parseFloat(e.target.value) })}
                className="w-full accent-[#059669]"
              />
            </div>

            {/* Rainfall & Temperature Row */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[11px] font-bold text-[#526B60] mb-1 font-display">Rainfall (mm)</label>
                <input
                  type="number"
                  value={formData.annual_rainfall_mm}
                  onChange={(e) => setFormData({ ...formData, annual_rainfall_mm: parseFloat(e.target.value) || 0 })}
                  className="w-full px-3.5 py-2.5 rounded-2xl bg-[#F8FAF9] border border-[#D0E5DA] text-xs font-semibold text-[#0F281E] font-sans"
                />
              </div>

              <div>
                <label className="block text-[11px] font-bold text-[#526B60] mb-1 font-display">Avg Temp (°C)</label>
                <input
                  type="number"
                  value={formData.temperature}
                  onChange={(e) => setFormData({ ...formData, temperature: parseFloat(e.target.value) || 0 })}
                  className="w-full px-3.5 py-2.5 rounded-2xl bg-[#F8FAF9] border border-[#D0E5DA] text-xs font-semibold text-[#0F281E] font-sans"
                />
              </div>
            </div>

            {/* Season Selection */}
            <div>
              <label className="block text-xs font-bold text-[#526B60] mb-1 font-display">Cultivation Season</label>
              <select
                value={formData.season}
                onChange={(e) => setFormData({ ...formData, season: e.target.value })}
                className="w-full px-3.5 py-2.5 rounded-2xl bg-[#F8FAF9] border border-[#D0E5DA] text-xs font-semibold text-[#0F281E] focus:border-[#059669] focus:outline-none font-sans"
              >
                <option value="Kharif">Kharif (Monsoon Season)</option>
                <option value="Rabi">Rabi (Winter Season)</option>
                <option value="Summer">Summer / Zaid</option>
                <option value="Whole Year">Whole Year (Perennial)</option>
              </select>
            </div>

            {/* Irrigation Checkbox */}
            <div className="flex items-center gap-2.5 pt-1">
              <input
                type="checkbox"
                id="irrigation_available"
                checked={formData.irrigation_available}
                onChange={(e) => setFormData({ ...formData, irrigation_available: e.target.checked })}
                className="w-4 h-4 rounded text-[#059669] accent-[#059669]"
              />
              <label htmlFor="irrigation_available" className="text-xs font-bold text-[#0F281E] font-sans cursor-pointer">
                Drip / Borewell Irrigation Available
              </label>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3.5 rounded-2xl bg-[#059669] hover:bg-[#047857] disabled:opacity-50 text-white font-bold text-sm shadow-md shadow-[#059669]/25 transition flex items-center justify-center gap-2 mt-4 font-display"
            >
              {loading ? (
                <span>Computing Agronomic Model...</span>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 text-amber-300" />
                  <span>Generate Recommendation</span>
                </>
              )}
            </button>

          </form>
        </div>

        {/* Output Column (7 Cols) */}
        <div className="lg:col-span-7 space-y-4">
          {result ? (
            <div className="space-y-4 animate-in fade-in">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-[#526B60] font-display">
                  Suitability Results & Explainability
                </span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleShare}
                    className="px-3 py-1.5 rounded-xl bg-white border border-[#D0E5DA] text-[#526B60] hover:text-[#0F281E] text-xs font-bold flex items-center gap-1.5 shadow-sm font-display"
                  >
                    {copiedShare ? <Check className="w-3.5 h-3.5 text-[#059669]" /> : <Share2 className="w-3.5 h-3.5" />}
                    <span>{copiedShare ? 'Copied' : 'Share'}</span>
                  </button>
                  <button
                    onClick={handlePrint}
                    className="px-3 py-1.5 rounded-xl bg-white border border-[#D0E5DA] text-[#526B60] hover:text-[#0F281E] text-xs font-bold flex items-center gap-1.5 shadow-sm font-display"
                  >
                    <Printer className="w-3.5 h-3.5" />
                    <span>Print</span>
                  </button>
                </div>
              </div>

              {/* Main Factor Breakdown Card */}
              <FactorBreakdownCard
                primary={result.primary_recommendation}
                alternatives={result.alternative_crops}
              />
            </div>
          ) : (
            <div className="h-full min-h-[380px] p-8 rounded-3xl border-2 border-dashed border-[#D0E5DA] bg-white flex flex-col items-center justify-center text-center space-y-3 shadow-panel">
              <div className="w-14 h-14 rounded-2xl bg-[#E8F5EF] border border-[#059669]/20 flex items-center justify-center text-[#059669]">
                <Sprout className="w-7 h-7" />
              </div>
              <h3 className="font-extrabold text-base text-[#0F281E] font-display">Ready for Agronomic Computation</h3>
              <p className="text-xs text-[#526B60] max-w-sm font-sans leading-relaxed">
                Configure your farm's parameters on the left and tap "Generate Recommendation" to view ML predictions with factor breakdowns.
              </p>
            </div>
          )}
        </div>

      </div>

    </div>
  );
};
