import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  Sprout,
  MapPin,
  Globe,
  MessageSquare,
  Menu,
  X,
  Sparkles,
  Layers,
  CloudSun,
  Tractor,
  Compass
} from 'lucide-react';
import { useFarm } from '../../contexts/FarmContext';
import { useLanguage } from '../../contexts/LanguageContext';

interface TopHeaderProps {
  onOpenLocation?: () => void;
  onOpenLanguage?: () => void;
  onOpenNotifications?: () => void;
}

export const TopHeader: React.FC<TopHeaderProps> = ({
  onOpenLocation,
  onOpenLanguage
}) => {
  const { farm } = useFarm();
  const { language } = useLanguage();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();

  const getLanguageLabel = () => {
    switch (language) {
      case 'te': return 'తెలుగు';
      case 'hi': return 'हिंदी';
      default: return 'English';
    }
  };

  const navLinks = [
    { to: '/chat', label: 'KrishiChat', badge: 'AI', isHighlighted: true },
    { to: '/recommend', label: 'Crop Advisory' },
    { to: '/market', label: 'Market & Profit' },
    { to: '/soil', label: 'Soil Health' },
    { to: '/weather', label: 'Weather Radar' },
    { to: '/crops', label: 'Crop Explorer' },
  ];

  return (
    <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-[#E2ECE6] px-4 sm:px-8 lg:px-12 py-3.5 transition-all shadow-sm">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        
        {/* Brand Logo: KrishiMitra AI */}
        <div className="flex items-center gap-8">
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-[#059669] to-[#047857] flex items-center justify-center text-white shadow-md shadow-[#059669]/25 group-hover:scale-105 transition-transform">
              <Sprout className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-display font-extrabold text-2xl tracking-tight text-[#0F281E]">
                  KrishiMitra
                </span>
                <span className="px-1.5 py-0.2 text-[10px] font-black tracking-wider uppercase rounded-md bg-[#059669] text-white shadow-sm">
                  AI
                </span>
              </div>
              <p className="text-[11px] text-[#526B60] hidden sm:block font-medium -mt-0.5">
                Smart Agriculture Assistant
              </p>
            </div>
          </Link>

          {/* Desktop Navigation Links */}
          <nav className="hidden md:flex items-center gap-6 text-sm font-semibold text-[#526B60]">
            {navLinks.map((link) => {
              const isActive = location.pathname === link.to;
              return (
                <Link
                  key={link.to}
                  to={link.to}
                  className={`transition hover:text-[#059669] flex items-center gap-1.5 ${
                    isActive ? 'text-[#059669] font-bold' : ''
                  }`}
                >
                  <span>{link.label}</span>
                  {link.badge && (
                    <span className="px-1.5 py-0.2 text-[9px] font-black rounded-full bg-[#E8F5EF] text-[#059669] border border-[#059669]/30">
                      {link.badge}
                    </span>
                  )}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Right Actions: Launch KrishiChat Pill + Location + Language */}
        <div className="hidden sm:flex items-center gap-3">
          
          {/* Location Badge */}
          <button
            type="button"
            onClick={onOpenLocation}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-[#F0FDF4] border border-[#DCFCE7] text-xs font-semibold text-[#0F281E] hover:border-[#059669] transition shadow-sm"
            title="Select Region"
          >
            <MapPin className="w-3.5 h-3.5 text-[#059669]" />
            <span>{farm.district || 'Kurnool'}, {farm.state || 'Andhra Pradesh'}</span>
          </button>

          {/* Language Toggle */}
          <button
            type="button"
            onClick={onOpenLanguage}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-[#F0FDF4] border border-[#DCFCE7] text-xs font-semibold text-[#0F281E] hover:border-[#059669] transition shadow-sm"
          >
            <Globe className="w-3.5 h-3.5 text-[#059669]" />
            <span>{getLanguageLabel()}</span>
          </button>

          {/* Primary Action Button: Launch KrishiChat */}
          <Link
            to="/chat"
            className="px-5 py-2.5 rounded-full bg-[#059669] hover:bg-[#047857] text-white text-xs sm:text-sm font-bold shadow-md shadow-[#059669]/25 transition hover:scale-105 flex items-center gap-2"
          >
            <Sparkles className="w-4 h-4 text-amber-300" />
            <span>Launch KrishiChat</span>
          </Link>

        </div>

        {/* Mobile Toggle */}
        <div className="md:hidden flex items-center gap-2">
          <Link
            to="/chat"
            className="px-4 py-1.5 rounded-full bg-[#059669] text-white text-xs font-bold shadow-sm flex items-center gap-1"
          >
            <Sparkles className="w-3 h-3 text-amber-300" />
            <span>Chat</span>
          </Link>
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 rounded-xl text-[#526B60] hover:text-[#059669]"
            aria-label="Toggle Navigation Menu"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>

      </div>

      {/* Mobile Drawer Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden pt-4 pb-2 border-t border-[#E2ECE6] mt-3 space-y-2 animate-in fade-in">
          {navLinks.map((link) => (
            <Link
              key={link.to}
              to={link.to}
              onClick={() => setMobileMenuOpen(false)}
              className="block px-3 py-2.5 rounded-xl text-sm font-semibold text-[#0F281E] hover:bg-[#F0FDF4] hover:text-[#059669]"
            >
              {link.label}
            </Link>
          ))}
          <div className="pt-2 flex items-center gap-2">
            <button
              onClick={() => {
                setMobileMenuOpen(false);
                if (onOpenLocation) onOpenLocation();
              }}
              className="flex-1 py-2 text-xs font-semibold rounded-xl bg-[#F0FDF4] text-[#0F281E]"
            >
              📍 {farm.district}, {farm.state}
            </button>
            <button
              onClick={() => {
                setMobileMenuOpen(false);
                if (onOpenLanguage) onOpenLanguage();
              }}
              className="px-4 py-2 text-xs font-semibold rounded-xl bg-[#F0FDF4] text-[#0F281E]"
            >
              🌐 {getLanguageLabel()}
            </button>
          </div>
        </div>
      )}

    </header>
  );
};
