import React from 'react';
import { Sprout, CheckCircle2, AlertTriangle, Droplets, Info, Sparkles, Table as TableIcon, BarChart3, HelpCircle } from 'lucide-react';
import { CropSummaryCardGroup } from './CropSummaryCardGroup';
import { StructuredComparisonTable } from './StructuredComparisonTable';
import { ComparativeInsightsPanel } from './ComparativeInsightsPanel';
import { ExplainabilityWeightsPanel } from './ExplainabilityWeightsPanel';
import { SourceCitationsBadge } from './SourceCitationsBadge';
import { CropSummary } from '../../data/dashboardMock';
import { useFarm } from '../../contexts/FarmContext';

interface StructuredResponseRendererProps {
  content: string;
  onSelectCrop?: (crop: CropSummary | string) => void;
  onExplainScore?: (cropName: string, score: number, conf: string) => void;
  onOpenSources?: () => void;
  onOpenFullAnalysis?: () => void;
}

export const StructuredResponseRenderer: React.FC<StructuredResponseRendererProps> = ({
  content,
  onSelectCrop,
  onExplainScore,
  onOpenSources,
  onOpenFullAnalysis
}) => {
  const { farm } = useFarm();
  if (!content) return null;

  // Strip raw markdown asterisks and clean formatting
  const cleanInlineMarkdown = (text: string): React.ReactNode => {
    const parts = text.split(/(\*\*.*?\*\*)/g);
    return parts.map((part, idx) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        const inner = part.slice(2, -2);
        return (
          <strong key={idx} className="font-bold text-[#0F281E]">
            {inner}
          </strong>
        );
      }
      return part;
    });
  };

  const lines = content.split('\n');
  const renderedBlocks: React.ReactNode[] = [];
  let inTable = false;
  let tableRows: string[][] = [];

  for (let i = 0; i < lines.length; i++) {
    const rawLine = lines[i].trim();

    // Table row detection
    if (rawLine.startsWith('|') && rawLine.endsWith('|')) {
      if (rawLine.includes('---')) {
        continue; // Skip markdown separator row
      }
      inTable = true;
      const cells = rawLine
        .split('|')
        .slice(1, -1)
        .map((c) => c.trim().replace(/\*\*/g, ''));
      tableRows.push(cells);
      continue;
    } else if (inTable) {
      // Table ended, flush table
      inTable = false;
      if (tableRows.length > 0) {
        renderedBlocks.push(
          <div key={`table-${i}`} className="my-3 overflow-x-auto rounded-2xl border border-[#E2ECE6] bg-white shadow-sm">
            <table className="w-full text-xs text-left">
              <thead>
                <tr className="bg-[#F8FAF9] border-b border-[#E2ECE6] text-[#0F281E]">
                  {tableRows[0]?.map((th, thIdx) => (
                    <th key={thIdx} className="p-3 font-semibold">{th}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E2ECE6]">
                {tableRows.slice(1).map((row, rIdx) => (
                  <tr key={rIdx} className="hover:bg-[#F0F7F3]">
                    {row.map((cell, cIdx) => (
                      <td key={cIdx} className="p-3 text-[#526B60]">{cell}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
        tableRows = [];
      }
    }

    if (!rawLine) {
      renderedBlocks.push(<div key={`sp-${i}`} className="h-1.5" />);
      continue;
    }

    // Heading lines
    if (
      rawLine.startsWith('🌾') ||
      rawLine.startsWith('🔍') ||
      rawLine.startsWith('📊') ||
      rawLine.startsWith('###') ||
      rawLine.startsWith('🌟') ||
      rawLine.startsWith('🍅') ||
      rawLine.startsWith('🧪') ||
      rawLine.startsWith('📍') ||
      rawLine.startsWith('🌱')
    ) {
      const headingText = rawLine.replace(/^###\s*/, '').replace(/\*\*/g, '');
      renderedBlocks.push(
        <h4
          key={`h-${i}`}
          className="font-bold text-sm sm:text-base text-[#00A859] mt-3 mb-1 flex items-center gap-2"
        >
          {headingText}
        </h4>
      );
      continue;
    }

    // Bullet points
    if (rawLine.startsWith('•') || rawLine.startsWith('-') || rawLine.startsWith('*')) {
      const bulletText = rawLine.replace(/^[•\-\*]\s*/, '');
      renderedBlocks.push(
        <div key={`b-${i}`} className="flex items-start gap-2.5 text-xs sm:text-sm text-[#526B60] my-1">
          <span className="text-[#00A859] font-bold mt-0.5">•</span>
          <span className="leading-relaxed">{cleanInlineMarkdown(bulletText)}</span>
        </div>
      );
      continue;
    }

    // Numbered List
    if (/^\d+\.\s/.test(rawLine)) {
      renderedBlocks.push(
        <div key={`num-${i}`} className="flex items-start gap-2 text-xs sm:text-sm text-[#0F281E] font-medium my-1 pl-1">
          <span className="leading-relaxed">{cleanInlineMarkdown(rawLine)}</span>
        </div>
      );
      continue;
    }

    // Warning / Caution blocks
    if (rawLine.startsWith('⚠️') || rawLine.startsWith('Warning:') || rawLine.startsWith('గమనిక:') || rawLine.startsWith('సావధాని:')) {
      const warnText = rawLine.replace(/\*\*/g, '');
      renderedBlocks.push(
        <div
          key={`w-${i}`}
          className="my-3 p-3.5 rounded-2xl bg-amber-50 border border-amber-200 text-xs text-amber-900 font-medium flex items-start gap-2.5"
        >
          <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
          <span>{warnText}</span>
        </div>
      );
      continue;
    }

    // Interactive Level 2 Analysis Trigger Buttons
    if (
      rawLine.includes('[View Full Analysis]') ||
      rawLine.includes('[View Details]') ||
      rawLine.includes('[పూర్తి విశ్లేషణ చూడండి]') ||
      rawLine.includes('[పూర్తి విశ్లేషణ]') ||
      rawLine.includes('[पूर्ण विश्लेषण देखें]') ||
      rawLine.includes('[पूर्ण विश्लेषण]')
    ) {
      let btnLabel = 'View Full Analysis';
      if (rawLine.includes('పూర్తి విశ్లేషణ')) btnLabel = 'పూర్తి విశ్లేషణ చూడండి (View Full Analysis)';
      else if (rawLine.includes('पूर्ण विश्लेषण')) btnLabel = 'पूर्ण विश्लेषण देखें (View Full Analysis)';

      renderedBlocks.push(
        <div key={`btn-${i}`} className="my-3">
          <button
            type="button"
            onClick={onOpenFullAnalysis}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-2xl bg-[#E8F5EF] text-[#00A859] border border-[#00A859]/30 hover:bg-[#00A859] hover:text-white font-bold text-xs shadow-sm transition hover:scale-105"
          >
            <BarChart3 className="w-4 h-4" />
            <span>{btnLabel}</span>
          </button>
        </div>
      );
      continue;
    }

    // General Paragraph
    renderedBlocks.push(
      <p key={`p-${i}`} className="text-xs sm:text-sm text-[#526B60] leading-relaxed my-1">
        {cleanInlineMarkdown(rawLine)}
      </p>
    );
  }

  // Flush remaining table if still open at end of text
  if (inTable && tableRows.length > 0) {
    renderedBlocks.push(
      <div key="table-end" className="my-3 overflow-x-auto rounded-2xl border border-[#E2ECE6] bg-white shadow-sm">
        <table className="w-full text-xs text-left">
          <thead>
            <tr className="bg-[#F8FAF9] border-b border-[#E2ECE6] text-[#0F281E]">
              {tableRows[0]?.map((th, thIdx) => (
                <th key={thIdx} className="p-3 font-semibold">{th}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-[#E2ECE6]">
            {tableRows.slice(1).map((row, rIdx) => (
              <tr key={rIdx} className="hover:bg-[#F0F7F3]">
                {row.map((cell, cIdx) => (
                  <td key={cIdx} className="p-3 text-[#526B60]">{cell}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  return (
    <div className="space-y-1">
      {renderedBlocks}
      <SourceCitationsBadge onOpenSources={onOpenSources} />
    </div>
  );
};
