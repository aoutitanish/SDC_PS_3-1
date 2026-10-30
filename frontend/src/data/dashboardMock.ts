export interface ConsultationItem {
  id: string;
  title: string;
  category: 'Crops' | 'Soil' | 'Weather' | 'General';
  date: string;
  preview: string;
  cropCount?: number;
}

export const INITIAL_CONSULTATIONS: ConsultationItem[] = [
  {
    id: 'consult_1',
    title: 'Compare the top recommended crops',
    category: 'Crops',
    date: '10 mins ago',
    preview: 'Multi-factor comparison of Cotton, Arhar/Tur, and Groundnut for 4 acres black soil.',
    cropCount: 3
  },
  {
    id: 'consult_2',
    title: 'Benefits of drip irrigation',
    category: 'Crops',
    date: '2 hours ago',
    preview: 'Water efficiency analysis for borewell setup in Warangal.',
  },
  {
    id: 'consult_3',
    title: 'Which crop suits black soil?',
    category: 'Soil',
    date: 'Yesterday',
    preview: 'SoilGrids clay content 32.6% compatibility analysis.',
  },
  {
    id: 'consult_4',
    title: 'My farm is 4 acres in Warangal',
    category: 'General',
    date: '2 days ago',
    preview: 'Initial farm profile setup and geographic baseline.',
  },
  {
    id: 'consult_5',
    title: 'Suitable crops for the Kharif season',
    category: 'Crops',
    date: '3 days ago',
    preview: 'Monsoon onset and seasonal thermal normal recommendations.',
    cropCount: 4
  },
  {
    id: 'consult_6',
    title: 'Crop and soil advisory',
    category: 'Soil',
    date: '5 days ago',
    preview: 'Soil pH 7.1 and nitrogen fertility status review.',
  }
];

export interface CropSummary {
  name: string;
  teluguName?: string;
  hindiName?: string;
  agronomicScore: number;
  confidence: 'High' | 'Medium' | 'Low';
  waterRequirement: string;
  benchmarkYield: string;
  bestFit: string;
  isTopRecommendation?: boolean;
  category: string;
  soilSuitability: string;
  rainfallFit: string;
  thermalRange: string;
  dripFit: string;
  advantage: string;
  caution: string;
}

export const TOP_RECOMMENDED_CROPS: CropSummary[] = [
  {
    name: 'Cotton',
    teluguName: 'ప్రత్తి',
    hindiName: 'कपास',
    agronomicScore: 94.8,
    confidence: 'High',
    waterRequirement: 'Moderate, 650–900 mm',
    benchmarkYield: '2.07 t/ha',
    bestFit: 'Black soil and warm temperatures',
    isTopRecommendation: true,
    category: 'Commercial / Fiber',
    soilSuitability: '99.3% (23.6–40.5% clay, pH 5.5–7.8)',
    rainfallFit: '94.9% (~482–2386 mm)',
    thermalRange: '23.8–27.6°C',
    dripFit: 'Optimal (40-50% water savings)',
    advantage: 'Highest benchmark yield & strong market value under drip',
    caution: 'Monitor bollworm, sucking pests & timely nutrient scheduling'
  },
  {
    name: 'Arhar / Tur (Pigeon Pea)',
    teluguName: 'కంది',
    hindiName: 'अरहर / तूर',
    agronomicScore: 94.3,
    confidence: 'High',
    waterRequirement: 'Low to moderate, 400–650 mm',
    benchmarkYield: '0.8 t/ha',
    bestFit: 'Black soil and moderate rainfall',
    category: 'Pulses / Legumes',
    soilSuitability: '98.9% (23.5–39.9% clay, pH 5.6–7.6)',
    rainfallFit: '95.7% (~502–2045 mm)',
    thermalRange: '23.9–27.2°C',
    dripFit: 'Optimal',
    advantage: 'High atmospheric nitrogen fixation & drought tolerance',
    caution: 'Monitor pod borer during flowering; avoid prolonged standing water'
  },
  {
    name: 'Groundnut',
    teluguName: 'వేరుశనగ',
    hindiName: 'मूंगफली',
    agronomicScore: 94.2,
    confidence: 'High',
    waterRequirement: 'Low to moderate, 400–650 mm',
    benchmarkYield: '1.21 t/ha',
    bestFit: 'Well-drained soil and suitable rainfall',
    category: 'Oilseeds',
    soilSuitability: '99.5% (23.9–40.4% clay, pH 6.0–7.4)',
    rainfallFit: '93.3% (~729–2045 mm)',
    thermalRange: '24.2–27.5°C',
    dripFit: 'Optimal',
    advantage: 'Strong soil compatibility & quick cash-flow crop cycle',
    caution: 'Apply gypsum at flowering; ensure loose soil for peg penetration'
  }
];

export interface NextActionItem {
  id: string;
  title: string;
  description: string;
  iconName: string;
  type: 'market' | 'seed' | 'soil' | 'weather' | 'scheme';
  badge?: string;
}

export const RECOMMENDED_NEXT_ACTIONS: NextActionItem[] = [
  {
    id: 'act_1',
    title: 'Review current market prices',
    description: 'Cotton APMC Warangal: ₹7,450/quintal (Strong demand)',
    iconName: 'TrendingUp',
    type: 'market',
    badge: 'Live APMC'
  },
  {
    id: 'act_2',
    title: 'Check certified seed availability',
    description: 'Bt-II Cotton & PRG-158 Arhar stock in local Rythu Vedika',
    iconName: 'PackageCheck',
    type: 'seed',
    badge: 'In Stock'
  },
  {
    id: 'act_3',
    title: 'Schedule soil nutrient test',
    description: 'Verify available Nitrogen & Phosphorus before sowing',
    iconName: 'FlaskConical',
    type: 'soil'
  },
  {
    id: 'act_4',
    title: 'Monitor rainfall forecast',
    description: 'Light showers (12mm) expected over next 48 hours',
    iconName: 'CloudRain',
    type: 'weather',
    badge: 'Kharif Normal'
  },
  {
    id: 'act_5',
    title: 'Compare crop insurance schemes',
    description: 'PMFBY Kharif enrollment deadline approaching',
    iconName: 'ShieldCheck',
    type: 'scheme'
  }
];
