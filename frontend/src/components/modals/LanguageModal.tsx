import React from 'react';
import { X, Globe, Check } from 'lucide-react';
import { useLanguage } from '../../contexts/LanguageContext';
import { LanguageCode } from '../../types';

interface LanguageModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const LANGUAGES: { code: LanguageCode; name: string; nativeName: string; region: string }[] = [
  { code: 'en', name: 'English', nativeName: 'English', region: 'All India Standard' },
  { code: 'te', name: 'Telugu', nativeName: 'తెలుగు', region: 'Telangana & Andhra Pradesh' },
  { code: 'hi', name: 'Hindi', nativeName: 'हिंदी', region: 'North & Central India' }
];

export const LanguageModal: React.FC<LanguageModalProps> = ({ isOpen, onClose }) => {
  const { language, setLanguage } = useLanguage();

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in">
      <div className="w-full max-w-md bg-white border border-[#E2ECE6] rounded-3xl shadow-2xl overflow-hidden">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#E2ECE6] bg-[#F8FAF9]">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-2xl bg-[#E8F5EF] text-[#00A859] border border-[#00A859]/20">
              <Globe className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-base text-[#0F281E]">Select Language</h3>
              <p className="text-xs text-[#526B60]">భాషను ఎంచుకోండి / भाषा चुनें</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-xl text-[#526B60] hover:text-[#0F281E] hover:bg-[#E2ECE6] transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Options */}
        <div className="p-5 space-y-3 bg-[#F8FAF9]">
          {LANGUAGES.map((l) => {
            const isSelected = language === l.code;
            return (
              <div
                key={l.code}
                onClick={() => {
                  setLanguage(l.code);
                  onClose();
                }}
                className={`p-4 rounded-2xl border cursor-pointer flex items-center justify-between transition ${
                  isSelected
                    ? 'bg-[#E8F5EF] border-[#00A859] text-[#0F281E] shadow-sm'
                    : 'bg-white border-[#E2ECE6] hover:border-[#B6D7C8] text-[#526B60]'
                }`}
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-base text-[#0F281E]">{l.nativeName}</span>
                    <span className="text-xs px-2 py-0.5 rounded bg-[#F0F7F3] text-[#526B60] font-medium">{l.name}</span>
                  </div>
                  <p className="text-xs text-[#526B60] mt-1">{l.region}</p>
                </div>
                {isSelected && (
                  <div className="p-1 rounded-full bg-[#00A859] text-white">
                    <Check className="w-4 h-4" />
                  </div>
                )}
              </div>
            );
          })}
        </div>

      </div>
    </div>
  );
};
