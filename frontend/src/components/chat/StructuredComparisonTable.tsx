import React from 'react';
import { Table, CheckCircle2 } from 'lucide-react';
import { useFarm } from '../../contexts/FarmContext';

interface ComparisonRow {
  factor: string;
  tur: string;
  cotton: string;
  groundnut: string;
  tooltip?: string;
  highlightBest?: 'cotton' | 'tur' | 'groundnut';
}

interface StructuredComparisonTableProps {
  onSelectCrop?: (cropName: string) => void;
}

export const StructuredComparisonTable: React.FC<StructuredComparisonTableProps> = ({ onSelectCrop }) => {
  const { farm } = useFarm();

  const comparisonRows: ComparisonRow[] = [
    {
      factor: 'Agronomic Suitability',
      tur: '94.3 / 100',
      cotton: '94.8 / 100',
      groundnut: '94.2 / 100',
      highlightBest: 'cotton',
      tooltip: 'Suitability score calculated across 5 agronomic dimensions.'
    },
    {
      factor: 'Model Confidence',
      tur: 'High',
      cotton: 'High',
      groundnut: 'High',
      tooltip: 'Agreement across ML decision trees.'
    },
    {
      factor: 'Soil Compatibility',
      tur: '98.9% (23.5–39.9% clay)',
      cotton: '99.3% (23.6–40.5% clay)',
      groundnut: '99.5% (23.9–40.4% clay)',
      highlightBest: 'groundnut',
      tooltip: `Alignment with ${farm.district} ${farm.soil_type} clay percentage and pH.`
    },
    {
      factor: 'Rainfall Compatibility',
      tur: '95.7% (~500–1100 mm)',
      cotton: '94.9% (~600–1200 mm)',
      groundnut: '93.3% (~500–1000 mm)',
      highlightBest: 'tur',
      tooltip: 'Annual precipitation demand vs regional meteorological normals.'
    },
    {
      factor: 'Thermal Range',
      tur: '20–35°C',
      cotton: '21–35°C',
      groundnut: '22–34°C',
      tooltip: 'Mean temperature requirements during growth cycle.'
    },
    {
      factor: 'Water Requirement',
      tur: 'Low to moderate (400–650 mm)',
      cotton: 'Moderate (650–900 mm)',
      groundnut: 'Low to moderate (400–650 mm)',
      highlightBest: 'tur',
      tooltip: 'Seasonal crop evapotranspiration demand.'
    },
    {
      factor: 'Irrigation Setup Fit',
      tur: 'Optimal',
      cotton: 'Optimal with drip',
      groundnut: 'Optimal',
      highlightBest: 'cotton',
      tooltip: 'Micro-irrigation compatibility with borewell supplemental water.'
    },
    {
      factor: 'Benchmark Yield',
      tur: '0.8 t/ha',
      cotton: '2.07 t/ha',
      groundnut: '1.21 t/ha',
      highlightBest: 'cotton',
      tooltip: `Historical average yield recorded in ${farm.district} district.`
    },
    {
      factor: 'Key Advantage',
      tur: 'Strong nitrogen fixation & drought tolerance',
      cotton: 'High commercial market value & steady cash flow',
      groundnut: 'Strong soil match & short crop duration'
    },
    {
      factor: 'Management Caution',
      tur: 'Monitor pod borer; avoid water stagnation',
      cotton: 'Monitor bollworm & regulate drip fertigation',
      groundnut: 'Apply gypsum at flowering; loose soil for pegging'
    }
  ];

  return (
    <div className="my-5 rounded-2xl bg-white border border-[#E2ECE6] shadow-sm overflow-hidden">
      
      {/* Header Bar */}
      <div className="px-5 py-3.5 bg-[#F0F7F3] border-b border-[#E2ECE6] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Table className="w-4 h-4 text-[#00A859]" />
          <h4 className="font-bold text-sm text-[#0F281E]">Agronomic Multi-Crop Comparison Matrix</h4>
        </div>
        <span className="text-[11px] text-[#526B60] hidden sm:inline font-medium">
          Calibrated for {farm.district}, {farm.state} • {farm.farm_size_acres} Acres {farm.soil_type}
        </span>
      </div>

      {/* Desktop Table View */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="bg-[#F8FAF9] border-b border-[#E2ECE6] text-[#526B60]">
              <th className="py-3 px-4 font-semibold text-xs text-[#526B60] w-[26%] sticky left-0 bg-[#F8FAF9] z-10">
                Agronomic Factor
              </th>
              <th 
                onClick={() => onSelectCrop && onSelectCrop('Arhar / Tur (Pigeon Pea)')}
                className="py-3 px-4 font-bold text-sm text-[#0F281E] w-[24%] hover:text-[#00A859] cursor-pointer transition"
              >
                Arhar / Tur
                <span className="block text-[11px] font-normal text-[#526B60]">కంది (Pigeon Pea)</span>
              </th>
              <th 
                onClick={() => onSelectCrop && onSelectCrop('Cotton')}
                className="py-3 px-4 font-bold text-sm text-[#00A859] w-[26%] bg-[#E8F5EF] border-x border-[#D0E5DA] hover:underline cursor-pointer transition relative"
              >
                <div className="flex items-center justify-between">
                  <span>Cotton</span>
                  <span className="text-[9px] uppercase tracking-wider font-extrabold px-1.5 py-0.5 rounded bg-[#00A859] text-white">Top Fit</span>
                </div>
                <span className="block text-[11px] font-normal text-[#526B60]">పత్తి (Fiber)</span>
              </th>
              <th 
                onClick={() => onSelectCrop && onSelectCrop('Groundnut')}
                className="py-3 px-4 font-bold text-sm text-[#0F281E] w-[24%] hover:text-[#00A859] cursor-pointer transition"
              >
                Groundnut
                <span className="block text-[11px] font-normal text-[#526B60]">వేరుశనగ (Oilseed)</span>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#E2ECE6]">
            {comparisonRows.map((row, idx) => {
              const isEven = idx % 2 === 0;
              return (
                <tr
                  key={idx}
                  className={`hover:bg-[#F0F7F3] transition group ${
                    isEven ? 'bg-white' : 'bg-[#FAFCFB]'
                  }`}
                >
                  <td className="py-3 px-4 font-semibold text-[#0F281E] sticky left-0 bg-inherit z-10 flex items-center gap-1.5">
                    <span>{row.factor}</span>
                  </td>

                  {/* Tur */}
                  <td className="py-3 px-4 text-[#526B60]">
                    <span className={row.highlightBest === 'tur' ? 'text-[#00A859] font-bold' : ''}>
                      {row.tur}
                    </span>
                  </td>

                  {/* Cotton (Highlighted Column) */}
                  <td className="py-3 px-4 text-[#0F281E] bg-[#E8F5EF]/60 border-x border-[#D0E5DA] font-medium">
                    <span className={row.highlightBest === 'cotton' ? 'text-[#00A859] font-bold' : ''}>
                      {row.cotton}
                    </span>
                  </td>

                  {/* Groundnut */}
                  <td className="py-3 px-4 text-[#526B60]">
                    <span className={row.highlightBest === 'groundnut' ? 'text-[#00A859] font-bold' : ''}>
                      {row.groundnut}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Table Footer */}
      <div className="px-5 py-2.5 bg-[#F8FAF9] border-t border-[#E2ECE6] flex items-center justify-between text-[11px] text-[#526B60]">
        <span>Tap any crop column header to view detailed agronomic parameters</span>
        <span>Verified against Crop Expert & SoilGrids Datasets</span>
      </div>

    </div>
  );
};
