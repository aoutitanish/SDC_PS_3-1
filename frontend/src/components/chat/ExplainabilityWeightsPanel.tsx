import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Cpu, Info, ShieldAlert, BarChart3 } from 'lucide-react';

export const ExplainabilityWeightsPanel: React.FC = () => {
  const [isExpanded, setIsExpanded] = useState(false);

  const factorWeights = [
    { name: 'Soil Compatibility (Clay %, Silt %, pH, Bulk Density)', weight: 30, color: '#00A859' },
    { name: 'Climate & Thermal Normal (Monthly Temp & Kharif Rain)', weight: 25, color: '#0284C7' },
    { name: 'Water Suitability (Demand vs Borewell / Drip Efficiency)', weight: 20, color: '#10B981' },
    { name: 'Yield Potential (Benchmark Historic District Yield)', weight: 15, color: '#D97706' },
    { name: 'Micro-Irrigation Fit (Drip / Fertigation System)', weight: 10, color: '#06B6D4' },
  ];

  return (
    <div className="my-4 rounded-2xl bg-white border border-[#E2ECE6] shadow-sm overflow-hidden transition">
      
      {/* Toggle Header */}
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-5 py-3.5 flex items-center justify-between bg-[#F8FAF9] hover:bg-[#F0F7F3] text-left transition"
      >
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-lg bg-[#E8F5EF] text-[#00A859] border border-[#00A859]/20">
            <Cpu className="w-4 h-4" />
          </div>
          <div>
            <h4 className="font-bold text-sm text-[#0F281E]">How did KrishiMitra calculate this?</h4>
            <span className="text-[11px] text-[#526B60]">Explainable Factor Weights & Scientific Pipeline</span>
          </div>
        </div>
        <div className="flex items-center gap-2 text-xs font-semibold text-[#00A859]">
          <span>{isExpanded ? 'Collapse' : 'Expand Details'}</span>
          {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </div>
      </button>

      {/* Expandable Body */}
      {isExpanded && (
        <div className="p-5 space-y-4 bg-white border-t border-[#E2ECE6] animate-in fade-in duration-200">
          <p className="text-xs text-[#526B60] leading-relaxed">
            Recommendations are determined by feeding your farm profile through a multi-factor agricultural envelope that assigns weighted scores to five core ecological and agronomic pillars:
          </p>

          {/* Factor Weight Bars */}
          <div className="space-y-2.5 pt-1">
            {factorWeights.map((f, i) => (
              <div key={i} className="p-3 rounded-xl bg-[#F8FAF9] border border-[#E2ECE6] space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-[#0F281E]">{f.name}</span>
                  <span className="font-bold text-sm" style={{ color: f.color }}>{f.weight}%</span>
                </div>
                <div className="w-full bg-[#E2ECE6] h-2 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{ width: `${f.weight * 3.3}%`, backgroundColor: f.color }}
                  />
                </div>
              </div>
            ))}
          </div>

          {/* Disclaimer Box */}
          <div className="p-3.5 rounded-xl bg-[#F8FAF9] border border-[#E2ECE6] flex items-start gap-2.5 text-[11px] text-[#526B60] leading-relaxed">
            <Info className="w-4 h-4 text-[#00A859] shrink-0 mt-0.5" />
            <span>
              <strong className="text-[#0F281E]">Decision Support Notice:</strong> These scores are calculated estimates grounded in historical datasets and empirical agronomic bounds. Always validate with local weather outlooks, market conditions, and your local Rythu Vedika agricultural officer before final planting.
            </span>
          </div>
        </div>
      )}

    </div>
  );
};
