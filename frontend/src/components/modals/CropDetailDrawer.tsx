import React from 'react';
import { X, Sprout, Droplets, Thermometer, ShieldAlert, Sparkles, Compass, Layers } from 'lucide-react';
import { CropSummary } from '../../data/dashboardMock';
import { useFarm } from '../../contexts/FarmContext';

interface CropDetailDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  crop: CropSummary | null;
}

export const CropDetailDrawer: React.FC<CropDetailDrawerProps> = ({ isOpen, onClose, crop }) => {
  const { farm } = useFarm();
  if (!isOpen || !crop) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/70 backdrop-blur-sm animate-in fade-in">
      <div className="w-full max-w-lg h-full bg-[#111E31] border-l border-[#26374D] shadow-2xl flex flex-col animate-in slide-in-from-right duration-300">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#26374D] bg-[#17263A]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#08A873] to-[#044c33] flex items-center justify-center text-white shadow-md">
              <Sprout className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-bold text-lg text-[#F5F8FC]">{crop.name}</h3>
                {crop.isTopRecommendation && (
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#08A873] text-white">
                    Top Pick
                  </span>
                )}
              </div>
              <p className="text-xs text-[#A9B7C8]">{crop.teluguName} • {crop.hindiName} ({crop.category})</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg text-[#A9B7C8] hover:text-white hover:bg-[#26374D] transition">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-5 bg-[#0C1728]">
          {/* Key metrics grid */}
          <div className="grid grid-cols-2 gap-3">
            <div className="p-4 rounded-xl bg-[#17263A] border border-[#26374D]">
              <span className="text-xs font-bold uppercase tracking-wider text-[#718197]">Agronomic Score</span>
              <div className="text-2xl font-black text-[#08A873] mt-0.5">{crop.agronomicScore} <span className="text-xs font-medium text-[#A9B7C8]">/100</span></div>
              <span className="text-[11px] text-[#A9B7C8]">High scientific match</span>
            </div>
            <div className="p-4 rounded-xl bg-[#17263A] border border-[#26374D]">
              <span className="text-xs font-bold uppercase tracking-wider text-[#718197]">Benchmark Yield</span>
              <div className="text-2xl font-black text-[#F5F8FC] mt-0.5">{crop.benchmarkYield}</div>
              <span className="text-[11px] text-[#718197]">{farm.district} District Normal</span>
            </div>
          </div>

          {/* Factor Details */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-[#A9B7C8] flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-[#08A873]" />
              <span>Agronomic Environment Matching</span>
            </h4>

            <div className="p-3.5 rounded-xl bg-[#17263A] border border-[#26374D] space-y-1">
              <div className="flex items-center gap-2 text-xs font-semibold text-[#F5F8FC]">
                <Compass className="w-4 h-4 text-[#08A873]" />
                <span>Soil Texture & pH Compatibility</span>
              </div>
              <p className="text-xs text-[#A9B7C8] pl-6">{crop.soilSuitability}</p>
            </div>

            <div className="p-3.5 rounded-xl bg-[#17263A] border border-[#26374D] space-y-1">
              <div className="flex items-center gap-2 text-xs font-semibold text-[#F5F8FC]">
                <Droplets className="w-4 h-4 text-[#55A9E8]" />
                <span>Water & Irrigation Dynamics</span>
              </div>
              <p className="text-xs text-[#A9B7C8] pl-6">
                Demand: {crop.waterRequirement} • Setup: {farm.irrigation_type} ({crop.dripFit})
              </p>
            </div>

            <div className="p-3.5 rounded-xl bg-[#17263A] border border-[#26374D] space-y-1">
              <div className="flex items-center gap-2 text-xs font-semibold text-[#F5F8FC]">
                <Thermometer className="w-4 h-4 text-[#F4B740]" />
                <span>Thermal & Rainfall Window</span>
              </div>
              <p className="text-xs text-[#A9B7C8] pl-6">
                Optimal Temp: {crop.thermalRange} • Rainfall: {crop.rainfallFit}
              </p>
            </div>
          </div>

          {/* Advantages & Cautions */}
          <div className="p-4 rounded-xl bg-[#103C38]/40 border border-[#08A873]/30 space-y-1.5">
            <span className="text-xs font-bold uppercase tracking-wider text-[#08A873] flex items-center gap-1">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Key Advantage</span>
            </span>
            <p className="text-xs text-[#F5F8FC] leading-relaxed">{crop.advantage}</p>
          </div>

          <div className="p-4 rounded-xl bg-[#17263A] border border-[#F4B740]/40 space-y-1.5">
            <span className="text-xs font-bold uppercase tracking-wider text-[#F4B740] flex items-center gap-1">
              <ShieldAlert className="w-3.5 h-3.5" />
              <span>Management Caution</span>
            </span>
            <p className="text-xs text-[#A9B7C8] leading-relaxed">{crop.caution}</p>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-[#26374D] bg-[#17263A] flex justify-end">
          <button onClick={onClose} className="px-5 py-2 rounded-xl text-sm font-semibold bg-[#08A873] hover:bg-[#09C486] text-white">
            Close Overview
          </button>
        </div>

      </div>
    </div>
  );
};
