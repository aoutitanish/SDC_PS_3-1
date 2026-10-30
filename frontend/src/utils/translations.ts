import { LanguageCode } from '../types';

export interface TranslationDictionary {
  appName: string;
  tagline: string;
  navHome: string;
  navChat: string;
  navRecommend: string;
  navSoil: string;
  navWeather: string;
  navCrops: string;
  navFarm: string;
  navAdmin: string;
  navSettings: string;
  heroHeadline: string;
  heroSubtitle: string;
  startChatting: string;
  getCropRec: string;
  quickPromptsTitle: string;
  chatPlaceholder: string;
  send: string;
  listening: string;
  listenToAudio: string;
  stopAudio: string;
  whyThisRec: string;
  suitabilityBreakdown: string;
  supportingFactors: string[];
  limitationsTitle: string;
  confidenceTitle: string;
  alternativeCropsTitle: string;
  sourcesTitle: string;
  viewSources: string;
  soilAnalysisTitle: string;
  analyzeSoilBtn: string;
  weatherAdvisoryTitle: string;
  myFarmTitle: string;
  saveProfile: string;
  selectState: string;
  selectDistrict: string;
  selectSoilType: string;
  guestUser: string;
  offlineNotice: string;
}

export const translations: Record<LanguageCode, TranslationDictionary> = {
  en: {
    appName: "KrishiMitra AI",
    tagline: "Explainable Smart Agriculture Assistant",
    navHome: "Home",
    navChat: "AI Assistant",
    navRecommend: "Crop Recommend",
    navSoil: "Soil Analysis",
    navWeather: "Weather & Agro",
    navCrops: "Crop Explorer",
    navFarm: "My Farm",
    navAdmin: "Admin Health",
    navSettings: "Settings",
    heroHeadline: "Smarter Decisions for Better Farming.",
    heroSubtitle: "Explainable AI-powered agricultural guidance grounded in soil, weather, crop agronomy, and location datasets.",
    startChatting: "Ask KrishiMitra",
    getCropRec: "Get Crop Recommendation",
    quickPromptsTitle: "Quick Agricultural Questions",
    chatPlaceholder: "Ask anything about crops, soil, weather, pests, or schemes...",
    send: "Send",
    listening: "Listening to your voice...",
    listenToAudio: "Listen Aloud",
    stopAudio: "Stop Audio",
    whyThisRec: "Why this recommendation?",
    suitabilityBreakdown: "Agronomic Suitability Breakdown",
    supportingFactors: ["Optimal soil conditions", "Compatible rainfall", "Suitable temperature range", "Nutrient alignment"],
    limitationsTitle: "Potential Considerations & Risks",
    confidenceTitle: "Confidence Level",
    alternativeCropsTitle: "Alternative Recommended Crops",
    sourcesTitle: "Verified Agricultural Sources",
    viewSources: "View Citations",
    soilAnalysisTitle: "Soil Health & Nutrient Assessment",
    analyzeSoilBtn: "Analyze Soil Health",
    weatherAdvisoryTitle: "Live Weather & Agro-Advisory",
    myFarmTitle: "My Farm Profile",
    saveProfile: "Save Farm Profile",
    selectState: "Select State",
    selectDistrict: "Select District",
    selectSoilType: "Select Soil Type",
    guestUser: "Guest Farmer",
    offlineNotice: "You are currently offline. Displaying cached agricultural benchmarks."
  },
  te: {
    appName: "కృషిమిత్ర AI",
    tagline: "వివరణాత్మక స్మార్ట్ వ్యవసాయ సహాయకుడు",
    navHome: "హోమ్",
    navChat: "AI సహాయకుడు",
    navRecommend: "పంట సిఫార్సు",
    navSoil: "నేల విశ్లేషణ",
    navWeather: "వాతావరణం",
    navCrops: "పంటల సమాచారం",
    navFarm: "నా పొలం",
    navAdmin: "సిస్టమ్ స్టేటస్",
    navSettings: "సెట్టింగులు",
    heroHeadline: "మెరుగైన వ్యవసాయం కోసం శాస్త్రీయ నిర్ణయాలు.",
    heroSubtitle: "నేల రకం, వర్షపాతం, ఉష్ణోగ్రత మరియు పంట సమాచారంతో పనిచేసే తెలివైన AI వ్యవసాయ సహాయకుడు.",
    startChatting: "కృషిమిత్రను అడగండి",
    getCropRec: "పంట సిఫార్సు పొందండి",
    quickPromptsTitle: "త్వరిత ప్రశ్నలు",
    chatPlaceholder: "పంటలు, నేల, వాతావరణం లేదా ఎరువుల గురించి అడగండి...",
    send: "పంపండి",
    listening: "మీ వాయిస్ వింటోంది...",
    listenToAudio: "వినండి",
    stopAudio: "ఆపండి",
    whyThisRec: "ఈ సిఫార్సు ఎందుకు?",
    suitabilityBreakdown: "నేల & వాతావరణ అనుకూలత కొలమానాలు",
    supportingFactors: ["అనుకూల నేల లక్షణాలు", "తగినంత వర్షపాతం", "సరిపడే ఉష్ణోగ్రత", "పోషక సమతుల్యత"],
    limitationsTitle: "గమనించవలసిన జాగ్రత్తలు & సూచనలు",
    confidenceTitle: "ఖచ్చితత్వ స్థాయి",
    alternativeCropsTitle: "ప్రత్యామ్నాయ పంటలు",
    sourcesTitle: "ప్రమాణిక సమాచార వనరులు",
    viewSources: "వనరులు చూడండి",
    soilAnalysisTitle: "నేల పరీక్ష & పోషకాల విశ్లేషణ",
    analyzeSoilBtn: "నేల ఆరోగ్యం విశ్లేషించండి",
    weatherAdvisoryTitle: "వాతావరణం & వ్యవసాయ సలహాలు",
    myFarmTitle: "నా పొలం వివరాలు",
    saveProfile: "వివరాలు భద్రపరచండి",
    selectState: "రాష్ట్రాన్ని ఎంచుకోండి",
    selectDistrict: "జిల్లాను ఎంచుకోండి",
    selectSoilType: "నేల రకాన్ని ఎంచుకోండి",
    guestUser: "రైతు మిత్రుడు (అతిథి)",
    offlineNotice: "మీరు ఆఫ్‌లైన్‌లో ఉన్నారు. సేవ్ చేసిన సమాచారం చూపిస్తున్నాము."
  },
  hi: {
    appName: "कृषिमित्र AI",
    tagline: "व्याख्यात्मक स्मार्ट कृषि सहायक",
    navHome: "होम",
    navChat: "AI सहायक",
    navRecommend: "फसल सिफारिश",
    navSoil: "मृदा परीक्षण",
    navWeather: "मौसम व सलाह",
    navCrops: "फसल ज्ञानकोश",
    navFarm: "मेरा खेत",
    navAdmin: "सिस्टम स्वास्थ्य",
    navSettings: "सेटिंग्स",
    heroHeadline: "उन्नत खेती के लिए सही और सटीक निर्णय।",
    heroSubtitle: "मिट्टी, वर्षा, तापमान और फसल विज्ञान पर आधारित व्याख्यात्मक AI कृषि मार्गदर्शक।",
    startChatting: "कृषिमित्र से पूछें",
    getCropRec: "फसल सिफारिश प्राप्त करें",
    quickPromptsTitle: "महत्वपूर्ण कृषि प्रश्न",
    chatPlaceholder: "फसल, मिट्टी, मौसम, खाद या योजनाओं के बारे में पूछें...",
    send: "भेजें",
    listening: "आपकी आवाज सुन रहे हैं...",
    listenToAudio: "आवाज सुनें",
    stopAudio: "आवाज बंद करें",
    whyThisRec: "यह सिफारिश क्यों की गई?",
    suitabilityBreakdown: "कृषि उपयुक्तता कारक विश्लेषण",
    supportingFactors: ["अनुकूल मिट्टी संरचना", "पर्याप्त वर्षा", "उपयुक्त तापमान", "पोषक तत्व संतुलन"],
    limitationsTitle: "सावधानियां व जोखिम प्रबंधन",
    confidenceTitle: "विश्वसनीयता स्तर",
    alternativeCropsTitle: "वैकल्पिक अनुशंसित फसलें",
    sourcesTitle: "प्रमाणित डेटा स्रोत",
    viewSources: "स्रोत देखें",
    soilAnalysisTitle: "मृदा स्वास्थ्य व पोषक तत्व विश्लेषण",
    analyzeSoilBtn: "मृदा विश्लेषण करें",
    weatherAdvisoryTitle: "लाइव मौसम व कृषि सलाह",
    myFarmTitle: "मेरे खेत का विवरण",
    saveProfile: "प्रोफ़ाइल सहेजें",
    selectState: "राज्य चुनें",
    selectDistrict: "जिला चुनें",
    selectSoilType: "मिट्टी का प्रकार चुनें",
    guestUser: "किसान मित्र (अतिथि)",
    offlineNotice: "आप वर्तमान में ऑफ़लाइन हैं। सहेजा गया डेटा दिखाया जा रहा है।"
  }
};
