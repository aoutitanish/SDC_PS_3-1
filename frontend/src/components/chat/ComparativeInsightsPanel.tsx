import React from 'react';
import { CheckCircle2, Lightbulb, ShieldCheck } from 'lucide-react';
import { useFarm } from '../../contexts/FarmContext';

export const ComparativeInsightsPanel: React.FC = () => {
  const { farm } = useFarm();

  return (
    <div className="my-5 p-5 rounded-2xl bg-white border border-[#E2ECE6] shadow-sm space-y-4">
      
      {/* Title */}
      <div className="flex items-center gap-2 pb-3 border-b border-[#E2ECE6]">
        <div className="p-2 rounded-xl bg-[#E8F5EF] text-[#00A859] border border-[#00A859]/20">
          <Lightbulb className="w-4 h-4" />
        </div>
        <div>
          <h4 className="font-bold text-sm text-[#0F281E]">What This Means for Your Farm</h4>
          <p className="text-xs text-[#526B60]">
            Actionable comparative insights for {farm.district} ({farm.farm_size_acres} acres • {farm.soil_type} • {farm.irrigation_type})
          </p>
        </div>
      </div>

      {/* Grid of Key Takeaways */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        
        {/* Fit Item 1 */}
        <div className="p-3.5 rounded-xl bg-[#F8FAF9] border border-[#E2ECE6] flex items-start gap-2.5">
          <CheckCircle2 className="w-4 h-4 text-[#00A859] shrink-0 mt-0.5" />
          <div className="text-xs">
            <span className="font-bold text-[#0F281E] block">High Suitability: Cotton</span>
            <span className="text-[#526B60]">Achieves strong agronomic suitability score (94.8/100) and high commercial potential under drip irrigation.</span>
          </div>
        </div>

        {/* Fit Item 2 */}
        <div className="p-3.5 rounded-xl bg-[#F8FAF9] border border-[#E2ECE6] flex items-start gap-2.5">
          <CheckCircle2 className="w-4 h-4 text-blue-500 shrink-0 mt-0.5" />
          <div className="text-xs">
            <span className="font-bold text-[#0F281E] block">Low water demand: Arhar/Tur & Groundnut</span>
            <span className="text-[#526B60]">Requires only 400–650 mm total water, conserving borewell reserves and reducing electricity expenditure.</span>
          </div>
        </div>

        {/* Fit Item 3 */}
        <div className="p-3.5 rounded-xl bg-[#F8FAF9] border border-[#E2ECE6] flex items-start gap-2.5">
          <CheckCircle2 className="w-4 h-4 text-[#00A859] shrink-0 mt-0.5" />
          <div className="text-xs">
            <span className="font-bold text-[#0F281E] block">Strongest soil match: Groundnut</span>
            <span className="text-[#526B60]">Excellent alignment with regional soil chemistry and efficient root zone calcium and gypsum uptake.</span>
          </div>
        </div>

        {/* Fit Item 4 */}
        <div className="p-3.5 rounded-xl bg-[#F8FAF9] border border-[#E2ECE6] flex items-start gap-2.5">
          <CheckCircle2 className="w-4 h-4 text-[#00A859] shrink-0 mt-0.5" />
          <div className="text-xs">
            <span className="font-bold text-[#0F281E] block">Water-conscious plan: Arhar / Tur</span>
            <span className="text-[#526B60]">Fixes atmospheric nitrogen into soil while providing harvest resilience during mid-season dry spells.</span>
          </div>
        </div>

      </div>

      {/* Pre-planting Caution Banner */}
      <div className="p-3.5 rounded-xl bg-[#E8F5EF] border border-[#00A859]/30 flex items-start gap-3">
        <ShieldCheck className="w-4 h-4 text-[#00A859] shrink-0 mt-0.5" />
        <div className="text-xs">
          <span className="font-bold text-[#0F281E] block">Before Planting Checklist</span>
          <span className="text-[#526B60]">
            Always cross-check current {farm.district} APMC market rates, procure certified high-germination seeds from verified government centers, and check borewell water discharge.
          </span>
        </div>
      </div>

    </div>
  );
};
