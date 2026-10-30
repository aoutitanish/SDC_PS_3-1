import React from 'react';
import { SourceCitation } from '../../types';
import { X, BookOpen, ShieldCheck, Database } from 'lucide-react';
import { useLanguage } from '../../contexts/LanguageContext';

interface SourcesModalProps {
  isOpen: boolean;
  onClose: () => void;
  sources: SourceCitation[];
}

export const SourcesModal: React.FC<SourcesModalProps> = ({ isOpen, onClose, sources }) => {
  const { t } = useLanguage();

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-in fade-in">
      <div className="bg-white dark:bg-slate-800 w-full max-w-lg rounded-2xl border border-stone-200 dark:border-slate-700 shadow-2xl overflow-hidden animate-in zoom-in-95">
        
        {/* Header */}
        <div className="p-4 bg-stone-50 dark:bg-slate-900 border-b border-stone-200 dark:border-slate-700 flex items-center justify-between">
          <div className="flex items-center gap-2 text-emerald-800 dark:text-emerald-400 font-bold text-sm sm:text-base">
            <BookOpen className="w-5 h-5 text-emerald-600" />
            <span>{t.sourcesTitle}</span>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-700 dark:hover:text-white"
            aria-label="Close Citations Modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Sources List */}
        <div className="p-4 sm:p-5 max-h-[60vh] overflow-y-auto space-y-3">
          {sources.length === 0 ? (
            <p className="text-sm text-stone-500">No external datasets directly linked for this response.</p>
          ) : (
            sources.map((src, idx) => (
              <div
                key={idx}
                className="p-3.5 rounded-xl bg-stone-50 dark:bg-slate-700/50 border border-stone-200 dark:border-slate-600 flex items-start gap-3"
              >
                <div className="w-8 h-8 rounded-lg bg-emerald-100 dark:bg-emerald-950 flex items-center justify-center text-emerald-700 shrink-0 mt-0.5">
                  <Database className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-slate-900 dark:text-white">
                    {src.name}
                  </h4>
                  {src.title && (
                    <p className="text-xs text-stone-600 dark:text-slate-300 mt-0.5">
                      {src.title}
                    </p>
                  )}
                  <span className="inline-block mt-1 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider rounded bg-stone-200 dark:bg-slate-600 text-slate-700 dark:text-slate-200">
                    {src.category || 'Agricultural Dataset'}
                  </span>
                </div>
              </div>
            ))
          )}

          <div className="p-3 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-xs text-emerald-800 dark:text-emerald-300 flex items-center gap-2 mt-4">
            <ShieldCheck className="w-4 h-4 shrink-0 text-emerald-600" />
            <span>Retrieved dynamically from authoritative agricultural sources (ICAR, FAO, open scientific repositories).</span>
          </div>
        </div>

        {/* Footer */}
        <div className="p-3 bg-stone-50 dark:bg-slate-900 border-t border-stone-200 dark:border-slate-700 text-right">
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-xl bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-semibold"
          >
            Close
          </button>
        </div>

      </div>
    </div>
  );
};
