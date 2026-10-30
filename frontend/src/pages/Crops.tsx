import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';
import { useLanguage } from '../contexts/LanguageContext';
import { CropSummary } from '../types';
import { BookOpen, Search, Filter, Sprout, ArrowRight, Sparkles } from 'lucide-react';

export const Crops: React.FC = () => {
  const { t } = useLanguage();
  const [crops, setCrops] = useState<CropSummary[]>([]);
  const [search, setSearch] = useState('');
  const [seasonFilter, setSeasonFilter] = useState('All');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    api.getCrops(search, seasonFilter)
      .then((data) => {
        if (data && data.crops) setCrops(data.crops);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [search, seasonFilter]);

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12 animate-in fade-in">
      
      {/* Header Banner */}
      <div className="bg-gradient-to-br from-[#059669] to-[#047857] text-white p-6 sm:p-8 rounded-3xl shadow-depth flex flex-wrap items-center justify-between gap-4">
        <div>
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/15 backdrop-blur-md text-emerald-100 text-xs font-bold uppercase tracking-wider font-display mb-2">
            <BookOpen className="w-3.5 h-3.5 text-amber-300" />
            <span>KisanKosh • 105+ Crop Agronomy & Benchmark Database</span>
          </span>
          <h1 className="text-2xl sm:text-4xl font-extrabold tracking-tight font-display">
            Indian Agricultural Crop Explorer
          </h1>
          <p className="text-xs sm:text-sm text-emerald-100 mt-1 max-w-xl font-sans">
            Search and explore historical yields, seasonal schedules, and agronomic profiles for 105+ crops across India.
          </p>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-col sm:flex-row items-center gap-3 bg-white p-4 rounded-3xl border border-[#E2ECE6] shadow-panel">
        <div className="relative flex-1 w-full">
          <Search className="w-4 h-4 absolute left-4 top-3.5 text-[#526B60]" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search crop name (e.g., Cotton, Rice, Maize, Groundnut, Chilli)..."
            className="w-full pl-11 pr-4 py-2.5 rounded-2xl bg-[#F8FAF9] text-xs sm:text-sm border border-[#D0E5DA] text-[#0F281E] placeholder-[#526B60] focus:border-[#059669] focus:outline-none font-sans"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Filter className="w-4 h-4 text-[#526B60] shrink-0" />
          <select
            value={seasonFilter}
            onChange={(e) => setSeasonFilter(e.target.value)}
            className="px-4 py-2.5 rounded-2xl bg-[#F8FAF9] border border-[#D0E5DA] text-xs font-bold text-[#0F281E] focus:border-[#059669] focus:outline-none font-display"
          >
            <option value="All">All Seasons</option>
            <option value="Kharif">Kharif (Monsoon)</option>
            <option value="Rabi">Rabi (Winter)</option>
            <option value="Whole Year">Whole Year</option>
            <option value="Autumn">Autumn</option>
          </select>
        </div>
      </div>

      {/* Crops Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
        {crops.map((c, idx) => (
          <Link
            key={idx}
            to={`/crops/${encodeURIComponent(c.crop)}`}
            className="group p-6 rounded-3xl bg-white border border-[#E2ECE6] shadow-panel hover:shadow-depth hover:border-[#059669] transition-all flex flex-col justify-between hover:scale-[1.02]"
          >
            <div>
              <div className="flex items-center justify-between mb-3">
                <div className="w-10 h-10 rounded-2xl bg-[#E8F5EF] flex items-center justify-center text-[#059669]">
                  <Sprout className="w-5 h-5" />
                </div>
                {c.has_agronomic_profile && (
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#E8F5EF] text-[#059669] border border-[#059669]/25 font-display">
                    ML Profile Ready
                  </span>
                )}
              </div>
              <h3 className="text-lg font-extrabold text-[#0F281E] group-hover:text-[#059669] transition-colors font-display">
                {c.crop}
              </h3>
              <p className="text-xs text-[#526B60] mt-1.5 font-sans">
                Historical Benchmark Yield: <strong className="text-[#0F281E] font-display">{c.mean_yield_tonnes_ha} tonnes/ha</strong>
              </p>
              <div className="flex flex-wrap gap-1.5 mt-3.5">
                {c.top_seasons.map((s, sIdx) => (
                  <span key={sIdx} className="px-2.5 py-1 rounded-full bg-[#F0F7F3] border border-[#D0E5DA] text-[10px] font-bold text-[#0F281E] font-display">
                    {s}
                  </span>
                ))}
              </div>
            </div>

            <div className="mt-5 pt-4 border-t border-[#E2ECE6] flex items-center justify-between text-xs font-bold text-[#059669] group-hover:translate-x-1 transition-transform font-display">
              <span>View Full Agronomic Profile</span>
              <ArrowRight className="w-4 h-4" />
            </div>
          </Link>
        ))}
      </div>

    </div>
  );
};
