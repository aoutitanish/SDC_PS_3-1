import React from 'react';
import { X, HelpCircle, BookOpen, ShieldCheck, Cpu, Database } from 'lucide-react';

interface HelpCenterModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const HelpCenterModal: React.FC<HelpCenterModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in">
      <div className="w-full max-w-2xl bg-[#111E31] border border-[#26374D] rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#26374D] bg-[#17263A]">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-[#08A873]/15 text-[#08A873] border border-[#08A873]/30">
              <HelpCircle className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-base text-[#F5F8FC]">KrishiMitra Help & Documentation</h3>
              <p className="text-xs text-[#A9B7C8]">Explainability principles, data sources & user guide</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg text-[#A9B7C8] hover:text-white hover:bg-[#26374D] transition">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-[#0C1728]">
          {/* Section 1 */}
          <div className="p-4 rounded-xl bg-[#17263A] border border-[#26374D] space-y-2">
            <div className="flex items-center gap-2 text-[#08A873] font-semibold text-sm">
              <Cpu className="w-4 h-4" />
              <span>How are recommendations calculated?</span>
            </div>
            <p className="text-xs text-[#A9B7C8] leading-relaxed">
              KrishiMitra combines a Random Forest machine learning model (trained on 136,128 historical crop-yield records) with a deterministic Agronomic Scoring Engine. Suitability (0–100) measures how closely your farm’s soil texture, pH, temperature normal, rainfall, and irrigation match the crop’s 10th–90th percentile agronomic tolerance envelope.
            </p>
          </div>

          {/* Section 2 */}
          <div className="p-4 rounded-xl bg-[#17263A] border border-[#26374D] space-y-2">
            <div className="flex items-center gap-2 text-[#55A9E8] font-semibold text-sm">
              <Database className="w-4 h-4" />
              <span>Which verified datasets are used?</span>
            </div>
            <ul className="text-xs text-[#A9B7C8] space-y-1.5 list-disc list-inside">
              <li><strong className="text-[#F5F8FC]">Crop Expert Dataset:</strong> 246,091 district-level crop records across India.</li>
              <li><strong className="text-[#F5F8FC]">Soil Expert Dataset:</strong> SoilGrids physical and chemical parameters for 643 districts.</li>
              <li><strong className="text-[#F5F8FC]">Weather Expert Dataset:</strong> 145,236 monthly meteorological records (1997–2015).</li>
              <li><strong className="text-[#F5F8FC]">Master Geography Dataset:</strong> 643 officially registered Indian revenue districts.</li>
            </ul>
          </div>

          {/* Section 3 */}
          <div className="p-4 rounded-xl bg-[#17263A] border border-[#26374D] space-y-2">
            <div className="flex items-center gap-2 text-[#F4B740] font-semibold text-sm">
              <ShieldCheck className="w-4 h-4" />
              <span>Decision Support Disclaimer</span>
            </div>
            <p className="text-xs text-[#A9B7C8] leading-relaxed">
              These agricultural scores are decision-support estimates. Realized yields depend on field management, seed quality, seasonal pest infestation, and microclimate fluctuations. Always cross-reference with local agricultural extension officers (Rythu Vedika / KVK) before large-scale planting.
            </p>
          </div>
        </div>

        <div className="p-4 border-t border-[#26374D] bg-[#17263A] flex justify-end">
          <button onClick={onClose} className="px-5 py-2 rounded-xl text-sm font-semibold bg-[#08A873] hover:bg-[#09C486] text-white">
            Got it
          </button>
        </div>

      </div>
    </div>
  );
};
