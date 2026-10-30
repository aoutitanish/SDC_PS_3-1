import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  Home,
  MessageSquare,
  Sparkles,
  Layers,
  CloudSun,
  BookOpen,
  Tractor,
  Activity,
  Settings,
  HelpCircle
} from 'lucide-react';
import { useLanguage } from '../../contexts/LanguageContext';
import { useFarm } from '../../contexts/FarmContext';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const { t } = useLanguage();
  const { farm } = useFarm();

  const navItems = [
    { to: '/', label: t.navHome, icon: Home },
    { to: '/chat', label: t.navChat, icon: MessageSquare, badge: 'AI' },
    { to: '/recommend', label: t.navRecommend, icon: Sparkles },
    { to: '/soil', label: t.navSoil, icon: Layers },
    { to: '/weather', label: t.navWeather, icon: CloudSun },
    { to: '/crops', label: t.navCrops, icon: BookOpen },
    { to: '/admin', label: t.navAdmin, icon: Activity },
    { to: '/settings', label: t.navSettings, icon: Settings },
  ];

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-40 md:hidden animate-in fade-in"
          aria-hidden="true"
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed md:sticky top-16 left-0 z-40 h-[calc(100vh-4rem)] w-64 bg-white dark:bg-slate-900 border-r border-stone-200 dark:border-slate-800 flex flex-col justify-between p-4 transition-transform duration-300 ease-in-out md:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Navigation Links */}
        <div className="space-y-1 overflow-y-auto">
          <div className="px-3 py-2 text-[11px] font-bold uppercase tracking-wider text-stone-400 dark:text-slate-500">
            Agricultural Intelligence
          </div>

          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={() => onClose()}
                className={({ isActive }) =>
                  `flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-emerald-600 text-white font-semibold shadow-sm shadow-emerald-600/30'
                      : 'text-slate-700 dark:text-slate-300 hover:bg-stone-100 dark:hover:bg-slate-800 hover:text-emerald-700 dark:hover:text-emerald-400'
                  }`
                }
              >
                <div className="flex items-center gap-3">
                  <Icon className="w-4 h-4 shrink-0" />
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span className="px-1.5 py-0.5 text-[10px] font-bold rounded bg-emerald-500/20 text-emerald-100 uppercase">
                    {item.badge}
                  </span>
                )}
              </NavLink>
            );
          })}
        </div>

        {/* Farm Profile Card at Bottom */}
        <div className="mt-auto pt-4 border-t border-stone-200 dark:border-slate-800">
          <div className="p-3 rounded-xl bg-stone-50 dark:bg-slate-800/60 border border-stone-200 dark:border-slate-700/60">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-semibold text-slate-900 dark:text-white truncate">
                {farm.farm_name}
              </span>
              <span className="text-[10px] px-1.5 py-0.2 rounded bg-emerald-100 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-400 font-bold">
                {farm.farm_size_acres} Ac
              </span>
            </div>
            <p className="text-[11px] text-stone-500 dark:text-slate-400 truncate">
              {farm.district}, {farm.state}
            </p>
          </div>
        </div>
      </aside>
    </>
  );
};
