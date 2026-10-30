import React from 'react';
import { Database, BookOpen } from 'lucide-react';

interface SourceCitationsBadgeProps {
  onOpenSources?: () => void;
}

const SOURCES = [
  'Crop Expert Dataset',
  'Soil Expert Dataset',
  'Weather Expert Dataset',
  'Master Geography Dataset'
];

export const SourceCitationsBadge: React.FC<SourceCitationsBadgeProps> = ({ onOpenSources }) => {
  return (
    <div className="my-3 pt-3 border-t border-[#E2ECE6] flex flex-wrap items-center justify-between gap-2 text-xs">
      <div className="flex items-center gap-1.5 text-[#526B60]">
        <Database className="w-3.5 h-3.5 text-[#00A859]" />
        <span className="font-semibold text-[#0F281E]">Verified Sources:</span>
      </div>

      <div className="flex flex-wrap items-center gap-1.5">
        {SOURCES.map((s, idx) => (
          <span
            key={idx}
            className="px-2.5 py-1 rounded-full bg-[#F0F7F3] border border-[#D0E5DA] text-[#0F281E] text-[11px] font-medium"
          >
            {s}
          </span>
        ))}

        <button
          type="button"
          onClick={onOpenSources}
          className="ml-1 inline-flex items-center gap-1 px-3 py-1 rounded-full text-[11px] font-bold bg-[#00A859] text-white hover:bg-[#00924D] transition shadow-sm"
        >
          <BookOpen className="w-3 h-3" />
          <span>View Details</span>
        </button>
      </div>
    </div>
  );
};
