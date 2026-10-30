import React, { useState } from 'react';
import { PrimaryRecommendation, AlternativeCrop } from '../../types';
import {
  CheckCircle2,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  BookOpen,
  Sprout,
  Droplets,
  Thermometer,
  Compass,
  FileCheck
} from 'lucide-react';
import { useLanguage } from '../../contexts/LanguageContext';

interface FactorBreakdownCardProps {
  primary: PrimaryRecommendation;
  alternatives?: AlternativeCrop[];
  onOpenSources?: () => void;
}

export const FactorBreakdownCard: React.FC<FactorBreakdownCardProps> = ({
  primary,
  alternatives = [],
  onOpenSources
}) => {
  const { t } = useLanguage();
  const [isExpanded, setIsExpanded] = useState(true);

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'bg-emerald-500';
    if (score >= 65) return 'bg-amber-500';
    return 'bg-rose-500';
  };

  const getBadgeClass = (rating: 'High' | 'Medium' | 'Low') => {
    if (rating === 'High') return 'bg-emerald-100 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-300 border-emerald-300';
    if (rating === 'Medium') return 'bg-amber-100 dark:bg-amber-950 text-amber-800 dark:text-amber-300 border-amber-300';
    return 'bg-rose-100 dark:bg-rose-950 text-rose-800 dark:text-rose-300 border-rose-300';
  };

  return (
    <div className="bg-white dark:bg-slate-800/90 rounded-2xl border border-stone-200 dark:border-slate-700 shadow-md overflow-hidden transition-all">
      
      {/* Card Header: Crop Name + Confidence */}
      <div className="bg-gradient-to-r from-emerald-700 via-emerald-800 to-green-900 text-white p-4 sm:p-5 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-white/10 backdrop-blur border border-white/20 flex items-center justify-center text-2xl shadow-inner">
            🌱
          </div>
          <div>
            <span className="text-xs uppercase tracking-wider font-bold text-emerald-200">
              Primary Recommended Crop
            </span>
            <h3 className="text-xl sm:text-2xl font-black tracking-tight font-serif">
              {primary.crop}
            </h3>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="text-right hidden sm:block">
            <div className="text-xs text-emerald-200">Agronomic Match</div>
            <div className="text-lg font-black">{primary.confidence_score_pct}%</div>
          </div>
          <span className={`px-2.5 py-1 text-xs font-bold rounded-full border shadow-sm ${
            primary.confidence_level === 'High'
              ? 'bg-emerald-400/20 text-emerald-100 border-emerald-300/40'
              : 'bg-amber-400/20 text-amber-100 border-amber-300/40'
          }`}>
            {primary.confidence_level} Confidence
          </span>
        </div>
      </div>

      {/* Main Body */}
      <div className="p-4 sm:p-5 space-y-5">
        
        {/* Visual Suitability Breakdown */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-xs sm:text-sm font-bold uppercase tracking-wide text-slate-700 dark:text-slate-200 flex items-center gap-2">
              <Compass className="w-4 h-4 text-emerald-600" />
              {t.suitabilityBreakdown}
            </h4>
            <span className="text-xs text-stone-500 font-medium">Calibrated Factors</span>
          </div>

          <div className="space-y-2.5">
            
            {/* Soil Suitability */}
            <div>
              <div className="flex justify-between text-xs font-semibold mb-1 text-slate-700 dark:text-slate-300">
                <span className="flex items-center gap-1.5">
                  <Sprout className="w-3.5 h-3.5 text-emerald-600" />
                  Soil Texture & Physicochemical Fit
                </span>
                <span className="font-bold">{primary.factor_scores.soil_suitability}%</span>
              </div>
              <div className="w-full h-2 rounded-full bg-stone-100 dark:bg-slate-700 overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-700 ${getScoreColor(primary.factor_scores.soil_suitability)}`}
                  style={{ width: `${primary.factor_scores.soil_suitability}%` }}
                />
              </div>
            </div>

            {/* Rainfall Suitability */}
            <div>
              <div className="flex justify-between text-xs font-semibold mb-1 text-slate-700 dark:text-slate-300">
                <span className="flex items-center gap-1.5">
                  <Droplets className="w-3.5 h-3.5 text-blue-500" />
                  Precipitation & Moisture Alignment
                </span>
                <span className="font-bold">{primary.factor_scores.rainfall_suitability}%</span>
              </div>
              <div className="w-full h-2 rounded-full bg-stone-100 dark:bg-slate-700 overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-700 ${getScoreColor(primary.factor_scores.rainfall_suitability)}`}
                  style={{ width: `${primary.factor_scores.rainfall_suitability}%` }}
                />
              </div>
            </div>

            {/* Temperature Suitability */}
            <div>
              <div className="flex justify-between text-xs font-semibold mb-1 text-slate-700 dark:text-slate-300">
                <span className="flex items-center gap-1.5">
                  <Thermometer className="w-3.5 h-3.5 text-amber-500" />
                  Seasonal Thermal Range
                </span>
                <span className="font-bold">{primary.factor_scores.temperature_suitability}%</span>
              </div>
              <div className="w-full h-2 rounded-full bg-stone-100 dark:bg-slate-700 overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-700 ${getScoreColor(primary.factor_scores.temperature_suitability)}`}
                  style={{ width: `${primary.factor_scores.temperature_suitability}%` }}
                />
              </div>
            </div>

            {/* pH Suitability */}
            <div>
              <div className="flex justify-between text-xs font-semibold mb-1 text-slate-700 dark:text-slate-300">
                <span className="flex items-center gap-1.5">
                  <FileCheck className="w-3.5 h-3.5 text-teal-500" />
                  Soil pH Absorption Index
                </span>
                <span className="font-bold">{primary.factor_scores.ph_suitability}%</span>
              </div>
              <div className="w-full h-2 rounded-full bg-stone-100 dark:bg-slate-700 overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-700 ${getScoreColor(primary.factor_scores.ph_suitability)}`}
                  style={{ width: `${primary.factor_scores.ph_suitability}%` }}
                />
              </div>
            </div>

          </div>
        </div>

        {/* Expandable Why This Recommendation */}
        <div className="border-t border-stone-200 dark:border-slate-700/80 pt-3">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="w-full flex items-center justify-between text-xs sm:text-sm font-bold text-emerald-800 dark:text-emerald-400 hover:text-emerald-900 transition-colors py-1"
          >
            <span>{t.whyThisRec}</span>
            {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>

          {isExpanded && (
            <div className="mt-3 space-y-3 animate-in fade-in">
              
              {/* Supporting Factors */}
              <div className="p-3 rounded-xl bg-emerald-50/70 dark:bg-emerald-950/30 border border-emerald-200/60 dark:border-emerald-800/40">
                <div className="text-xs font-bold text-emerald-900 dark:text-emerald-300 mb-2 flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                  Key Positive Agronomic Drivers
                </div>
                <ul className="space-y-1.5">
                  {primary.supporting_factors.map((factor, idx) => (
                    <li key={idx} className="text-xs text-slate-700 dark:text-slate-300 flex items-start gap-2">
                      <span className="text-emerald-600 font-bold">•</span>
                      <span>{factor}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Potential Limitations & Risks if any */}
              {primary.potential_limitations.length > 0 && (
                <div className="p-3 rounded-xl bg-amber-50/70 dark:bg-amber-950/30 border border-amber-200/60 dark:border-amber-800/40">
                  <div className="text-xs font-bold text-amber-900 dark:text-amber-300 mb-2 flex items-center gap-1.5">
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                    {t.limitationsTitle}
                  </div>
                  <ul className="space-y-1.5">
                    {primary.potential_limitations.map((lim, idx) => (
                      <li key={idx} className="text-xs text-slate-700 dark:text-slate-300 flex items-start gap-2">
                        <span className="text-amber-600 font-bold">⚠</span>
                        <span>{lim}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

            </div>
          )}
        </div>

        {/* Alternative Crops Badges */}
        {alternatives.length > 0 && (
          <div className="border-t border-stone-200 dark:border-slate-700/80 pt-3">
            <span className="text-xs font-bold uppercase tracking-wider text-stone-500 dark:text-slate-400 block mb-2">
              {t.alternativeCropsTitle}
            </span>
            <div className="flex flex-wrap gap-2">
              {alternatives.map((alt, idx) => (
                <div
                  key={idx}
                  className="px-3 py-1.5 rounded-xl bg-stone-100 dark:bg-slate-700/60 border border-stone-200 dark:border-slate-600 flex items-center gap-2"
                >
                  <span className="text-xs font-bold text-slate-800 dark:text-slate-200">
                    {alt.crop}
                  </span>
                  <span className="text-[11px] px-1.5 py-0.5 rounded-md bg-white dark:bg-slate-800 text-emerald-700 dark:text-emerald-400 font-black border border-stone-200 dark:border-slate-700">
                    {alt.confidence_score_pct}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Citations / Sources Footer */}
        <div className="pt-2 flex items-center justify-between text-[11px] text-stone-500 dark:text-slate-400">
          <div className="flex items-center gap-1">
            <BookOpen className="w-3.5 h-3.5 text-emerald-600" />
            <span>ICAR & SoilGrids Verified Data</span>
          </div>
          {onOpenSources && (
            <button
              onClick={onOpenSources}
              className="text-emerald-700 dark:text-emerald-400 hover:underline font-semibold"
            >
              {t.viewSources} ({primary.sources.length})
            </button>
          )}
        </div>

      </div>
    </div>
  );
};
