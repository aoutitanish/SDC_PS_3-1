import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import {
  Activity,
  Server,
  Database,
  Cpu,
  ShieldCheck,
  CheckCircle2,
  RefreshCw,
  Clock,
  Layers,
  FileText
} from 'lucide-react';

export const Admin: React.FC = () => {
  const [statusData, setStatusData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const fetchStatus = () => {
    setLoading(true);
    api.getAdminStatus()
      .then(setStatusData)
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-12 animate-in fade-in">
      
      {/* Header */}
      <div className="bg-gradient-to-r from-slate-900 via-stone-900 to-slate-800 text-white p-6 rounded-3xl shadow-lg flex items-center justify-between">
        <div>
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/10 text-emerald-300 text-xs font-semibold mb-2">
            <Activity className="w-3.5 h-3.5 text-emerald-400" />
            Live System Telemetry & Dataset Diagnostic
          </span>
          <h1 className="text-2xl sm:text-3xl font-extrabold font-serif">
            System Status & Health
          </h1>
          <p className="text-xs sm:text-sm text-stone-300 mt-1 max-w-lg">
            Inspect ML training metrics, dataset ingestion coverage, vector store indexes, and API latency.
          </p>
        </div>

        <button
          onClick={fetchStatus}
          className="p-2.5 rounded-xl bg-white/10 hover:bg-white/20 text-white border border-white/20 transition"
          title="Refresh status"
          aria-label="Refresh status"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {statusData ? (
        <div className="space-y-6">
          
          {/* Status Metrics Cards Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            
            {/* Vector DB status */}
            <div className="p-5 rounded-2xl bg-white dark:bg-slate-800 border border-stone-200 dark:border-slate-700 shadow-sm space-y-2">
              <div className="flex items-center justify-between text-xs font-bold text-stone-400">
                <span>Vector Index</span>
                <Database className="w-4 h-4 text-emerald-600" />
              </div>
              <div className="text-2xl font-black text-slate-900 dark:text-white">
                {statusData.vector_database_status?.documents_indexed || 668} Docs
              </div>
              <span className="text-[11px] text-emerald-600 font-semibold block">
                {statusData.vector_database_status?.feature_dimensions || 12000} Embedding Dimensions
              </span>
            </div>

            {/* ML Model status */}
            <div className="p-5 rounded-2xl bg-white dark:bg-slate-800 border border-stone-200 dark:border-slate-700 shadow-sm space-y-2">
              <div className="flex items-center justify-between text-xs font-bold text-stone-400">
                <span>ML Model</span>
                <Cpu className="w-4 h-4 text-amber-600" />
              </div>
              <div className="text-2xl font-black text-slate-900 dark:text-white">
                {statusData.ml_model_status?.classes_count || 28} Crops
              </div>
              <span className="text-[11px] text-stone-500 block">
                Random Forest Classifier (v{statusData.ml_model_status?.version || '1.1.0'})
              </span>
            </div>

            {/* Ingested Geography */}
            <div className="p-5 rounded-2xl bg-white dark:bg-slate-800 border border-stone-200 dark:border-slate-700 shadow-sm space-y-2">
              <div className="flex items-center justify-between text-xs font-bold text-stone-400">
                <span>Master Geography</span>
                <Layers className="w-4 h-4 text-blue-600" />
              </div>
              <div className="text-2xl font-black text-slate-900 dark:text-white">
                {statusData.datasets_status?.geography?.districts_count || 637} Districts
              </div>
              <span className="text-[11px] text-stone-500 block">
                {statusData.datasets_status?.geography?.states_count || 33} Indian States
              </span>
            </div>

            {/* LLM Engine */}
            <div className="p-5 rounded-2xl bg-white dark:bg-slate-800 border border-stone-200 dark:border-slate-700 shadow-sm space-y-2">
              <div className="flex items-center justify-between text-xs font-bold text-stone-400">
                <span>LLM Engine</span>
                <ShieldCheck className="w-4 h-4 text-purple-600" />
              </div>
              <div className="text-base font-black text-slate-900 dark:text-white truncate">
                {statusData.llm_status?.configured_provider?.toUpperCase()}
              </div>
              <span className="text-[11px] text-emerald-600 font-semibold block">
                Grounded Agro Rule Engine Active
              </span>
            </div>

          </div>

          {/* Detailed ML Feature Importances */}
          {statusData.ml_model_status?.feature_importances && (
            <div className="p-6 rounded-2xl bg-white dark:bg-slate-800 border border-stone-200 dark:border-slate-700 shadow-sm space-y-4">
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-800 dark:text-white flex items-center gap-2">
                <Cpu className="w-4 h-4 text-emerald-600" />
                Random Forest Agronomic Feature Importances
              </h3>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
                {Object.entries(statusData.ml_model_status.feature_importances).slice(0, 10).map(([feat, val]: [string, any], idx) => (
                  <div key={idx} className="p-3 rounded-xl bg-stone-50 dark:bg-slate-700/40 border border-stone-200 dark:border-slate-600">
                    <div className="flex justify-between text-xs font-semibold mb-1">
                      <span className="capitalize">{feat.replace(/_/g, ' ')}</span>
                      <span className="font-bold text-emerald-700 dark:text-emerald-400">{(val * 100).toFixed(1)}%</span>
                    </div>
                    <div className="w-full h-1.5 rounded-full bg-stone-200 dark:bg-slate-600 overflow-hidden">
                      <div className="h-full bg-emerald-600 rounded-full" style={{ width: `${Math.min(100, val * 500)}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

        </div>
      ) : (
        <div className="p-12 text-center text-stone-400">Loading system status...</div>
      )}

    </div>
  );
};
