import React from 'react';
import { NavLink } from 'react-router-dom';
import { Home, Sparkles, Sprout, Compass, CloudSun, TrendingUp } from 'lucide-react';
import { useLanguage } from '../../contexts/LanguageContext';

export const BottomNav: React.FC = () => {
  const { t } = useLanguage();

  const navItems = [
    { to: '/', label: 'Home', icon: Home },
    { to: '/chat', label: 'AI Assistant', icon: Sparkles, badge: 'AI' },
    { to: '/recommend', label: 'Crops', icon: Sprout },
    { to: '/soil', label: 'Soil', icon: Compass },
    { to: '/weather', label: 'Weather', icon: CloudSun },
    { to: '/market', label: 'Market', icon: TrendingUp },
  ];

  return (
    <nav className="lg:hidden fixed bottom-0 left-0 right-0 z-40 bg-[#0C1728]/95 backdrop-blur-lg border-t border-[#26374D] pb-safe">
      <div className="flex items-center justify-around h-16 px-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex flex-col items-center justify-center w-full h-full text-[10px] font-bold transition-all relative ${
                  isActive
                    ? 'text-[#08A873]'
                    : 'text-[#718197] hover:text-[#F5F8FC]'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  {isActive && (
                    <span className="absolute top-0 w-8 h-0.5 bg-[#08A873] rounded-full" />
                  )}
                  <div className="relative">
                    <Icon className="w-5 h-5 mb-1" />
                    {item.badge && (
                      <span className="absolute -top-1 -right-2 px-1 text-[8px] font-black rounded-full bg-[#08A873] text-white">
                        {item.badge}
                      </span>
                    )}
                  </div>
                  <span className="truncate max-w-[60px]">{item.label}</span>
                </>
              )}
            </NavLink>
          );
        })}
      </div>
    </nav>
  );
};

