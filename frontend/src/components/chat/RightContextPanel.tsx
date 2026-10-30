import React from 'react';
import {
  MapPin,
  Sprout,
  Compass,
  Droplets,
  Thermometer,
  Calendar,
  CloudSun,
  Activity,
  ChevronRight,
  TrendingUp,
  PackageCheck,
  FlaskConical,
  CloudRain,
  ShieldCheck,
  CheckCircle2,
  ExternalLink
} from 'lucide-react';
import { useFarm } from '../../contexts/FarmContext';
import { RECOMMENDED_NEXT_ACTIONS, NextActionItem } from '../../data/dashboardMock';

interface RightContextPanelProps {
  onOpenAction?: (action: NextActionItem) => void;
  onOpenLocation?: () => void;
  isOpenMobile?: boolean;
  onCloseMobile?: () => void;
}

export const RightContextPanel: React.FC<RightContextPanelProps> = ({
  onOpenAction,
  onOpenLocation,
  isOpenMobile,
  onCloseMobile
}) => {
  const { farm } = useFarm();

  const getActionIcon = (iconName: string) => {
    switch (iconName) {
      case 'TrendingUp': return <TrendingUp className="w-4 h-4 text-[#08A873]" />;
      case 'PackageCheck': return <PackageCheck className="w-4 h-4 text-[#55A9E8]" />;
      case 'FlaskConical': return <FlaskConical className="w-4 h-4 text-[#F4B740]" />;
      case 'CloudRain': return <CloudRain className="w-4 h-4 text-[#38BDF8]" />;
      default: return <ShieldCheck className="w-4 h-4 text-[#08A873]" />;
    }
  };

  return (
    <aside className={`w-80 bg-[#0C1728] border-l border-[#26374D] flex flex-col h-full shrink-0 overflow-y-auto ${
      isOpenMobile ? 'fixed inset-y-0 right-0 z-40 block shadow-2xl' : 'hidden xl:flex'
    }`}>
      
      {/* Panel Top Header */}
      <div className="p-4 border-b border-[#26374D] flex items-center justify-between bg-[#111E31]">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-[#08A873]" />
          <h3 className="font-bold text-sm text-[#F5F8FC]">Agricultural Context</h3>
        </div>
        <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#103C38] text-[#08A873] border border-[#08A873]/30">
          Live Telemetry
        </span>
      </div>

      <div className="p-4 space-y-4">
        
        {/* Section 1: Regional Agro Context */}
        <div className="rounded-2xl bg-[#111E31] border border-[#26374D] p-4 space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-[#26374D]">
            <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-[#A9B7C8]">
              <MapPin className="w-3.5 h-3.5 text-[#08A873]" />
              <span>Regional Context</span>
            </div>
            <button
              onClick={onOpenLocation}
              className="text-[11px] text-[#08A873] hover:underline font-semibold"
            >
              Change
            </button>
          </div>

          <div className="space-y-2 text-xs">
            <div className="flex justify-between items-center text-[#A9B7C8]">
              <span>Region</span>
              <span className="font-semibold text-[#F5F8FC]">{farm.district || 'Kurnool'}, {farm.state || 'Andhra Pradesh'}</span>
            </div>
            <div className="flex justify-between items-center text-[#A9B7C8]">
              <span>Current Season</span>
              <span className="font-bold text-[#F4B740]">Kharif 2026</span>
            </div>
            <div className="flex justify-between items-center text-[#A9B7C8]">
              <span>Query Intelligence</span>
              <span className="font-semibold text-[#08A873]">Question-First RAG</span>
            </div>
          </div>
        </div>

        {/* Section 2: Live Conditions */}
        <div className="rounded-2xl bg-[#111E31] border border-[#26374D] p-4 space-y-3">
          <div className="flex items-center gap-1.5 pb-2 border-b border-[#26374D] text-xs font-bold uppercase tracking-wider text-[#A9B7C8]">
            <CloudSun className="w-3.5 h-3.5 text-[#55A9E8]" />
            <span>Live Field Conditions</span>
          </div>

          <div className="grid grid-cols-2 gap-2.5">
            <div className="p-2.5 rounded-xl bg-[#17263A] border border-[#26374D]">
              <span className="text-[10px] text-[#718197] block">Temperature</span>
              <span className="text-base font-bold text-[#F5F8FC]">28.4°C</span>
              <span className="text-[10px] text-[#08A873] block">Feels like 30°C</span>
            </div>

            <div className="p-2.5 rounded-xl bg-[#17263A] border border-[#26374D]">
              <span className="text-[10px] text-[#718197] block">Rainfall Outlook</span>
              <span className="text-base font-bold text-[#55A9E8]">12 mm</span>
              <span className="text-[10px] text-[#A9B7C8] block">Next 48 Hours</span>
            </div>

            <div className="p-2.5 rounded-xl bg-[#17263A] border border-[#26374D]">
              <span className="text-[10px] text-[#718197] block">Soil Moisture</span>
              <span className="text-base font-bold text-[#08A873]">42%</span>
              <span className="text-[10px] text-[#A9B7C8] block">Root zone fit</span>
            </div>

            <div className="p-2.5 rounded-xl bg-[#17263A] border border-[#26374D]">
              <span className="text-[10px] text-[#718197] block">Irrigation Status</span>
              <span className="text-xs font-bold text-[#08A873] mt-1 block">Active</span>
              <span className="text-[10px] text-[#718197] block">Drip Scheduled</span>
            </div>
          </div>
        </div>

        {/* Section 3: Recommended Next Actions */}
        <div className="rounded-2xl bg-[#111E31] border border-[#26374D] p-4 space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-[#26374D]">
            <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-[#A9B7C8]">
              <Sprout className="w-3.5 h-3.5 text-[#08A873]" />
              <span>Next Recommended Actions</span>
            </div>
          </div>

          <div className="space-y-2">
            {RECOMMENDED_NEXT_ACTIONS.map((action) => (
              <div
                key={action.id}
                onClick={() => onOpenAction && onOpenAction(action)}
                className="p-3 rounded-xl bg-[#17263A] border border-[#26374D] hover:border-[#08A873] cursor-pointer transition text-left group"
              >
                <div className="flex items-start gap-2.5">
                  <div className="p-2 rounded-lg bg-[#0C1728] border border-[#26374D] shrink-0 mt-0.5">
                    {getActionIcon(action.iconName)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-1">
                      <h5 className="font-semibold text-xs text-[#F5F8FC] group-hover:text-[#08A873] transition truncate">
                        {action.title}
                      </h5>
                      {action.badge && (
                        <span className="text-[9px] font-bold px-1.5 py-0.2 rounded bg-[#103C38] text-[#08A873] shrink-0">
                          {action.badge}
                        </span>
                      )}
                    </div>
                    <p className="text-[11px] text-[#718197] mt-0.5 line-clamp-1">
                      {action.description}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>

    </aside>
  );
};
