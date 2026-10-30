import React from 'react';
import { Sparkles, Sprout, Layers, CloudSun, ShieldAlert } from 'lucide-react';
import { useLanguage } from '../../contexts/LanguageContext';

interface QuickPromptChipsProps {
  onSelectPrompt: (prompt: string) => void;
}

export const QuickPromptChips: React.FC<QuickPromptChipsProps> = ({ onSelectPrompt }) => {
  const { language } = useLanguage();

  const prompts = language === 'te' ? [
    { text: "నల్లరేగడి నేలలో ఏ పంట వేయాలి?", icon: "🌱" },
    { text: "నా నేల pH 7.2 - ఇది ఏ పంటలకు మంచిది?", icon: "🧪" },
    { text: "వరి పంటలో ఆకు ఎండు తెగులు నివారణ ఏమిటి?", icon: "🌾" },
    { text: "వర్షపాతం తక్కువగా ఉంటే ఏ పంట సాగు చేయాలి?", icon: "🌦" },
    { text: "PM-KISAN పథకం వివరాలు ఏమిటి?", icon: "🏛" },
  ] : language === 'hi' ? [
    { text: "काली मिट्टी में कौन सी फसल उगानी चाहिए?", icon: "🌱" },
    { text: "मिट्टी का pH 7.2 है, कौन सी फसल सही रहेगी?", icon: "🧪" },
    { text: "कपास के कीट नियंत्रण के क्या उपाय हैं?", icon: "🐛" },
    { text: "कम वर्षा वाले क्षेत्रों के लिए उपयुक्त फसलें", icon: "🌦" },
    { text: "पीएम किसान सम्मान निधि योजना की जानकारी", icon: "🏛" },
  ] : [
    { text: "Which crop is suitable for black soil and moderate rainfall?", icon: "🌱" },
    { text: "My soil pH is 7.2. What crops are best suited?", icon: "🧪" },
    { text: "How to manage sucking pests in cotton safely?", icon: "🐛" },
    { text: "What are the benefits of the PM-KISAN scheme?", icon: "🏛" },
    { text: "Recommended crops for Kharif season in Telangana", icon: "🌾" },
  ];

  return (
    <div className="py-2">
      <div className="flex items-center gap-1.5 text-xs font-bold text-stone-500 dark:text-slate-400 mb-2 uppercase tracking-wider">
        <Sparkles className="w-3.5 h-3.5 text-amber-500" />
        <span>Suggested Agricultural Questions</span>
      </div>
      <div className="flex flex-wrap gap-2">
        {prompts.map((p, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => onSelectPrompt(p.text)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white dark:bg-slate-800 text-xs font-medium text-slate-700 dark:text-slate-300 border border-stone-200 dark:border-slate-700 hover:border-emerald-500 hover:text-emerald-700 dark:hover:text-emerald-400 shadow-sm transition-all text-left"
          >
            <span>{p.icon}</span>
            <span>{p.text}</span>
          </button>
        ))}
      </div>
    </div>
  );
};
