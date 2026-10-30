import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '../services/api';
import {
  Sprout,
  ArrowLeft,
  Droplets,
  Thermometer,
  Layers,
  Calendar,
  TrendingUp,
  ShieldCheck,
  BookOpen
} from 'lucide-react';

export const CropDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [cropData, setCropData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      api.getCropDetail(id)
        .then(setCropData)
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [id]);

  if (loading) {
    return <div className="p-12 text-center text-stone-400">Loading crop agronomy data...</div>;
  }

  if (!cropData || !cropData.success) {
    return (
      <div className="p-12 text-center space-y-3">
        <h2 className="text-lg font-bold">Crop Information Unavailable</h2>
        <Link to="/crops" className="text-emerald-600 font-semibold hover:underline">
          ← Back to Crop Explorer
        </Link>
      </div>
    );
  }

  const req = cropData.agronomic_requirements || {};
  const summary = cropData.summary || {};

  return (
    <div className="space-y-6 max-w-4xl mx-auto pb-12 animate-in fade-in">
      
      {/* Back link */}
      <Link to="/crops" className="inline-flex items-center gap-1.5 text-xs font-semibold text-stone-500 hover:text-emerald-700">
        <ArrowLeft className="w-4 h-4" />
        <span>Back to Crop Explorer</span>
      </Link>

      {/* Header Banner */}
      <div className="bg-gradient-to-r from-emerald-800 to-green-950 text-white p-6 sm:p-8 rounded-3xl shadow-xl flex items-center justify-between">
        <div className="space-y-2">
          <span className="px-3 py-1 rounded-full bg-white/10 text-emerald-200 text-xs font-bold uppercase">
            Agronomic Profile
          </span>
          <h1 className="text-3xl sm:text-4xl font-black font-serif tracking-tight">
            {cropData.crop}
          </h1>
          <p className="text-xs sm:text-sm text-emerald-100 max-w-lg">
            Grounded in historical district production data (1997-2015) and ICAR package of practices.
          </p>
        </div>
        <div className="w-16 h-16 rounded-2xl bg-white/10 backdrop-blur flex items-center justify-center text-3xl hidden sm:flex">
          🌱
        </div>
      </div>

      {/* Requirements Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        
        {/* Soil & pH */}
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-800 border border-stone-200 dark:border-slate-700 shadow-sm space-y-2">
          <div className="flex items-center gap-2 text-xs font-bold uppercase text-emerald-700 dark:text-emerald-400">
            <Layers className="w-4 h-4" />
            <span>Optimal Soil pH</span>
          </div>
          <div className="text-2xl font-black text-slate-900 dark:text-white">
            {req.ph_optimal ? `${req.ph_optimal[0]} - ${req.ph_optimal[1]}` : "6.0 - 7.5"}
          </div>
          <p className="text-xs text-stone-500">Neutral to slightly alkaline absorption window</p>
        </div>

        {/* Rainfall */}
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-800 border border-stone-200 dark:border-slate-700 shadow-sm space-y-2">
          <div className="flex items-center gap-2 text-xs font-bold uppercase text-blue-600 dark:text-blue-400">
            <Droplets className="w-4 h-4" />
            <span>Rainfall Needs</span>
          </div>
          <div className="text-2xl font-black text-slate-900 dark:text-white">
            {req.rainfall_optimal_mm ? `${Math.round(req.rainfall_optimal_mm[0])} - ${Math.round(req.rainfall_optimal_mm[1])} mm` : "600 - 1100 mm"}
          </div>
          <p className="text-xs text-stone-500">Annual cumulative moisture demand</p>
        </div>

        {/* Temperature */}
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-800 border border-stone-200 dark:border-slate-700 shadow-sm space-y-2">
          <div className="flex items-center gap-2 text-xs font-bold uppercase text-amber-600 dark:text-amber-400">
            <Thermometer className="w-4 h-4" />
            <span>Thermal Window</span>
          </div>
          <div className="text-2xl font-black text-slate-900 dark:text-white">
            {req.temp_optimal_c ? `${req.temp_optimal_c[0]}° - ${req.temp_optimal_c[1]}°C` : "20° - 32°C"}
          </div>
          <p className="text-xs text-stone-500">Vegetative growth & boll/grain filling</p>
        </div>

      </div>

      {/* Benchmark Yield and Leading States */}
      <div className="p-6 rounded-2xl bg-white dark:bg-slate-800 border border-stone-200 dark:border-slate-700 shadow-sm space-y-4">
        <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-emerald-600" />
          Production & Yield Metrics
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="p-4 rounded-xl bg-stone-50 dark:bg-slate-700/50 border border-stone-200 dark:border-slate-600">
            <span className="text-xs text-stone-400 font-semibold block">Average Yield</span>
            <span className="text-xl font-bold text-slate-900 dark:text-white">
              {summary.mean_yield ? `${round(summary.mean_yield)} tonnes / hectare` : "Verified benchmark yield"}
            </span>
          </div>

          <div className="p-4 rounded-xl bg-stone-50 dark:bg-slate-700/50 border border-stone-200 dark:border-slate-600">
            <span className="text-xs text-stone-400 font-semibold block">Primary Cultivation Seasons</span>
            <span className="text-sm font-bold text-slate-900 dark:text-white">
              {summary.top_seasons?.join(', ') || "Kharif, Rabi"}
            </span>
          </div>
        </div>

        {summary.top_states && (
          <div>
            <span className="text-xs font-bold text-stone-400 block mb-2">Major Producing States in India</span>
            <div className="flex flex-wrap gap-2">
              {summary.top_states.map((st: string, idx: number) => (
                <span key={idx} className="px-3 py-1 rounded-lg bg-emerald-50 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-300 font-semibold text-xs border border-emerald-200 dark:border-emerald-800">
                  {st}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

    </div>
  );
};

function round(val: any) {
  return Number(val).toFixed(2);
}
