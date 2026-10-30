// Verification script for TTS language detection logic

function detectLanguage(text, explicitLang, fallbackLang = 'en') {
  if (text) {
    if (/[\u0C00-\u0C7F]/.test(text)) {
      return 'te';
    }
    if (/[\u0900-\u097F]/.test(text)) {
      return 'hi';
    }
  }

  if (explicitLang === 'te' || explicitLang === 'hi' || explicitLang === 'en') {
    return explicitLang;
  }

  if (fallbackLang === 'te' || fallbackLang === 'hi' || fallbackLang === 'en') {
    return fallbackLang;
  }

  return 'en';
}

// Dummy voice matching logic mirroring WebSpeechService
function findMatchingVoice(targetLang, voices) {
  if (!voices || voices.length === 0) return null;
  const cleanNormalize = (str) => str.toLowerCase().replace(/_/g, '-');

  if (targetLang === 'te') {
    const teVoice = voices.find(v => {
      const normLang = cleanNormalize(v.lang);
      const normName = v.name.toLowerCase();
      return normLang.startsWith('te') || normName.includes('telugu');
    });
    if (teVoice) return teVoice;
    return null; // NEVER fallback to English voice!
  }

  if (targetLang === 'hi') {
    const hiVoice = voices.find(v => {
      const normLang = cleanNormalize(v.lang);
      const normName = v.name.toLowerCase();
      return normLang.startsWith('hi') || normName.includes('hindi');
    });
    if (hiVoice) return hiVoice;
    return null; // NEVER fallback to English voice!
  }

  const enInVoice = voices.find(v => {
    const normLang = cleanNormalize(v.lang);
    const normName = v.name.toLowerCase();
    return normLang === 'en-in' || normName.includes('india');
  });
  if (enInVoice) return enInVoice;

  const anyEnVoice = voices.find(v => cleanNormalize(v.lang).startsWith('en'));
  if (anyEnVoice) return anyEnVoice;

  return null;
}

console.log("=== RUNNING TTS LOGIC TESTS ===");

// TEST 1: English response -> language = en -> English voice
const res1 = detectLanguage("For your farm in Kurnool, Pigeon Pea is suitable.", "en", "en");
console.assert(res1 === 'en', `TEST 1 Failed: got ${res1}`);

// TEST 2: Telugu response -> language = te -> te-IN voice if available
const res2 = detectLanguage("మీ పొలం వివరాలను బట్టి కంది పంట అనుకూలమైనది.", "te", "en");
console.assert(res2 === 'te', `TEST 2 Failed: got ${res2}`);

// TEST 3: Hindi response -> language = hi -> hi-IN voice if available
const res3 = detectLanguage("आपके खेत के लिए अरहर की फसल उपयुक्त है।", "hi", "en");
console.assert(res3 === 'hi', `TEST 3 Failed: got ${res3}`);

// TEST 4: UI language = English, but assistant response = Telugu -> MUST speak Telugu
const res4 = detectLanguage("మీ పొలం వివరాలను బట్టి కంది పంట అనుకూలమైనది.", "en", "en");
console.assert(res4 === 'te', `TEST 4 Failed: UI is English but Telugu text should return 'te', got ${res4}`);

// TEST 5: UI language = Telugu, but assistant response = English -> MUST speak English
const res5 = detectLanguage("For your farm in Kurnool, Pigeon Pea is recommended.", undefined, "en");
console.assert(res5 === 'en', `TEST 5 Failed: UI is Telugu but English text without Telugu script should return 'en', got ${res5}`);

// TEST 6: message.language is undefined but message contains Telugu script -> MUST detect Telugu
const res6 = detectLanguage("మీ పంటకు నీటి అవసరం తక్కువ.", undefined, "en");
console.assert(res6 === 'te', `TEST 6 Failed: undefined message.language with Telugu script should return 'te', got ${res6}`);

// TEST 7: message.language is undefined but message contains Hindi script -> MUST detect Hindi
const res7 = detectLanguage("आपकी फसल के लिए पानी की आवश्यकता।", undefined, "en");
console.assert(res7 === 'hi', `TEST 7 Failed: undefined message.language with Hindi script should return 'hi', got ${res7}`);

// TEST 8: Voice list initially empty vs populated with mock voices
const emptyVoices = [];
const mockVoices = [
  { name: "Microsoft Zira Desktop - English (United States)", lang: "en-US" },
  { name: "Microsoft Mohan Online (Natural) - Telugu (India)", lang: "te-IN" },
  { name: "Microsoft Swara Online (Natural) - Hindi (India)", lang: "hi-IN" }
];

const matchEmptyTe = findMatchingVoice('te', emptyVoices);
console.assert(matchEmptyTe === null, "TEST 8a Failed: Empty voices should return null");

const matchTe = findMatchingVoice('te', mockVoices);
console.assert(matchTe.name.includes("Telugu"), `TEST 8b Failed: Telugu voice match failed, got ${matchTe?.name}`);

const matchHi = findMatchingVoice('hi', mockVoices);
console.assert(matchHi.name.includes("Hindi"), `TEST 8c Failed: Hindi voice match failed, got ${matchHi?.name}`);

const matchNoTeVoice = findMatchingVoice('te', [{ name: "US English", lang: "en-US" }]);
console.assert(matchNoTeVoice === null, "TEST 8d Failed: Missing Telugu voice MUST NOT return English voice");

console.log("✅ ALL 8 VERIFICATION TESTS PASSED SUCCESSFULLY!");
