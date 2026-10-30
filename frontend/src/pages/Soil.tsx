import React, { useState } from 'react';
import { api } from '../services/api';
import { useLanguage } from '../contexts/LanguageContext';
import { useFarm } from '../contexts/FarmContext';
import { SoilAnalysisData } from '../types';
import { FactorBreakdownCard } from '../components/explainability/FactorBreakdownCard';
import {
  Layers,
  FlaskConical,
  Sprout,
  ShieldCheck,
  AlertCircle,
  CheckCircle2,
  Sparkles,
  Droplet
} from 'lucide-react';

export const Soil: React.FC = () => {
  const { t } = useLanguage();
  const { farm } = useFarm();

  const [soilForm, setSoilForm] = useState({
    state: farm.state || 'Andhra Pradesh',
    district: farm.district || 'Kurnool',
    ph: 7.0,
    clay_pct: 35.0,
    sand_pct: 35.0,
    silt_pct: 30.0,
    nitrogen_cg_kg: 180.0,
    soc_dg_kg: 210.0
  });

  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState<SoilAnalysisData | null>(null);

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await api.analyzeSoil(soilForm);
      if (res && res.success) {
        setAnalysis(res);
      }
    } catch (err) {
      console.error("Soil analysis error:", err);
      alert("Failed to analyze soil parameters. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12 animate-in fade-in">
      
      {/* Header Banner */}
      <div className="bg-gradient-to-br from-[#059669] to-[#047857] text-white p-6 sm:p-8 rounded-3xl shadow-depth flex flex-wrap items-center justify-between gap-4">
        <div>
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/15 backdrop-blur-md text-emerald-100 text-xs font-bold uppercase tracking-wider font-display mb-2">
            <Layers className="w-3.5 h-3.5 text-amber-300" />
            <span>BhumiPariksha • USDA Soil Texture & Nutrient Studio</span>
          </span>
          <h1 className="text-2xl sm:text-4xl font-extrabold tracking-tight font-display">
            Soil Health & Physicochemical Diagnosis
          </h1>
          <p className="text-xs sm:text-sm text-emerald-100 mt-1 max-w-xl font-sans">
            Evaluate soil texture composition, chemical pH balance, nitrogen reserves, and get personalized amendment advisories.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Sliders & Parameters Form */}
        <div className="lg:col-span-5 bg-white p-6 rounded-3xl border border-[#E2ECE6] shadow-panel space-y-4">
          <h2 className="text-sm font-extrabold uppercase tracking-wider text-[#0F281E] flex items-center gap-2 font-display">
            <FlaskConical className="w-4 h-4 text-[#059669]" />
            <span>Physicochemical Inputs</span>
          </h2>

          <form onSubmit={handleAnalyze} className="space-y-4">
            
            {/* pH Slider */}
            <div>
              <div className="flex justify-between text-xs font-bold text-[#526B60] mb-1 font-display">
                <span>Soil pH Level</span>
                <span className="font-extrabold text-[#059669]">{soilForm.ph}</span>
              </div>
              <input
                type="range"
                min="4.5"
                max="9.0"
                step="0.1"
                value={soilForm.ph}
                onChange={(e) => setSoilForm({ ...soilForm, ph: parseFloat(e.target.value) })}
                className="w-full accent-[#059669]"
              />
              <div className="flex justify-between text-[10px] text-[#526B60] mt-0.5 font-medium">
                <span>Acidic (4.5)</span>
                <span>Neutral (6.5 - 7.5)</span>
                <span>Alkaline (9.0)</span>
              </div>
            </div>

            {/* Clay % Slider */}
            <div>
              <div className="flex justify-between text-xs font-bold text-[#526B60] mb-1 font-display">
                <span>Clay Content</span>
                <span className="font-extrabold text-[#0F281E]">{soilForm.clay_pct}%</span>
              </div>
              <input
                type="range"
                min="5"
                max="65"
                step="1"
                value={soilForm.clay_pct}
                onChange={(e) => setSoilForm({ ...soilForm, clay_pct: parseFloat(e.target.value) })}
                className="w-full accent-[#059669]"
              />
            </div>

            {/* Sand % Slider */}
            <div>
              <div className="flex justify-between text-xs font-bold text-[#526B60] mb-1 font-display">
                <span>Sand Content</span>
                <span className="font-extrabold text-[#0F281E]">{soilForm.sand_pct}%</span>
              </div>
              <input
                type="range"
                min="5"
                max="80"
                step="1"
                value={soilForm.sand_pct}
                onChange={(e) => setSoilForm({ ...soilForm, sand_pct: parseFloat(e.target.value) })}
                className="w-full accent-amber-600"
              />
            </div>

            {/* Silt % Slider */}
            <div>
              <div className="flex justify-between text-xs font-bold text-[#526B60] mb-1 font-display">
                <span>Silt Content</span>
                <span className="font-extrabold text-[#0F281E]">{soilForm.silt_pct}%</span>
              </div>
              <input
                type="range"
                min="5"
                max="65"
                step="1"
                value={soilForm.silt_pct}
                onChange={(e) => setSoilForm({ ...soilForm, silt_pct: parseFloat(e.target.value) })}
                className="w-full accent-blue-600"
              />
            </div>

            {/* Nitrogen Input */}
            <div>
              <div className="flex justify-between text-xs font-bold text-[#526B60] mb-1 font-display">
                <span>Total Nitrogen (cg/kg)</span>
                <span className="font-extrabold text-[#059669]">{soilForm.nitrogen_cg_kg}</span>
              </div>
              <input
                type="range"
                min="50"
                max="400"
                step="5"
                value={soilForm.nitrogen_cg_kg}
                onChange={(e) => setSoilForm({ ...soilForm, nitrogen_cg_kg: parseFloat(e.target.value) })}
                className="w-full accent-[#059669]"
              />
              <div className="flex justify-between text-[10px] text-[#526B60] mt-0.5 font-medium">
                <span>Low (&lt;150)</span>
                <span>Medium (150-250)</span>
                <span>High (&gt;250)</span>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3.5 rounded-2xl bg-[#059669] hover:bg-[#047857] text-white font-bold text-sm shadow-md shadow-[#059669]/25 transition flex items-center justify-center gap-2 mt-2 font-display"
            >
              {loading ? <span>Analyzing Soil Health...</span> : <span>Run Soil Analysis</span>}
            </button>

          </form>
        </div>

        {/* Output & Interpretation Column */}
        <div className="lg:col-span-7 space-y-4">
          {analysis ? (
            <div className="space-y-4 animate-in fade-in">
              
              {/* Soil Health Summary Card */}
              <div className="p-6 rounded-3xl bg-white border border-[#E2ECE6] shadow-panel space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-[#E2ECE6]">
                  <div>
                    <span className="text-xs uppercase font-bold text-[#526B60] font-display">USDA Soil Texture Class</span>
                    <h3 className="text-xl sm:text-2xl font-black text-[#0F281E] font-display">
                      {analysis.soil_profile.usda_texture}
                    </h3>
                  </div>
                  <span className="px-3.5 py-1.5 rounded-full bg-[#E8F5EF] text-[#059669] font-bold text-xs border border-[#059669]/30 font-display">
                    {analysis.soil_profile.indian_soil_group}
                  </span>
                </div>

                {/* pH Status & Amendment Advice */}
                <div className="p-4 rounded-2xl bg-[#F8FAF9] border border-[#D0E5DA] space-y-1">
                  <div className="flex items-center justify-between text-xs font-bold text-[#0F281E] font-display">
                    <span>pH Assessment: {analysis.soil_profile.ph_category}</span>
                    <span className="text-[#059669]">{analysis.soil_profile.ph_status}</span>
                  </div>
                  <p className="text-xs text-[#526B60] leading-relaxed pt-1 font-sans">
                    💡 <strong>Agronomic Guidance:</strong> {analysis.soil_profile.ph_amendment_advice}
                  </p>
                </div>

                {/* Nitrogen Status */}
                <div className="p-4 rounded-2xl bg-[#F0FDF4] border border-[#DCFCE7] space-y-1">
                  <div className="flex items-center justify-between text-xs font-bold text-[#059669] font-display">
                    <span>Available Nitrogen Level</span>
                    <span>{analysis.soil_profile.nitrogen_status}</span>
                  </div>
                  <p className="text-xs text-[#0F281E] leading-relaxed pt-1 font-sans">
                    🌱 {analysis.soil_profile.nitrogen_advice}
                  </p>
                </div>
              </div>

              {/* Recommended Crops for this Soil */}
              {analysis.recommendations?.primary_recommendation && (
                <FactorBreakdownCard
                  primary={analysis.recommendations.primary_recommendation}
                  alternatives={analysis.recommendations.alternative_crops}
                />
              )}

            </div>
          ) : (
            <div className="h-full min-h-[380px] flex flex-col items-center justify-center p-8 rounded-3xl border-2 border-dashed border-[#D0E5DA] bg-white text-center space-y-3 shadow-panel">
              <div className="w-14 h-14 rounded-2xl bg-[#E8F5EF] border border-[#059669]/20 flex items-center justify-center text-[#059669]">
                <Layers className="w-7 h-7" />
              </div>
              <h3 className="font-extrabold text-base text-[#0F281E] font-display">
                Awaiting Soil Physicochemical Parameters
              </h3>
              <p className="text-xs max-w-sm text-[#526B60] font-sans leading-relaxed">
                Adjust clay, sand, silt, and pH sliders on the left to calculate USDA soil texture class and amendment recommendations.
              </p>
            </div>
          )}
        </div>

      </div>

    </div>
  );
};
