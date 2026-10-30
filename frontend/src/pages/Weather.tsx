import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { useLanguage } from '../contexts/LanguageContext';
import { useFarm } from '../contexts/FarmContext';
import { WeatherData } from '../types';
import {
  CloudSun,
  Droplets,
  Wind,
  Thermometer,
  Calendar,
  AlertTriangle,
  Compass,
  MapPin,
  RefreshCw,
  Sparkles
} from 'lucide-react';

export const Weather: React.FC = () => {
  const { t } = useLanguage();
  const { farm } = useFarm();

  const [weatherData, setWeatherData] = useState<WeatherData | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedDistrict, setSelectedDistrict] = useState(farm.district || 'Kurnool');
  const [selectedState, setSelectedState] = useState(farm.state || 'Andhra Pradesh');

  const fetchWeather = async () => {
    setLoading(true);
    try {
      const data = await api.getWeather({ state: selectedState, district: selectedDistrict });
      if (data && data.success) {
        setWeatherData(data);
      }
    } catch (err) {
      console.error("Weather fetch failed:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWeather();
  }, [selectedState, selectedDistrict]);

  const handleUseGeo = () => {
    if (!navigator.geolocation) {
      alert("Geolocation is not supported by your browser.");
      return;
    }
    setLoading(true);
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        try {
          const data = await api.getWeather({ lat: pos.coords.latitude, lon: pos.coords.longitude });
          if (data && data.success) {
            setWeatherData(data);
          }
        } catch (err) {
          console.error(err);
        } finally {
          setLoading(false);
        }
      },
      (err) => {
        console.warn("Geolocation denied:", err);
        setLoading(false);
      }
    );
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12 animate-in fade-in">
      
      {/* Header Banner */}
      <div className="bg-gradient-to-br from-[#059669] to-[#047857] text-white p-6 sm:p-8 rounded-3xl shadow-depth flex flex-wrap items-center justify-between gap-4">
        <div>
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/15 backdrop-blur-md text-emerald-100 text-xs font-bold uppercase tracking-wider font-display mb-2">
            <CloudSun className="w-3.5 h-3.5 text-amber-300" />
            <span>MausamRadar • Open-Meteo High-Resolution Telemetry</span>
          </span>
          <h1 className="text-2xl sm:text-4xl font-extrabold tracking-tight font-display">
            Live Weather & Agricultural Radar
          </h1>
          <p className="text-xs sm:text-sm text-emerald-100 mt-1 max-w-xl font-sans">
            Live meteorological data paired with actionable crop management, irrigation, and foliar spray advisories.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={handleUseGeo}
            className="px-4 py-2.5 rounded-2xl bg-white/15 hover:bg-white/25 text-white text-xs font-bold border border-white/30 backdrop-blur-md flex items-center gap-2 transition hover:scale-105 font-display"
          >
            <Compass className="w-4 h-4" />
            <span>Use GPS Location</span>
          </button>

          <button
            onClick={fetchWeather}
            className="p-2.5 rounded-2xl bg-white/15 hover:bg-white/25 text-white border border-white/30 backdrop-blur-md transition hover:scale-105"
            title="Refresh Weather"
            aria-label="Refresh Weather Data"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {weatherData ? (
        <div className="space-y-6">
          
          {/* Current Weather Cards Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            
            {/* Temperature Card */}
            <div className="p-6 rounded-3xl bg-white border border-[#E2ECE6] shadow-panel flex items-center gap-4 hover:scale-[1.02] transition-transform">
              <div className="w-12 h-12 rounded-2xl bg-amber-50 text-amber-600 flex items-center justify-center shrink-0 border border-amber-200">
                <Thermometer className="w-6 h-6" />
              </div>
              <div>
                <span className="text-xs font-bold text-[#526B60] block font-display">Temperature</span>
                <span className="text-2xl font-black text-[#0F281E] font-display">
                  {weatherData.current.temperature_c}°C
                </span>
                <span className="text-[11px] text-[#526B60] block font-sans">{weatherData.current.condition}</span>
              </div>
            </div>

            {/* Humidity Card */}
            <div className="p-6 rounded-3xl bg-white border border-[#E2ECE6] shadow-panel flex items-center gap-4 hover:scale-[1.02] transition-transform">
              <div className="w-12 h-12 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center shrink-0 border border-blue-200">
                <Droplets className="w-6 h-6" />
              </div>
              <div>
                <span className="text-xs font-bold text-[#526B60] block font-display">Relative Humidity</span>
                <span className="text-2xl font-black text-[#0F281E] font-display">
                  {weatherData.current.relative_humidity_pct}%
                </span>
                <span className="text-[11px] text-[#526B60] block font-sans">Atmospheric Vapor</span>
              </div>
            </div>

            {/* Precipitation Card */}
            <div className="p-6 rounded-3xl bg-white border border-[#E2ECE6] shadow-panel flex items-center gap-4 hover:scale-[1.02] transition-transform">
              <div className="w-12 h-12 rounded-2xl bg-emerald-50 text-[#059669] flex items-center justify-center shrink-0 border border-emerald-200">
                <CloudSun className="w-6 h-6" />
              </div>
              <div>
                <span className="text-xs font-bold text-[#526B60] block font-display">Current Rainfall</span>
                <span className="text-2xl font-black text-[#0F281E] font-display">
                  {weatherData.current.rainfall_mm} mm
                </span>
                <span className="text-[11px] text-[#526B60] block font-sans">Precipitation Today</span>
              </div>
            </div>

            {/* Wind Card */}
            <div className="p-6 rounded-3xl bg-white border border-[#E2ECE6] shadow-panel flex items-center gap-4 hover:scale-[1.02] transition-transform">
              <div className="w-12 h-12 rounded-2xl bg-teal-50 text-teal-600 flex items-center justify-center shrink-0 border border-teal-200">
                <Wind className="w-6 h-6" />
              </div>
              <div>
                <span className="text-xs font-bold text-[#526B60] block font-display">Wind Velocity</span>
                <span className="text-2xl font-black text-[#0F281E] font-display">
                  {weatherData.current.wind_speed_ms} m/s
                </span>
                <span className="text-[11px] text-[#059669] font-bold block font-sans">Foliar Spray Feasible</span>
              </div>
            </div>

          </div>

          {/* Agricultural Advisory Callout */}
          <div className="p-6 rounded-3xl bg-[#EAF5EF] border border-[#D0E5DA] shadow-panel space-y-2">
            <div className="flex items-center gap-2 text-xs font-bold text-[#059669] uppercase tracking-wide font-display">
              <AlertTriangle className="w-4 h-4 text-[#059669]" />
              <span>Real-Time Agronomic Telemetry Advisory</span>
            </div>
            <p className="text-xs sm:text-sm text-[#0F281E] leading-relaxed font-semibold font-sans">
              {weatherData.agricultural_advisory}
            </p>
          </div>

          {/* 7-Day Forecast Strip */}
          <div className="bg-white p-6 rounded-3xl border border-[#E2ECE6] shadow-panel space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-extrabold uppercase tracking-wider text-[#0F281E] flex items-center gap-2 font-display">
                <Calendar className="w-4 h-4 text-[#059669]" />
                <span>7-Day Meteorological Outlook</span>
              </h3>
              <span className="text-xs font-bold text-[#526B60] font-display">
                {weatherData.location.district}, {weatherData.location.state}
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3 pt-2">
              {weatherData.forecast.map((day, idx) => (
                <div
                  key={idx}
                  className="p-4 rounded-2xl bg-[#F8FAF9] border border-[#D0E5DA] text-center space-y-2 hover:bg-[#E8F5EF] transition"
                >
                  <span className="text-[11px] font-bold text-[#526B60] block font-display">
                    {new Date(day.date).toLocaleDateString(undefined, { weekday: 'short', month: 'numeric', day: 'numeric' })}
                  </span>
                  <div className="text-2xl">🌦</div>
                  <div className="text-xs font-extrabold text-[#0F281E] font-display">
                    {day.max_temp_c ? `${Math.round(day.max_temp_c)}°` : '--'} / {day.min_temp_c ? `${Math.round(day.min_temp_c)}°` : '--'}
                  </div>
                  <span className="text-[10px] text-[#059669] font-bold block font-sans">
                    {day.rainfall_mm} mm
                  </span>
                </div>
              ))}
            </div>
          </div>

        </div>
      ) : (
        <div className="p-12 text-center text-[#526B60] font-sans">Loading live weather data...</div>
      )}

    </div>
  );
};
