import React from 'react';
import { Sprout, CheckCircle2, Droplets, TrendingUp, Sparkles, ChevronRight } from 'lucide-react';
import { TOP_RECOMMENDED_CROPS, CropSummary } from '../../data/dashboardMock';

interface CropSummaryCardGroupProps {
  onSelectCrop?: (crop: CropSummary) => void;
  onExplainScore?: (cropName: string, score: number, conf: string) => void;
}

export const CropSummaryCardGroup: React.FC<CropSummaryCardGroupProps> = ({
  onSelectCrop,
  onExplainScore
}) => {
  return (
    <div className="my-4 space-y-2">
      <div className="flex items-center justify-between">
        <h4 className="font-bold text-xs uppercase tracking-wider text-[#526B60] flex items-center gap-1.5">
          <Sparkles className="w-3.5 h-3.5 text-[#00A859]" />
          <span>Top Recommended Crop Candidates</span>
        </h4>
        <span className="text-[11px] text-[#526B60]">Ranked by Agronomic Suitability</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {TOP_RECOMMENDED_CROPS.map((crop) => {
          const isTop = crop.isTopRecommendation;
          return (
            <div
              key={crop.name}
              onClick={() => onSelectCrop && onSelectCrop(crop)}
              className={`p-4 rounded-2xl border transition duration-200 cursor-pointer flex flex-col justify-between relative group ${
                isTop
                  ? 'bg-gradient-to-b from-[#E8F5EF] to-white border-[#00A859] shadow-md ring-2 ring-[#00A859]/20'
                  : 'bg-white border-[#E2ECE6] hover:border-[#B6D7C8] hover:bg-[#F8FAF9]'
              }`}
            >
              {isTop && (
                <div className="absolute -top-2.5 right-4 px-2.5 py-0.5 rounded-full bg-[#00A859] text-white text-[10px] font-extrabold uppercase tracking-wider shadow-sm flex items-center gap-1">
                  <Sparkles className="w-3 h-3" />
                  <span>Top Match</span>
                </div>
              )}

              <div>
                {/* Header */}
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div>
                    <h5 className="font-bold text-base text-[#0F281E] group-hover:text-[#00A859] transition">
                      {crop.name}
                    </h5>
                    <span className="text-xs text-[#526B60]">
                      {crop.teluguName} • {crop.category}
                    </span>
                  </div>
                  
                  {/* Suitability Badge */}
                  <div
                    onClick={(e) => {
                      e.stopPropagation();
                      onExplainScore && onExplainScore(crop.name, crop.agronomicScore, crop.confidence);
                    }}
                    className={`px-2.5 py-1 rounded-xl text-right shrink-0 border ${
                      isTop
                        ? 'bg-[#00A859]/10 border-[#00A859]/40 text-[#00A859]'
                        : 'bg-[#F0F7F3] border-[#D0E5DA] text-[#00A859]'
                    }`}
                    title="Click to explain suitability calculation"
                  >
                    <div className="font-black text-sm leading-tight">{crop.agronomicScore}</div>
                    <span className="text-[9px] uppercase tracking-wider text-[#526B60] block font-semibold">Suitability</span>
                  </div>
                </div>

                {/* Metrics Breakdown */}
                <div className="space-y-1.5 pt-2 border-t border-[#E2ECE6] text-xs">
                  <div className="flex items-center justify-between text-[#526B60]">
                    <span className="flex items-center gap-1">
                      <CheckCircle2 className="w-3.5 h-3.5 text-[#00A859]" />
                      <span>Confidence</span>
                    </span>
                    <span className="font-semibold text-[#0F281E]">{crop.confidence}</span>
                  </div>

                  <div className="flex items-center justify-between text-[#526B60]">
                    <span className="flex items-center gap-1">
                      <Droplets className="w-3.5 h-3.5 text-blue-500" />
                      <span>Water Demand</span>
                    </span>
                    <span className="font-medium text-[#0F281E] text-[11px] truncate max-w-[120px]">{crop.waterRequirement}</span>
                  </div>

                  <div className="flex items-center justify-between text-[#526B60]">
                    <span className="flex items-center gap-1">
                      <TrendingUp className="w-3.5 h-3.5 text-amber-500" />
                      <span>Benchmark Yield</span>
                    </span>
                    <span className="font-bold text-[#0F281E]">{crop.benchmarkYield}</span>
                  </div>
                </div>

                {/* Best Fit Note */}
                <p className="text-[11px] text-[#526B60] bg-[#F0F7F3] p-2 rounded-xl mt-3 border border-[#D0E5DA]">
                  <strong className="text-[#0F281E]">Best Fit:</strong> {crop.bestFit}
                </p>
              </div>

              {/* Card Footer Action */}
              <div className="mt-3 pt-2 flex items-center justify-between text-[11px] text-[#00A859] font-semibold">
                <span>View Full Agronomic Profile</span>
                <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition" />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
