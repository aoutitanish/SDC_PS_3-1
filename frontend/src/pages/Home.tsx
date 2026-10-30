import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  MessageSquare,
  Sparkles,
  Camera,
  Mic,
  MapPin,
  ChevronRight,
  ShieldCheck,
  CheckCircle2,
  Volume2,
  TrendingUp,
  ArrowRight,
  Droplets,
  Sprout,
  Compass,
  Layers,
  CloudSun
} from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';
import { useFarm } from '../contexts/FarmContext';

export const Home: React.FC = () => {
  const { t, language } = useLanguage();
  const { farm } = useFarm();
  const navigate = useNavigate();
  const [interactiveInput, setInteractiveInput] = useState('');

  const handleInteractiveSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (interactiveInput.trim()) {
      navigate(`/chat?q=${encodeURIComponent(interactiveInput)}`);
    } else {
      navigate('/chat');
    }
  };

  return (
    <div className="space-y-16 sm:space-y-24 max-w-6xl mx-auto pb-20 animate-in fade-in duration-300">
      
      {/* 1. By The Numbers Section with Distinctive Typography & Grounded Metrics */}
      <section className="space-y-4 pt-4">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-2">
          <div>
            <span className="text-xs font-bold uppercase tracking-widest text-[#059669] font-display">
              Verified Platform Metrics
            </span>
            <h2 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold text-[#0F281E] tracking-tight font-display mt-0.5">
              KrishiMitra AI By The Numbers
            </h2>
          </div>
          <span className="text-xs font-semibold text-[#526B60]">
            Calibrated on Indian Agricultural Census & ICAR Datasets
          </span>
        </div>

        {/* 3 Large Emerald Metric Cards with Depth */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 sm:gap-6">
          
          <div className="p-6 sm:p-8 rounded-3xl bg-gradient-to-br from-[#059669] to-[#047857] text-white shadow-depth flex flex-col justify-between hover:scale-[1.02] transition-transform group">
            <div>
              <span className="text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight font-display block">
                640+
              </span>
              <p className="text-base sm:text-lg font-bold text-white/95 mt-2 font-display">
                Districts Covered
              </p>
            </div>
            <div className="mt-6 pt-4 border-t border-white/20 text-xs text-emerald-100 font-medium flex items-center justify-between">
              <span>Hyper-local soil & rainfall data</span>
              <MapPin className="w-4 h-4 text-emerald-200 group-hover:translate-x-0.5 transition-transform" />
            </div>
          </div>

          <div className="p-6 sm:p-8 rounded-3xl bg-gradient-to-br from-[#059669] to-[#047857] text-white shadow-depth flex flex-col justify-between hover:scale-[1.02] transition-transform group">
            <div>
              <span className="text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight font-display block">
                136K+
              </span>
              <p className="text-base sm:text-lg font-bold text-white/95 mt-2 font-display">
                ML Crop Yield Records
              </p>
            </div>
            <div className="mt-6 pt-4 border-t border-white/20 text-xs text-emerald-100 font-medium flex items-center justify-between">
              <span>105+ crops & seasonal schedules</span>
              <Sprout className="w-4 h-4 text-emerald-200 group-hover:translate-x-0.5 transition-transform" />
            </div>
          </div>

          <div className="p-6 sm:p-8 rounded-3xl bg-gradient-to-br from-[#059669] to-[#047857] text-white shadow-depth flex flex-col justify-between hover:scale-[1.02] transition-transform group">
            <div>
              <span className="text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight font-display block">
                100%
              </span>
              <p className="text-base sm:text-lg font-bold text-white/95 mt-2 font-display">
                Explainable Decision Scoring
              </p>
            </div>
            <div className="mt-6 pt-4 border-t border-white/20 text-xs text-emerald-100 font-medium flex items-center justify-between">
              <span>Zero-hallucination agronomic weights</span>
              <ShieldCheck className="w-4 h-4 text-emerald-200 group-hover:translate-x-0.5 transition-transform" />
            </div>
          </div>

        </div>
      </section>

      {/* 2. Hero Photo Banner with Saree Farmer (Grounded in KrishiMitra AI Mission) */}
      <section className="relative rounded-3xl overflow-hidden shadow-2xl min-h-[380px] sm:min-h-[460px] flex items-center justify-center p-6 sm:p-12 text-center group">
        <img
          src="/images/farmer_hero_saree.jpg"
          alt="Indian woman farmer in field with smartphone"
          className="absolute inset-0 w-full h-full object-cover object-center group-hover:scale-105 transition-transform duration-700"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/45 to-black/35 backdrop-blur-[1px]" />
        
        <div className="relative z-10 max-w-3xl mx-auto space-y-6">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/20 backdrop-blur-md text-white text-xs font-bold uppercase tracking-wider font-display">
            <Sparkles className="w-3.5 h-3.5 text-amber-300" />
            <span>Explainable Smart Agriculture for Indian Farmers</span>
          </div>

          <h1 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-extrabold text-white leading-tight tracking-tight font-display drop-shadow-md">
            With KrishiMitra AI, Indian farmers make data-driven crop decisions in seconds with complete explainability.
          </h1>

          <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
            <Link
              to="/chat"
              className="px-8 py-3.5 rounded-full bg-[#059669] hover:bg-[#047857] text-white font-bold text-sm sm:text-base font-display shadow-lg shadow-[#059669]/30 transition hover:scale-105 flex items-center gap-2"
            >
              <MessageSquare className="w-5 h-5" />
              <span>Launch KrishiChat AI</span>
            </Link>
            <Link
              to="/recommend"
              className="px-6 py-3.5 rounded-full bg-white/15 hover:bg-white/25 text-white font-bold text-sm sm:text-base font-display backdrop-blur border border-white/30 transition hover:scale-105 flex items-center gap-2"
            >
              <Sprout className="w-5 h-5 text-emerald-300" />
              <span>Crop Advisory Studio</span>
            </Link>
          </div>
        </div>
      </section>

      {/* 3. Solution Showcase 1: "Ask a question any way" with Interactive Floating Glass Bar */}
      <section className="space-y-8">
        <div>
          <span className="text-xs font-bold uppercase tracking-widest text-[#059669] font-display">
            Multi-Modal Intelligence
          </span>
          <h2 className="text-2xl sm:text-4xl font-extrabold text-[#0F281E] tracking-tight font-display mt-1">
            KrishiChat delivers personalized farming guidance & tips instantly
          </h2>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
          
          {/* Left: Farmer photo with floating glass input pill */}
          <div className="lg:col-span-7 relative rounded-3xl overflow-hidden shadow-depth group">
            <img
              src="/images/farmer_man_field.jpg"
              alt="Indian farmer man in lush green field"
              className="w-full h-[380px] sm:h-[440px] object-cover group-hover:scale-105 transition-transform duration-700"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/75 via-black/20 to-transparent" />

            {/* Overlaid Floating Glass Input Bar */}
            <div className="absolute bottom-6 left-6 right-6">
              <form
                onSubmit={handleInteractiveSubmit}
                className="glass-pill rounded-full p-2 pl-4 flex items-center justify-between shadow-2xl border border-white/60 backdrop-blur-md bg-white/85"
              >
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <div className="w-9 h-9 rounded-full bg-[#059669] flex items-center justify-center text-white shrink-0 shadow-sm">
                    <Camera className="w-4 h-4" />
                  </div>
                  <input
                    type="text"
                    value={interactiveInput}
                    onChange={(e) => setInteractiveInput(e.target.value)}
                    placeholder="Ask about your crops, soil, or pests..."
                    className="w-full bg-transparent text-sm font-semibold text-[#0F281E] placeholder-[#526B60] focus:outline-none font-sans"
                  />
                </div>
                <button
                  type="submit"
                  className="w-10 h-10 rounded-full bg-[#0F281E] hover:bg-[#059669] text-white flex items-center justify-center shrink-0 transition shadow-sm ml-2"
                  aria-label="Send query"
                >
                  <Mic className="w-4 h-4" />
                </button>
              </form>
            </div>
          </div>

          {/* Right: Typography & Feature Description */}
          <div className="lg:col-span-5 space-y-4 lg:pl-4">
            <h3 className="text-2xl sm:text-3xl font-extrabold text-[#0F281E] tracking-tight font-display">
              Ask a question any way
            </h3>
            <p className="text-base sm:text-lg text-[#526B60] leading-relaxed font-sans">
              Voice, text, or photo. Farmers communicate naturally in Telugu, Hindi, or English, and KrishiChat responds with verifiable agronomic evidence.
            </p>
            <div className="pt-2">
              <Link
                to="/chat"
                className="inline-flex items-center gap-2 text-sm sm:text-base font-bold text-[#059669] hover:text-[#047857] hover:underline font-display"
              >
                <span>Try asking with voice or photo</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>

        </div>
      </section>

      {/* 4. Solution Showcase 2: "Personalized to every location" */}
      <section className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
        
        {/* Left: Typography */}
        <div className="lg:col-span-5 space-y-4 order-2 lg:order-1">
          <span className="text-xs font-bold uppercase tracking-widest text-[#059669] font-display">
            Hyper-Local Precision
          </span>
          <h3 className="text-2xl sm:text-3xl font-extrabold text-[#0F281E] tracking-tight font-display">
            Personalized to every Indian district
          </h3>
          <p className="text-base sm:text-lg text-[#526B60] leading-relaxed font-sans">
            Advice is tuned to local soils, micro-climate, and seasonal patterns so guidance matches what actually thrives in your field.
          </p>
          <div className="pt-2">
            <Link
              to="/recommend"
              className="inline-flex items-center gap-2 text-sm sm:text-base font-bold text-[#059669] hover:text-[#047857] hover:underline font-display"
            >
              <span>Explore district agronomic profiles</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>

        {/* Right: Farmer Woman photo with floating location pill */}
        <div className="lg:col-span-7 relative rounded-3xl overflow-hidden shadow-depth group order-1 lg:order-2">
          <img
            src="/images/farmer_woman_field.jpg"
            alt="Indian farmer woman in field against green hills"
            className="w-full h-[380px] sm:h-[440px] object-cover group-hover:scale-105 transition-transform duration-700"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/15 to-transparent" />

          {/* Overlaid Floating Location Card */}
          <div className="absolute bottom-6 left-6 right-6">
            <Link
              to="/chat"
              className="glass-pill rounded-2xl p-4 flex items-center justify-between shadow-2xl border border-white/60 bg-white/90 hover:bg-white transition backdrop-blur-md"
            >
              <div>
                <span className="text-xs font-bold text-[#526B60] block font-display">Your Farm Location</span>
                <div className="flex items-center gap-2 mt-1">
                  <span className="w-5 h-5 rounded-full bg-[#059669] text-white text-[11px] font-bold flex items-center justify-center font-display">
                    ✓
                  </span>
                  <span className="font-extrabold text-sm text-[#0F281E] font-display">
                    {farm.district || 'Kurnool'}, {farm.state || 'Andhra Pradesh'}
                  </span>
                </div>
              </div>
              <div className="w-8 h-8 rounded-full bg-[#E8F5EF] text-[#059669] flex items-center justify-center">
                <ChevronRight className="w-4 h-4" />
              </div>
            </Link>
          </div>
        </div>

      </section>

      {/* 5. The Challenge Hero Banner */}
      <section className="relative rounded-3xl overflow-hidden shadow-2xl min-h-[380px] sm:min-h-[460px] flex items-center justify-center p-6 sm:p-12 text-center group">
        <img
          src="/images/farmer_inspecting_crops.jpg"
          alt="Indian woman farmer inspecting crop leaves"
          className="absolute inset-0 w-full h-full object-cover object-center group-hover:scale-105 transition-transform duration-700"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/55 to-black/35 backdrop-blur-[1px]" />
        
        <div className="relative z-10 max-w-3xl mx-auto space-y-4 text-white">
          <span className="inline-block px-3.5 py-1 rounded-full bg-white/20 backdrop-blur-md text-xs font-bold uppercase tracking-wider text-white font-display">
            The Agricultural Challenge
          </span>
          <h2 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-extrabold leading-tight tracking-tight font-display drop-shadow-md">
            Millions of farmers make critical decisions every day without timely agronomic advice
          </h2>
          <p className="text-sm sm:text-base text-white/90 max-w-xl mx-auto leading-relaxed font-sans">
            Every season, smallholder farmers face choices with massive consequences for yield, soil fertility, and household income. KrishiMitra AI puts verified agricultural science into their hands.
          </p>
        </div>
      </section>

      {/* 6. Multi-lingual & Voice Accessibility Callout */}
      <section className="p-8 sm:p-12 rounded-3xl bg-[#EAF5EF] border border-[#D0E5DA] shadow-depth flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="space-y-2 text-center md:text-left">
          <span className="text-xs font-bold uppercase tracking-widest text-[#059669] font-display">
            Vernacular Accessibility
          </span>
          <h3 className="text-2xl sm:text-3xl font-extrabold text-[#0F281E] font-display">
            Available in native languages, by voice or text
          </h3>
          <p className="text-sm sm:text-base text-[#526B60] max-w-xl font-sans">
            Supports Telugu (తెలుగు), Hindi (हिंदी), and English with high-accuracy speech-to-text and native audio narration.
          </p>
        </div>
        <Link
          to="/chat"
          className="px-8 py-3.5 rounded-full bg-[#059669] hover:bg-[#047857] text-white font-bold text-sm sm:text-base font-display shadow-md shadow-[#059669]/25 transition hover:scale-105 shrink-0 flex items-center gap-2"
        >
          <Volume2 className="w-5 h-5" />
          <span>Launch Voice Assistant</span>
        </Link>
      </section>

      {/* 7. Floating Quick-Launch Chat Pill */}
      <Link
        to="/chat"
        className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full bg-[#059669] hover:bg-[#047857] text-white flex items-center justify-center shadow-2xl hover:scale-110 transition-all group"
        aria-label="Open KrishiChat"
      >
        <MessageSquare className="w-6 h-6 group-hover:scale-110 transition-transform" />
      </Link>

    </div>
  );
};
