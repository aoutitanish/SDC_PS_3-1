import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  Store,
  Warehouse,
  Scale,
  ShieldAlert,
  Calendar,
  Layers,
  Info,
  MapPin,
  CheckCircle2,
  Clock,
  AlertCircle,
  BarChart3,
  DollarSign,
  Droplet
} from 'lucide-react';
import { useFarm } from '../contexts/FarmContext';
import { api } from '../services/api';

const SUPPORTED_CROPS = [
  "Arhar/Tur (Pigeon Pea)",
  "Gram (Chickpea)",
  "Rice",
  "Wheat",
  "Maize",
  "Cotton",
  "Groundnut",
  "Sugarcane",
  "Soyabean",
  "Mustard",
  "Jute",
  "Bajra (Pearl Millet)",
  "Jowar (Sorghum)",
  "Ragi (Finger Millet)",
  "Barley",
  "Sesamum (Til)",
  "Sunflower",
  "Safflower",
  "Nigerseed",
  "Moong (Green Gram)",
  "Urad (Black Gram)",
  "Masoor (Lentil)",
  "Horse-gram"
];

export const Market: React.FC = () => {
  const { farm } = useFarm();

  const [selectedCrop, setSelectedCrop] = useState<string>("Arhar/Tur (Pigeon Pea)");
  const [comparisonCrops, setComparisonCrops] = useState<string[]>(["Arhar/Tur (Pigeon Pea)", "Gram (Chickpea)", "Cotton"]);

  const [loadingMarket, setLoadingMarket] = useState<boolean>(false);
  const [marketData, setMarketData] = useState<any>(null);

  const [loadingEcon, setLoadingEcon] = useState<boolean>(false);
  const [econData, setEconData] = useState<any>(null);

  const [loadingPostHarvest, setLoadingPostHarvest] = useState<boolean>(false);
  const [postHarvestData, setPostHarvestData] = useState<any>(null);

  const [loadingComparison, setLoadingComparison] = useState<boolean>(false);
  const [comparisonResults, setComparisonResults] = useState<any[]>([]);

  // Fetch telemetry & analytics on crop or location change
  useEffect(() => {
    fetchMarketData(selectedCrop);
    fetchEconData(selectedCrop);
    fetchPostHarvestData(selectedCrop);
  }, [selectedCrop, farm.state, farm.district, farm.farm_size_acres]);

  useEffect(() => {
    fetchComparisonData();
  }, [comparisonCrops, farm.farm_size_acres]);

  const fetchMarketData = async (cropName: string) => {
    setLoadingMarket(true);
    try {
      const res = await api.getMarketPrices(cropName, farm.state, farm.district);
      setMarketData(res);
    } catch (e) {
      setMarketData({ status: 'unavailable', data_type: 'unavailable', markets: [] });
    } finally {
      setLoadingMarket(false);
    }
  };

  const fetchEconData = async (cropName: string) => {
    setLoadingEcon(true);
    try {
      const farmSize = farm.farm_size_acres || 2.5;
      const res = await api.calculateEconomics({
        crop: cropName,
        farm_size_acres: farmSize
      });
      setEconData(res);
    } catch (e) {
      setEconData({ status: 'unavailable' });
    } finally {
      setLoadingEcon(false);
    }
  };

  const fetchPostHarvestData = async (cropName: string) => {
    setLoadingPostHarvest(true);
    try {
      const farmSize = farm.farm_size_acres || 2.5;
      const res = await api.getPostHarvest(cropName, farmSize);
      setPostHarvestData(res);
    } catch (e) {
      setPostHarvestData({ status: 'unavailable' });
    } finally {
      setLoadingPostHarvest(false);
    }
  };

  const fetchComparisonData = async () => {
    setLoadingComparison(true);
    try {
      const farmSize = farm.farm_size_acres || 2.5;
      const cropBatch = comparisonCrops.map(c => ({ crop: c }));
      const res = await api.calculateEconomics({
        crops: cropBatch,
        farm_size_acres: farmSize
      });
      setComparisonResults(res.results || []);
    } catch (e) {
      setComparisonResults([]);
    } finally {
      setLoadingComparison(false);
    }
  };

  const toggleComparisonCrop = (cropName: string) => {
    if (comparisonCrops.includes(cropName)) {
      if (comparisonCrops.length > 1) {
        setComparisonCrops(comparisonCrops.filter(c => c !== cropName));
      }
    } else {
      if (comparisonCrops.length < 5) {
        setComparisonCrops([...comparisonCrops, cropName]);
      }
    }
  };

  const renderStatusBadge = (dataType?: string) => {
    if (dataType === 'live') {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 text-xs font-bold border border-emerald-300">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          🟢 Live Mandi Telemetry
        </span>
      );
    }
    if (dataType === 'cached') {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-100 text-amber-800 text-xs font-bold border border-amber-300">
          <span className="w-2 h-2 rounded-full bg-amber-500"></span>
          🟡 Cached Telemetry
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-100 text-slate-700 text-xs font-bold border border-slate-300">
        <span className="w-2 h-2 rounded-full bg-slate-400"></span>
        ⚪ Live Market Unavailable
      </span>
    );
  };

  const farmSizeNum = farm.farm_size_acres || 2.5;

  return (
    <div className="max-w-7xl mx-auto space-y-8 pb-12">
      
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-[#0F281E] via-[#163D2E] to-[#059669] rounded-3xl p-6 sm:p-8 text-white shadow-xl relative overflow-hidden">
        <div className="relative z-10 space-y-2">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 backdrop-blur-md text-emerald-200 text-xs font-semibold">
            <TrendingUp className="w-4 h-4 text-emerald-300" />
            <span>Economic Intelligence & Market Telemetry</span>
          </div>
          <h1 className="text-2xl sm:text-4xl font-extrabold tracking-tight">
            Market & Profit Intelligence
          </h1>
          <p className="text-emerald-100/80 text-sm max-w-2xl">
            Real-time APMC mandi telemetry, cost of cultivation analysis, and post-harvest storage guidance for verified Indian crop economic benchmarks.
          </p>
        </div>
      </div>

      {/* SECTION 1: Farm Context */}
      <div className="bg-white rounded-2xl p-6 border border-[#E2ECE6] shadow-sm">
        <div className="flex items-center gap-2 mb-4">
          <MapPin className="w-5 h-5 text-[#059669]" />
          <h2 className="text-lg font-bold text-[#0F281E]">Active Farm Context</h2>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-4 text-xs">
          <div className="bg-[#F8FAF9] p-3 rounded-xl border border-[#E2ECE6]">
            <span className="text-[#526B60] block font-medium">Farm Size</span>
            <span className="font-bold text-[#0F281E] text-sm">{farmSizeNum} Acres</span>
          </div>
          <div className="bg-[#F8FAF9] p-3 rounded-xl border border-[#E2ECE6]">
            <span className="text-[#526B60] block font-medium">State</span>
            <span className="font-bold text-[#0F281E] text-sm">{farm.state || 'Andhra Pradesh'}</span>
          </div>
          <div className="bg-[#F8FAF9] p-3 rounded-xl border border-[#E2ECE6]">
            <span className="text-[#526B60] block font-medium">District</span>
            <span className="font-bold text-[#0F281E] text-sm">{farm.district || 'Kurnool'}</span>
          </div>
          <div className="bg-[#F8FAF9] p-3 rounded-xl border border-[#E2ECE6]">
            <span className="text-[#526B60] block font-medium">Soil Type</span>
            <span className="font-bold text-[#0F281E] text-sm">{farm.soil_type || 'Black Soil'}</span>
          </div>
          <div className="bg-[#F8FAF9] p-3 rounded-xl border border-[#E2ECE6]">
            <span className="text-[#526B60] block font-medium">Irrigation</span>
            <span className="font-bold text-[#0F281E] text-sm">{farm.irrigation_type || 'Borewell'}</span>
          </div>
          <div className="bg-[#F8FAF9] p-3 rounded-xl border border-[#E2ECE6]">
            <span className="text-[#526B60] block font-medium">Water Supply</span>
            <span className="font-bold text-[#0F281E] text-sm">{farm.water_availability || 'Moderate'}</span>
          </div>
          <div className="bg-[#F8FAF9] p-3 rounded-xl border border-[#E2ECE6]">
            <span className="text-[#526B60] block font-medium">Season</span>
            <span className="font-bold text-[#0F281E] text-sm">{farm.season || 'Kharif'}</span>
          </div>
        </div>
      </div>

      {/* SECTION 2: Crop Selection */}
      <div className="bg-white rounded-2xl p-6 border border-[#E2ECE6] shadow-sm">
        <label className="block text-sm font-bold text-[#0F281E] mb-2">
          Select Target Crop for Economic Analysis:
        </label>
        <select
          value={selectedCrop}
          onChange={(e) => setSelectedCrop(e.target.value)}
          className="w-full max-w-md px-4 py-2.5 rounded-xl border border-[#E2ECE6] bg-[#F8FAF9] text-[#0F281E] font-semibold focus:outline-none focus:ring-2 focus:ring-[#059669]"
        >
          {SUPPORTED_CROPS.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </div>

      {/* Grid: SECTION 3 (Live Market) & SECTION 4 (Economic Summary) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* SECTION 3: Live Market Price */}
        <div className="bg-white rounded-2xl p-6 border border-[#E2ECE6] shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Store className="w-5 h-5 text-[#059669]" />
              <h2 className="text-lg font-bold text-[#0F281E]">Mandi Market Telemetry</h2>
            </div>
            {renderStatusBadge(marketData?.data_type)}
          </div>

          {loadingMarket ? (
            <div className="p-8 text-center text-[#526B60] font-medium animate-pulse">
              Retrieving live Agmarknet mandi telemetry...
            </div>
          ) : marketData?.status === 'success' && marketData?.markets?.length > 0 ? (
            <div className="space-y-4">
              {marketData.markets.map((m: any, idx: number) => (
                <div key={idx} className="p-4 rounded-xl bg-[#F0FDF4] border border-[#DCFCE7] space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-[#0F281E] text-base">{m.mandi_name || 'APMC Mandi'}</span>
                    <span className="text-xs text-[#526B60] font-semibold">{m.arrival_date || 'Today'}</span>
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-center pt-2">
                    <div className="bg-white p-2 rounded-lg border border-[#E2ECE6]">
                      <span className="text-[10px] text-[#526B60] uppercase font-bold block">Min Price</span>
                      <span className="text-sm font-extrabold text-[#0F281E]">₹{m.min_price}</span>
                    </div>
                    <div className="bg-[#059669] text-white p-2 rounded-lg shadow-sm">
                      <span className="text-[10px] uppercase font-bold block text-emerald-100">Modal Price</span>
                      <span className="text-base font-black">₹{m.modal_price}</span>
                    </div>
                    <div className="bg-white p-2 rounded-lg border border-[#E2ECE6]">
                      <span className="text-[10px] text-[#526B60] uppercase font-bold block">Max Price</span>
                      <span className="text-sm font-extrabold text-[#0F281E]">₹{m.max_price}</span>
                    </div>
                  </div>
                  <p className="text-[11px] text-[#526B60] pt-1">
                    Unit: {m.price_unit || 'INR/quintal'} • Source: {m.data_source || 'Agmarknet'}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-6 rounded-xl bg-slate-50 border border-slate-200 text-center space-y-2">
              <AlertCircle className="w-8 h-8 text-slate-400 mx-auto" />
              <p className="font-bold text-[#0F281E]">Current mandi price unavailable</p>
              <p className="text-xs text-[#526B60]">
                No live or cached mandi records were found for {selectedCrop} in {farm.district || 'this district'}.
                Calculations fallback safely to official MSP reference benchmarks.
              </p>
            </div>
          )}
        </div>

        {/* SECTION 4: Economic Summary */}
        <div className="bg-white rounded-2xl p-6 border border-[#E2ECE6] shadow-sm space-y-4">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-[#059669]" />
            <h2 className="text-lg font-bold text-[#0F281E]">Economic Engine Summary</h2>
          </div>

          {loadingEcon ? (
            <div className="p-8 text-center text-[#526B60] font-medium animate-pulse">
              Computing deterministic economic metrics...
            </div>
          ) : econData?.status === 'success' && econData?.economic_metrics ? (
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-3 bg-[#F8FAF9] rounded-xl border border-[#E2ECE6]">
                <span className="text-[#526B60] font-medium block">Estimated Production</span>
                <span className="text-base font-extrabold text-[#0F281E]">
                  {econData.economic_metrics.production_quintals} quintals
                </span>
              </div>
              <div className="p-3 bg-[#F8FAF9] rounded-xl border border-[#E2ECE6]">
                <span className="text-[#526B60] font-medium block">Gross Revenue</span>
                <span className="text-base font-extrabold text-[#0F281E]">
                  ₹{econData.economic_metrics.gross_revenue_inr?.toLocaleString()}
                </span>
              </div>
              <div className="p-3 bg-[#F8FAF9] rounded-xl border border-[#E2ECE6]">
                <span className="text-[#526B60] font-medium block">Cultivation Cost (A2+FL)</span>
                <span className="text-base font-extrabold text-rose-700">
                  ₹{econData.economic_metrics.total_cultivation_cost_inr?.toLocaleString()}
                </span>
              </div>
              <div className="p-3 bg-[#F0FDF4] rounded-xl border border-[#DCFCE7]">
                <span className="text-[#059669] font-semibold block">Estimated Net Return</span>
                <span className="text-base font-black text-[#059669]">
                  ₹{econData.economic_metrics.estimated_net_return_inr?.toLocaleString()}
                </span>
              </div>
              <div className="p-3 bg-[#F8FAF9] rounded-xl border border-[#E2ECE6]">
                <span className="text-[#526B60] font-medium block">Gross Margin</span>
                <span className="text-base font-extrabold text-[#0F281E]">
                  {econData.economic_metrics.gross_margin_pct}%
                </span>
              </div>
              <div className="p-3 bg-[#F8FAF9] rounded-xl border border-[#E2ECE6]">
                <span className="text-[#526B60] font-medium block">Break-even Price</span>
                <span className="text-base font-extrabold text-[#0F281E]">
                  ₹{econData.economic_metrics.break_even_price_inr_per_quintal}/q
                </span>
              </div>
              <div className="col-span-2 p-3 bg-amber-50 rounded-xl border border-amber-200 flex justify-between items-center">
                <span className="text-amber-900 font-bold">Return on Investment (ROI)</span>
                <span className="text-lg font-black text-amber-950">
                  {econData.economic_metrics.roi_pct}%
                </span>
              </div>
            </div>
          ) : (
            <div className="p-6 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-900">
              Economic metrics unavailable or missing inputs for this selection.
            </div>
          )}
        </div>

      </div>

      {/* SECTION 5: DATA PROVENANCE */}
      {econData?.provenance && (
        <div className="bg-white rounded-2xl p-6 border border-[#E2ECE6] shadow-sm space-y-4">
          <div className="flex items-center gap-2">
            <Layers className="w-5 h-5 text-[#059669]" />
            <h2 className="text-lg font-bold text-[#0F281E]">Data Provenance & Source Metadata</h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
            <div className="p-4 rounded-xl bg-[#F8FAF9] border border-[#E2ECE6] space-y-1">
              <span className="px-2 py-0.5 rounded bg-blue-100 text-blue-800 font-bold uppercase text-[10px]">
                {econData.provenance.yield?.data_type || 'Historical'}
              </span>
              <p className="font-bold text-[#0F281E] pt-1">Yield Benchmark</p>
              <p className="text-[#526B60]">{econData.provenance.yield?.value} quintals/acre</p>
              <p className="text-[10px] text-[#526B60]">Source: {econData.provenance.yield?.source}</p>
            </div>

            <div className="p-4 rounded-xl bg-[#F8FAF9] border border-[#E2ECE6] space-y-1">
              <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 font-bold uppercase text-[10px]">
                {econData.provenance.price?.data_type || 'Official'} ({econData.provenance.price?.price_basis})
              </span>
              <p className="font-bold text-[#0F281E] pt-1">Price Basis</p>
              <p className="text-[#526B60]">₹{econData.provenance.price?.value}/quintal</p>
              <p className="text-[10px] text-[#526B60]">Source: {econData.provenance.price?.source}</p>
            </div>

            <div className="p-4 rounded-xl bg-[#F8FAF9] border border-[#E2ECE6] space-y-1">
              <span className="px-2 py-0.5 rounded bg-purple-100 text-purple-800 font-bold uppercase text-[10px]">
                {econData.provenance.cost?.data_type || 'Official'}
              </span>
              <p className="font-bold text-[#0F281E] pt-1">Cultivation Cost Basis</p>
              <p className="text-[#526B60]">₹{econData.provenance.cost?.value}/acre</p>
              <p className="text-[10px] text-[#526B60]">Source: {econData.provenance.cost?.source}</p>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-[11px] text-[#526B60] flex items-start gap-2">
            <Info className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
            <span>{econData.provenance.calculation?.disclaimer}</span>
          </div>
        </div>
      )}

      {/* SECTION 6: SELL NOW & STORE INFORMATION & SEASONAL LIMITATION */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* SUB-SECTION 4: SELL NOW VALUE */}
        <div className="bg-white rounded-2xl p-6 border border-[#E2ECE6] shadow-sm space-y-4">
          <div className="flex items-center gap-2">
            <DollarSign className="w-5 h-5 text-[#059669]" />
            <h2 className="text-lg font-bold text-[#0F281E]">Current Sale-Value Estimate</h2>
          </div>

          {marketData?.status === 'success' && marketData?.markets?.length > 0 && econData?.economic_metrics ? (
            <div className="space-y-3 text-xs">
              <div className="p-3 bg-[#F0FDF4] rounded-xl border border-[#DCFCE7] space-y-1">
                <span className="text-[#526B60] block font-medium">Estimated Gross Sale Value</span>
                <span className="text-xl font-black text-[#059669]">
                  ₹{(
                    (marketData.markets[0].modal_price || 0) * (econData.economic_metrics.production_quintals || 0)
                  ).toLocaleString()}
                </span>
                <p className="text-[11px] text-[#526B60] pt-1">
                  Based on current mandi modal price of ₹{marketData.markets[0].modal_price}/quintal and estimated yield of {econData.economic_metrics.production_quintals} quintals.
                </p>
              </div>
              <div className="p-3 bg-[#F8FAF9] rounded-xl border border-[#E2ECE6] space-y-1">
                <p className="text-[#526B60]">Mandi: <strong className="text-[#0F281E]">{marketData.markets[0].mandi_name}</strong></p>
                <p className="text-[#526B60]">Date: <strong className="text-[#0F281E]">{marketData.markets[0].arrival_date || 'Current'}</strong></p>
                <p className="text-[#526B60]">Source: <strong className="text-[#0F281E]">{marketData.markets[0].data_source}</strong></p>
              </div>
              <p className="text-[10px] text-slate-500 italic">
                * Note: Illustrative current sale-value estimate based on current telemetry. Not a financial recommendation to sell.
              </p>
            </div>
          ) : (
            <div className="p-6 rounded-xl bg-slate-50 border border-slate-200 text-center text-xs text-[#526B60]">
              <AlertCircle className="w-6 h-6 text-slate-400 mx-auto mb-2" />
              Current sale-value estimate unavailable. Requires real mandi price telemetry and farm size inputs.
            </div>
          )}
        </div>

        {/* SUB-SECTION 5: STORE INFORMATION */}
        <div className="bg-white rounded-2xl p-6 border border-[#E2ECE6] shadow-sm space-y-4">
          <div className="flex items-center gap-2">
            <Warehouse className="w-5 h-5 text-[#059669]" />
            <h2 className="text-lg font-bold text-[#0F281E]">Store Information</h2>
          </div>

          {postHarvestData?.status === 'success' && postHarvestData?.post_harvest_profile ? (
            <div className="space-y-3 text-xs">
              <div className="grid grid-cols-2 gap-2">
                <div className="p-2.5 bg-[#F8FAF9] rounded-xl border border-[#E2ECE6]">
                  <span className="text-[#526B60] block text-[10px] font-medium">Storage Method</span>
                  <span className="font-bold text-[#0F281E]">
                    {postHarvestData.post_harvest_profile.storage_method || 'Dry Warehouse'}
                  </span>
                </div>
                <div className="p-2.5 bg-[#F8FAF9] rounded-xl border border-[#E2ECE6]">
                  <span className="text-[#526B60] block text-[10px] font-medium">Target Moisture</span>
                  <span className="font-bold text-[#0F281E]">
                    {postHarvestData.post_harvest_profile.optimal_moisture_pct}%
                  </span>
                </div>
                <div className="p-2.5 bg-[#F8FAF9] rounded-xl border border-[#E2ECE6]">
                  <span className="text-[#526B60] block text-[10px] font-medium">Shelf Life</span>
                  <span className="font-bold text-[#0F281E]">
                    {postHarvestData.post_harvest_profile.shelf_life_days} days
                  </span>
                </div>
                <div className="p-2.5 bg-[#F8FAF9] rounded-xl border border-[#E2ECE6]">
                  <span className="text-[#526B60] block text-[10px] font-medium">Perishability</span>
                  <span className="font-bold uppercase text-[#059669]">
                    {postHarvestData.post_harvest_profile.perishability}
                  </span>
                </div>
              </div>
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-[11px] text-[#526B60]">
                <p className="font-semibold text-[#0F281E] mb-1">Storage Risk & Handling:</p>
                <p>{postHarvestData.storage_advisory?.storage_risk}</p>
                <p className="mt-1">{postHarvestData.storage_advisory?.handling_notes}</p>
              </div>
              <p className="text-[10px] text-slate-500 italic">
                * Note: Storage details provided for guidance only. Storing does not guarantee a higher financial return.
              </p>
            </div>
          ) : (
            <div className="p-6 rounded-xl bg-slate-50 border border-slate-200 text-center text-xs text-[#526B60]">
              Storage information unavailable for this crop selection.
            </div>
          )}
        </div>

        {/* SUB-SECTION 6: HISTORICAL SEASONAL ANALYSIS (LIMITATION) */}
        <div className="bg-white rounded-2xl p-6 border border-[#E2ECE6] shadow-sm space-y-4">
          <div className="flex items-center gap-2">
            <Scale className="w-5 h-5 text-amber-600" />
            <h2 className="text-lg font-bold text-[#0F281E]">Historical Seasonal Analysis</h2>
          </div>

          <div className="p-5 rounded-xl bg-amber-50 border border-amber-200 space-y-3 text-xs">
            <div className="flex items-start gap-2 text-amber-900 font-bold text-sm">
              <ShieldAlert className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
              <span>Sell-vs-store financial comparison unavailable</span>
            </div>
            <p className="text-amber-800 leading-relaxed">
              Sell-vs-store financial comparison unavailable: historical monthly wholesale-price data is required to estimate future seasonal price movement.
            </p>
            <div className="pt-2 border-t border-amber-200/80 text-[11px] text-amber-900 space-y-1">
              <p>• <strong>Seasonal Price Index:</strong> Uncalculated (Awaiting verified multi-year monthly dataset)</p>
              <p>• <strong>Expected Price Movement:</strong> Unavailable</p>
              <p>• <strong>Storage-Adjusted Value:</strong> Unavailable</p>
            </div>
          </div>
        </div>

      </div>

      {/* SECTION 7: MULTI-CROP ECONOMIC COMPARISON (FACTUAL SIDE-BY-SIDE, NO RANKING) */}
      <div className="bg-white rounded-2xl p-6 border border-[#E2ECE6] shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h2 className="text-lg font-bold text-[#0F281E]">Multi-Crop Economic Comparison</h2>
            <p className="text-xs text-[#526B60]">
              Side-by-side factual economic benchmarks for selected crops (No speculative rankings or recommendations).
            </p>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {SUPPORTED_CROPS.slice(0, 10).map(c => {
              const selected = comparisonCrops.includes(c);
              return (
                <button
                  key={c}
                  onClick={() => toggleComparisonCrop(c)}
                  className={`px-2.5 py-1 rounded-lg text-xs font-semibold border transition ${
                    selected
                      ? 'bg-[#059669] text-white border-[#059669]'
                      : 'bg-white text-[#526B60] border-[#E2ECE6] hover:border-[#059669]'
                  }`}
                >
                  {c.split(' ')[0]}
                </button>
              );
            })}
          </div>
        </div>

        {loadingComparison ? (
          <div className="p-8 text-center text-[#526B60] font-medium animate-pulse">
            Computing comparison profiles...
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-[#F8FAF9] border-b border-[#E2ECE6] text-[#526B60] uppercase text-[10px] tracking-wider">
                  <th className="p-3 font-bold">Crop</th>
                  <th className="p-3 font-bold">Est. Production</th>
                  <th className="p-3 font-bold">Gross Revenue</th>
                  <th className="p-3 font-bold">Cultivation Cost (A2+FL)</th>
                  <th className="p-3 font-bold">Estimated Net Return</th>
                  <th className="p-3 font-bold">ROI %</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E2ECE6]">
                {comparisonResults.map((r: any, idx: number) => {
                  const m = r.economic_metrics || {};
                  return (
                    <tr key={idx} className="hover:bg-[#F0FDF4]/50 transition">
                      <td className="p-3 font-bold text-[#0F281E]">{r.crop}</td>
                      <td className="p-3">{m.production_quintals ? `${m.production_quintals} q` : 'N/A'}</td>
                      <td className="p-3">₹{m.gross_revenue_inr?.toLocaleString() || 'N/A'}</td>
                      <td className="p-3 text-rose-700 font-semibold">₹{m.total_cultivation_cost_inr?.toLocaleString() || 'N/A'}</td>
                      <td className="p-3 font-extrabold text-[#059669]">₹{m.estimated_net_return_inr?.toLocaleString() || 'N/A'}</td>
                      <td className="p-3 font-extrabold text-amber-900">{m.roi_pct ? `${m.roi_pct}%` : 'N/A'}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

    </div>
  );
};

export default Market;
