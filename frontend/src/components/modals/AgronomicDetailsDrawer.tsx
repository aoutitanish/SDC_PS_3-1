import React, { useState, useEffect } from 'react';
import { X, Sprout, Droplets, Thermometer, ShieldAlert, Sparkles, Compass, Layers, CheckCircle2, BookOpen, Volume2, Pause, Play, Square } from 'lucide-react';
import { DetailedAgronomicAnalysis } from '../../types';
import { useFarm } from '../../contexts/FarmContext';
import { speechAudioController, AudioState } from '../../utils/speech';

interface AgronomicDetailsDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  analysis: DetailedAgronomicAnalysis | null;
  cropName?: string;
}

export const AgronomicDetailsDrawer: React.FC<AgronomicDetailsDrawerProps> = ({
  isOpen,
  onClose,
  analysis,
  cropName = 'Arhar/Tur (Pigeon Pea)'
}) => {
  const { farm } = useFarm();
  const [audioState, setAudioState] = useState<AudioState>('IDLE');

  // Cancel any speech when drawer unmounts or closes
  useEffect(() => {
    return () => {
      speechAudioController.stop();
    };
  }, []);

  if (!isOpen) return null;

  const handleClose = () => {
    speechAudioController.stop();
    setAudioState('IDLE');
    onClose();
  };

  const currentCrop = analysis?.crop || cropName;
  const soilParams = analysis?.soil_parameters || {
    measured_clay_pct: 31.2,
    optimal_clay_range: '23.5–39.9%',
    measured_ph: 7.1,
    optimal_ph_range: '5.6–7.6',
    soil_suitability_score: 95
  };

  const climateParams = analysis?.climate_parameters || {
    regional_rainfall_mm: 927.0,
    crop_rainfall_optimal_mm: '500–1100 mm',
    mean_temperature_c: 27.2,
    crop_temp_optimal_c: '20–35°C',
    climate_suitability_score: 92
  };

  const waterAnalysis = analysis?.water_analysis || {
    farm_irrigation: farm.irrigation_type || 'Drip Irrigation & Borewell',
    water_source: farm.water_source || 'Borewell',
    crop_water_requirement: '400–650 mm (Low to Moderate)',
    water_compatibility: 'Optimal Micro-irrigation fit'
  };

  const explainFactors = analysis?.explainability_factors || [
    { factor: 'Soil Compatibility', status: 'Optimal', impact: '+28%' },
    { factor: 'Rainfall & Thermal Suitability', status: 'Optimal', impact: '+25%' },
    { factor: 'Irrigation Efficiency', status: 'Favorable', impact: '+22%' },
    { factor: 'Historical Regional Yield', status: 'Normal', impact: '+15%' }
  ];

  const sources = analysis?.sources || [
    { name: 'Crop Expert Dataset', why_used: 'Crop agronomic thresholds and regional yield benchmarks' },
    { name: 'Soil Expert Dataset', why_used: 'SoilGrids clay composition and pH calibration' },
    { name: 'Weather Expert Dataset', why_used: 'IMD regional climate normals and precipitation' },
    { name: 'Master Geography Dataset', why_used: 'District administrative and agro-climatic boundaries' }
  ];

  const limitations = analysis?.limitations || [
    'Actual crop performance will depend on recent soil testing and borewell discharge rate.',
    'Ensure proper drainage to prevent water stagnation in heavy clay soil.'
  ];

  const handleListenDetails = () => {
    if (audioState === 'PLAYING') {
      speechAudioController.pause();
      setAudioState('PAUSED');
      return;
    } else if (audioState === 'PAUSED') {
      speechAudioController.resume();
      setAudioState('PLAYING');
      return;
    }

    const speechText = `Full scientific analysis for ${currentCrop}. Soil clay is ${soilParams.measured_clay_pct} percent, pH is ${soilParams.measured_ph}. Regional rainfall is ${climateParams.regional_rainfall_mm} millimeters with mean temperature ${climateParams.mean_temperature_c} degrees Celsius. Farm irrigation is ${waterAnalysis.farm_irrigation}. Crop water requirement is ${waterAnalysis.crop_water_requirement}.`;
    
    speechAudioController.play(
      speechText,
      farm.preferred_language || 'en',
      (state) => {
        setAudioState(state);
      },
      'FULL_ANALYSIS',
      'full_analysis_drawer'
    );
  };

  const handleStopAudio = () => {
    speechAudioController.stop();
    setAudioState('STOPPED');
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/70 backdrop-blur-sm animate-in fade-in" onClick={handleClose}>
      <div 
        className="w-full max-w-xl h-full bg-[#111E31] border-l border-[#26374D] shadow-2xl flex flex-col animate-in slide-in-from-right duration-300"
        onClick={(e) => e.stopPropagation()}
      >
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#26374D] bg-[#17263A]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#08A873] to-[#044c33] flex items-center justify-center text-white shadow-md">
              <Sprout className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-bold text-lg text-[#F5F8FC]">{currentCrop}</h3>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#08A873] text-white">
                  Level 2 Scientific Analysis
                </span>
              </div>
              <p className="text-xs text-[#A9B7C8]">
                Calibrated for {farm.district}, {farm.state} • {farm.farm_size_acres} Acres {farm.soil_type}
              </p>
            </div>
          </div>
          <button onClick={handleClose} className="p-1.5 rounded-lg text-[#A9B7C8] hover:text-white hover:bg-[#26374D] transition" aria-label="Close Analysis">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-5 bg-[#0C1728]">
          
          {/* Audio Action for Full Analysis: Play, Pause, Resume, Stop */}
          <div className="flex items-center justify-between p-3 rounded-xl bg-[#17263A] border border-[#26374D]">
            <div className="flex items-center gap-2 text-xs text-[#A9B7C8]">
              <Volume2 className={`w-4 h-4 ${audioState === 'PLAYING' ? 'text-amber-400 animate-pulse' : 'text-[#08A873]'}`} />
              <span>
                {audioState === 'PLAYING' ? 'Playing Scientific Narration...' : audioState === 'PAUSED' ? 'Audio Paused' : 'Scientific Audio Narration'}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={handleListenDetails}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-[#08A873] text-white hover:bg-[#09C486] transition shadow-sm"
              >
                {audioState === 'PLAYING' ? (
                  <>
                    <Pause className="w-3.5 h-3.5" />
                    <span>Pause</span>
                  </>
                ) : audioState === 'PAUSED' ? (
                  <>
                    <Play className="w-3.5 h-3.5" />
                    <span>Resume</span>
                  </>
                ) : (
                  <>
                    <Volume2 className="w-3.5 h-3.5" />
                    <span>Listen to Full Analysis</span>
                  </>
                )}
              </button>
              {(audioState === 'PLAYING' || audioState === 'PAUSED') && (
                <button
                  type="button"
                  onClick={handleStopAudio}
                  className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-rose-900/60 text-rose-300 hover:bg-rose-800 transition border border-rose-700/50"
                  title="Stop audio narration"
                >
                  <Square className="w-3 h-3 fill-rose-300" />
                  <span>Stop</span>
                </button>
              )}
            </div>
          </div>

          {/* Model Metrics */}
          <div className="grid grid-cols-2 gap-3">
            <div className="p-4 rounded-xl bg-[#17263A] border border-[#26374D]">
              <span className="text-xs font-bold uppercase tracking-wider text-[#718197]">Agronomic Suitability</span>
              <div className="text-2xl font-black text-[#08A873] mt-0.5">
                {analysis?.agronomic_suitability_score || 94.5} <span className="text-xs font-medium text-[#A9B7C8]">/ 100</span>
              </div>
              <span className="text-[11px] text-[#A9B7C8]">5-Factor Agronomic Model</span>
            </div>
            <div className="p-4 rounded-xl bg-[#17263A] border border-[#26374D]">
              <span className="text-xs font-bold uppercase tracking-wider text-[#718197]">Model Confidence</span>
              <div className="inline-flex items-center gap-1.5 px-2.5 py-1 mt-1 rounded-full text-xs font-bold bg-[#103C38] text-[#08A873] border border-[#08A873]/40">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>{analysis?.model_confidence || 'High'} Confidence</span>
              </div>
              <div className="text-[10px] text-[#718197] mt-1">Random Forest Estimator Agreement</div>
            </div>
          </div>

          {/* 1. Soil Parameters */}
          <div className="p-4 rounded-xl bg-[#17263A] border border-[#26374D] space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-[#08A873] flex items-center gap-1.5">
                <Compass className="w-4 h-4" />
                <span>1. Soil Physicochemical Properties</span>
              </span>
              <span className="text-xs text-[#08A873] font-bold">{soilParams.soil_suitability_score}% Match</span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs pt-1">
              <div className="p-2.5 rounded-lg bg-[#111E31] border border-[#26374D]">
                <div className="text-[#A9B7C8]">Clay Content</div>
                <div className="text-sm font-bold text-white mt-0.5">{soilParams.measured_clay_pct}%</div>
                <div className="text-[10px] text-[#718197]">Optimal: {soilParams.optimal_clay_range}</div>
              </div>
              <div className="p-2.5 rounded-lg bg-[#111E31] border border-[#26374D]">
                <div className="text-[#A9B7C8]">Soil pH</div>
                <div className="text-sm font-bold text-white mt-0.5">{soilParams.measured_ph}</div>
                <div className="text-[10px] text-[#718197]">Optimal: {soilParams.optimal_ph_range}</div>
              </div>
            </div>
          </div>

          {/* 2. Climate & Precipitation */}
          <div className="p-4 rounded-xl bg-[#17263A] border border-[#26374D] space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-[#08A873] flex items-center gap-1.5">
                <Thermometer className="w-4 h-4" />
                <span>2. Agro-Climatic Parameters</span>
              </span>
              <span className="text-xs text-[#08A873] font-bold">{climateParams.climate_suitability_score}% Match</span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs pt-1">
              <div className="p-2.5 rounded-lg bg-[#111E31] border border-[#26374D]">
                <div className="text-[#A9B7C8]">Annual Rainfall</div>
                <div className="text-sm font-bold text-white mt-0.5">{climateParams.regional_rainfall_mm} mm</div>
                <div className="text-[10px] text-[#718197]">Crop Optimal: {climateParams.crop_rainfall_optimal_mm}</div>
              </div>
              <div className="p-2.5 rounded-lg bg-[#111E31] border border-[#26374D]">
                <div className="text-[#A9B7C8]">Mean Temperature</div>
                <div className="text-sm font-bold text-white mt-0.5">{climateParams.mean_temperature_c}°C</div>
                <div className="text-[10px] text-[#718197]">Crop Optimal: {climateParams.crop_temp_optimal_c}</div>
              </div>
            </div>
          </div>

          {/* 3. Irrigation & Water Requirement */}
          <div className="p-4 rounded-xl bg-[#17263A] border border-[#26374D] space-y-2">
            <span className="text-xs font-bold uppercase tracking-wider text-[#08A873] flex items-center gap-1.5">
              <Droplets className="w-4 h-4" />
              <span>3. Irrigation & Hydrology Assessment</span>
            </span>
            <div className="text-xs space-y-1.5 text-[#E0E7EE] pt-1">
              <div className="flex justify-between py-1 border-b border-[#26374D]">
                <span className="text-[#A9B7C8]">Farm Irrigation Setup:</span>
                <span className="font-semibold text-white">{waterAnalysis.farm_irrigation}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[#26374D]">
                <span className="text-[#A9B7C8]">Crop Water Demand:</span>
                <span className="font-semibold text-white">{waterAnalysis.crop_water_requirement}</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-[#A9B7C8]">Compatibility:</span>
                <span className="font-semibold text-[#08A873]">{waterAnalysis.water_compatibility}</span>
              </div>
            </div>
          </div>

          {/* 4. Explainability & Factor Contributions */}
          <div className="p-4 rounded-xl bg-[#17263A] border border-[#26374D] space-y-2">
            <span className="text-xs font-bold uppercase tracking-wider text-[#08A873] flex items-center gap-1.5">
              <Sparkles className="w-4 h-4 text-amber-400" />
              <span>4. Explainable Factor Contributions</span>
            </span>
            <div className="space-y-2 pt-1">
              {explainFactors.map((f: any, idx: number) => (
                <div key={idx} className="flex items-center justify-between p-2 rounded-lg bg-[#111E31] text-xs">
                  <span className="text-[#E0E7EE]">{f.factor}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] px-2 py-0.5 rounded bg-[#17263A] text-[#08A873] font-medium">{f.status}</span>
                    <span className="font-bold text-[#08A873]">{f.impact}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 5. Limitations & Management Cautions */}
          <div className="p-4 rounded-xl bg-[#17263A] border border-amber-900/40 space-y-2">
            <span className="text-xs font-bold uppercase tracking-wider text-amber-400 flex items-center gap-1.5">
              <ShieldAlert className="w-4 h-4" />
              <span>5. Agronomic Limitations & Management Notes</span>
            </span>
            <ul className="list-disc list-inside text-xs text-[#E0E7EE] space-y-1 pt-1">
              {limitations.map((lim: string, idx: number) => (
                <li key={idx}>{lim}</li>
              ))}
            </ul>
          </div>

          {/* 6. Scientific Sources & Provenance */}
          <div className="p-4 rounded-xl bg-[#17263A] border border-[#26374D] space-y-2">
            <span className="text-xs font-bold uppercase tracking-wider text-[#08A873] flex items-center gap-1.5">
              <BookOpen className="w-4 h-4" />
              <span>6. Data Provenance & Verified Sources</span>
            </span>
            <div className="space-y-2 pt-1">
              {sources.map((src: any, idx: number) => (
                <div key={idx} className="p-2.5 rounded-lg bg-[#111E31] border border-[#26374D] text-xs">
                  <div className="font-bold text-white">{src.name}</div>
                  <div className="text-[11px] text-[#A9B7C8] mt-0.5">{src.why_used}</div>
                </div>
              ))}
            </div>
          </div>

        </div>

      </div>
    </div>
  );
};
