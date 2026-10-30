import React, { useState } from 'react';
import { X, Download, FileText, Table, Copy, Check } from 'lucide-react';

interface ExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  chatContent?: string;
}

export const ExportModal: React.FC<ExportModalProps> = ({ isOpen, onClose, chatContent = '' }) => {
  const [copied, setCopied] = useState(false);

  if (!isOpen) return null;

  const handleDownloadPDF = () => {
    window.print();
    onClose();
  };

  const handleDownloadCSV = () => {
    const csvContent = "data:text/csv;charset=utf-8," +
      "Crop,Agronomic Suitability,Model Confidence,Water Requirement,Benchmark Yield,Best Fit\n" +
      "Cotton,94.8/100,High,Moderate (650-900 mm),2.07 t/ha,Black soil & warm temp\n" +
      "Arhar/Tur,94.3/100,High,Low to moderate (400-650 mm),0.8 t/ha,Black soil & moderate rain\n" +
      "Groundnut,94.2/100,High,Low to moderate (400-650 mm),1.21 t/ha,Well-drained soil\n";
    
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `krishimitra_crop_advisory_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    onClose();
  };

  const handleCopyText = () => {
    navigator.clipboard.writeText(chatContent || 'KrishiMitra Agricultural Advisory Report');
    setCopied(true);
    setTimeout(() => {
      setCopied(false);
      onClose();
    }, 1500);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in">
      <div className="w-full max-w-md bg-[#111E31] border border-[#26374D] rounded-2xl shadow-2xl overflow-hidden">
        
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#26374D] bg-[#17263A]">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-[#08A873]/15 text-[#08A873] border border-[#08A873]/30">
              <Download className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-base text-[#F5F8FC]">Export Consultation</h3>
              <p className="text-xs text-[#A9B7C8]">Download official advisory summaries</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg text-[#A9B7C8] hover:text-white hover:bg-[#26374D] transition">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-5 space-y-3 bg-[#0C1728]">
          <button
            onClick={handleDownloadPDF}
            className="w-full p-4 rounded-xl bg-[#17263A] border border-[#26374D] hover:border-[#08A873] flex items-center justify-between transition text-left group"
          >
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-rose-500/15 text-rose-400 border border-rose-500/30">
                <FileText className="w-5 h-5" />
              </div>
              <div>
                <h4 className="font-semibold text-sm text-[#F5F8FC] group-hover:text-[#08A873] transition">Download PDF Advisory</h4>
                <p className="text-xs text-[#718197]">Print-ready formatted document with charts and factor cards</p>
              </div>
            </div>
          </button>

          <button
            onClick={handleDownloadCSV}
            className="w-full p-4 rounded-xl bg-[#17263A] border border-[#26374D] hover:border-[#08A873] flex items-center justify-between transition text-left group"
          >
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-emerald-500/15 text-[#08A873] border border-emerald-500/30">
                <Table className="w-5 h-5" />
              </div>
              <div>
                <h4 className="font-semibold text-sm text-[#F5F8FC] group-hover:text-[#08A873] transition">Export CSV Data Matrix</h4>
                <p className="text-xs text-[#718197]">Raw agronomic scores, thermal bounds, and yield benchmarks</p>
              </div>
            </div>
          </button>

          <button
            onClick={handleCopyText}
            className="w-full p-4 rounded-xl bg-[#17263A] border border-[#26374D] hover:border-[#08A873] flex items-center justify-between transition text-left group"
          >
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-sky-500/15 text-[#55A9E8] border border-sky-500/30">
                {copied ? <Check className="w-5 h-5 text-[#08A873]" /> : <Copy className="w-5 h-5" />}
              </div>
              <div>
                <h4 className="font-semibold text-sm text-[#F5F8FC] group-hover:text-[#08A873] transition">
                  {copied ? 'Copied to Clipboard!' : 'Copy Summary to Clipboard'}
                </h4>
                <p className="text-xs text-[#718197]">Plain-text formatted summary for WhatsApp or SMS</p>
              </div>
            </div>
          </button>
        </div>

      </div>
    </div>
  );
};
