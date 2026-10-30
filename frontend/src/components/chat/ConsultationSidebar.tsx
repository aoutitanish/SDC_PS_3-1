import React, { useState } from 'react';
import { Plus, Search, MessageSquare, Sprout, Compass, CloudRain, Filter, Trash2, Calendar } from 'lucide-react';
import { INITIAL_CONSULTATIONS, ConsultationItem } from '../../data/dashboardMock';

interface ConsultationSidebarProps {
  activeId: string;
  onSelectConsultation: (item: ConsultationItem) => void;
  onNewConsultation: () => void;
  isOpenMobile?: boolean;
  onCloseMobile?: () => void;
}

export const ConsultationSidebar: React.FC<ConsultationSidebarProps> = ({
  activeId,
  onSelectConsultation,
  onNewConsultation,
  isOpenMobile,
  onCloseMobile
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [activeFilter, setActiveFilter] = useState<'All' | 'Today' | 'Crops' | 'Soil' | 'Weather'>('All');
  const [consultations, setConsultations] = useState<ConsultationItem[]>(INITIAL_CONSULTATIONS);

  const filtered = consultations.filter((item) => {
    const matchesSearch =
      item.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.preview.toLowerCase().includes(searchTerm.toLowerCase());
    
    if (!matchesSearch) return false;
    if (activeFilter === 'All') return true;
    if (activeFilter === 'Today') return item.date.includes('mins') || item.date.includes('hours') || item.date.includes('Today');
    return item.category === activeFilter;
  });

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'Crops': return <Sprout className="w-3.5 h-3.5 text-[#08A873]" />;
      case 'Soil': return <Compass className="w-3.5 h-3.5 text-[#F4B740]" />;
      case 'Weather': return <CloudRain className="w-3.5 h-3.5 text-[#55A9E8]" />;
      default: return <MessageSquare className="w-3.5 h-3.5 text-[#A9B7C8]" />;
    }
  };

  return (
    <aside className={`w-72 bg-[#0C1728] border-r border-[#26374D] flex flex-col h-full shrink-0 ${
      isOpenMobile ? 'fixed inset-y-0 left-0 z-40 block shadow-2xl' : 'hidden lg:flex'
    }`}>
      
      {/* Top Header / New Action */}
      <div className="p-4 border-b border-[#26374D] space-y-3 bg-[#0C1728]">
        <button
          onClick={() => {
            onNewConsultation();
            if (onCloseMobile) onCloseMobile();
          }}
          className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl bg-[#08A873] hover:bg-[#09C486] text-white font-bold text-sm shadow-md transition group"
        >
          <Plus className="w-4 h-4 group-hover:rotate-90 transition-transform duration-200" />
          <span>New consultation</span>
        </button>

        {/* Search Input */}
        <div className="relative">
          <Search className="w-4 h-4 text-[#718197] absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search consultations..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-2 rounded-xl bg-[#111E31] border border-[#26374D] text-xs text-[#F5F8FC] placeholder-[#718197] focus:outline-none focus:border-[#08A873]"
          />
        </div>

        {/* Filter Chips */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 no-scrollbar text-[11px]">
          {(['All', 'Today', 'Crops', 'Soil', 'Weather'] as const).map((chip) => (
            <button
              key={chip}
              onClick={() => setActiveFilter(chip)}
              className={`px-2.5 py-1 rounded-lg font-semibold whitespace-nowrap transition ${
                activeFilter === chip
                  ? 'bg-[#103C38] text-[#08A873] border border-[#08A873]/50'
                  : 'bg-[#17263A] text-[#A9B7C8] border border-transparent hover:border-[#26374D]'
              }`}
            >
              {chip}
            </button>
          ))}
        </div>
      </div>

      {/* Consultations List */}
      <div className="flex-1 overflow-y-auto p-3 space-y-1.5">
        <span className="text-[10px] font-bold uppercase tracking-wider text-[#718197] px-2 block mb-1">
          Recent Consultations ({filtered.length})
        </span>

        {filtered.length === 0 ? (
          <div className="p-6 text-center text-xs text-[#718197]">
            <p>No consultations found matching "{searchTerm}"</p>
          </div>
        ) : (
          filtered.map((item) => {
            const isSelected = activeId === item.id;
            return (
              <div
                key={item.id}
                onClick={() => {
                  onSelectConsultation(item);
                  if (onCloseMobile) onCloseMobile();
                }}
                className={`p-3 rounded-xl border cursor-pointer transition text-left relative group ${
                  isSelected
                    ? 'bg-[#17263A] border-[#08A873] shadow-sm text-[#F5F8FC]'
                    : 'bg-[#111E31]/70 border-transparent hover:border-[#26374D] hover:bg-[#111E31] text-[#A9B7C8]'
                }`}
              >
                {isSelected && (
                  <div className="absolute left-0 top-3 bottom-3 w-1 bg-[#08A873] rounded-r" />
                )}

                <div className="flex items-start justify-between gap-1.5">
                  <div className="flex items-center gap-1.5 font-semibold text-xs text-[#F5F8FC] truncate">
                    {getCategoryIcon(item.category)}
                    <span className="truncate">{item.title}</span>
                  </div>
                  <span className="text-[10px] text-[#718197] shrink-0">{item.date}</span>
                </div>

                <p className="text-[11px] text-[#718197] mt-1 line-clamp-1 leading-normal pl-5">
                  {item.preview}
                </p>
              </div>
            );
          })
        )}
      </div>

      {/* Sidebar Footer Stats */}
      <div className="p-3 border-t border-[#26374D] bg-[#0C1728] flex items-center justify-between text-[11px] text-[#718197]">
        <span>6 Saved Sessions</span>
        <span className="text-[#08A873] font-semibold">Synced to Farm</span>
      </div>

    </aside>
  );
};

