import React, { useState, useEffect } from 'react';
import { useLanguage } from '../contexts/LanguageContext';
import { LanguageCode } from '../types';
import {
  Settings as SettingsIcon,
  Globe,
  Moon,
  Sun,
  Volume2,
  Download,
  ShieldCheck,
  Check
} from 'lucide-react';

export const Settings: React.FC = () => {
  const { language, setLanguage, t } = useLanguage();
  const [isDarkMode, setIsDarkMode] = useState(() => {
    return document.documentElement.classList.contains('dark');
  });
  const [speechRate, setSpeechRate] = useState('1.0');
  const [responseDetail, setResponseDetail] = useState(() => {
    return localStorage.getItem('krishi_response_detail') || 'simple';
  });
  const [savedSuccess, setSavedSuccess] = useState(false);

  const toggleDarkMode = () => {
    if (isDarkMode) {
      document.documentElement.classList.remove('dark');
      setIsDarkMode(false);
      localStorage.setItem('theme', 'light');
    } else {
      document.documentElement.classList.add('dark');
      setIsDarkMode(true);
      localStorage.setItem('theme', 'dark');
    }
  };

  const handleSave = () => {
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 2000);
  };

  return (
    <div className="space-y-6 max-w-3xl mx-auto pb-12 animate-in fade-in">
      
      {/* Header */}
      <div className="bg-gradient-to-r from-stone-800 to-slate-900 text-white p-6 rounded-3xl shadow-lg">
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/10 text-emerald-300 text-xs font-semibold mb-2">
          <SettingsIcon className="w-3.5 h-3.5" />
          Application Preferences
        </span>
        <h1 className="text-2xl sm:text-3xl font-extrabold font-serif">
          {t.navSettings}
        </h1>
        <p className="text-xs sm:text-sm text-stone-300 mt-1">
          Customize language, audio playback, units, and appearance for your farming experience.
        </p>
      </div>

      <div className="bg-white dark:bg-slate-800 p-6 rounded-2xl border border-stone-200 dark:border-slate-700 shadow-sm space-y-6">
        
        {/* Language Selection */}
        <div className="space-y-3">
          <label className="text-xs font-bold uppercase tracking-wider text-slate-800 dark:text-white flex items-center gap-2">
            <Globe className="w-4 h-4 text-emerald-600" />
            Display & Voice Language
          </label>
          <div className="grid grid-cols-3 gap-3">
            {[
              { code: 'en' as LanguageCode, label: 'English', native: 'English' },
              { code: 'te' as LanguageCode, label: 'Telugu', native: 'తెలుగు' },
              { code: 'hi' as LanguageCode, label: 'Hindi', native: 'हिंदी' },
            ].map((l) => (
              <button
                key={l.code}
                onClick={() => setLanguage(l.code)}
                className={`p-3.5 rounded-xl border text-center transition-all ${
                  language === l.code
                    ? 'bg-emerald-50 dark:bg-emerald-950/60 border-emerald-500 text-emerald-800 dark:text-emerald-300 font-bold shadow-sm ring-2 ring-emerald-200 dark:ring-emerald-900'
                    : 'bg-stone-50 dark:bg-slate-900 border-stone-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-stone-100'
                }`}
              >
                <div className="text-sm">{l.native}</div>
                <div className="text-[10px] text-stone-400 mt-0.5">{l.label}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Response Detail Setting */}
        <div className="pt-4 border-t border-stone-100 dark:border-slate-700 space-y-3">
          <label className="text-xs font-bold uppercase tracking-wider text-slate-800 dark:text-white flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            AI Advisory Detail Level
          </label>
          <div className="grid grid-cols-2 gap-3">
            {[
              { id: 'simple', label: 'Simple (Farmer Mode)', desc: 'Concise, clear recommendations answering What, Why, and Watch out for.' },
              { id: 'detailed', label: 'Detailed (Expert Mode)', desc: 'Complete scientific parameters, feature ranges, and in-depth factors.' }
            ].map((opt) => (
              <button
                key={opt.id}
                type="button"
                onClick={() => {
                  setResponseDetail(opt.id);
                  localStorage.setItem('krishi_response_detail', opt.id);
                }}
                className={`p-3.5 rounded-xl border text-left transition-all ${
                  responseDetail === opt.id
                    ? 'bg-emerald-50 dark:bg-emerald-950/60 border-emerald-500 text-emerald-800 dark:text-emerald-300 font-bold shadow-sm ring-2 ring-emerald-200 dark:ring-emerald-900'
                    : 'bg-stone-50 dark:bg-slate-900 border-stone-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-stone-100'
                }`}
              >
                <div className="text-sm font-semibold">{opt.label}</div>
                <div className="text-[11px] text-stone-500 dark:text-slate-400 mt-1">{opt.desc}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Dark Mode Toggle */}
        <div className="pt-4 border-t border-stone-100 dark:border-slate-700 flex items-center justify-between">
          <div>
            <span className="text-sm font-bold text-slate-800 dark:text-white block">Theme Appearance</span>
            <span className="text-xs text-stone-500">Switch between daylight and high-contrast dark theme</span>
          </div>
          <button
            onClick={toggleDarkMode}
            className="p-2.5 rounded-xl bg-stone-100 dark:bg-slate-700 text-slate-700 dark:text-slate-200 hover:bg-emerald-50 hover:text-emerald-700 transition flex items-center gap-2 text-xs font-semibold"
          >
            {isDarkMode ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-slate-600" />}
            <span>{isDarkMode ? "Light Mode" : "Dark Mode"}</span>
          </button>
        </div>

        {/* Voice Speech Speed */}
        <div className="pt-4 border-t border-stone-100 dark:border-slate-700 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-bold text-slate-800 dark:text-white flex items-center gap-2">
              <Volume2 className="w-4 h-4 text-emerald-600" />
              Voice Synthesis Speed
            </span>
            <span className="text-xs font-bold text-emerald-600">{speechRate}x</span>
          </div>
          <input
            type="range"
            min="0.75"
            max="1.25"
            step="0.05"
            value={speechRate}
            onChange={(e) => setSpeechRate(e.target.value)}
            className="w-full accent-emerald-600"
          />
        </div>

        {/* Agricultural Units */}
        <div className="pt-4 border-t border-stone-100 dark:border-slate-700 space-y-1">
          <span className="text-sm font-bold text-slate-800 dark:text-white block">Standard Units</span>
          <p className="text-xs text-stone-500">
            Metric standard: Temperatures in °C, Rainfall in millimeters (mm), Farm area in Acres / Hectares, Yield in tonnes/ha.
          </p>
        </div>

        {/* Save button */}
        <div className="pt-4 border-t border-stone-100 dark:border-slate-700 flex justify-end">
          <button
            onClick={handleSave}
            className="px-6 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs sm:text-sm shadow-md transition flex items-center gap-2"
          >
            {savedSuccess ? <Check className="w-4 h-4" /> : null}
            <span>{savedSuccess ? "Preferences Saved" : "Save Preferences"}</span>
          </button>
        </div>

      </div>

    </div>
  );
};
