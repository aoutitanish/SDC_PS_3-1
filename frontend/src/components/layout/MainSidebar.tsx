import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  Home,
  Sparkles,
  Sprout,
  Compass,
  CloudSun,
  BookOpen,
  MapPin,
  BarChart2,
  Bell,
  Settings,
  HelpCircle,
  ChevronRight,
  ShieldCheck,
  CheckCircle2,
  X
} from 'lucide-react';
import { useFarm } from '../../contexts/FarmContext';

interface MainSidebarProps {
  isOpen: boolean;
  onClose: () => void;
  onOpenNotifications: () => void;
  onOpenHelp: () => void;
}

export const MainSidebar: React.FC<MainSidebarProps> = ({
  isOpen,
  onClose,
  onOpenNotifications,
  onOpenHelp
}) => {
  const { farm } = useFarm();

  const navIntelligence = [
    { to: '/', label: 'Home', icon: Home },
    { to: '/chat', label: 'AI Assistant', icon: Sparkles, badge: 'AI', isPrimary: true },
    { to: '/recommend', label: 'Crop Recommendations', icon: Sprout },
    { to: '/soil', label: 'Soil Analysis', icon: Compass },
    { to: '/weather', label: 'Weather & Agro', icon: CloudSun },
    { to: '/crops', label: 'Crop Explorer', icon: BookOpen },
    { to: '/admin', label: 'Reports & Telemetry', icon: BarChart2 }
  ];

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden animate-in fade-in"
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed lg:static inset-y-0 left-0 z-40 w-64 bg-[#0C1728] border-r border-[#26374D] flex flex-col justify-between transition-transform duration-300 ease-in-out shrink-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        
        {/* Navigation Groups */}
        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          
          {/* Mobile Close Bar */}
          <div className="flex items-center justify-between lg:hidden pb-3 border-b border-[#26374D]">
            <span className="font-bold text-sm text-[#F5F8FC]">Menu</span>
            <button onClick={onClose} className="p-1 rounded-lg text-[#A9B7C8] hover:text-white">
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Group 1: Agricultural Intelligence */}
          <div>
            <span className="text-[10px] font-extrabold uppercase tracking-wider text-[#718197] px-3 block mb-2">
              AGRICULTURAL INTELLIGENCE
            </span>
            <nav className="space-y-1">
              {navIntelligence.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    onClick={onClose}
                    className={({ isActive }) =>
                      `flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-semibold transition group ${
                        isActive
                          ? 'bg-[#103C38] text-[#F5F8FC] border-l-4 border-[#08A873] shadow-glow-primary'
                          : 'text-[#A9B7C8] hover:bg-[#111E31] hover:text-[#F5F8FC]'
                      }`
                    }
                  >
                    <div className="flex items-center gap-2.5">
                      <Icon className="w-4 h-4 text-[#08A873] group-hover:scale-110 transition-transform" />
                      <span>{item.label}</span>
                    </div>
                    {item.badge && (
                      <span className="px-1.5 py-0.2 text-[9px] font-extrabold uppercase rounded bg-[#08A873] text-white">
                        {item.badge}
                      </span>
                    )}
                  </NavLink>
                );
              })}
            </nav>
          </div>

          {/* Group 2: Account & Support */}
          <div>
            <span className="text-[10px] font-extrabold uppercase tracking-wider text-[#718197] px-3 block mb-2">
              ACCOUNT & SUPPORT
            </span>
            <div className="space-y-1">
              <button
                onClick={() => {
                  onClose();
                  onOpenNotifications();
                }}
                className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-semibold text-[#A9B7C8] hover:bg-[#111E31] hover:text-[#F5F8FC] transition text-left"
              >
                <Bell className="w-4 h-4 text-[#A9B7C8]" />
                <span>Notifications</span>
              </button>

              <NavLink
                to="/settings"
                onClick={onClose}
                className={({ isActive }) =>
                  `flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-semibold transition ${
                    isActive
                      ? 'bg-[#103C38] text-[#F5F8FC] border-l-4 border-[#08A873]'
                      : 'text-[#A9B7C8] hover:bg-[#111E31] hover:text-[#F5F8FC]'
                  }`
                }
              >
                <Settings className="w-4 h-4 text-[#A9B7C8]" />
                <span>Settings</span>
              </NavLink>

              <button
                onClick={() => {
                  onClose();
                  onOpenHelp();
                }}
                className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-semibold text-[#A9B7C8] hover:bg-[#111E31] hover:text-[#F5F8FC] transition text-left"
              >
                <HelpCircle className="w-4 h-4 text-[#A9B7C8]" />
                <span>Help Center</span>
              </button>
            </div>
          </div>

        </div>

        {/* Bottom Regional Status Card */}
        <div className="p-3 border-t border-[#26374D] bg-[#0E1A2B]">
          <div className="p-3 rounded-xl bg-[#111E31] border border-[#26374D]">
            <div className="flex items-center justify-between mb-1">
              <span className="font-bold text-xs text-[#F5F8FC]">
                Regional Context
              </span>
              <div className="flex items-center gap-1 text-[10px] text-[#08A873] font-bold">
                <span className="w-1.5 h-1.5 rounded-full bg-[#08A873] animate-pulse" />
                <span>Live RAG</span>
              </div>
            </div>
            <p className="text-[11px] text-[#A9B7C8]">
              {farm.district || 'Kurnool'}, {farm.state || 'Andhra Pradesh'}
            </p>
          </div>
        </div>

      </aside>
    </>
  );
};
