import React from 'react';
import { X, Sparkles, CheckCircle2, Layers } from 'lucide-react';
import { useFarm } from '../../contexts/FarmContext';

interface ScoreExplainModalProps {
  isOpen: boolean;
  onClose: () => void;
  cropName?: string;
  score?: number;
  confidence?: string;
}

export const ScoreExplainModal: React.FC<ScoreExplainModalProps> = ({
  isOpen,
  onClose,
  cropName = 'Arhar/Tur (Pigeon Pea)',
  score = 94.5,
  confidence = 'High'
}) => {
  const { farm } = useFarm();
  if (!isOpen) return null;

  const factors = [
    { name: 'Soil Compatibility (Clay & pH)', weight: '30%', score: 98.9, note: `Matches ${farm.soil_type} clay content & optimal pH bounds` },
    { name: 'Climate & Thermal Fit', weight: '25%', score: 94.9, note: `Precipitation & mean temperature normals for ${farm.district}` },
    { name: 'Water & Irrigation Fit', weight: '20%', score: 95.0, note: `${farm.irrigation_type} delivers targeted moisture to roots` },
    { name: 'Benchmark Yield Potential', weight: '15%', score: 92.5, note: `Historical benchmark yield in ${farm.district} district` },
    { name: 'Seasonal Growth Window', weight: '10%', score: 92.0, note: 'Optimal vegetative and reproductive cycle match' },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in">
      <div className="w-full max-w-lg bg-[#111E31] border border-[#26374D] rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#26374D] bg-[#17263A]">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-[#08A873]/15 text-[#08A873] border border-[#08A873]/30">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-base text-[#F5F8FC]">{cropName} Suitability Breakdown</h3>
              <p className="text-xs text-[#A9B7C8]">Score: {score}/100 • Confidence: {confidence}</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg text-[#A9B7C8] hover:text-white hover:bg-[#26374D] transition">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-[#0C1728]">
          <div className="p-4 rounded-xl bg-[#17263A] border border-[#26374D] flex items-center justify-between">
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-[#718197]">Composite Metric</span>
              <div className="text-2xl font-black text-[#08A873] mt-0.5">{score} <span className="text-sm font-medium text-[#A9B7C8]">/ 100</span></div>
            </div>
            <div className="text-right">
              <span className="text-xs font-bold uppercase tracking-wider text-[#718197]">Model Confidence</span>
              <div className="inline-flex items-center gap-1.5 px-3 py-1 mt-1 rounded-full text-xs font-bold bg-[#103C38] text-[#08A873] border border-[#08A873]/40">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>{confidence} Confidence</span>
              </div>
            </div>
          </div>

          <div className="space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-[#A9B7C8] flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-[#08A873]" />
              <span>Factor Contribution Weights</span>
            </h4>
            
            {factors.map((f, i) => (
              <div key={i} className="p-3 rounded-xl bg-[#17263A] border border-[#26374D] space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-[#F5F8FC]">{f.name}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] text-[#718197]">Weight: {f.weight}</span>
                    <span className="font-bold text-[#08A873]">{f.score}%</span>
                  </div>
                </div>
                <div className="w-full bg-[#0C1728] h-2 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-[#08A873] to-[#09C486] rounded-full transition-all duration-500"
                    style={{ width: `${f.score}%` }}
                  />
                </div>
                <p className="text-[11px] text-[#A9B7C8]">{f.note}</p>
              </div>
            ))}
          </div>

          <div className="p-3 rounded-xl bg-[#17263A] border border-[#26374D] text-[11px] text-[#718197] leading-relaxed">
            Note: Agronomic Suitability measures empirical distance from optimal growing parameters. Model Confidence measures classification tree agreement across 100 Random Forest estimators.
          </div>
        </div>

        <div className="p-4 border-t border-[#26374D] bg-[#17263A] flex justify-end">
          <button onClick={onClose} className="px-5 py-2 rounded-xl text-sm font-semibold bg-[#26374D] hover:bg-[#3B5270] text-[#F5F8FC]">
            Close
          </button>
        </div>

      </div>
    </div>
  );
};
