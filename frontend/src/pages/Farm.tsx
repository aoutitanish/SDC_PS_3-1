import React, { useState, useEffect } from 'react';
import { useFarm } from '../contexts/FarmContext';
import { useLanguage } from '../contexts/LanguageContext';
import { api } from '../services/api';
import { Tractor, Save, Check, MapPin, Layers, Droplets, Sparkles, Sprout } from 'lucide-react';

export const Farm: React.FC = () => {
  const { farm, setFarm, loading: farmLoading } = useFarm();
  const { t } = useLanguage();

  const [states, setStates] = useState<string[]>([]);
  const [districts, setDistricts] = useState<{ State_Name: string; District_Name: string }[]>([]);
  const [savedSuccess, setSavedSuccess] = useState(false);

  const [errorMsg, setErrorMsg] = useState('');
  const [form, setForm] = useState({
    farm_name: farm.farm_name,
    state: farm.state,
    district: farm.district,
    soil_type: farm.soil_type,
    farm_size_acres: farm.farm_size_acres,
    irrigation_type: farm.irrigation_type,
    season: farm.season || 'Kharif',
    water_source: farm.water_source || 'Borewell',
    water_availability: farm.water_availability || 'Moderate',
    primary_crops: farm.primary_crops || ['Cotton', 'Chilli'],
    preferred_language: farm.preferred_language
  });

  useEffect(() => {
    api.getStates().then(setStates).catch(console.error);
  }, []);

  useEffect(() => {
    if (form.state) {
      api.getDistricts(form.state).then(setDistricts).catch(console.error);
    }
  }, [form.state]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.farm_size_acres || form.farm_size_acres <= 0) {
      setErrorMsg('Farm size must be a valid positive number greater than 0.');
      return;
    }
    setErrorMsg('');
    await setFarm(form);
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 3000);
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-12 animate-in fade-in">
      
      {/* Header Banner */}
      <div className="bg-gradient-to-br from-[#059669] to-[#047857] text-white p-6 sm:p-8 rounded-3xl shadow-depth flex items-center justify-between">
        <div>
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/15 backdrop-blur-md text-emerald-100 text-xs font-bold uppercase tracking-wider font-display mb-2">
            <Tractor className="w-3.5 h-3.5 text-amber-300" />
            <span>Farm Context Hub</span>
          </span>
          <h1 className="text-2xl sm:text-4xl font-extrabold tracking-tight font-display">
            Personalized Farm Profile
          </h1>
          <p className="text-xs sm:text-sm text-emerald-100 mt-1 max-w-lg font-sans">
            Configure your farm's location, soil type, and irrigation system to automatically personalize every AI consultation.
          </p>
        </div>
      </div>

      {/* Profile Form Card */}
      <div className="bg-white p-6 sm:p-8 rounded-3xl border border-[#E2ECE6] shadow-panel">
        <form onSubmit={handleSubmit} className="space-y-6">
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            
            {/* Farm Name */}
            <div>
              <label className="block text-xs font-bold text-[#526B60] mb-1 font-display">
                Farm / Landholding Name
              </label>
              <input
                type="text"
                value={form.farm_name}
                onChange={(e) => setForm({ ...form, farm_name: e.target.value })}
                className="w-full px-4 py-2.5 rounded-2xl bg-[#F8FAF9] border border-[#D0E5DA] text-xs sm:text-sm text-[#0F281E] focus:border-[#059669] focus:outline-none font-sans"
              />
            </div>

            {/* Farm Size */}
            <div>
              <label className="block text-xs font-bold text-[#526B60] mb-1 font-display">
                Farm Size (in Acres)
              </label>
              <input
                type="number"
                step="0.1"
                min="0.1"
                value={form.farm_size_acres}
                onChange={(e) => setForm({ ...form, farm_size_acres: parseFloat(e.target.value) || 0 })}
                className="w-full px-4 py-2.5 rounded-2xl bg-[#F8FAF9] border border-[#D0E5DA] text-xs sm:text-sm text-[#0F281E] focus:border-[#059669] focus:outline-none font-sans"
              />
            </div>

            {/* State */}
            <div>
              <label className="block text-xs font-bold text-[#526B60] mb-1 font-display">
                State
              </label>
              <select
                value={form.state}
                onChange={(e) => setForm({ ...form, state: e.target.value })}
                className="w-full px-4 py-2.5 rounded-2xl bg-[#F8FAF9] border border-[#D0E5DA] text-xs sm:text-sm text-[#0F281E] focus:border-[#059669] focus:outline-none font-sans"
              >
                {states.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>

            {/* District */}
            <div>
              <label className="block text-xs font-bold text-[#526B60] mb-1 font-display">
                District
              </label>
              <select
                value={form.district}
                onChange={(e) => setForm({ ...form, district: e.target.value })}
                className="w-full px-4 py-2.5 rounded-2xl bg-[#F8FAF9] border border-[#D0E5DA] text-xs sm:text-sm text-[#0F281E] focus:border-[#059669] focus:outline-none font-sans"
              >
                {districts.map((d, idx) => (
                  <option key={idx} value={d.District_Name}>{d.District_Name}</option>
                ))}
              </select>
            </div>

            {/* Soil Type */}
            <div>
              <label className="block text-xs font-bold text-[#526B60] mb-1 font-display">
                Dominant Soil Type
              </label>
              <select
                value={form.soil_type}
                onChange={(e) => setForm({ ...form, soil_type: e.target.value })}
                className="w-full px-4 py-2.5 rounded-2xl bg-[#F8FAF9] border border-[#D0E5DA] text-xs sm:text-sm text-[#0F281E] focus:border-[#059669] focus:outline-none font-sans"
              >
                <option value="Black Soil (Regur/Vertisol)">Black Soil (Regur/Vertisol)</option>
                <option value="Red and Yellow Soil">Red and Yellow Soil</option>
                <option value="Alluvial Soil">Alluvial Soil</option>
                <option value="Laterite Soil">Laterite Soil</option>
                <option value="Desert / Arid Soil">Desert / Arid Soil</option>
                <option value="Saline / Alkaline Soil">Saline / Alkaline Soil</option>
              </select>
            </div>

            {/* Irrigation Type */}
            <div>
              <label className="block text-xs font-bold text-[#526B60] mb-1 font-display">
                Irrigation System
              </label>
              <select
                value={form.irrigation_type}
                onChange={(e) => setForm({ ...form, irrigation_type: e.target.value })}
                className="w-full px-4 py-2.5 rounded-2xl bg-[#F8FAF9] border border-[#D0E5DA] text-xs sm:text-sm text-[#0F281E] focus:border-[#059669] focus:outline-none font-sans"
              >
                <option value="Drip Irrigation & Borewell">Drip Irrigation & Borewell</option>
                <option value="Sprinkler Irrigation">Sprinkler Irrigation</option>
                <option value="Canal / Flood Irrigation">Canal / Flood Irrigation</option>
                <option value="Rainfed (No Irrigation)">Rainfed (No Permanent Irrigation)</option>
                <option value="Open Well">Open Well</option>
              </select>
            </div>

            {/* Cultivation Season */}
            <div>
              <label className="block text-xs font-bold text-[#526B60] mb-1 font-display">
                Cultivation Season
              </label>
              <select
                value={form.season}
                onChange={(e) => setForm({ ...form, season: e.target.value })}
                className="w-full px-4 py-2.5 rounded-2xl bg-[#F8FAF9] border border-[#D0E5DA] text-xs sm:text-sm text-[#0F281E] focus:border-[#059669] focus:outline-none font-sans"
              >
                <option value="Kharif">Kharif (Monsoon / Autumn)</option>
                <option value="Rabi">Rabi (Winter / Spring)</option>
                <option value="Summer">Summer / Zaid</option>
                <option value="Whole Year">Whole Year / Perennial</option>
              </select>
            </div>

            {/* Water Availability */}
            <div>
              <label className="block text-xs font-bold text-[#526B60] mb-1 font-display">
                Water Availability
              </label>
              <select
                value={form.water_availability}
                onChange={(e) => setForm({ ...form, water_availability: e.target.value })}
                className="w-full px-4 py-2.5 rounded-2xl bg-[#F8FAF9] border border-[#D0E5DA] text-xs sm:text-sm text-[#0F281E] focus:border-[#059669] focus:outline-none font-sans"
              >
                <option value="Low">Low (Limited supplementary water)</option>
                <option value="Moderate">Moderate (Reliable for medium water crops)</option>
                <option value="Adequate">Adequate (Sufficient throughout season)</option>
                <option value="Unknown">Unknown / Uncertain</option>
              </select>
            </div>

          </div>

          {errorMsg && (
            <div className="p-3 bg-red-50 text-red-700 text-xs rounded-xl border border-red-200">
              {errorMsg}
            </div>
          )}

          <div className="pt-4 flex flex-col sm:flex-row items-center justify-between gap-4 border-t border-[#E2ECE6]">
            <div>
              {savedSuccess && (
                <span className="text-[#059669] font-bold text-xs flex items-center gap-1.5 font-display animate-in fade-in">
                  <Check className="w-4 h-4" />
                  <span>Farm profile updated successfully! Grounded in active session.</span>
                </span>
              )}
            </div>

            <button
              type="submit"
              disabled={farmLoading}
              className="px-8 py-3 rounded-2xl bg-[#059669] hover:bg-[#047857] text-white font-bold text-xs sm:text-sm shadow-md shadow-[#059669]/25 transition flex items-center gap-2 font-display hover:scale-105"
            >
              <Save className="w-4 h-4" />
              <span>{t.saveProfile}</span>
            </button>
          </div>

        </form>
      </div>

    </div>
  );
};
