import React, { useState } from 'react';
import { X, MapPin, Check, Search } from 'lucide-react';
import { useFarm } from '../../contexts/FarmContext';

interface LocationModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const POPULAR_DISTRICTS = [
  { district: 'Warangal', state: 'Telangana', soil: 'Black Soil (Regur/Vertisol)', rainfall: '945 mm' },
  { district: 'Karimnagar', state: 'Telangana', soil: 'Red Sandy Loam', rainfall: '910 mm' },
  { district: 'Khammam', state: 'Telangana', soil: 'Alluvial & Black Soil', rainfall: '1020 mm' },
  { district: 'Nalgonda', state: 'Telangana', soil: 'Red Loam', rainfall: '750 mm' },
  { district: 'Nizamabad', state: 'Telangana', soil: 'Black Soil', rainfall: '980 mm' },
  { district: 'Guntur', state: 'Andhra Pradesh', soil: 'Black Clayey Soil', rainfall: '890 mm' },
  { district: 'Kurnool', state: 'Andhra Pradesh', soil: 'Black & Red Soil', rainfall: '670 mm' },
];

export const LocationModal: React.FC<LocationModalProps> = ({ isOpen, onClose }) => {
  const { farm, setFarm } = useFarm();
  const [searchTerm, setSearchTerm] = useState('');
  const [selected, setSelected] = useState({ district: farm.district, state: farm.state });

  if (!isOpen) return null;

  const filtered = POPULAR_DISTRICTS.filter(d => 
    d.district.toLowerCase().includes(searchTerm.toLowerCase()) ||
    d.state.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleSave = () => {
    const matched = POPULAR_DISTRICTS.find(d => d.district === selected.district);
    setFarm({
      ...farm,
      district: selected.district,
      state: selected.state,
      soil_type: matched ? matched.soil : farm.soil_type
    });
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in">
      <div className="w-full max-w-lg bg-white border border-[#E2ECE6] rounded-3xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#E2ECE6] bg-[#F8FAF9]">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-2xl bg-[#E8F5EF] text-[#00A859] border border-[#00A859]/20">
              <MapPin className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-base text-[#0F281E]">Select Farm Location</h3>
              <p className="text-xs text-[#526B60]">Calibrates regional SoilGrids and Weather Expert telemetry</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-xl text-[#526B60] hover:text-[#0F281E] hover:bg-[#E2ECE6] transition"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Search */}
        <div className="p-4 border-b border-[#E2ECE6] bg-[#F0F7F3]">
          <div className="relative">
            <Search className="w-4 h-4 text-[#526B60] absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search district or state..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 rounded-2xl bg-white border border-[#D0E5DA] text-sm text-[#0F281E] placeholder-[#526B60] focus:outline-none focus:border-[#00A859]"
            />
          </div>
        </div>

        {/* List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {filtered.map((item) => {
            const isSelected = selected.district === item.district;
            return (
              <div
                key={item.district}
                onClick={() => setSelected({ district: item.district, state: item.state })}
                className={`p-3.5 rounded-2xl border cursor-pointer flex items-center justify-between transition ${
                  isSelected
                    ? 'bg-[#E8F5EF] border-[#00A859] text-[#0F281E] shadow-sm'
                    : 'bg-white border-[#E2ECE6] hover:border-[#B6D7C8] text-[#526B60]'
                }`}
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-sm text-[#0F281E]">{item.district}</span>
                    <span className="text-xs px-2 py-0.5 rounded-md bg-[#F0F7F3] text-[#526B60] font-medium">{item.state}</span>
                  </div>
                  <p className="text-xs text-[#526B60] mt-1">
                    Typical Soil: {item.soil} • Annual Rainfall: ~{item.rainfall}
                  </p>
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

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-[#E2ECE6] bg-[#F8FAF9]">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-sm font-semibold text-[#526B60] hover:bg-[#E2ECE6] transition"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-6 py-2 rounded-full text-sm font-bold bg-[#00A859] hover:bg-[#00924D] text-white shadow-md shadow-[#00A859]/20 transition"
          >
            Apply Location
          </button>
        </div>

      </div>
    </div>
  );
};
