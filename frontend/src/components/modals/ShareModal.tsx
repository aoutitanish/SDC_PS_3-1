import React, { useState } from 'react';
import { X, Share2, Copy, Check, MessageSquare, Mail } from 'lucide-react';

interface ShareModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
}

export const ShareModal: React.FC<ShareModalProps> = ({ isOpen, onClose, title = 'Crop Advisory for My Smart Farm' }) => {
  const [copied, setCopied] = useState(false);
  const shareUrl = window.location.href;

  if (!isOpen) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(shareUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleWhatsApp = () => {
    const text = encodeURIComponent(`Check out this KrishiMitra agricultural advisory: ${title} - ${shareUrl}`);
    window.open(`https://api.whatsapp.com/send?text=${text}`, '_blank');
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in">
      <div className="w-full max-w-md bg-[#111E31] border border-[#26374D] rounded-2xl shadow-2xl overflow-hidden">
        
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#26374D] bg-[#17263A]">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-[#08A873]/15 text-[#08A873] border border-[#08A873]/30">
              <Share2 className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-base text-[#F5F8FC]">Share Analysis</h3>
              <p className="text-xs text-[#A9B7C8]">{title}</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg text-[#A9B7C8] hover:text-white hover:bg-[#26374D] transition">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-4 bg-[#0C1728]">
          <div>
            <label className="block text-xs font-semibold text-[#A9B7C8] mb-2">Shareable Consultation Link</label>
            <div className="flex items-center gap-2">
              <input
                type="text"
                readOnly
                value={shareUrl}
                className="flex-1 px-3.5 py-2.5 rounded-xl bg-[#111E31] border border-[#26374D] text-xs text-[#F5F8FC] focus:outline-none"
              />
              <button
                onClick={handleCopy}
                className="px-4 py-2.5 rounded-xl bg-[#08A873] hover:bg-[#09C486] text-white text-xs font-bold flex items-center gap-1.5 transition"
              >
                {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                <span>{copied ? 'Copied!' : 'Copy'}</span>
              </button>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 pt-2">
            <button
              onClick={handleWhatsApp}
              className="flex items-center justify-center gap-2 p-3 rounded-xl bg-[#17263A] border border-[#26374D] hover:border-[#08A873] text-sm font-semibold text-[#F5F8FC] transition"
            >
              <MessageSquare className="w-4 h-4 text-[#08A873]" />
              <span>WhatsApp</span>
            </button>
            <button
              onClick={() => {
                window.location.href = `mailto:?subject=${encodeURIComponent(title)}&body=${encodeURIComponent(shareUrl)}`;
              }}
              className="flex items-center justify-center gap-2 p-3 rounded-xl bg-[#17263A] border border-[#26374D] hover:border-[#55A9E8] text-sm font-semibold text-[#F5F8FC] transition"
            >
              <Mail className="w-4 h-4 text-[#55A9E8]" />
              <span>Email</span>
            </button>
          </div>
        </div>

      </div>
    </div>
  );
};
